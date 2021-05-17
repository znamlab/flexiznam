"""
Class to handle dataset identification and validation
"""
import pathlib

import flexiznam
import flexiznam as fzn


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
                raise AttributeError('Specify either flm_rep OR project and name')
        else:
            data_series = fzn.get_entities(project_id=project, datatype='dataset', name=name)
            assert len(data_series) == 1
            data_series = data_series.loc[name]
        dataset_type = data_series.dataset_type
        if dataset_type in Dataset.SUBCLASSES:
            return Dataset.SUBCLASSES[datatype].from_flexilims(rep=rep)
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

    def get_flexilims_entry(self):
        """Get the flexilims entry for this dataset

        return a dictionary or [] if the entry is not found
        """
        if self.project_id is None:
            raise IOError('You must specify the project to get flexilims status')
        if self.name is None:
            raise IOError('You must specify the dataset name to get flexilims status')
        sess = fzn.get_session(self.project_id)
        rep = sess.get(datatype='dataset', name=self.name)
        if rep:
            assert len(rep) == 1
            rep = rep[0]
        return rep

    def flexilims_status(self):
        """Status of the dataset on flexilims

        Status can be 'up-to-date', 'different' or 'not online'
        """
        rep = self.get_flexilims_entry()
        if not len(rep):
            return 'not online'
        differences = self.flexilims_report(flm_data=rep)
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
            if not flm_data:
                raise IOError('No flexilims entry for dataset %s' % self.name)

        differences = dict()
        fmt = self.format()
        # need to deal with the attributes differently as they are not guaranteed to be all present
        dst_attr = fmt.pop('attributes')
        flm_attr = flm_data.pop('attributes')
        # flatten with the non valid keys to "N/A"
        all_keys = set(dst_attr.keys()).union(set(flm_attr.keys()))
        for k in all_keys:
            fmt[k] = dst_attr.get(k, "N/A")
            flm_data[k] = flm_attr.get(k, "N/A")

        for k, v in fmt.items():
            if flm_data[k] != v:
                differences[k] = (v, flm_data[k])
        return differences

    def format(self):
        """Format a dataset as a flexilims output

        This will not include elements that are not used by the Dataset class such as created_by for instance"""
        attributes = dict(path=str(self.path), created=self.created, dataset_type=self.dataset_type,
                          is_raw='yes' if self.is_raw else 'no')
        attributes.update(self.extra_attributes)
        return dict(attributes=attributes, name=self.name, project=self.project_id, type='dataset')

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

    def is_valid(self):
        """
        Dummy method definition. Should be reimplemented in children classes

        Should return True if the dataset is found a valid, false otherwise
        """
        raise NotImplementedError

