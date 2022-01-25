import datetime
import os
import pathlib

from flexiznam.schema.datasets import Dataset


class CameraData(Dataset):
    DATASET_TYPE = 'camera'
    VIDEO_EXTENSIONS = {'.mp4', '.bin', '.avi'}
    VALID_EXTENSIONS = {'.txt', '.csv'}.union(VIDEO_EXTENSIONS)

    @staticmethod
    def from_folder(folder, camera_name=None, verbose=True, mouse=None, session=None,
                    recording=None, flm_session=None, project=None):
        """Create a Camera dataset by loading info from folder"""
        fnames = [f for f in os.listdir(folder) if f.endswith(tuple(CameraData.VALID_EXTENSIONS))]
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
        video_files = [f for f in fnames if f.endswith(tuple(CameraData.VIDEO_EXTENSIONS))]

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
            extra_attributes = dict(timestamp_file='%s_timestamps.csv' % camera_name,
                                    metadata_file='%s_metadata.txt' % camera_name,
                                    video_file=vid[0],
)
            output[camera_name] = CameraData(path=folder,
                                             extra_attributes=extra_attributes,
                                             created=created.strftime('%Y-%m-%d '
                                                                      '%H:%M:%S'),
                                             flm_session=flm_session,
                                             project=project)
            for field in ('mouse', 'session', 'recording'):
                setattr(output[camera_name], field, locals()[field])
            output[camera_name].dataset_name = camera_name
        return output

    def __init__(self, path, is_raw=None, name=None, extra_attributes=None,
                 created=None, project=None, project_id=None, origin_id=None,
                 flm_session=None):
        """Create a Camera dataset

        Args:
            path: folder containing the dataset or path to file (valid only for single
                  file datasets)
            is_raw: bool, used to sort in raw and processed subfolders
            name: name of the dataset as on flexilims. Is expected to include mouse,
                  session etc...
            extra_attributes: dict, optional attributes.
            created: Creation date, in "YYYY-MM-DD HH:mm:SS"
            project: name of the project. Must be in config, can be guessed from
                     project_id
            project_id: hexadecimal code for the project. Must be in config, can be
                        guessed from project
            origin_id: hexadecimal code for the origin on flexilims.
            flm_session: authentication session to connect to flexilims

        Expected extra_attributes:
            video_file: file name of the video file, usually
                        camera_name_data.bin/.avi/.mp4
            timestamp_file (optional): file name of the timestamp file, usually
                            camera_name_timestamps.csv
            metadata_file (optional): file name of the metadata file, usually
                           camera_name_metadata.txt
        """
        if 'video_file' not in extra_attributes:
            raise IOError('Camera dataset require to have `video_file` in extra '
                          'attributes')

        super().__init__(name=name, path=path, is_raw=is_raw,
                         dataset_type=CameraData.DATASET_TYPE,
                         extra_attributes=extra_attributes, created=created,
                         project=project, project_id=project_id,
                         origin_id=origin_id, flm_session=flm_session)

    @property
    def timestamp_file(self):
        return self.extra_attributes.get('timestamp_file', None)
    
    @timestamp_file.setter
    def timestamp_file(self, value):
        self.extra_attributes['timestamp_file'] = str(value)

    @property
    def metadata_file(self):
        return self.extra_attributes.get('metadata_file', None)

    @metadata_file.setter
    def metadata_file(self, value):
        self.extra_attributes['metadata_file'] = str(value)

    @property
    def video_file(self):
        return self.extra_attributes.get('video_file', None)

    @video_file.setter
    def video_file(self, value):
        self.extra_attributes['video_file'] = str(value)

    def is_valid(self):
        """Check that video, metadata and timestamps files exist"""
        if not (pathlib.Path(self.path) / self.timestamp_file).exists():
            return False
        if not (pathlib.Path(self.path) / self.metadata_file).exists():
            return False
        if not (pathlib.Path(self.path) / self.video_file).exists():
            return False
        return True
