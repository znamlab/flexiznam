import datetime
import os
import pathlib
import re
import pandas as pd
from tifffile import TiffFile, TiffFileError
from flexiznam.schema.datasets import Dataset
import math

class ScanimageData(Dataset):
    DATASET_TYPE = 'scanimage'

    @staticmethod
    def from_folder(folder, verbose=True, mouse=None, session=None, recording=None,
                    flm_session=None, project=None):
        """Create a scanimage dataset by loading info from folder"""
        folder = pathlib.Path(folder)
        assert folder.is_dir()
        fnames = [f for f in os.listdir(folder) if f.endswith(('.csv', '.tiff', '.tif'))]
        tif_files = [f for f in fnames if f.endswith(('.tif', '.tiff'))]
        csv_files = [f for f in fnames if f.endswith('.csv')]
        if not tif_files:
            raise IOError('Cannot find any tif file')

        # find SI files and group them by acquisition
        si_df = {}
        non_si_tiff = []
        while len(tif_files) > 0:
            # find valid tiff by running ScanImageTiffReader
            fname = tif_files[0]
            parsed_name = parse_si_filename(folder / fname)
            if parsed_name is None:
                # could not read metadata, that is not a SI tif
                non_si_tiff.append(fname)
                tif_files.remove(fname)
                continue
            # We have a SI file, remove all files from this acquisition from the tif list
            this_acq = [t for t in tif_files if t.startswith(parsed_name['acq_uid'])]
            # remove matched files to not re-read metadata
            for file in this_acq:
                tif_files.remove(file)
            parsed_name['file_list'] = this_acq
            si_df[parsed_name['acq_uid']] = parsed_name
        if verbose:
            if non_si_tiff:
                print('Found %d tif files that are NOT scanimage data.' %
                      len(non_si_tiff))
                for s in non_si_tiff:
                    print('    %s' % s)

        # Process all acquisition sequentially
        output = {}
        matched_csv = set()
        for acq_id, acq in si_df.items():
            # Find associated CSV files
            associated_csv = {f for f in csv_files if f.startswith(acq['file_stem']) and
                              f.endswith(acq['acq_num'] + '.csv')}
            if associated_csv in matched_csv:
                raise IOError('A csv file matched with 2 scanimage tif datasets')
            matched_csv.update(associated_csv)
            # rename the csv key to keep only the new info:
            associated_csv = {f[len(acq['file_stem']): -(len(acq['acq_num']) + 4)].strip(
                '_'): f for f in associated_csv}

            # get creation date from one tif
            first_acq_tif = folder / sorted(acq['file_list'])[0]
            created = datetime.datetime.fromtimestamp(first_acq_tif.stat().st_mtime)
            extra_attributes = dict(acq)
            # remove file specific fields
            for field in ['file_num', 'channel']:
                extra_attributes.pop(field, None)
            extra_attributes.update(csv_files=associated_csv)

            output[acq_id] = ScanimageData(path=folder,
                                           extra_attributes=extra_attributes,
                                           created=created.strftime('%Y-%m-%d %H:%M:%S'),
                                           flm_session=flm_session,
                                           project=project)
            for field in ('mouse', 'session', 'recording'):
                setattr(output[acq_id], field, locals()[field])
            output[acq_id].dataset_name = acq_id

        if verbose:
            unmatched = set(csv_files) - matched_csv
            if unmatched and verbose:
                print('%d csv files did not match any scanimage acquisition:' % len(
                    unmatched))
                for m in unmatched:
                    print('    %s' % m)
        return output

    def __init__(self, path, name=None, tif_files=None, csv_files=None,
                 extra_attributes=None, created=None, project=None, is_raw=True,
                 origin_id=None, flm_session=None, project_id=None):
        """Create a Scanimage dataset

        Args:
            name: Identifier. Unique name on flexilims. When imported from folder,
                  default to the acquisition name
            path: Path to the folder containing all the files
            extra_attributes: Other optional attributes (from or for flexilims)
            created: Date of creation. Default to the creation date of a tif file
            project: name of hexadecimal id of the project to which the dataset belongs
            is_raw: default to True. Is it processed data or raw data?
            origin_id: hexadecimal code for the origin on flexilims.
            flm_session: authentication session for connecting to flexilims

        Expected extra_attributes:
            tif_files (optional): List of file names associated with this dataset
            csv_files (optional): Dictionary of csv files associated to the scanimage
                                  recording file. Keys are identifier provided for
                                  convenience, values are the full file name

        """
        super().__init__(name=name, path=path, is_raw=is_raw,
                         dataset_type=ScanimageData.DATASET_TYPE,
                         extra_attributes=extra_attributes, created=created,
                         project=project, flm_session=flm_session,
                         origin_id=origin_id,
                         project_id=project_id)

    @property
    def csv_files(self):
        """List of csv files"""
        return self.extra_attributes['csv_files']

    @csv_files.setter
    def csv_files(self, value):
        self.extra_attributes['csv_files'] = value

    @property
    def tif_files(self):
        """List of tif files

        Tif files are sorted alphabetically automatically done when setting this property
        """
        return self.extra_attributes['tif_files']

    @tif_files.setter
    def tif_files(self, value):
        if value is None:
            self.extra_attributes['tif_files'] = None
            return
        if isinstance(value, str):
            value = [value]
        value = list(sorted(value))
        if not self.is_valid(tif_files=value):
            raise IOError('One or more file do not exist. Set self._tif_files if you want'
                          ' to skip check')
        self.extra_attributes['tif_files'] = value

    def is_valid(self, tif_files=None):
        """Check that associated files exist"""
        if tif_files is None:
            tif_files = self.tif_files
        # checking file one by one is long, compare sets
        tif_files = set(tif_files)
        existing_file = {f for f in os.listdir(self.path) if f.endswith(('tif', '.tiff'))}
        if tif_files - existing_file:
            return False
        for _, file_path in self.csv_files.items():
            if not (pathlib.Path(self.path) / file_path).exists():
                return False
        return True

    def __len__(self):
        """Number of tif files in the dataset"""
        return len(self.tif_files)


