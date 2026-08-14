import datetime
import os
import pathlib
import re

import pandas as pd

from flexiznam.schema.datasets import Dataset


class NeuropixelData(Dataset):
    DATASET_TYPE = "neuropixel"
    VALID_EXTENSIONS = {".raw", ".csv"}

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
        """Create a Neuropixel dataset by loading info from folder

        Args:
            folder (str): path to the folder
            folder_genealogy (tuple): genealogy of the folder, if None assume that
                                      the genealogy is just (folder,), i.e. no parents
            is_raw (bool): does this folder contain raw data?
            verbose (bool=True): print info about what is found
            flexilims_session (flm.Session): session to interact with flexilims
            project (str): project ID or name
            enforce_validity (bool): True by default. Refuse to create neuropixel
                dataset if they don't have at least one ephys file.

        Returns:
            dict of datasets (fzm.schema.neuropixel_data.NeuropixelData)

        """
        folder = pathlib.Path(folder)
        if folder_genealogy is None:
            folder_genealogy = (folder.stem,)
        elif isinstance(folder_genealogy, list):
            folder_genealogy = tuple(folder_genealogy)

        fnames = [
            f
            for f in os.listdir(folder)
            if any(f.endswith(ext) for ext in NeuropixelData.VALID_EXTENSIONS)
        ]
        if not fnames:
            raise IOError("No valid files found in folder %s" % folder)

        data = []
        for fname in fnames:
            m = re.match(r"(.*)_(\d+)\..*", fname)
            if not m:
                continue
            device_name, index = m.groups()
            data.append(
                dict(
                    device_name=device_name,
                    index=int(index),
                    file=fname,
                )
            )

        if not data:
            raise IOError("No Neuropixel data found in folder %s" % folder)

        data_df = pd.DataFrame(data)
        output = {}

        for index, group in data_df.groupby("index"):
            if enforce_validity and not any(
                "ephys" in f for f in group["device_name"].values
            ):
                if verbose:
                    print(f"Skipping partial Neuropixel dataset for index {index}")
                continue

            dataset_name = f"neuropixel_{index}"
            extra_attributes = {
                row["device_name"].replace("-", "_"): row["file"]
                for _, row in group.iterrows()
            }

            # Use the modification time of the first file for the creation date
            first_file_path = folder / group["file"].iloc[0]
            created = datetime.datetime.fromtimestamp(first_file_path.stat().st_mtime)

            output[dataset_name] = NeuropixelData(
                path=folder,
                genealogy=folder_genealogy + (dataset_name,),
                extra_attributes=extra_attributes,
                created=created.strftime("%Y-%m-%d %H:%M:%S"),
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
        """Create a Neuropixel dataset"""
        super().__init__(
            genealogy=genealogy,
            path=path,
            is_raw=is_raw,
            dataset_type=NeuropixelData.DATASET_TYPE,
            extra_attributes=extra_attributes,
            created=created,
            project=project,
            project_id=project_id,
            origin_id=origin_id,
            id=id,
            flexilims_session=flexilims_session,
        )

    def is_valid(self, return_reason=False):
        """Check that the Neuropixel dataset is valid"""
        if not self.extra_attributes:
            msg = "No files found in dataset"
            return msg if return_reason else False

        for file_path in self.extra_attributes.values():
            p = self.path_full / file_path
            if not p.exists():
                msg = f"File {p} does not exist"
                return msg if return_reason else False

        return "" if return_reason else True
