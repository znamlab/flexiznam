"""
Class to handle dataset identification and validation
"""
import os
import pathlib
import flexiznam as fzn


class Dataset(object):
    """Master class. Should be inherited by all datasets"""
    VALID_TYPES = ('scanimage', 'camera', 'ephys', 'suite2p_rois', 'suite2p_traces', 'harp')

    def __init__(self, project, name, path, is_raw, dataset_type, extra_attributes={}, created=None):
        """Construct a dataset manually"""
        self.name = str(name)
        self.path = pathlib.Path(path)
        self.is_raw = is_raw
        self.dataset_type = str(dataset_type)
        self.extra_attributes = extra_attributes
        self.created = str(created)
        self.project = project

    def flexilims_status(self):
        """Status of the dataset on flexilims

        Status can be 'up-to-date', 'different' or 'not online'
        """
        sess = fzn.get_session(self._projet_id)
        rep = sess.get(datatype='dataset', name=self.name)
        if not len(rep):
            return 'not online'
        assert len(rep) == 1  # name should be unique
        differences = self.flexilims_report(flm_data=rep[0])
        if len(differences):
            return 'different'
        return 'up-to-date'

    def flexilims_report(self, flm_data=None):
        """Describe the difference between the dataset and what is on flexilims"""
        if flm_data is None:
            sess = fzn.get_session(self._projet_id)
            rep = sess.get(datatype='dataset', name=self.name)
            assert len(rep) == 1
            flm_data = rep[0]
        differences = dict()
        for k, v in self.format().items():
            if flm_data[k] != v:
                differences[k] = (v, flm_data[k])
        return differences

    def format(self):
        """Format a dataset as a flexilims output

        This will not include elements that are not used by the Dataset class such as created_by for instance"""
        attributes = dict(path=str(self.path), created=self.created, dataset_type=self.dataset_type,
                          is_raw='yes' if self.is_raw else 'no')
        attributes.update(self.extra_attributes)
        return dict(attributes=attributes, name=self.name, project=self._project_id, type='dataset')

    @property
    def project(self):
        """Parent project. Must be defined in config project list"""
        return self._project

    @project.setter
    def project(self, value):
        proj_id = fzn.PARAMETERS['project_ids'][value]
        self._projet_id = proj_id
        self._project = value

    @property
    def dataset_type(self):
        """Type of the dataset. Must be in Dataset.VALID_TYPES"""
        return self._dataset_type

    @dataset_type.setter
    def dataset_type(self, value):
        assert value.lower() in Dataset.VALID_TYPES
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


class Camera(Dataset):
    DATASET_TYPE = 'camera'

    def __init__(self, path, camera_name):
        super.__init__(self, path)
        self.camera_name = camera_name
        self.timestamps_file = '%s_timestamps.csv' % camera_name
        self.metadata_file = '%s_metadata.txt' % camera_name
        self.video_file = None


    def is_valid(self):
        """Check that video, metadata and timestamps files exist"""
        fnames = os.listdir(self.path)
