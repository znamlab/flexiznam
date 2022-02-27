import pytest
from flexiznam.schema.camera_data import CameraData
from flexiznam.schema.datasets import Dataset
from tests.tests_resources.data_for_testing import DATA_ROOT, TEST_PROJECT


@pytest.mark.integtest
def test_create_directly(flm_sess):
    """Create by directly calling the function"""
    # first just make sure it can create an object without epic failure
    extra_attributes = dict(timestamp_file='camel.csv',
                            metadata_file='none',
                            video_file='none')
    data = CameraData(path='test_path',
                      name=None,
                      extra_attributes=extra_attributes,
                      created='now',
                      project=TEST_PROJECT,
                      is_raw=True,
                      flexilims_session=flm_sess)
    assert str(data.path) == 'test_path'
    assert not data.is_valid()
    assert data.name is None
    assert data.timestamp_file == 'camel.csv'


@pytest.mark.integtest
def test_create_from_folder(flm_sess):
    """Test creation from folder

    This method doesn't populate mouse, recording etc...
    """
    data_dir = DATA_ROOT / 'mouse_physio_2p' / 'S20211102' / 'R165821_SpheresPermTube'
    data = CameraData.from_folder(folder=data_dir,
                                  camera_name=None,
                                  verbose=False,
                                  project=TEST_PROJECT,
                                  flm_session=flm_sess)
    assert len(data) == 5
    data = CameraData.from_folder(folder=data_dir,
                                  camera_name='face_camera',
                                  verbose=False,
                                  project=TEST_PROJECT,
                                  flm_session=flm_sess)
    assert len(data) == 1
    ds = data['face_camera']
    assert ds.flexilims_status() == 'not online'


@pytest.mark.integtest
def test_create_from_flexilims(flm_sess):
    """Create from the flexilims instance made in the test_create_directly"""
    ds_name = 'mouse_physio_2p_S20211102_R173917_SpheresPermTube_face_camera'
    data = CameraData.from_flexilims(project=TEST_PROJECT, name=ds_name)
    data_dir = DATA_ROOT / 'mouse_physio_2p' / 'S20211102' / 'R173917_SpheresPermTube'
    assert data.name == ds_name
    assert str(data.path_full) == str(data_dir)
    assert data.timestamp_file == 'face_camera_timestamps.csv'

    # I should get the same using the parent dataset class
    data2 = Dataset.from_flexilims(project=TEST_PROJECT, name=ds_name)
    assert data2.extra_attributes == data.extra_attributes
    assert data2.path == data.path
    assert isinstance(data2, CameraData)
