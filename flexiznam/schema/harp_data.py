import datetime
import os
import pathlib
import re

from flexiznam.schema.datasets import Dataset


class HarpData(Dataset):
    DATASET_TYPE = "harp"

    @classmethod
    def from_folder(
        cls,
        folder,
        folder_genealogy=None,
        is_raw=None,
        verbose=True,
        flexilims_session=None,
        project=None,
    ):
        """Create a harp dataset by loading info from folder

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

        fnames = [f for f in os.listdir(folder) if f.endswith((".csv", ".bin"))]
        bin_files = [f for f in fnames if f.endswith(".bin")]
        csv_files = [f for f in fnames if f.endswith(".csv")]
        if not bin_files:
            raise IOError("Cannot find binary file")

        if folder_genealogy is None:
            folder_genealogy = (pathlib.Path(folder).stem,)
        elif isinstance(folder_genealogy, list):
            folder_genealogy = tuple(folder_genealogy)
        output = {}
        matched_files = set()
        for bin_file in bin_files:
            m = re.match(r"(.*?)_?harpmessage_?(.*?).bin", bin_file)
            if not m:
                if verbose:
                    print(
                        "%s is not a binary harp file: `_harpmessage_` is not in "
                        "file name." % bin_file
                    )
                continue

            pattern = "(.*)".join(m.groups()) + ".csv"
            matches = [re.match(pattern, f) for f in csv_files]
            associated_csv = {
                m.groups()[0].strip("_"): f for f, m in zip(csv_files, matches) if m
            }
            if matched_files.intersection(associated_csv.values()):
                raise IOError("A csv file matched with multiple binary files.")
            matched_files.update(associated_csv.values())

            bin_path = pathlib.Path(folder) / bin_file
            created = datetime.datetime.fromtimestamp(bin_path.stat().st_mtime)
            extra_attributes = dict(
                binary_file=bin_file,
                csv_files=associated_csv,
            )
            genealogy = folder_genealogy + (bin_file[:-4],)
            output[bin_file[:-4]] = HarpData(
                genealogy=genealogy,
                is_raw=is_raw,
                path=folder,
                extra_attributes=extra_attributes,
                created=created.strftime("%Y-%m-%d %H:%M:%S"),
                flexilims_session=flexilims_session,
                project=project,
            )
        if verbose:
            unmatched = set(csv_files) - matched_files
            if unmatched and verbose:
                print("%d csv files did not match any binary file:" % len(unmatched))
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
        """Create a Harp dataset

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
            binary_file: File name of the binary file.
            csv_files (optional): Dictionary of csv files associated to the binary file.
                                  Keys are identifier provided for convenience,
                                  values are the full file name
        """
        if "binary_file" not in extra_attributes:
            raise IOError(
                "Harp dataset require `binary_file` in their extra_attributes"
            )

        super().__init__(
            genealogy=genealogy,
            path=path,
            is_raw=is_raw,
            dataset_type=HarpData.DATASET_TYPE,
            extra_attributes=extra_attributes,
            created=created,
            project=project,
            project_id=project_id,
            origin_id=origin_id,
            id=id,
            flexilims_session=flexilims_session,
        )

    @property
    def binary_file(self):
        return self.extra_attributes.get("binary_file", None)

    @binary_file.setter
    def binary_file(self, value):
        self.extra_attributes["binary_file"] = str(value)

    @property
    def csv_files(self):
        return self.extra_attributes.get("csv_files", None)

    @csv_files.setter
    def csv_files(self, value):
        self.extra_attributes["csv_files"] = str(value)

    def is_valid(self, return_reason=False):
        """Check that video, metadata and timestamps files exist

        Args:
            return_reason (bool): if True, return a string with the reason why the
                                  dataset is not valid
        Returns:"""
        if not (self.path_full / self.binary_file).exists():
            msg = f"Missing file {self.binary_file}"
            return msg if return_reason else False
        for _, file_path in self.csv_files.items():
            if not (self.path_full / file_path).exists():
                msg = f"Missing file {file_path}"
                return msg if return_reason else False
        return "" if return_reason else True
