"""
Class to handle dataset identification and validation
"""
import pathlib

import flexiznam
import flexiznam as fzn
import pandas as pd


class Dataset(object):
    """Master class. Should be inherited by all datasets

    SUBCLASSES are held in different files and added to the Dataset class by
    schema.__init__.py
    """
    VALID_TYPES = ('scanimage', 'camera', 'ephys', 'suite2p_rois', 'suite2p_traces', 'harp')
    SUBCLASSES = dict()

    @classmethod
    def from_folder(cls, folder):
        """Try to load all datasets found in the folder.

        Will try all defined subclasses of datasets and keep everything that does not crash
        If you know which dataset to expect, use the subclass directly
        """
        data = dict()
        for ds_type, ds_class in cls.VALID_TYPES.items():
            try:
                res = ds_class.from_folder(folder)
            except OSError:
                continue
            data[ds_type] = res
        return res

    @staticmethod
    def from_flexilims(project=None, name=None, data_series=None):
        """Loads a dataset from flexilims.


        If the dataset_type attribute of the flexilims entry defined in Dataset.SUBCLASSES, this
        subclass will be used. Otherwise a generic Dataset is returned

        Args:
            project: Name of the project or hexadecimal project_id
            name: Unique name of the dataset on flexilims
            data_series: default to None. pd.Series as returned by fzn.get_entities. If provided, superseeds project and name
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
        ds = Dataset(**kwargs)
        return ds

    @staticmethod
    def _format_series_to_kwargs(flm_series):
        """Format a flm get reply into kwargs valid for Dataset constructor"""
        flm_attributes = {'id', 'type', 'name', 'incrementalId', 'createdBy', 'dateCreated', 'origin_id', 'objects',
                          'customEntities',  'project'}
        d = dict()
        for k,v in flm_series.items():
            d[k] = v
        attr = {k:v for k, v in flm_series.items() if k not in flm_attributes}
        kwargs = dict(path=attr.pop('path'),
                      is_raw=attr.pop('is_raw'),
                      dataset_type=attr.pop('dataset_type'),
                      created=attr.pop('created', None),
                      extra_attributes=attr,
                      project_id=flm_series.project,
                      name=flm_series.name)
        return kwargs

    def __init__(self, path, is_raw, dataset_type, extra_attributes={}, created=None, project=None, name=None,
                 project_id=None):
        """Construct a dataset manually"""
        if name is not None:
            self.name = str(name)
        else:
            self._name = None
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

    def get_flexilims_entry(self):
        """Get the flexilims entry for this dataset

        return a dictionary or [] if the entry is not found
        """
        if self.project_id is None:
            raise IOError('You must specify the project to get flexilims status')
        if self.name is None:
            raise IOError('You must specify the dataset name to get flexilims status')
        series = fzn.get_entities(datatype='dataset', project_id=self.project_id, name=self.name)
        if len(series):
            assert len(series) == 1
            series = series.iloc[0]
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
        if (status == 'different'):
            raise NotImplementedError('Updating entries is not')
        if (status == 'up-to-date'):
            print('Already up to date, nothing to do')
            return
        # we are in 'not online' case
        resp = fzn.add_dataset(parent_id=parent_id, dataset_type=self.dataset_type, created=self.created, path=self.path,
                        is_raw='yes' if self.is_raw else 'no', project_id=self.project_id, dataset_name=self.name,
                        attributes=self.extra_attributes)
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
        offline_index = set(fmt.index)
        online_index = set(flm_data.index)

        intersection = offline_index.intersection(online_index)
        differences = fmt[intersection].compare(flm_data[intersection])
        differences.columns = ['offline', 'flexilims']

        only_offline = offline_index - online_index
        off = pd.DataFrame([fmt[only_offline].rename('offline', axis=0),
                            pd.Series({k: 'N/A' for k in only_offline}, name='flexilims')])
        differences = pd.concat((differences, off.T))

        only_online = online_index - offline_index
        online = pd.DataFrame([pd.Series({k: 'N/A' for k in only_online}, name='offline'),
                            flm_data[only_online].rename('flexilims', axis=0)])
        differences = pd.concat((differences, online.T))
        return differences

    def format(self):
        """Format a dataset as a series similar to get_entities output

        This will not include elements that are not used by the Dataset class such as created_by for instance
        """
        data = dict(path=str(self.path), created=self.created, dataset_type=self.dataset_type,
                          is_raw='yes' if self.is_raw else 'no')
        data.update(self.extra_attributes)
        data.update(dict(name=self.name, project=self.project_id, type='dataset'))
        series = pd.Series(data, name=self.name)
        return series

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


