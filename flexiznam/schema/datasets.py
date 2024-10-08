import pathlib
from datetime import datetime
from pathlib import Path, PurePosixPath
import pandas as pd
import flexiznam as flz
from flexiznam import utils
from flexiznam.errors import FlexilimsError, DatasetError
from flexiznam.config import PARAMETERS


class Dataset(object):
    """Master class. Should be inherited by all datasets

    Class to handle dataset identification and validation

    SUBCLASSES are held in different files and added to the Dataset class by
    schema.__init__.py
    """

    SUBCLASSES = dict()

    @classmethod
    def from_folder(cls, folder, verbose=False, flexilims_session=None, project=None):
        """Try to load all datasets found in the folder.

        Will try all defined subclasses of datasets and keep everything that does not
        crash. If you know which dataset to expect, use the subclass directly
        """
        folder = pathlib.Path(folder)
        if not folder.is_dir():
            raise IOError("%s is not a directory." % folder)
        data = dict()
        if not cls.SUBCLASSES:
            raise IOError("Dataset subclasses not assigned")
        for ds_type, ds_class in cls.SUBCLASSES.items():
            if verbose:
                print("Looking for %s" % ds_type)
            try:
                res = ds_class.from_folder(
                    folder,
                    verbose=verbose,
                    flexilims_session=flexilims_session,
                    project=project,
                )
            except OSError:
                continue
            if any(k in data for k in res):
                raise DatasetError("Found two datasets with the same name")
            data.update(res)
        return data

    @staticmethod
    def from_flexilims(
        project=None,
        name=None,
        id=None,
        flexilims_session=None,
    ):
        """Loads a dataset from flexilims

        If the dataset_type attribute of the flexilims entry defined in
        Dataset.SUBCLASSES,this subclass will be used. Otherwise a generic Dataset is
        returned

        Args:
            project (str, optional): Name of the project or hexadecimal project_id. If
                not provided, can be read from flexilims_session
            name (str, optional): Unique name of the dataset on flexilims. Ignored if
                `dataseries` is provided
            id (str, optional): Hexadecimal id of the dataset on flexilims. Ignored if
                `dataseries` is provided
            flexilims_session (flexilims.Session, optional): authentication session to
                access flexilims.
        """
        dataseries = flz.get_entity(
            project_id=project,
            datatype="dataset",
            name=name,
            id=id,
            flexilims_session=flexilims_session,
        )

        if dataseries is None:
            if project is None:
                project = flexilims_session.project_id
            raise FlexilimsError(
                "No dataset named {} in project {}".format(name, project)
            )
        ds = Dataset.from_dataseries(dataseries, flexilims_session=flexilims_session)
        return ds

    @staticmethod
    def from_dataseries(
        dataseries,
        flexilims_session=None,
    ):
        """Create dataset from a flexilims dataseries

        This function does not call flexilims, but uses the dataseries object directly.
        Args:
            dataseries (flexilims.DataSeries): flexilims dataseries object
            flexilims_session (flexilims.Session, optional): authentication session to
                access flexilims. Will be added to dataset object.
        """
        dataset_type = dataseries.dataset_type

        kwargs = Dataset._format_series_to_kwargs(dataseries)
        name = kwargs.pop("name")
        kwargs["flexilims_session"] = flexilims_session
        if dataset_type in Dataset.SUBCLASSES:
            # dataset_type is already specified by subclass
            kwargs.pop("dataset_type")
            ds = Dataset.SUBCLASSES[dataset_type](**kwargs)
        else:
            ds = Dataset(**kwargs)

        if ds.full_name != name:
            raise DatasetError(
                "Genealogy does not correspond to flexilims name:"
                + "\n %s: %s" % (name, ds.genealogy)
            )
        return ds

    @staticmethod
    def from_origin(
        project=None,
        origin_type=None,
        origin_id=None,
        origin_name=None,
        dataset_type=None,
        base_name=None,
        conflicts=None,
        flexilims_session=None,
        extra_attributes=None,
        ignore_attributes=(),
        verbose=False,
    ):
        """Creates a dataset of a given type as a child of a parent entity

        This function will create a dataset with a unique name based on the origin name
        and the dataset type. If a dataset of this type already exists, the behaviour is
        defined by the `conflicts` argument. If `extra_attributes` is provided, only
        consider datasets that have the exact same extra_attributes when resolving
        conflicts.


        Args:
            project (str): Name of the project or hexadecimal project_id
            origin_type (str): sample type of the origin
            origin_id (str): hexadecimal ID of the origin. This or origin_name must be
                provided
            origin_name (str): name of the origin. This or origin_id must be provided
            dataset_type (str): type of dataset to create. Must be defined in the config
                file
            base_name (str): How is this dataset name? Use dataset_type if base_name is
                             None (default)
            conflicts (str): How to resolve conflicts? One of `abort`, `skip`, `append`,
                `overwrite`. Default is `abort`
            flexilims_session (:py:class:`flexilims.Flexilims`): authentication session
                to connect to flexilims
            extra_attributes (dict): additional arguments. If provided, change the
                `conflicts` behaviour to consider only datasets that have the exact
                same extra_attributes.
            ignore_attributes (list): list of arguments to ignore when comparing datasets
                for conflicts resolution. Used only if `extra_attributes` is provided.
            verbose (bool): print debug information

        Returns:
            :py:class:`flexiznam.schema.datasets.Dataset`: a dataset object (WITHOUT updating flexilims)

        """
        if base_name is None:
            base_name = dataset_type
        assert (origin_id is not None) or (origin_name is not None)
        assert dataset_type is not None  # not sure why it is not a mandatory argument
        origin = flz.get_entity(
            datatype=origin_type,
            id=origin_id,
            name=origin_name,
            project_id=project,
            flexilims_session=flexilims_session,
        )
        if origin is None:
            raise FlexilimsError("Origin not found")
        processed = flz.get_entities(
            project_id=project,
            datatype="dataset",
            origin_id=origin["id"],
            query_key="dataset_type",
            query_value=dataset_type,
            flexilims_session=flexilims_session,
        )
        if len(processed):
            processed = processed[
                [g[-1].startswith(base_name + "_") for g in processed.genealogy]
            ]

        # If extra_attributes is provided, only consider datasets that have the exact
        # same extra_attributes
        if extra_attributes is not None:
            valid_processed = []
            to_compare = utils.clean_recursively(
                extra_attributes.copy(), keys=ignore_attributes
            )
            for _, proc in processed.iterrows():
                online = Dataset._format_series_to_kwargs(proc)["extra_attributes"]
                online = utils.clean_recursively(online, keys=ignore_attributes)
                differences = utils.compare_dictionaries_recursively(to_compare, online)
                if not differences:
                    valid_processed.append(proc)
        else:
            valid_processed = [ser for _, ser in processed.iterrows()]

        already_processed = len(processed) > 0

        def _create_new_ds(
            origin,
            base_name,
            project,
            flexilims_session,
            dataset_type,
            extra_attributes,
        ):
            """Inner function to create a new dataset object"""
            dataset_root = "%s_%s" % (origin["name"], base_name)
            dataset_name = flz.generate_name(
                "dataset",
                dataset_root,
                project_id=project,
                flexilims_session=flexilims_session,
            )
            short_name = dataset_name[len(origin["name"]) + 1 :]
            genealogy = tuple(origin.genealogy) + (short_name,)
            dataset_path = str(Path(origin["path"]) / short_name)
            return Dataset(
                path=dataset_path,
                is_raw="no",
                dataset_type=dataset_type,
                genealogy=genealogy,
                created=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                project=project,
                origin_id=origin["id"],
                flexilims_session=flexilims_session,
                extra_attributes=extra_attributes,
            )

        # CONFLICTS RESOLUTION
        # There are no datasets, create one
        if not already_processed:
            if verbose:
                print("No datasets of type %s found. Creating new" % dataset_type)
            return _create_new_ds(
                origin,
                base_name,
                project,
                flexilims_session,
                dataset_type,
                extra_attributes,
            )
        # There are some datasets of this type already online and we abort
        if (conflicts is None) or (conflicts == "abort"):
            raise flz.errors.DatasetError(
                f"Dataset(s) of type {dataset_type} already exist(s):"
                + f" {processed.loc[:, 'name']}"
            )
        # Three cases left: skip, append, overwrite
        if conflicts == "overwrite":
            # If overwrite, ensure there is only one dataset of this type as we
            # won't be able to guess which one should be replaced
            if len(valid_processed) == 1:
                if verbose:
                    print("Overwriting dataset %s" % valid_processed[0].name)
                dataset = Dataset.from_dataseries(dataseries=valid_processed[0])
                dataset.extra_attributes = extra_attributes
                return dataset
            if len(processed) == 1:
                if verbose:
                    print("Overwriting dataset %s" % processed.iloc[0].name)
                dataset = Dataset.from_dataseries(dataseries=processed.iloc[0])
                dataset.extra_attributes = extra_attributes
                return dataset
            raise flz.errors.NameNotUniqueError(
                f"Multiple datasets of type {dataset_type} already exist(s):"
                + f" {processed.loc[:, 'name']}"
            )
        if conflicts == "skip":
            # If skip and we have an exact match, return it
            if len(valid_processed) == 1:
                if verbose:
                    print("Skip. Returning dataset %s" % valid_processed[0].name)
                return Dataset.from_dataseries(dataseries=valid_processed[0])
            # If there is no match, create a new dataset
            if len(valid_processed) == 0:
                if verbose:
                    print("No matching dataset found. Creating new dataset")
                return _create_new_ds(
                    origin,
                    base_name,
                    project,
                    flexilims_session,
                    dataset_type,
                    extra_attributes,
                )
            raise flz.errors.NameNotUniqueError(
                f"Multiple datasets of type {dataset_type} already exist(s):"
                + f" {processed.loc[:, 'name']}"
            )
        if conflicts == "append":
            # Create a new dataset
            if verbose:
                print("Appending dataset")
            return _create_new_ds(
                origin,
                base_name,
                project,
                flexilims_session,
                dataset_type,
                extra_attributes,
            )

    @staticmethod
    def _format_series_to_kwargs(flm_series):
        """Format a flm get reply into kwargs valid for Dataset constructor"""
        flm_attributes = {
            "id",
            "type",
            "name",
            "incrementalId",
            "createdBy",
            "dateCreated",
            "origin_id",
            "objects",
            "customEntities",
            "project",
        }
        d = dict()
        for k, v in flm_series.items():
            d[k] = v
        attr = {k: v for k, v in flm_series.items() if k not in flm_attributes}
        kwargs = dict(
            path=attr.pop("path"),
            is_raw=attr.pop("is_raw", None),
            dataset_type=attr.pop("dataset_type"),
            created=attr.pop("created", None),
            genealogy=attr.pop("genealogy", None),
            origin_id=flm_series.get("origin_id", None),
            extra_attributes=attr,
            project_id=flm_series.project,
            name=flm_series.name,
            id=flm_series.id,
        )
        return kwargs

    def __init__(
        self,
        path,
        is_raw,
        dataset_type,
        genealogy=None,
        extra_attributes=None,
        created=None,
        project=None,
        project_id=None,
        origin_id=None,
        id=None,
        flexilims_session=None,
    ):
        """Construct a dataset manually. Is usually called through static methods
        'from_folder', 'from_flexilims', or 'from_origin'

        Args:
            path: folder containing the dataset or path to file (valid only for single
                file datasets)
            is_raw: bool, used to sort in raw and processed subfolders
            dataset_type: type of the dataset, must be in PARAMETERS['dataset_types']
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
        """
        if extra_attributes is None:
            extra_attributes = {}
        else:
            extra_attributes = dict(extra_attributes)
            double_args = [
                kw
                for kw in ("path", "is_raw", "dataset_type", "genealogy", "created")
                if kw in extra_attributes
            ]
            if len(double_args):
                raise DatasetError(
                    "Mandatory attribute(s) present in "
                    "extra_attributes: %s" % (double_args)
                )

        self._project = None
        self._project_id = None
        self._flexilims_session = None
        self.extra_attributes = extra_attributes
        self.genealogy = genealogy
        self.path = Path(path)
        self.is_raw = is_raw
        self.dataset_type = str(dataset_type)
        self.created = created
        self.origin_id = origin_id
        self.flexilims_session = flexilims_session
        self.id = id
        if project is not None:
            self.project = project
            if project_id is not None:
                if self.project_id != project_id:
                    raise DatasetError("project_id does not correspond to project")
        elif project_id is not None:
            self.project_id = project_id

    def is_valid(self, return_reason=False):
        """Check if the file path is valid for this dataset

        Should be reimplemented in children classes.
        Should return True if the dataset is found a valid, false otherwise
        """
        if not self.path_full.exists():
            msg = f"Path {self.path_full} does not exist"
            return msg if return_reason else False
        return "" if return_reason else True

    def associated_files(self, folder=None):
        """Give a list of all files associated with this dataset

        Args:
            folder: Where to look for files? default to self.path

        Returns:
        """
        raise NotImplementedError(
            "`associated_files` is not defined for generic " "datasets"
        )

    def get_flexilims_entry(self):
        """Get the flexilims entry for this dataset

        Returns:
            dict: a dictionary or [] if the entry is not found
        """
        if self.project_id is None:
            raise IOError("You must specify the project to get flexilims status")
        if (self.id is None) and (self.full_name is None):
            raise IOError(
                "You must specify the dataset name or id to get flexilims status"
            )
        series = flz.get_entity(
            datatype="dataset",
            project_id=self.project_id,
            name=self.full_name,
            id=self.id,
            flexilims_session=self.flexilims_session,
        )
        if (series is not None) and (self.id is None):
            self.id = series.id
        return series

    def update_flexilims(self, mode="safe"):
        """Create or update flexilims entry for this dataset

        Args:
            mode (str): One of: 'update', 'overwrite', 'safe' (default).
                If 'safe', will only create entry if it does not exist online.
                If 'update' will update existing entry but keep any existing
                attributes that are not specified. If 'overwrite' will update
                existing entry and clear any attributes that are not specified.

        Returns:
            Flexilims reply
        """
        if self.genealogy is None:
            raise DatasetError("Genealogy must be set to upload to flexilims")

        status = self.flexilims_status()
        attributes = self.extra_attributes.copy()

        if status == "different":
            if mode == "safe":
                raise FlexilimsError(
                    "Cannot change existing flexilims entry with "
                    "mode=`safe`. \nDifferences:%s" % self.flexilims_report()
                )
            if (mode == "overwrite") or (mode == "update"):
                # I need to pack the dataset field in attributes
                fmt = self.format()
                for field in ["path", "created", "is_raw", "dataset_type", "genealogy"]:
                    attributes[field] = fmt[field]

                # resetting origin_id to null is not implemented. Specifically check
                # that it is not attempted and crash if it is
                if self.origin_id is None:
                    if self.get_flexilims_entry().get("origin_id", None) is not None:
                        raise FlexilimsError("Cannot set origin_id to null")
                utils.clean_recursively(attributes)
                resp = flz.update_entity(
                    datatype="dataset",
                    id=self.id,
                    name=self.full_name,
                    origin_id=self.origin_id,
                    mode=mode,
                    attributes=attributes,
                    project_id=self.project_id,
                    flexilims_session=self.flexilims_session,
                )
            else:
                raise IOError("`mode` must be `safe`, `overwrite` or `update`")
            return resp
        if status == "up-to-date":
            print("Already up to date, nothing to do")
            return
        # we are in 'not online' case
        utils.clean_recursively(attributes)
        resp = flz.add_dataset(
            parent_id=self.origin_id,
            dataset_type=self.dataset_type,
            created=self.created,
            path=str(PurePosixPath(self.path)),
            is_raw="yes" if self.is_raw else "no",
            project_id=self.project_id,
            dataset_name=self.dataset_name,
            attributes=attributes,
            flexilims_session=self.flexilims_session,
            conflicts="abort",
        )

        online_name = resp["name"]
        assert online_name == self.full_name
        root_name = "_".join(self.genealogy)
        assert online_name.startswith(root_name)
        self.id = resp["id"]
        return resp

    def flexilims_status(self):
        """Status of the dataset on flexilims

        Status can be 'up-to-date', 'different' or 'not online'

        This function does not check flexilims these only value:
        'createdBy', 'objects', 'dateCreated', 'customEntities',
        'incrementalId', 'id', 'origin_id'
        """
        series = self.get_flexilims_entry()
        if series is None:
            return "not online"
        differences = self.flexilims_report(flm_data=series)
        if len(differences):
            return "different"
        return "up-to-date"

    def flexilims_report(self, flm_data=None):
        """Describe the difference between the dataset and what is on flexilims

        Differences are returned in a dictionary:
        property: (value in dataset, value in flexilims)

        Attributes not present in either dataset or on flexilims are labelled as 'N/A'
        """
        if flm_data is None:
            flm_data = self.get_flexilims_entry()
            if flm_data is None:
                raise IOError("No flexilims entry for dataset %s" % self.full_name)

        # remove the flexilims keywords that are not used by Dataset if they are present
        flm_data = flm_data.drop(
            [
                "createdBy",
                "objects",
                "dateCreated",
                "customEntities",
                "incrementalId",
                "id",
            ],
            errors="ignore",
        )
        # add the fields that are always present in Dataset but returned by flexilims
        # only when they are non null
        for na_field in ["origin_id", "is_raw", "dataset_type", "path", "created"]:
            if na_field not in flm_data:
                flm_data[na_field] = None
        fmt = self.format()

        differences = utils.compare_series(
            fmt, flm_data, series_name=("offline", "flexilims")
        )
        # flexilims transforms empty structures into None. Consider that equal
        to_remove = []
        for what, series in differences.iterrows():
            if series.flexilims is not None:
                continue
            if not isinstance(series.offline, bool) and not series.offline:
                # we have a non-boolean that is False, flexilims will make it None on
                # upload, it is not a real difference
                to_remove.append(what)
        if len(to_remove):
            print(
                "\nWarning: %s is/are empty and will be uploaded as None on "
                "flexilims.\n" % to_remove
            )
        differences = differences.drop(to_remove)
        return differences

    def format(self, mode="flexilims"):
        """Format a dataset

        This can generate either a 'flexilims' type of output (a series similar to
        get_entities output) or a 'yaml' type as that used by flexiznam.camp

        The flexilims series will not include elements that are not used by the Dataset
        class such as created_by and will make sure that the output is JSON serializable

        Args:
            mode: 'flexilims' or 'yaml'
        """
        data = dict(
            path=str(PurePosixPath(self.path)),
            created=self.created,
            dataset_type=self.dataset_type,
            is_raw="yes" if self.is_raw else "no",
            name=self.full_name,
            genealogy=self.genealogy,
            project=self.project_id,
            origin_id=self.origin_id,
            type="dataset",
        )

        if mode.lower() == "flexilims":
            data.update(self.extra_attributes)
            series = pd.Series(data, name=self.full_name)
            return series
        elif mode.lower() in ["yaml", "json", "yml"]:
            data["extra_attributes"] = self.extra_attributes
            flz.utils.clean_recursively(data)
            return data
        else:
            raise IOError('Unknown mode "%s". Must be `flexilims` or `yaml`' % mode)

    @property
    def project_id(self):
        """Hexadecimal ID of the parent project. Must be defined in config project list"""
        return self._project_id

    @project_id.setter
    def project_id(self, value):
        project = flz.main.lookup_project(value, flz.PARAMETERS)
        if project is None:
            raise IOError("Unknown project ID. Please update config file")
        if self.flexilims_session is not None:
            sp = self.flexilims_session.project_id
            if (sp is not None) and (sp != value):
                raise DatasetError("Project must match that of flexilims_session")
        self._project = project
        self._project_id = value

    @property
    def project(self):
        """Parent project. Must be defined in config project list"""
        return self._project

    @project.setter
    def project(self, value):
        if value not in flz.PARAMETERS["project_ids"]:
            raise IOError("Unknown project name. Please update config file")

        proj_id = flz.PARAMETERS["project_ids"][value]
        if self.flexilims_session is not None:
            sp = self.flexilims_session.project_id
            if (sp is not None) and (sp != proj_id):
                raise DatasetError("Project must match that of flexilims_session")
        self._project_id = proj_id
        self._project = value

    @property
    def flexilims_session(self):
        """Flexilims session. It's project must match self.project"""
        return self._flexilims_session

    @flexilims_session.setter
    def flexilims_session(self, value):
        self._flexilims_session = value
        if value is None:
            return
        if hasattr(value, "project_id") and (value.project_id is not None):
            if self.project_id is None:
                self.project_id = value.project_id
            elif self.project_id != value.project_id:
                raise DatasetError(
                    "Cannot use a flexilims_session from a different " "project"
                )

    @property
    def full_name(self):
        """Full name of the dataset as it would appear on Flexilims.

        Including mouse, sample, session and recording, whichever apply.
        """
        if self.genealogy is not None:
            name = "_".join([e for e in self.genealogy if e is not None])
        else:
            name = None
        return name

    @full_name.setter
    def full_name(self, value):
        raise DatasetError(
            "Full name cannot be set directly. Set self.genealogy instead"
        )

    @property
    def dataset_name(self):
        """Short name of the dataset"""
        if self.genealogy is not None:
            return self.genealogy[-1]
        else:
            return None

    @full_name.setter
    def full_name(self, value):
        raise DatasetError(
            "Full name cannot be set directly. Set self.genealogy instead"
        )

    @property
    def dataset_type(self):
        """Type of the dataset. Must be in PARAMETERS['dataset_types']"""
        return self._dataset_type

    @dataset_type.setter
    def dataset_type(self, value):
        if PARAMETERS["enforce_dataset_types"]:
            if value.lower() not in PARAMETERS["dataset_types"]:
                raise DatasetError(
                    'dataset_type "%s" not valid. Valid types are: '
                    "%s" % (value, PARAMETERS["dataset_types"])
                )
        self._dataset_type = value.lower()

    @property
    def genealogy(self):
        """Parents of this dataset from the project (excluded) down to the dataset name
        itself (included)"""
        return self._genealogy

    @genealogy.setter
    def genealogy(self, value):
        if value is None:
            self._genealogy = value
            return
        if isinstance(value, list) or isinstance(value, tuple):
            if all([isinstance(el, str) for el in value]):
                self._genealogy = tuple(value)
                return
        raise DatasetError("Genealogy must be a tuple of strings.\n Got: %s" % value)

    @property
    def is_raw(self):
        """Is that dataset containing raw or processed data?"""
        return self._is_raw

    @is_raw.setter
    def is_raw(self, value):
        """Set the `is_raw` flag.

        Valid values are 'yes' and 'no'. If set to None, try to guess from path and
        crash if it doesn't work"""
        if value is None:
            paths = PARAMETERS["data_root"]
            if Path(paths["raw"]) in self.path.parents:
                value = "yes"
            elif Path(paths["processed"]) in self.path.parents:
                value = "no"
            else:
                raise IOError("Cannot create a dataset without setting `is_raw`")
        if isinstance(value, str):
            if value.lower() == "yes":
                value = True
            elif value.lower() == "no":
                value = False
            else:
                raise IOError("is_raw must be `yes` or `no`")
        else:
            value = bool(value)
        self._is_raw = value

    @property
    def path_root(self):
        """Get CAMP root path that should apply to this dataset"""
        if self.is_raw is None:
            raise AttributeError("`is_raw` must be set to find path.")
        return flz.get_data_root(
            which="raw" if self.is_raw else "processed", project=self.project
        )

    @property
    def path_full(self):
        """Get full path including the CAMP root"""
        return self.path_root / self.path
