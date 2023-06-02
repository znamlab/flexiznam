import datetime
import os
import pathlib
import re
import warnings

from flexiznam.schema.datasets import Dataset
from flexiznam.config import PARAMETERS


class SequencingData(Dataset):
    DATASET_TYPE = "sequencing"
    try:
        VALID_EXTENSIONS = PARAMETERS["sequencing_extensions"]
    except KeyError:
        VALID_EXTENSIONS = [
            ".fastq.gz",
            ".fastq",
            ".fq.gz",
            ".fq",
            ".bam",
            ".sam",
        ]
        warnings.warn(
            "Could not find `sequencing_extensions` in config. Please update "
            "config file",
            stacklevel=2,
        )

    @staticmethod
    def from_folder(
        folder,
        folder_genealogy=None,
        is_raw=None,
        verbose=True,
        flexilims_session=None,
        project=None,
    ):
        """Create a sequencing dataset by loading info from folder

        All files with extensions defined in the "sequencing_extensions" parameter
        of the config file are considered as valid datasets

        Args:
            folder (str): path to the folder
            folder_genealogy (tuple): genealogy of the folder, if None assume that
                                      the genealogy is just (folder,), i.e. no parents
            is_raw (bool): does this folder contain raw data?
            verbose (bool=True): print info about what is found
            flexilims_session (flm.Session): session to interact with flexilims
            project (str): project ID or name

        Returns:
            dict of datasets (fzm.schema.sequencing_data.SequencingData)
        """
        folder = pathlib.Path(folder)
        assert folder.is_dir()

        if folder_genealogy is None:
            folder_genealogy = (pathlib.Path(folder).stem,)
        elif isinstance(folder_genealogy, list):
            folder_genealogy = tuple(folder_genealogy)
        datasets = dict()
        valid_files = []
        for ext in SequencingData.VALID_EXTENSIONS:
            valid_files.extend([(ext, fl) for fl in folder.glob(f"*{ext}")])

        for ext, file in valid_files:
            created = datetime.datetime.fromtimestamp(file.stat().st_mtime)
            ds_name = file.name.replace(ext, "")
            if verbose:
                print("Found sequencing dataset %s" % ds_name)
            datasets[ds_name] = SequencingData(
                path=file,
                is_raw=is_raw,
                genealogy=folder_genealogy + (ds_name,),
                flexilims_session=flexilims_session,
                project=project,
                created=created.strftime("%Y-%m-%d %H:%M:%S"),
            )
        return datasets

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
        """Create a Sequencing dataset

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
            dataset_type=SequencingData.DATASET_TYPE,
            extra_attributes=extra_attributes,
            created=created,
            project=project,
            flexilims_session=flexilims_session,
            origin_id=origin_id,
            id=id,
            project_id=project_id,
        )

    def is_valid(self):
        """Check that the file exist"""
        if not self.path_full.exists():
            return False
        return True
