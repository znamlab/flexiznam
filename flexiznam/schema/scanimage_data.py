import datetime
import os
import pathlib
import re

import pandas as pd
from flexiznam.schema.datasets import Dataset


class ScanimageData(Dataset):
    DATASET_TYPE = 'scanimage'

    @staticmethod
    def from_folder(folder, verbose=True, mouse=None, session=None, recording=None):
        """Create a scanimage dataset by loading info from folder"""
        fnames = [f for f in os.listdir(folder) if f.endswith(('.csv', '.tiff', '.tif'))]
        tif_files = [f for f in fnames if f.endswith(('.tif', '.tiff'))]
        csv_files = [f for f in fnames if f.endswith('.csv')]
        if not tif_files:
            raise IOError('Cannot find any tif file')

        # scanimage files finish with _acqnum_filenum.tif. All files with the same filename until acqnum are grouped
        # together
        pattern = '(.*)_(\d*)_(\d*).tiff?'
        matches = [re.match(pattern, f) for f in tif_files]
        if verbose:
            non_si_tiff = {f for f, m in zip(tif_files, matches) if not m}
            if non_si_tiff:
                print('Found %d tif files that are NOT scanimage data.' % len(non_si_tiff))
                for s in non_si_tiff:
                    print('    %s' % s)
        tif_df = [dict(filename=f, fname=m.groups()[0], acq_num=m.groups()[1], file_num=m.groups()[2])
                  for f, m in zip(tif_files, matches) if m]
        tif_df = pd.DataFrame(tif_df)
        tif_df['acq_identifier'] = tif_df.fname + tif_df.acq_num

        output = {}
        matched_csv = set()
        for acq_id, acq_df in tif_df.groupby('acq_identifier'):
            # find if there is any corresponding csv
            fname = acq_df.fname.iloc[0]
            acq_num = acq_df.acq_num.iloc[0]
            associated_csv = {f for f in csv_files if f.startswith(fname) and f.endswith(acq_num + '.csv')}
            if associated_csv in matched_csv:
                raise IOError('A csv file matched with 2 scanimage tif datasets')
            matched_csv.update(associated_csv)
            associated_csv = {f[len(fname):-(len(acq_num) + 4)].strip('_'): f for f in associated_csv}

            example_tif = pathlib.Path(folder) / acq_df.filename.iloc[0]
            created = datetime.datetime.fromtimestamp(example_tif.stat().st_mtime)
            output[acq_id] = ScanimageData(path=folder,
                                           tif_files=list(acq_df.filename.values),
                                           csv_files=associated_csv,
                                           created=created.strftime('%Y-%m-%d %H:%M:%S'))
            for field in ('mouse', 'session', 'recording'):
                setattr(output[acq_id], field, locals()[field])
            output[acq_id].dataset_name = acq_id

        if verbose:
            unmatched = set(csv_files) - matched_csv
            if unmatched and verbose:
                print('%d csv files did not match any scanimage acquisition:' % len(unmatched))
                for m in unmatched:
                    print('    %s' % m)
        return output

    def from_flexilims(project=None, name=None, data_series=None):
        """Create a camera dataset from flexilims entry"""
        raise NotImplementedError

    def __init__(self, path, name=None, tif_files=None, csv_files={}, extra_attributes={}, created=None, project=None,
                 is_raw=True, si_acquisition_name=None):
        """Create a Scanimage dataset

        Args:
            name: Identifier. Unique name on flexilims. When imported from folder, default to the acquisition name
            path: Path to the folder containing all the files
            tif_files: List of file names associated with this dataset
            csv_files: Dictionary of csv files associated to the binary file. Keys are identifier provided for
                       convenience, values are the full file name
            extra_attributes: Other optional attributes (from or for flexilims)
            created: Date of creation. Default to the creation date of a tif file
            project: name of hexadecimal id of the project to which the dataset belongs
            is_raw: default to True. Is it processed data or raw data?
            si_acquisition_name: name of the acquisition in si if different from name
        """
        super().__init__(name=name, path=path, is_raw=is_raw, dataset_type=ScanimageData.DATASET_TYPE,
                         extra_attributes=extra_attributes, created=created, project=project)
        self.csv_files = csv_files
        if si_acquisition_name is None:
            self.si_acquisition_name = self.name
        else:
            self.si_acquisition_name = str(si_acquisition_name)
        self.tif_files = tif_files


    @property
    def tif_files(self):
        """List of tif files, sorted alphabetically (automatically)"""
        return self._tif_files

    @tif_files.setter
    def tif_files(self, value):
        if value is None:
            self._tif_files = None
            return
        if isinstance(value, str):
            value = [value]
        value = list(sorted(value))
        if not self.is_valid(tif_files=value):
            raise IOError('One or more file do not exist. Set self._tif_files if you want to skip check')
        self._tif_files = value

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

    def format(self, mode='flexilims'):
        """Format a dataset

        This can generate either a 'flexilims' type of output (a series similar to get_entities output) or a 'yaml'
        type as that used by flexiznam.camp

        The flexilims series will not include elements that are not used by the Dataset class such as created_by

        Args:
            mode: 'flexilims' or 'yaml'
        """
        formatted = Dataset.format(self, mode=mode)
        formatted['si_acquisition_name'] = self.si_acquisition_name
        return formatted

    def __len__(self):
        """Number of tif files in the dataset"""
        return len(self.tif_files)
