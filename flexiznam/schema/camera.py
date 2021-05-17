import datetime
import os
import pathlib

from flexiznam.schema.datasets import Dataset


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

    def from_flexilims(project=None, name=None, flm_rep=None):
        """Create a camera dataset from flexilims entry"""


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