def parse_si_filename(path2file):
    """Parse the filename of a SI tif using metadata

    SI file names are created like that:
    fileName = '_'.join([file_stem, acq_num, file_num, channel, extension])

    - file_stem is the string entered in the SI acq windows and is always present.
    - acq_num is the acquisition number, in the form of 5 digit ('000001' for instance)
      and is always present.
    - file_num is formatted like acq_num but is present only if the number of frame per
      file is not infinite (if obj.hLinScan.logFramesPerFile is not inf)
    - channel if 'chanX' and present only if we save multiple channels in different files
    - extension is always '.tif'

    This function reads the metadata and returns the individual elements of the
    filename. It returns None if path2file is not a scanimage tif file

    Args:
        path2file (str or pathlib.Path): the path to a scanimage tif file

    Returns:
        a dictionary with the defined part of the file name or None

    """

    path2file = pathlib.Path(path2file)
    fname = path2file.stem + path2file.suffix
    try:
        with TiffFile(str(path2file)) as reader:
            if not reader.is_scanimage:
                return None
            else:
                mdata = reader.scanimage_metadata
    except TiffFileError:
        return None

    # find if there are multiple files (i.e. frame per file is not inf)
    try:
        frames_per_file = mdata['FrameData']['SI.hScan2D.logFramesPerFile']
    except KeyError:
        raise IOError('Could not find logFramesPerFile in metadata of %s' % fname)
    if math.isfinite(frames_per_file):
        pattern = '(.*)_(\d*)_(\d*)(.*).tiff?'
    else:
        pattern = '(.*)_(\d*)(.*).tiff?'
    parsed_name = re.match(pattern, fname)
    if parsed_name is None:
        raise IOError('Cannot parse file name %s with expected pattern %s' % (fname,
                                                                              pattern))
    stem = parsed_name.groups()[0]
    acq_num = parsed_name.groups()[1]
    acq_uid = '_'.join([stem, acq_num])
    out = dict(file_stem=stem, acq_num=acq_num, acq_uid=acq_uid)
    if math.isfinite(frames_per_file):
        out['file_num'] = parsed_name.groups()[2]
    if parsed_name.groups()[-1]:
        out['channel'] = parsed_name.groups()[-1]
    return out
