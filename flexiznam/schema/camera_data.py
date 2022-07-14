import datetime
import os
import pathlib

from flexiznam.schema.datasets import Dataset


class CameraData(Dataset):
    DATASET_TYPE = 'camera'
    VIDEO_EXTENSIONS = {'.mp4', '.bin', '.avi'}
    VALID_EXTENSIONS = {'.txt', '.csv'}.union(VIDEO_EXTENSIONS)

    @staticmethod
    def from_folder(folder, camera_name=None, folder_genealogy=None, is_raw=None,
                    verbose=True, flexilims_session=None, project=None,
                    enforce_validity=True):
        """Create a Camera dataset by loading info from folder

        Args:
            folder (str): path to the folder
            camera_name (str): name of the camera, all file names must start by this name
            folder_genealogy (tuple): genealogy of the folder, if None assume that
                                      the genealogy is just (folder,), i.e. no parents
            is_raw (bool): does this folder contain raw data?
            verbose (bool=True): print info about what is found
            flexilims_session (flm.Session): session to interact with flexilims
            project (str): project ID or name
            enforce_validity (bool): True by default. Refuse to create camera dataset
                                     if they don't have a video, metadata and timestamp
                                     file

        Returns:
            dict of datasets (fzm.schema.camera_data.CameraData)

        """
        if folder_genealogy is None:
            folder_genealogy = (pathlib.Path(folder).stem,)
        elif isinstance(folder_genealogy, list):
            folder_genealogy = tuple(folder_genealogy)

        fnames = [f for f in os.listdir(folder) if
                  f.endswith(tuple(CameraData.VALID_EXTENSIONS))]
        metadata_files = [f for f in fnames if f.endswith('_metadata.txt')]
        if (not metadata_files) and enforce_validity:
            raise IOError('Cannot find metadata')
        timestamp_files = [f for f in fnames if f.endswith('_timestamps.csv')]
        if (not timestamp_files) and enforce_validity:
            raise IOError('Cannot find timestamp')
        metadata_names = {'_'.join(fname.split('_')[:-1]) for fname in metadata_files}
        timestamp_names = {'_'.join(fname.split('_')[:-1]) for fname in timestamp_files}
        valid_names = metadata_names.intersection(timestamp_names)
        if (not valid_names) and enforce_validity:
            raise IOError('Metadata do not correspond to timestamps')
        if verbose:
            print()
        video_files = [f for f in fnames if f.endswith(tuple(CameraData.VIDEO_EXTENSIONS))]

        if not enforce_validity:
            # add camera that are not already in valid_names
            for vid in video_files:
                if any([vid.startswith(vn) for vn in valid_names]):
                    continue
                valid_names.add(pathlib.Path(vid).stem)

        if camera_name is not None:
            if camera_name not in valid_names:
                raise IOError('Camera %s not found. I have %s' % (camera_name, valid_names))
            valid_names = {camera_name}
        elif verbose:
            print('Found metadata and timestamps for %d cameras: %s' % (len(valid_names),
                                                                        valid_names))

        output = dict()
        for camera_name in valid_names:
            vid = [f for f in video_files if f.startswith(camera_name)]
            if not vid:
                raise IOError('No video data for %s' % camera_name)
            if len(vid) > 1:
                raise IOError('Found more than one potential video file for camera %s' % camera_name)
            video_path = pathlib.Path(folder) / vid[0]
            created = datetime.datetime.fromtimestamp(video_path.stat().st_mtime)
            extra_attributes = dict(video_file=vid[0],)
            timestamp_file = '%s_timestamps.csv' % camera_name
            if timestamp_file in timestamp_files:
                extra_attributes['timestamp_file'] = timestamp_file
            elif enforce_validity:
                raise IOError('Error finding timestamp files. I should have it but I '
                              'don''t')
            metadata_file = '%s_metadata.txt' % camera_name
            if metadata_file in metadata_files:
                extra_attributes['metadata_file'] = metadata_file
            elif enforce_validity:
                raise IOError('Error finding metadata files. I should have it but I '
                              'don''t')

            output[camera_name] = CameraData(path=folder,
                                             genealogy=folder_genealogy + (camera_name,),
                                             extra_attributes=extra_attributes,
                                             created=created.strftime('%Y-%m-%d '
                                                                      '%H:%M:%S'),
                                             flexilims_session=flexilims_session,
                                             project=project,
                                             is_raw=is_raw)
        return output

    def __init__(self, path, is_raw, genealogy=None, extra_attributes=None,
                 created=None, project=None, project_id=None, origin_id=None,
                 flexilims_session=None):
        """Create a camera dataset

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
            flexilims_session: authentication session to connect to flexilims


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

        super().__init__(genealogy=genealogy, path=path, is_raw=is_raw,
                         dataset_type=CameraData.DATASET_TYPE,
                         extra_attributes=extra_attributes, created=created,
                         project=project, project_id=project_id, origin_id=origin_id,
                         flexilims_session=flexilims_session)

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
