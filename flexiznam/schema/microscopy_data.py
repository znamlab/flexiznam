import datetime
import os
import pathlib

from flexiznam.schema.datasets import Dataset


class MicroscopyData(Dataset):
    """Subclass to handle detection of ex vivo microscopy images

    It should deal with all images except scanimage datasets (which are handled by
    scanimage_data.ScanimageData)

    Extensions added to VALID_EXTENSIONS are considered as single file datasets
    """

    DATASET_TYPE = 'microscopy'
    VALID_EXTENSIONS = {'.czi', '.png', '.gif'}

    @staticmethod
    def from_folder(folder, verbose=True, mouse=None, flm_session=None, project=None):
        """Create Microscopy datasets by loading info from folder"""
        fnames = [f for f in os.listdir(folder) if
                  f.lower().endswith(tuple(MicroscopyData.VALID_EXTENSIONS))]

        output = dict()
        for fname in fnames:
            dataset_path = pathlib.Path(folder) / fname
            created = datetime.datetime.fromtimestamp(dataset_path.stat().st_mtime)
            output[fname] = MicroscopyData(
                path=dataset_path,
                created=created.strftime('%Y-%m-%d %H:%M:%S'),
                flm_session=flm_session,
                project=project
            )
            for field in ('mouse', ):
                setattr(output[fname], field, locals()[field])
            output[fname].dataset_name = fname
        return output

    def __init__(self, path, is_raw, name=None, extra_attributes=None,
                 created=None, project=None, project_id=None, origin_id=None,
                 flm_session=None):
        """Create a Microscopy dataset

        Args:
            path: folder containing the dataset or path to file (valid only for single
                  file datasets)
            is_raw: bool, used to sort in raw and processed subfolders
            name: name of the dataset as on flexilims. Is expected to include mouse,
                  session etc...
            extra_attributes: dict, optional attributes.
            created: Creation date, in "YYYY-MM-DD HH:mm:SS"
            project: name of the project. Must be in config, can be guessed from
                     project_id
            project_id: hexadecimal code for the project. Must be in config, can be
                        guessed from project
            origin_id: hexadecimal code for the origin on flexilims.
            flm_session: authentication session to connect to flexilims

        Expected extra_attributes:
            None
        """
        super().__init__(name=name, path=path, is_raw=is_raw,
                         dataset_type=MicroscopyData.DATASET_TYPE,
                         extra_attributes=extra_attributes, created=created,
                         project=project, project_id=project_id,
                         origin_id=origin_id, flm_session=flm_session)

    def is_valid(self):
        """Check that the file exist"""
        if not (pathlib.Path(self.path)).exists():
            return False
        return True
