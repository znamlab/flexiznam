"""
Class to handle dataset identification and validation
"""
import pathlib
import re

import pandas as pd
import flexiznam as fzn
from flexiznam.utils import compare_series
from flexiznam.errors import FlexilimsError, DatasetError


class Dataset(object):
    """Master class. Should be inherited by all datasets

    SUBCLASSES are held in different files and added to the Dataset class by
    schema.__init__.py
    """
    VALID_TYPES = ('scanimage', 'camera', 'ephys', 'suite2p_rois', 'suite2p_traces', 'harp')
    SUBCLASSES = dict()

    @staticmethod
    def parse_dataset_name(name):
        """Parse a name into mouse, session, recording, dataset_name

        Returns None if parsing fails, a dictionary otherwise
        """
        pattern = '(?P<mouse>.*?)_(?P<session>S\d{8})_?(?P<session_num>\d+)?'
        pattern += '_?(?P<recording>R\d{6})?_?(?P<recording_num>\d+)?'
        pattern += '_(?P<dataset>.*)'
        match = re.match(pattern, name)
        if not match:
            raise DatasetError('No match in: `%s`. Must be `<MOUSE>_SXXXXXX[...]_<DATASET>`.' % name)
        # group session num and recording num together
        output = match.groupdict()
        sess_num = output.pop('session_num')
        if sess_num is not None:
            if output['session'] is None:
                raise DatasetError('Found session number but not session name in `%s`' % name)
            output['session'] += '_%s' % sess_num
        rec_num = output.pop('recording_num')
        if rec_num is not None:
            if output['recording'] is None:
                raise DatasetError('Found recording number but not recording name in `%s`' % name)
            output['recording'] += '_%s' % rec_num
        return output


    @classmethod
    def from_folder(cls, folder, verbose=True):
        """Try to load all datasets found in the folder.

        Will try all defined subclasses of datasets and keep everything that does not crash
        If you know which dataset to expect, use the subclass directly
        """
        data = dict()
        if not cls.SUBCLASSES:
            raise IOError('Dataset subclasses not assigned')
        for ds_type, ds_class in cls.SUBCLASSES.items():
            if verbose:
                print('Looking for %s' % ds_type)
            try:
                res = ds_class.from_folder(folder, verbose=verbose)
            except OSError:
                continue
            if any(k in data for k in res):
                raise DatasetError('Found two datasets with the same name')
            data.update(res)
        return data

    @staticmethod
    def from_flexilims(project=None, name=None, data_series=None):
        """Loads a dataset from flexilims.


        If the dataset_type attribute of the flexilims entry defined in Dataset.SUBCLASSES, this
        subclass will be used. Otherwise a generic Dataset is returned

        Args:
            project: Name of the project or hexadecimal project_id
            name: Unique name of the dataset on flexilims
            data_series: default to None. pd.Series as returned by fzn.get_entities. If provided, superseeds project and
                         name
        """
        if data_series is not None:
            if (project is not None) or (name is not None):
                raise AttributeError('Specify either data_series OR project + name')
        else:
            data_series = fzn.get_entities(project_id=project, datatype='dataset', name=name)
            assert len(data_series) == 1
            data_series = data_series.loc[name]
        dataset_type = data_series.dataset_type
        if dataset_type in Dataset.SUBCLASSES:
            return Dataset.SUBCLASSES[dataset_type].from_flexilims(data_series=data_series)
        # No subclass, let's do it myself
        kwargs = Dataset._format_series_to_kwargs(data_series)
        name = kwargs.pop('name')
        ds = Dataset(**kwargs)
        ds = Dataset(**kwargs)
        try:
            ds.name = name
        except DatasetError:
            print('\n!!! Cannot parse the name !!!\nWill not set mouse, session or recording')
            ds.dataset_name = name
        return ds

    @staticmethod
    def _format_series_to_kwargs(flm_series):
        """Format a flm get reply into kwargs valid for Dataset constructor"""
        flm_attributes = {'id', 'type', 'name', 'incrementalId', 'createdBy', 'dateCreated', 'origin_id', 'objects',
                          'customEntities', 'project'}
        d = dict()
        for k, v in flm_series.items():
            d[k] = v
        attr = {k: v for k, v in flm_series.items() if k not in flm_attributes}
        kwargs = dict(path=attr.pop('path'),
                      is_raw=attr.pop('is_raw'),
                      dataset_type=attr.pop('dataset_type'),
                      created=attr.pop('created', None),
                      extra_attributes=attr,
                      project_id=flm_series.project,
                      name=flm_series.name)
        return kwargs

    def __init__(self, path, is_raw, dataset_type, name=None, extra_attributes={}, created=None, project=None,
                 project_id=None):
        """Construct a dataset manually. Is usually called through static methods 'from_folder' or 'from_flexilims'

        Args:
            path: folder containing the dataset or path to file (valid only for single file datasets)
            is_raw: bool, used to sort in raw and processed subfolders
            dataset_type: type of the dataset, must be in Dataset.VALID_TYPES
            name: name of the dataset as on flexilims. Is expected to include mouse, session etc...
            extra_attributes: optional attributes.
            created: Creation date, in "YYYY-MM-DD HH:mm:SS"
            project: name of the project. Must be in config, can be guessed from project_id
            project_id: hexadecimal code for the project. Must be in config, can be guessed from project
        """
        self.mouse = None
        self.session = None
        self.recording = None
        self.dataset_name = None
        self.name = name
        self.path = pathlib.Path(path)
        self.is_raw = is_raw
        self.dataset_type = str(dataset_type)
        self.extra_attributes = extra_attributes
        self.created = str(created)
        if project is not None:
            self.project = project
            if project_id is not None:
                assert self.project_id == project_id
        elif project_id is not None:
            self.project_id = project_id
        else:
            self._project = None
            self._project_id = None

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
        raise NotImplementedError

    def get_flexilims_entry(self):
        """Get the flexilims entry for this dataset

        return a dictionary or [] if the entry is not found
        """
        if self.project_id is None:
            raise IOError('You must specify the project to get flexilims status')
        if self.name is None:
            raise IOError('You must specify the dataset name to get flexilims status')
        series = fzn.get_entity(datatype='dataset', project_id=self.project_id, name=self.name)
        return series

    def update_flexilims(self, parent_id, mode='safe'):
        """Create or update (not implemented) flexilims entry for this dataset

        Args:
            parent_id: ID of the parent on flexilims
            mode: One of: 'update', 'overwrite', 'safe' (default).
                  If 'safe', will only create entry if it does not exist online.
                  If 'update' [NotImplemented] will update existing entry.
                  If 'overwrite' [NotImplemented] will delete existing entry and upload a new.

        Returns: Flexilims reply
        """
        status = self.flexilims_status()
        if status == 'different':
            if mode == 'safe':
                raise FlexilimsError('Cannot change existing flexilims entry with mode=`safe`')
            raise NotImplementedError('Updating entries is not')
        if status == 'up-to-date':
            print('Already up to date, nothing to do')
            return
        # we are in 'not online' case
        resp = fzn.add_dataset(parent_id=parent_id, dataset_type=self.dataset_type, created=self.created,
                               path=self.path, is_raw='yes' if self.is_raw else 'no', project_id=self.project_id,
                               dataset_name=self.name, attributes=self.extra_attributes)
        return resp

    def flexilims_status(self):
        """Status of the dataset on flexilims

        Status can be 'up-to-date', 'different' or 'not online'

        This function does not check flexilims these only value:
        'createdBy', 'objects', 'dateCreated', 'customEntities',
        'incrementalId', 'id', 'origin_id'
        """
        series = self.get_flexilims_entry()
        if not len(series):
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
            if not len(flm_data):
                raise IOError('No flexilims entry for dataset %s' % self.name)

        # remove the flexilims keywords that are not used by Dataset
        flm_data = flm_data.drop(['createdBy', 'objects', 'dateCreated', 'customEntities', 'incrementalId',
                                  'id', 'origin_id'])
        fmt = self.format()

        differences = compare_series(fmt, flm_data)
        return differences

    def format(self, mode='flexilims'):
        """Format a dataset

        This can generate either a 'flexilims' type of output (a series similar to get_entities output) or a 'yaml'
        type as that used by flexiznam.camp

        The flexilims series will not include elements that are not used by the Dataset class such as created_by

        Args:
            mode: 'flexilims' or 'yaml'
        """
        data = dict(path=str(self.path), created=self.created, dataset_type=self.dataset_type,
                    is_raw='yes' if self.is_raw else 'no')
        data.update(self.extra_attributes)
        if mode.lower() == 'flexilims':
            data.update(dict(name=self.name, project=self.project_id, type='dataset'))
            series = pd.Series(data, name=self.name)
            return series
        elif mode.lower() == 'yaml':
            return data
        else:
            raise IOError('Unknown mode "%s". Must be `flexilims` or `yaml`' % mode)

    @property
    def project_id(self):
        """Hexadecimal ID of the parent project. Must be defined in config project list"""
        return self._project_id

    @project_id.setter
    def project_id(self, value):
        project = fzn.main._lookup_project(value, fzn.PARAMETERS)
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
        if value not in fzn.PARAMETERS['project_ids']:
            raise IOError('Unknown project name. Please update config file')

        proj_id = fzn.PARAMETERS['project_ids'][value]
        self._project_id = proj_id
        self._project = value

    @property
    def name(self):
        """Full name of the dataset, including mouse, session etc ..."""
        if self.dataset_name is None:
            return
        elements = [getattr(self, w) for w in ('mouse', 'session', 'recording', 'dataset_name')]
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
                               '\nSet self.mouse, self.session, self.recording, and self.dataset_name individually')
        self.mouse = match['mouse']
        self.dataset_name = match['dataset']
        self.session = match['session']
        self.recording = match['recording']

    @property
    def dataset_type(self):
        """Type of the dataset. Must be in Dataset.VALID_TYPES"""
        return self._dataset_type

    @dataset_type.setter
    def dataset_type(self, value):
        if value.lower() not in Dataset.VALID_TYPES:
            raise IOError('dataset_type "%s" not valid. Valid types are: %s' % (value, Dataset.VALID_TYPES))
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
