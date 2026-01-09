import datetime
import os
import pathlib
import re
import warnings

import yaml

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
        unvalid_chars = re.compile(r'[\',\.@"+=\!#$%^&*<>?/\|}{~:]')
        folder = pathlib.Path(folder)

        # New format detection: device.yml and DEVICE_XX.bin files
        device_yml_path = folder / "device.yml"
        if device_yml_path.exists():
            if verbose:
                print(
                    f"Found device.yml in {folder}, attempting to parse new harp format"
                )
            with open(device_yml_path, "r") as f:
                device_info = yaml.safe_load(f)

            device_name = device_info.get("device")
            if not device_name:
                raise IOError("`device` field not found in device.yml")

            bin_files = list(folder.glob(f"{device_name}_*.bin"))
            if not bin_files:
                if verbose:
                    print(f"No binary files matching '{device_name}_*.bin' found.")
                # Fall through to old logic in case it's a mixed folder
            else:
                if folder_genealogy is None:
                    folder_genealogy = (folder.stem,)
                elif isinstance(folder_genealogy, list):
                    folder_genealogy = tuple(folder_genealogy)

                created = datetime.datetime.fromtimestamp(bin_files[0].stat().st_mtime)
                extra_attributes = {
                    "device_info": device_info,
                    "binary_files": sorted([f.name for f in bin_files]),
                }

                dataset_name = f"harp_{device_name}"
                genealogy = folder_genealogy + (dataset_name,)

                dataset = HarpData(
                    genealogy=genealogy,
                    is_raw=is_raw,
                    path=folder,
                    extra_attributes=extra_attributes,
                    created=created.strftime("%Y-%m-%d %H:%M:%S"),
                    flexilims_session=flexilims_session,
                    project=project,
                )
                return {dataset_name: dataset}

        # Original logic for old format
        if verbose:
            print("No device.yml found, parsing old harp format.")

        fnames = [f for f in os.listdir(folder) if f.endswith((".csv", ".bin", ".yml"))]
        bin_files = [f for f in fnames if f.endswith(".bin")]
        csv_files = [f for f in fnames if f.endswith(".csv")]
        if not bin_files:
            raise IOError("Cannot find binary file")

        if folder_genealogy is None:
            folder_genealogy = (folder.stem,)
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
            valid_csv = dict()
            for match in associated_csv:
                # special characters in the file name are replaced by underscores
                if re.search(unvalid_chars, match):
                    new_name = re.sub(r"[^\w\s]", "_", match)
                    warnings.warn(
                        f"Special characters in {match} were replaced by underscores"
                    )
                    valid_csv[new_name] = associated_csv[match]
                else:
                    valid_csv[match] = associated_csv[match]
            matched_files.update(valid_csv.values())

            bin_path = folder / bin_file
            created = datetime.datetime.fromtimestamp(bin_path.stat().st_mtime)
            extra_attributes = dict(
                binary_file=bin_file,
                csv_files=valid_csv,
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
            binary_file: File name of the binary file.
            csv_files (optional): Dictionary of csv files associated to the binary file.
                                  Keys are identifier provided for convenience,
                                  values are the full file name
            binary_files (list): For new format, list of binary file names.
            device_info (dict): For new format, content of device.yml.
        """
        is_new_format = "binary_files" in extra_attributes
        is_old_format = "binary_file" in extra_attributes
        if not is_new_format and not is_old_format:
            raise IOError(
                "Harp dataset requires 'binary_file' (old format) or 'binary_files' "
                + "(new format) in extra_attributes"
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
        if self.binary_file is None:
            for f in self.extra_attributes["binary_files"]:
                if not (self.path_full / f).exists():
                    msg = f"Missing file {f}"
                    return msg if return_reason else False
        elif not (self.path_full / self.binary_file).exists():  # Old format
            msg = f"Missing file {self.binary_file}"
            return msg if return_reason else False

        if self.csv_files:
            for _, file_path in self.csv_files.items():
                if not (self.path_full / file_path).exists():
                    msg = f"Missing file {file_path}"
                    return msg if return_reason else False
        return "" if return_reason else True
