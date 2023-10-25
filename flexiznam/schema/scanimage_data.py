import datetime
import os
import pathlib
import re
import warnings

from tifffile import TiffFile, TiffFileError
from flexiznam.schema.datasets import Dataset
import math


class ScanimageData(Dataset):
    DATASET_TYPE = "scanimage"
    DEFAULT_STACK_TYPE = "calcium"

    @staticmethod
    def from_folder(
        folder,
        folder_genealogy=None,
        is_raw=None,
        verbose=True,
        flexilims_session=None,
        project=None,
    ):
        """Create a scanimage dataset by loading info from folder

        Args:
            folder (str): path to the folder
            folder_genealogy (tuple): genealogy of the folder, if None assume that
                                      the genealogy is just (folder,), i.e. no parents
            is_raw (bool): does this folder contain raw data?
            verbose (bool=True): print info about what is found
            flexilims_session (flm.Session): session to interact with flexilims
            project (str): project ID or name

        Returns:
            dist of datasets (fzm.schema.scanimage_data.ScanimageData)
        """
        folder = pathlib.Path(folder)
        assert folder.is_dir()

        if folder_genealogy is None:
            folder_genealogy = (pathlib.Path(folder).stem,)
        elif isinstance(folder_genealogy, list):
            folder_genealogy = tuple(folder_genealogy)

        fnames = [
            f for f in os.listdir(folder) if f.endswith((".csv", ".tiff", ".tif"))
        ]
        tif_files = [f for f in fnames if f.endswith((".tif", ".tiff"))]
        csv_files = [f for f in fnames if f.endswith(".csv")]
        if not tif_files:
            raise IOError("Cannot find any tif file")

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
            this_acq = [t for t in tif_files if t.startswith(parsed_name["acq_uid"])]
            # remove matched files to not re-read metadata
            for file in this_acq:
                tif_files.remove(file)
            parsed_name["tif_files"] = this_acq
            si_df[parsed_name["acq_uid"]] = parsed_name
        if verbose:
            if non_si_tiff:
                print(
                    "Found %d tif files that are NOT scanimage data." % len(non_si_tiff)
                )
                for s in non_si_tiff:
                    print("    %s" % s)

        # Process all acquisition sequentially
        output = {}
        matched_csv = set()
        for acq_id, acq in si_df.items():
            # Find associated CSV files
            associated_csv = {
                f
                for f in csv_files
                if f.startswith(acq["file_stem"])
                and f.endswith(acq["acq_num"] + ".csv")
            }
            if associated_csv in matched_csv:
                raise IOError("A csv file matched with 2 scanimage tif datasets")
            matched_csv.update(associated_csv)
            # rename the csv key to keep only the new info:
            associated_csv = {
                f[len(acq["file_stem"]) : -(len(acq["acq_num"]) + 4)].strip("_"): f
                for f in associated_csv
            }

            # get creation date from one tif
            first_acq_tif = folder / sorted(acq["tif_files"])[0]
            created = datetime.datetime.fromtimestamp(first_acq_tif.stat().st_mtime)
            extra_attributes = dict(acq)
            # remove file specific fields
            for field in ["file_num", "channel"]:
                extra_attributes.pop(field, None)
            extra_attributes.update(csv_files=associated_csv)
            genealogy = folder_genealogy + (acq_id,)
            output[acq_id] = ScanimageData(
                path=folder,
                genealogy=genealogy,
                is_raw=is_raw,
                extra_attributes=extra_attributes,
                created=created.strftime("%Y-%m-%d %H:%M:%S"),
                flexilims_session=flexilims_session,
                project=project,
            )

        if verbose:
            unmatched = set(csv_files) - matched_csv
            if unmatched and verbose:
                print(
                    "%d csv files did not match any scanimage acquisition:"
                    % len(unmatched)
                )
                for m in unmatched:
                    print("    %s" % m)
        return output

    def __init__(
        self,
        path,
        is_raw=None,
        genealogy=None,
        extra_attributes=None,
        created=None,
        project=None,
        project_id=None,
        origin_id=None,
        id=None,
        flexilims_session=None,
    ):
        """Create a ScanImage dataset

        Args:
            path: folder containing the dataset or path to file (valid only for single
                  file datasets)
            is_raw: bool, used to sort in raw and processed subfolders
            genealogy (tuple): parents of this dataset from the project (excluded) down to
                               the dataset name itself (included)
            extra_attributes: dict, optional attributes.
            created: Creation date, in "YYYY-MM-DD HH:mm:SS"
            project: name of the project. Must be in config, can be guessed from
                     project_id
            project_id: hexadecimal code for the project. Must be in config, can be
                        guessed from project
            origin_id: hexadecimal code for the origin on flexilims.
            id: hexadecimal code for the dataset on flexilims.
            flexilims_session: authentication session to connect to flexilims

        Expected extra_attributes:
            tif_files (optional): List of file names associated with this dataset
            csv_files (optional): Dictionary of csv files associated to the scanimage
                                  recording file. Keys are identifier provided for
                                  convenience, values are the full file name
            stack_type (optional): Type of scanimage type. Expected values are in:
                                   'calcium', 'zstack', 'multichannel-reference',
                                   'motion-reference, 'overview'
        """
        if "stack_type" not in extra_attributes:
            warnings.warn(
                "No `stack_type` provided for SI dataset %s. "
                "Set to default: %s" % (genealogy, self.DEFAULT_STACK_TYPE),
                stacklevel=2,
            )
            extra_attributes["stack_type"] = self.DEFAULT_STACK_TYPE

        super().__init__(
            genealogy=genealogy,
            path=path,
            is_raw=is_raw,
            dataset_type=ScanimageData.DATASET_TYPE,
            extra_attributes=extra_attributes,
            created=created,
            project=project,
            flexilims_session=flexilims_session,
            origin_id=origin_id,
            id=id,
            project_id=project_id,
        )

    @property
    def csv_files(self):
        """List of csv files"""
        return self.extra_attributes["csv_files"]

    @csv_files.setter
    def csv_files(self, value):
        self.extra_attributes["csv_files"] = value

    @property
    def stack_type(self):
        """Type of scanimage stack.
        See ScanImageData.__init__ docstring for valid values"""
        return self.extra_attributes["stack_type"]

    @stack_type.setter
    def stack_type(self, value):
        self.extra_attributes["stack_type"] = value

    @property
    def tif_files(self):
        """List of tif files

        Tif files are sorted alphabetically automatically done when setting this property
        """
        return self.extra_attributes["tif_files"]

    @tif_files.setter
    def tif_files(self, value):
        if value is None:
            self.extra_attributes["tif_files"] = None
            return
        if isinstance(value, str):
            value = [value]
        value = list(sorted(value))
        if not self.is_valid(tif_files=value):
            raise IOError(
                "One or more file do not exist. Set self._tif_files if you want"
                " to skip check"
            )
        self.extra_attributes["tif_files"] = value

    def is_valid(self, return_reason=False, tif_files=None):
        """Check that associated files exist"""
        if tif_files is None:
            tif_files = self.tif_files
        # checking file one by one is long, compare sets
        tif_files = set(tif_files)
        existing_file = {
            f for f in os.listdir(self.path_full) if f.endswith(("tif", ".tiff"))
        }
        if tif_files - existing_file:
            msg = "Some tif files do not exist: %s" % (tif_files - existing_file)
            return msg if return_reason else False
        for _, file_path in self.csv_files.items():
            if not (self.path_full / file_path).exists():
                msg = "Csv file does not exist: %s" % file_path
                return msg if return_reason else False
        return "" if return_reason else True

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
        frames_per_file = mdata["FrameData"]["SI.hScan2D.logFramesPerFile"]
    except KeyError:
        raise IOError("Could not find logFramesPerFile in metadata of %s" % fname)
    if math.isfinite(frames_per_file):
        pattern = r"(.*)_(\d*)_(\d*)(.*).tiff?"
    else:
        pattern = r"(.*)_(\d*)(.*).tiff?"
    parsed_name = re.match(pattern, fname)
    if parsed_name is None:
        raise IOError(
            "Cannot parse file name %s with expected pattern %s" % (fname, pattern)
        )
    stem = parsed_name.groups()[0]
    acq_num = parsed_name.groups()[1]
    acq_uid = "_".join([stem, acq_num])
    out = dict(file_stem=stem, acq_num=acq_num, acq_uid=acq_uid)
    if math.isfinite(frames_per_file):
        out["file_num"] = parsed_name.groups()[2]
    if parsed_name.groups()[-1]:
        out["channel"] = parsed_name.groups()[-1]
    return out
