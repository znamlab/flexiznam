import datetime
import os
import pathlib
import re
import pandas as pd
from flexiznam.schema.datasets import Dataset


class OnixData(Dataset):
    DATASET_TYPE = "onix"
    VALID_EXTENSIONS = {".raw", ".csv"}
    DEVICE_NAMES = {"bno055", "breakout", "rhd2164", "ts4231", "vistim"}

    @staticmethod
    def from_folder(
        folder,
        onix_name=None,
        folder_genealogy=None,
        is_raw=None,
        verbose=True,
        flexilims_session=None,
        project=None,
        enforce_validity=True,
    ):
        """Create a Onix dataset by loading info from folder

        Args:
            folder (str): path to the folder
            onix_name (str): name of the onix, all file names must start by this name
            folder_genealogy (tuple): genealogy of the folder, if None assume that
                                      the genealogy is just (folder,), i.e. no parents
            is_raw (bool): does this folder contain raw data?
            verbose (bool=True): print info about what is found
            flexilims_session (flm.Session): session to interact with flexilims
            project (str): project ID or name
            enforce_validity (bool): True by default. Refuse to create onix dataset
                if they don't have a rhd2164 and a breakout file

        Returns:
            dict of datasets (fzm.schema.onix_data.OnixData)

        """
        if folder_genealogy is None:
            folder_genealogy = (pathlib.Path(folder).stem,)
        elif isinstance(folder_genealogy, list):
            folder_genealogy = tuple(folder_genealogy)

        fnames = [
            f
            for f in os.listdir(folder)
            if f.endswith(tuple(OnixData.VALID_EXTENSIONS))
        ]
        if not len(fnames):
            raise IOError("No valid files found in folder %s" % folder)
        timestamp_str = r"(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d)_(\d\d)_(\d\d)"
        data = []
        for device_name in OnixData.DEVICE_NAMES:
            device_files = [f for f in fnames if f.startswith(device_name)]
            if not device_files:
                continue

            for device_file in device_files:
                m = re.match(rf"{device_name}-(.*)_{timestamp_str}.(.*)", device_file)
                if not m:
                    continue
                subname = m.groups()[0]
                timestamp = datetime.datetime(*[int(x) for x in m.groups()[1:-1]])
                data.append(
                    dict(
                        device_name=device_name,
                        subname=subname,
                        timestamp=timestamp,
                        file=device_file,
                    )
                )

        if not len(data):
            raise IOError("No data found in folder %s" % folder)

        data = pd.DataFrame(data)
        output = dict()
        if max(data.timestamp - data.timestamp.min()).total_seconds() > 2:
            raise IOError(f"Multiple timestamps found in folder {folder}")

        ts = data.timestamp.min()
        if (
            enforce_validity
            and ("rhd2164" not in data.device_name.values)
            or ("breakout" not in data.device_name.values)
        ):
            if verbose:
                print(
                    "Skipping partial onix dataset %s"
                    % ts.strftime("%Y-%m-%d_%H_%M_%S")
                )
            return
        onix_name = "onix_data_%s" % ts.strftime("%Y-%m-%d_%H_%M_%S")
        extra_attributes = dict()
        for device, dev_df in data.groupby("device_name"):
            extra_attributes[device] = {s.subname: s.file for s in dev_df.itertuples()}
        output[onix_name] = OnixData(
            path=folder,
            genealogy=folder_genealogy + (onix_name,),
            extra_attributes=extra_attributes,
            created=ts.strftime("%Y-%m-%d " "%H:%M:%S"),
            flexilims_session=flexilims_session,
            project=project,
            is_raw=is_raw,
        )
        return output

    def __init__(
        self,
        path,
        is_raw,
        genealogy=None,
        extra_attributes=None,
        created=None,
        project=None,
        project_id=None,
        origin_id=None,
        id=None,
        flexilims_session=None,
    ):
        """Create a onix dataset

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
        """
        super().__init__(
            genealogy=genealogy,
            path=path,
            is_raw=is_raw,
            dataset_type=OnixData.DATASET_TYPE,
            extra_attributes=extra_attributes,
            created=created,
            project=project,
            project_id=project_id,
            origin_id=origin_id,
            id=id,
            flexilims_session=flexilims_session,
        )

    def is_valid(self, return_reason=False):
        """Check that the onix dataset is valid

        Args:
            return_reason (bool): if True, return a string with the reason why the
                dataset is not valid. If False, return True or False

        Returns:
            bool or str: True if valid, False if not. If return_reason is True, return
                a string with the reason why the dataset is not valid."""

        ndevices = 0
        for device_name in OnixData.DEVICE_NAMES:
            if device_name not in self.extra_attributes:
                continue
            ndevices += 1
            dev_dict = self.extra_attributes[device_name]
            for v in dev_dict.values():
                p = self.path_full / v
                if not p.exists():
                    msg = f"File {p} does not exist"
                    return msg if return_reason else False
        if ndevices == 0:
            msg = "No devices found"
            return msg if return_reason else False
        return "" if return_reason else True
