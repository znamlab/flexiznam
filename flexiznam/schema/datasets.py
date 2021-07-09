"""
Class to handle dataset identification and validation
"""
import pathlib
from pathlib import Path
import re
import numpy as np
import pandas as pd
import flexiznam as flz
from flexiznam import utils
from flexiznam.errors import FlexilimsError, DatasetError
from flexiznam.config import PARAMETERS
from datetime import datetime

class Dataset(object):
    """Master class. Should be inherited by all datasets

    SUBCLASSES are held in different files and added to the Dataset class by
    schema.__init__.py
    """
    SUBCLASSES = dict()

    @staticmethod
    def parse_dataset_name(name):
        """Parse a name into mouse, session, recording, dataset_name

        Args:
            name (str): name of the Dataset

        Returns:
            dict or None: None if parsing fails, a dictionary otherwise
        """
        pattern = (r'(?P<mouse>.*?)_(?P<session>S\d{8})_?(?P<session_num>\d+)?'
                   r'_?(?P<recording>R\d{6})?_?(?P<recording_num>\d+)?'
                   r'_(?P<dataset>.*)')
        match = re.match(pattern, name)
        if not match:
            raise DatasetError('No match in: `%s`. Must be '
                               '`<MOUSE>_SXXXXXX[...]_<DATASET>`.' % name)
        # group session num and recording num together
        output = match.groupdict()
        sess_num = output.pop('session_num')
        if sess_num is not None:
            if output['session'] is None:
                raise DatasetError('Found session number but not session name in `%s`'
                                   % name)
            output['session'] += '_%s' % sess_num
        rec_num = output.pop('recording_num')
        if rec_num is not None:
            if output['recording'] is None:
                raise DatasetError('Found recording number but not recording name in `%s`'
                                   % name)
            output['recording'] += '_%s' % rec_num
        return output

    @classmethod
    def from_folder(cls, folder, verbose=True, flm_session=None):
        """Try to load all datasets found in the folder.

        Will try all defined subclasses of datasets and keep everything that does not
        crash. If you know which dataset to expect, use the subclass directly
        """
        data = dict()
        if not cls.SUBCLASSES:
            raise IOError('Dataset subclasses not assigned')
        for ds_type, ds_class in cls.SUBCLASSES.items():
            if verbose:
                print('Looking for %s' % ds_type)
            try:
                res = ds_class.from_folder(folder, verbose=verbose,
                                           flm_session=flm_session)
            except OSError:
                continue
            if any(k in data for k in res):
                raise DatasetError('Found two datasets with the same name')
            data.update(res)
        return data

    @staticmethod
    def from_flexilims(project=None, name=None, data_series=None, flm_session=None):
        """Loads a dataset from flexilims.

        If the dataset_type attribute of the flexilims entry defined in
        Dataset.SUBCLASSES,this subclass will be used. Otherwise a generic Dataset is
        returned

        Args:
            project: Name of the project or hexadecimal project_id
            name: Unique name of the dataset on flexilims
            data_series: default to None. pd.Series as returned by flz.get_entities.
                         If provided, superseeds project and name
            flm_session: authentication session to access flexilims
        """
        if data_series is not None:
            if (project is not None) or (name is not None):
                raise AttributeError('Specify either data_series OR project + name')
        else:
            data_series = flz.get_entity(project_id=project, datatype='dataset',
                                         name=name, flexilims_session=flm_session)
            if data_series is None:
                raise FlexilimsError('No dataset named {} in project {}'.format(name,
                                                                                project))
        dataset_type = data_series.dataset_type
        if dataset_type in Dataset.SUBCLASSES:
            ds_cls = Dataset.SUBCLASSES[dataset_type]
            return ds_cls.from_flexilims(data_series=data_series, flm_session=flm_session)
        # No subclass, let's do it myself
        kwargs = Dataset._format_series_to_kwargs(data_series)
        name = kwargs.pop('name')
        kwargs['flm_session'] = flm_session
        ds = Dataset(**kwargs)
        try:
            ds.name = name
        except DatasetError:
            print('\n!!! Cannot parse the name !!!\nWill not set mouse, session '
                  'or recording')
            ds.dataset_name = name
        return ds

    @staticmethod
    def from_origin(project=None, origin_type=None, origin_id=None, origin_name=None,
                    dataset_type=None, conflicts=None, flm_session=None):
        """Creates a dataset of a given type as a child of a parent entity

        Args:
            project (str): Name of the project or hexadecimal project_id
            origin_type (str): sample type of the origin
            origin_id (str): hexadecimal ID of the origin. This or origin_name must be provided
            origin_name (str): name of the origin. This or origin_id must be provided
            dataset_type (str): type of dataset to create. Must be defined in the config file
            conflicts (str): What to do if a dataset of this type already exists
                as a child of the parent entity?
                
                `append`
                    Create a new dataset with a new name and path
                `abort` or None
                    Through a :py:class:`flexiznam.errors.NameNotUniqueError` and
                    exit
                `skip` or `overwrite`
                    Return a Dataset corresponding to the existing entry if there
                    is exactly one existing entry, otherwise through a
                    :py:class:`flexiznam.errors.NameNotUniqueError`
            flm_session (:py:class:`flexilims.Flexilims`): authentication session to connect to flexilims

        Returns:
            :py:class:`flexiznam.schema.datasets.Dataset`: a dataset object (WITHOUT updating flexilims)

        """
        assert (origin_id is not None) or (origin_name is not None)
        origin = flz.get_entity(
            datatype=origin_type,
            id=origin_id,
            name=origin_name,
            project_id=project,
            flexilims_session=flm_session,
        )
        if origin is None:
            raise FlexilimsError('Origin not found')
        processed = flz.get_entities(
            project_id=project,
            datatype='dataset',
            origin_id=origin['id'],
            query_key='dataset_type',
            query_value=dataset_type,
            flexilims_session=flm_session,
        )
        already_processed = len(processed) > 0
        if (not already_processed) or (conflicts == 'append'):
            dataset_root = '%s_%s' % (origin['name'], dataset_type)
            dataset_name = flz.generate_name(
                'dataset',
                dataset_root,
                project_id=project,
                flexilims_session=flm_session
            )
            dataset_path = str(
                Path(origin['path']) / Dataset.parse_dataset_name(dataset_name
                                                                  )['dataset'])
            return Dataset(
                path=dataset_path,
                is_raw='no',
                dataset_type=dataset_type,
                name=dataset_name,
                created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                project=project,
                origin_id=origin['id'],
                flm_session=flm_session
            )
        else:
            if (conflicts is None) or (conflicts == 'abort'):
                raise flz.errors.NameNotUniqueError(
                    'Dataset {} already processed'.format(processed['name']))
            elif conflicts == 'skip' or conflicts == 'overwrite':
                if len(processed) == 1:
                    return Dataset.from_flexilims(data_series=processed.iloc[0])
                else:
                    raise flz.errors.NameNotUniqueError(
                        '{} {} datasets exists for {}, which one to return?'.format(
                            len(processed),
                            dataset_type,
                            origin['name']
                        ))

    @staticmethod
    def _format_series_to_kwargs(flm_series):
        """Format a flm get reply into kwargs valid for Dataset constructor"""
        flm_attributes = {'id', 'type', 'name', 'incrementalId', 'createdBy',
                          'dateCreated', 'origin_id', 'objects',
                          'customEntities', 'project'}
        d = dict()
        for k, v in flm_series.items():
            d[k] = v
        attr = {k: v for k, v in flm_series.items() if k not in flm_attributes}
        kwargs = dict(path=attr.pop('path'),
                      is_raw=attr.pop('is_raw', None),
                      dataset_type=attr.pop('dataset_type'),
                      created=attr.pop('created', None),
                      origin_id=flm_series.get('origin_id', None),
                      extra_attributes=attr,
                      project_id=flm_series.project,
                      name=flm_series.name)
        return kwargs

    def __init__(self, path, is_raw, dataset_type, name=None, extra_attributes=None,
                 created=None, project=None, project_id=None, origin_id=None,
                 flm_session=None):
        """Construct a dataset manually. Is usually called through static methods
        'from_folder', 'from_flexilims', or 'from_origin'

        Args:
            path: folder containing the dataset or path to file (valid only for single
                  file datasets)
            is_raw: bool, used to sort in raw and processed subfolders
            dataset_type: type of the dataset, must be in PARAMETERS['dataset_types']
            name: name of the dataset as on flexilims. Is expected to include mouse,
                  session etc...
            extra_attributes: dict, optional attributes.
            created: Creation date, in "YYYY-MM-DD HH:mm:SS"
            project: name of the project. Must be in config, can be guessed from
                     project_id
            project_id: hexadecimal code for the project. Must be in config, can be
                        guessed from project
            flm_session: authentication session to connect to flexilims
        """
        self.mouse = None
        self.session = None
        self.recording = None
        self.dataset_name = None
        self.name = name
        self.path = Path(path)
        self.is_raw = is_raw
        self.dataset_type = str(dataset_type)
        self.extra_attributes = extra_attributes if extra_attributes is not None else {}
        self.created = created
        self.origin_id = origin_id
        if project is not None:
            self.project = project
            if project_id is not None:
                assert self.project_id == project_id
        elif project_id is not None:
            self.project_id = project_id
        else:
            self._project = None
            self._project_id = None
        self.flm_session = flm_session

    def is_valid(self):
        """
        Dummy method definition. Should be reimplemented in children classes

        Should return True if the dataset is found a valid, false otherwise
        """
        raise NotImplementedError('`is_valid` is not defined for generic datasets')

    def associated_files(self, folder=None):
        """Give a list of all files associated with this dataset

        Args:
            folder: Where to look for files? default to self.path

        Returns:
        """
        raise NotImplementedError('`associated_files` is not defined for generic '
                                  'datasets')

    def get_flexilims_entry(self):
        """Get the flexilims entry for this dataset

        Returns:
            dict: a dictionary or [] if the entry is not found
        """
        if self.project_id is None:
            raise IOError('You must specify the project to get flexilims status')
        if self.name is None:
            raise IOError('You must specify the dataset name to get flexilims status')
        series = flz.get_entity(datatype='dataset',
                                project_id=self.project_id,
                                name=self.name,
                                flexilims_session=self.flm_session)
        return series

    def update_flexilims(self, mode='safe'):
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
        status = self.flexilims_status()
        attributes = self.extra_attributes.copy()
        # the following lines are necessary because pandas converts python types to numpy
        # types, which JSON does not understand
        for attribute in attributes:
            if isinstance(attributes[attribute], np.integer):
                attributes[attribute] = int(attributes[attribute])
            if isinstance(attributes[attribute], np.bool_):
                attributes[attribute] = bool(attributes[attribute])

        if status == 'different':
            if mode == 'safe':
                raise FlexilimsError('Cannot change existing flexilims entry with '
                                     'mode=`safe`')
            if (mode == 'overwrite') or (mode == 'update'):
                # I need to pack the dataset field in attributes
                fmt = self.format()
                for field in ['path', 'created', 'is_raw', 'dataset_type']:
                    attributes[field] = fmt[field]

                # reseting origin_id to null is not implemented. Specifically check
                # that it is not attempted and crash if it is
                if self.origin_id is None:
                    if self.get_flexilims_entry().get('origin_id', None) is not None:
                        raise FlexilimsError('Cannot set origin_id to null')

                resp = flz.update_entity(
                    datatype='dataset',
                    name=self.name,
                    origin_id=self.origin_id,
                    mode=mode,
                    attributes=attributes,
                    project_id=self.project_id,
                    flexilims_session=self.flm_session
                )
            else:
                raise IOError('`mode` must be `safe`, `overwrite` or `update`')
            return resp
        if status == 'up-to-date':
            print('Already up to date, nothing to do')
            return
        # we are in 'not online' case
        utils.clean_dictionary_recursively(attributes)
        resp = flz.add_dataset(
            parent_id=self.origin_id,
            dataset_type=self.dataset_type,
            created=self.created,
            path=str(self.path),
            is_raw='yes' if self.is_raw else 'no',
            project_id=self.project_id,
            dataset_name=self.name,
            attributes=attributes,
            flexilims_session=self.flm_session,
            conflicts='abort',
        )
        # update the dataset name to reflex the potential new index due to append
        online_name = resp['name']
        root_name = '_'.join([e for e in [self.mouse, self.session, self.recording] if e
                             is not None])
        assert online_name.startswith(root_name)
        self.dataset_name = online_name[len(root_name) + 1:]
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
            return 'not online'
        differences = self.flexilims_report(flm_data=series)
        if len(differences):
            return 'different'
        return 'up-to-date'

    def flexilims_report(self, flm_data=None):
        """Describe the difference between the dataset and what is on flexilims

        Differences are returned in a dictionary:
        property: (value in dataset, value in flexilims)

        Attributes not present in either dataset or on flexilims are labelled as 'N/A'
        """
        if flm_data is None:
            flm_data = self.get_flexilims_entry()
            if flm_data is None:
                raise IOError('No flexilims entry for dataset %s' % self.name)

        # remove the flexilims keywords that are not used by Dataset if they are present
        flm_data = flm_data.drop(['createdBy', 'objects', 'dateCreated', 'customEntities',
                                  'incrementalId', 'id'], errors='ignore')
        # add the fields that are always present in Dataset but returned by flexilims
        # only when they are non null
        for na_field in ['origin_id', 'is_raw', 'dataset_type', 'path', 'created']:
            if na_field not in flm_data:
                flm_data[na_field] = None
        fmt = self.format()

        differences = utils.compare_series(fmt, flm_data, series_name=('offline', 'flexilims'))
        return differences

    def format(self, mode='flexilims'):
        """Format a dataset

        This can generate either a 'flexilims' type of output (a series similar to
        get_entities output) or a 'yaml' type as that used by flexiznam.camp

        The flexilims series will not include elements that are not used by the Dataset
        class such as created_by

        Args:
            mode: 'flexilims' or 'yaml'
        """
        data = dict(path=str(self.path),
                    created=self.created,
                    dataset_type=self.dataset_type,
                    is_raw='yes' if self.is_raw else 'no',
                    name=self.name,
                    project=self.project_id,
                    origin_id=self.origin_id,
                    type='dataset')

        if mode.lower() == 'flexilims':
            data.update(self.extra_attributes)
            series = pd.Series(data, name=self.name)
            return series
        elif mode.lower() == 'yaml':
            data['extra_attributes'] = self.extra_attributes
            return data
        else:
            raise IOError('Unknown mode "%s". Must be `flexilims` or `yaml`' % mode)

    @property
    def project_id(self):
        """Hexadecimal ID of the parent project. Must be defined in config project list"""
        return self._project_id

    @project_id.setter
    def project_id(self, value):
        project = flz.main._lookup_project(value, flz.PARAMETERS)
        if project is None:
            raise IOError('Unknown project ID. Please update config file')
        self._project = project
        self._project_id = value

    @property
    def project(self):
        """Parent project. Must be defined in config project list"""
        return self._project

    @project.setter
    def project(self, value):
        if value not in flz.PARAMETERS['project_ids']:
            raise IOError('Unknown project name. Please update config file')

        proj_id = flz.PARAMETERS['project_ids'][value]
        self._project_id = proj_id
        self._project = value

    @property
    def name(self):
        """Full name of the dataset, including mouse, session etc ..."""
        if self.dataset_name is None:
            return
        elements = [getattr(self, w) for w in ('mouse', 'session', 'recording',
                                               'dataset_name')]
        name = '_'.join([e for e in elements if e is not None])
        return name

    @name.setter
    def name(self, value):
        """Set the name if it is correctly formatted"""
        if value is None:
            for w in ('mouse', 'session', 'recording', 'dataset_name'):
                setattr(self, w, None)
            return
        try:
            match = Dataset.parse_dataset_name(value)
        except DatasetError as err:
            raise DatasetError('Cannot parse dataset name. ' + err.args[0] +
                               '\nSet self.mouse, self.session, self.recording, and '
                               'self.dataset_name individually')
        self.mouse = match['mouse']
        self.dataset_name = match['dataset']
        self.session = match['session']
        self.recording = match['recording']

    @property
    def dataset_type(self):
        """Type of the dataset. Must be in PARAMETERS['dataset_types']"""
        return self._dataset_type

    @dataset_type.setter
    def dataset_type(self, value):
        if value.lower() not in PARAMETERS['dataset_types']:
            raise IOError('dataset_type "%s" not valid. Valid types are: '
                          '%s' % (value, PARAMETERS['dataset_types']))
        self._dataset_type = value.lower()

    @property
    def is_raw(self):
        """Is that dataset containing raw or processed data?"""
        return self._is_raw

    @is_raw.setter
    def is_raw(self, value):
        if isinstance(value, str):
            if value.lower() == 'yes':
                value = True
            elif value.lower() == 'no':
                value = False
            else:
                raise IOError('is_raw must be `yes` or `no`')
        else:
            value = bool(value)
        self._is_raw = value

    @property
    def path_root(self):
        """Get CAMP root path that should apply to this dataset"""
        if self.is_raw:
            return Path(flz.config.PARAMETERS['data_root']['raw'])
        else:
            return Path(flz.config.PARAMETERS['data_root']['processed'])

    @property
    def path_full(self):
        """Get full path including the CAMP root"""
        return self.path_root / self.path
