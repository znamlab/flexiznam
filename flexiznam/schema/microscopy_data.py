import datetime
import os
import pathlib

from flexiznam.schema.datasets import Dataset


class MicroscopyData(Dataset):
    """Subclass to handle detection of ex vivo microscopy images

    """
    DATASET_TYPE = 'microscopy'
    VALID_EXTENSIONS = {'.czi',}

    @staticmethod
    def from_folder(folder, verbose=True, mouse=None, flm_session=None):
        """Create Microscopy datasets by loading info from folder"""
        fnames = [f for f in os.listdir(folder) if f.endswith(tuple(MicroscopyData.VALID_EXTENSIONS))]

        output = dict()
        for fname in fnames:
            dataset_path = pathlib.Path(folder) / fname
            created = datetime.datetime.fromtimestamp(dataset_path.stat().st_mtime)
            output[fname] = MicroscopyData(
                path=dataset_path,
                created=created.strftime('%Y-%m-%d %H:%M:%S'),
                flm_session=flm_session
            )
            for field in ('mouse', ):
                setattr(output[fname], field, locals()[field])
            output[fname].dataset_name = fname
        return output

    def from_flexilims(project=None, name=None, data_series=None, flm_session=None):
        """Create a microscopy dataset from flexilims entry"""
        raise NotImplementedError

    def __init__(self, path, name=None, extra_attributes=None, created=None,
                 project=None, is_raw=True, flm_session=None):
        """Create a Microscopy dataset

        Args:
            name: Identifier. Unique name on flexilims. Must contain mouse, session (and recording)
            path: Path to the folder containing all the files
            extra_attributes: Other optional attributes (from or for flexilims)
            created: Date of creation. Default to the creation date of the binary file
            project: name of hexadecimal id of the project to which the dataset belongs
            is_raw: default to True. Is it processed data or raw data?
            flm_session: authentication session for connecting to flexilims
        """
        super().__init__(name=name, path=path, is_raw=is_raw,
                         dataset_type=MicroscopyData.DATASET_TYPE,
                         extra_attributes=extra_attributes, created=created,
                         project=project, flm_session=flm_session)

    def is_valid(self):
        """Check that the file exist"""
        if not (pathlib.Path(self.path)).exists():
            return False
        return True
