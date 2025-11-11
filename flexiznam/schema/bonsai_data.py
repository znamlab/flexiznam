import datetime
import os
import pathlib

from flexiznam.schema.datasets import Dataset


class BonsaiData(Dataset):
    """
    Dataset for Bonsai workflow files.
    Each .bonsai file is considered a separate dataset.
    """

    DATASET_TYPE = "bonsai"
    VALID_EXTENSIONS = {".bonsai"}

    @staticmethod
    def from_folder(
        folder,
        folder_genealogy=None,
        is_raw=None,
        verbose=True,
        flexilims_session=None,
        project=None,
        enforce_validity=True,
    ):
        """Create Bonsai datasets by finding .bonsai files in a folder."""
        folder = pathlib.Path(folder)
        if folder_genealogy is None:
            folder_genealogy = (folder.stem,)
        elif isinstance(folder_genealogy, list):
            folder_genealogy = tuple(folder_genealogy)

        fnames = [
            f
            for f in os.listdir(folder)
            if any(f.endswith(ext) for ext in BonsaiData.VALID_EXTENSIONS)
        ]
        if not fnames:
            return {}

        output = {}
        for fname in fnames:
            dataset_name = pathlib.Path(fname).stem
            extra_attributes = {"file": fname}

            file_path = folder / fname
            created = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)

            dataset_instance = BonsaiData(
                path=folder,
                genealogy=folder_genealogy + (dataset_name,),
                extra_attributes=extra_attributes,
                created=created.strftime("%Y-%m-%d %H:%M:%S"),
                flexilims_session=flexilims_session,
                project=project,
                is_raw=is_raw,
            )

            if dataset_name in output:
                print(
                    f"Warning: Duplicate dataset name '{dataset_name}' found in "
                    + f"{folder}. Skipping."
                )
                continue

            output[dataset_name] = dataset_instance

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
        """Create a Bonsai dataset"""
        super().__init__(
            genealogy=genealogy,
            path=path,
            is_raw=is_raw,
            dataset_type=BonsaiData.DATASET_TYPE,
            extra_attributes=extra_attributes,
            created=created,
            project=project,
            project_id=project_id,
            origin_id=origin_id,
            id=id,
            flexilims_session=flexilims_session,
        )

    def is_valid(self, return_reason=False):
        """Check that the Bonsai dataset is valid."""
        if not self.extra_attributes or "file" not in self.extra_attributes:
            msg = "No file found in dataset"
            return msg if return_reason else False

        file_path = self.path_full / self.extra_attributes["file"]
        if not file_path.exists():
            msg = f"File {file_path} does not exist"
            return msg if return_reason else False

        return "" if return_reason else True
