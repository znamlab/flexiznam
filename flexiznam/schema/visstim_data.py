import datetime
import pathlib
import re
import warnings

from flexiznam.schema.datasets import Dataset


class VisStimData(Dataset):
    DATASET_TYPE = "visstim"

    @classmethod
    def from_folder(
        cls,
        folder,
        folder_genealogy=None,
        is_raw=None,
        verbose=True,
        flexilims_session=None,
        project=None,
        enforce_validity=True,
    ):
        """Create a visual stimulation dataset by loading info from folder

        A visual stimulation dataset is a folder containing at least a `FrameLog.csv`
        file and any number of other associated csvs.

        Args:
            folder (str): path to the folder
            folder_genealogy (tuple): genealogy of the folder, if None assume that
                                      the genealogy is just (folder,), i.e. no parents
            is_raw (bool): does this folder contain raw data?
            verbose (bool=True): print info about what is found
            flexilims_session (flm.Session): session to interact with flexilims
            project (str): project ID or name

        Returns:
            dict of dataset (flz.schema.harp_data.HarpData)
        """
        unvalid_chars = re.compile(r'[\',\.@"+=\!#$%^&*<>?/\|}{~:]')
        csv_files = list(pathlib.Path(folder).glob("*.csv"))

        fnames = [f.name for f in csv_files]
        fnames_lower = [f.lower() for f in fnames]
        valid_names = ["framelog.csv", "params.csv"]
        if not any([f in fnames_lower for f in valid_names]):
            raise IOError("Cannot find FrameLog.csv or Params.csv file")

        # Find the first available log file (prefer framelog.csv if both exist)
        log_file = None
        for valid_name in valid_names:
            matching_files = [f for f in csv_files if f.name.lower() == valid_name]
            if matching_files:
                log_file = matching_files[0]
                break

        assert log_file is not None

        if verbose:
            print(f"Found visstim log file: {log_file}")

        if folder_genealogy is None:
            folder_genealogy = (pathlib.Path(folder).stem,)
        elif isinstance(folder_genealogy, list):
            folder_genealogy = tuple(folder_genealogy)
        output = {}
        matched_csv_files = {f.stem: f.name for f in csv_files}
        valid_csv = dict()
        for fname, value in matched_csv_files.items():
            if unvalid_chars.search(fname):
                new_fname = re.sub(unvalid_chars, "_", fname)
                warnings.warn(f"Invalid characters in {fname}. Renaming to {new_fname}")
                valid_csv[new_fname] = value
            else:
                valid_csv[fname] = value
        if not valid_csv:
            raise IOError("No valid CSV files found in the folder.")

        genealogy = folder_genealogy + ("visstim",)
        created = datetime.datetime.fromtimestamp(log_file.stat().st_mtime)
        output["visstim"] = VisStimData(
            genealogy=genealogy,
            is_raw=is_raw,
            path=folder,
            extra_attributes=dict(csv_files=valid_csv),
            created=created.strftime("%Y-%m-%d %H:%M:%S"),
            flexilims_session=flexilims_session,
            project=project,
        )
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
        """Create a VisStim dataset

        Args:
            path: folder containing the dataset or path to file (valid only for single
                  file datasets)
            is_raw: bool, used to sort in raw and processed subfolders
            genealogy (tuple): parents of this dataset from the project (excluded) down
                to the dataset name itself (included)
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
            csv_files (optional): Dictionary of csv files associated to the binary file.
                Keys are identifier, values are the full file name
        """

        super().__init__(
            genealogy=genealogy,
            path=path,
            is_raw=is_raw,
            dataset_type=VisStimData.DATASET_TYPE,
            extra_attributes=extra_attributes,
            created=created,
            project=project,
            project_id=project_id,
            origin_id=origin_id,
            id=id,
            flexilims_session=flexilims_session,
        )

    @property
    def csv_files(self):
        return self.extra_attributes.get("csv_files", None)

    @csv_files.setter
    def csv_files(self, value):
        self.extra_attributes["csv_files"] = str(value)

    def is_valid(self, return_reason=False):
        """Check that all csv files exist

        Args:
            return_reason (bool): if True, return a string with the reason why the
                                  dataset is not valid
        Returns:"""
        for _, file_path in self.csv_files.items():
            if not (self.path_full / file_path).exists():
                msg = f"Missing file {file_path}"
                return msg if return_reason else False
        return "" if return_reason else True
