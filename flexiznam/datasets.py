"""
Class to handle dataset identification and validation
"""
import os
import pathlib
import flexiznam as fzn
import datetime


class Dataset(object):
    """Master class. Should be inherited by all datasets"""
    VALID_TYPES = ('scanimage', 'camera', 'ephys', 'suite2p_rois', 'suite2p_traces', 'harp')

    def __init__(self, path, is_raw, dataset_type, extra_attributes={}, created=None, project=None, name=None):
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
        if project is None:
            self._project = None
            self._project_id = None
        else:
            self.project = project

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
        id_projects = {v: k for k, v in fzn.PARAMETERS['project_ids'].items()}
        if value not in id_projects:
            raise IOError('Unknown project ID. Please update config file')
        project = id_projects[value]
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


class Camera(Dataset):
    DATASET_TYPE = 'camera'
    VIDEO_EXTENSIONS = {'.mp4', '.bin', '.avi'}
    VALID_EXTENSIONS = {'.txt', '.csv'}.union(VIDEO_EXTENSIONS)

    @staticmethod
    def from_folder(folder, camera_name=None, verbose=True):
        """Create a Camera dataset by loading info from folder"""
        fnames = [f for f in os.listdir(folder) if f.endswith(tuple(Camera.VALID_EXTENSIONS))]
        metadata_files = [f for f in fnames if f.endswith('_metadata.txt')]
        if not metadata_files:
            raise IOError('Cannot find metadata')
        timestamp_files = [f for f in fnames if f.endswith('_timestamps.csv')]
        if not timestamp_files:
            raise IOError('Cannot find timestamp')
        metadata_names = {'_'.join(fname.split('_')[:-1]) for fname in metadata_files}
        timestamp_names = {'_'.join(fname.split('_')[:-1]) for fname in timestamp_files}
        valid_names = metadata_names.intersection(timestamp_names)
        if not valid_names:
            raise IOError('Metadata do not correspond to timestamps')
        if verbose:
            print()
        video_files = [f for f in fnames if f.endswith(tuple(Camera.VIDEO_EXTENSIONS))]

        if camera_name is not None:
            if camera_name not in valid_names:
                raise IOError('Camera %s not found. I have %s' % (camera_name, valid_names))
            valid_names = {camera_name}
        elif verbose:
            print('Found metadata and timestamps for %d cameras: %s' % (len(valid_names), valid_names))
        output = dict()
        for camera_name in valid_names:
            vid = [f for f in video_files if f.startswith(camera_name)]
            if not vid:
                raise IOError('No video data for %s' % camera_name)
            if len(vid) > 1:
                raise IOError('Found more than one potential video file for camera %s' % camera_name)
            video_path = pathlib.Path(folder) / vid[0]
            created = datetime.datetime.fromtimestamp(video_path.stat().st_mtime)
            output[camera_name] = Camera(name=camera_name, path=folder, camera_name=camera_name,
                                         timestamp_file='%s_timestamps.csv' % camera_name,
                                         metadata_file='%s_metadata.txt' % camera_name, video_file=vid[0],
                                         created=created.strftime('%Y-%m-%d %H:%M:%S'))
        return output

    def __init__(self, name, path, camera_name, timestamp_file, metadata_file, video_file,
                 extra_attributes={}, created=None, project=None, is_raw=True):
        super().__init__(name=name, path=path, is_raw=is_raw, dataset_type=Camera.DATASET_TYPE,
                         extra_attributes=extra_attributes, created=created, project=project)
        self.camera_name = camera_name
        self.timestamp_file = timestamp_file
        self.metadata_file = metadata_file
        self.video_file = video_file

    def is_valid(self):
        """Check that video, metadata and timestamps files exist"""
        fnames = os.listdir(self.path)
