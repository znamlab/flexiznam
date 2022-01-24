import pytest
import pathlib
from flexiznam.schema import CameraData, Dataset
from tests.tests_resources import data_for_testing as test_data
from flexiznam.config import PARAMETERS

import pandas as pd

from flexiznam.config import PARAMETERS
from flexiznam.errors import DatasetError, NameNotUniqueError, FlexilimsError
from tests.tests_resources import data_for_testing

# Test creation of all dataset types.
#
# For each dataset type we want to test:
# - Creating by direct call
# - Creating from_folder
# - Creating from_flexilims
# - Creating from_origin?

EX_M = 'PZAD9.4d'
EX_S = 'S20211102'
EX_R = 'R165821_SpheresPermTube'
EX_P = test_data.DATA_ROOT / EX_M / EX_S / EX_R
EX_CAM = 'face_camera'


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
                      project=test_data.TEST_PROJECT,
                      is_raw=True,
                      flm_session=flm_sess)
    assert str(data.path) == 'test_path'
    assert not data.is_valid()
    assert data.name is None
    assert data.timestamp_file == 'camel.csv'

    # then create an actual test dataset
    extra_attributes = dict(timestamp_file='%s_timestamps.csv' % EX_CAM,
                            metadata_file='%s_metadata.txt' % EX_CAM,
                            video_file='%s_data.avi' % EX_CAM, )
    data = CameraData(path=EX_P,
                      name='_'.join([EX_M, EX_S, EX_R, EX_CAM]),
                      extra_attributes=extra_attributes,
                      created='now',
                      project=test_data.TEST_PROJECT,
                      is_raw=True,
                      flm_session=flm_sess)
    assert str(data.path) == str(test_data.DATA_ROOT / EX_P)
    assert data.is_valid()
    assert data.mouse == EX_M
    assert data.session == EX_S
    assert data.recording == EX_R.split('_')[0]  # there is still an issue with rec
    assert data.flexilims_status() == 'not online'
    data.update_flexilims()
    assert data.flexilims_status() == 'up-to-date'


@pytest.mark.integtest
def test_create_from_folder(flm_sess):
    """Test creation from folder

    This method doesn't populate mouse, recording etc...
    """
    data = CameraData.from_folder(folder=EX_P,
                                  camera_name=EX_CAM,
                                  verbose=False,
                                  mouse=None,
                                  session=None,
                                  recording=None,
                                  project=test_data.TEST_PROJECT,
                                  flm_session=flm_sess)
    assert len(data) == 1
    data = data[EX_CAM]

    assert data.name == EX_CAM
    assert str(data.path) == str(EX_P)
    assert data.mouse is None
    assert data.dataset_name == data.name
    assert data.is_valid()
    assert data.project == test_data.TEST_PROJECT
    assert data.flexilims_status() == 'not online'


def test_create_from_flexilims(flm_sess):
    """Create from the flexilims instance made in the test_create_directly"""
    data = CameraData.from_flexilims(project=test_data.TEST_PROJECT,
                                     name='_'.join([EX_M, EX_S, EX_R, EX_CAM]))
    assert data.name == '_'.join([EX_M, EX_S, EX_R, EX_CAM])
    assert str(data.path) == str(EX_P)
    assert data.timestamp_file == 'face_camera_timestamps.csv'

    # I should get the same using the parent dataset class
    data2 = Dataset.from_flexilims(project=test_data.TEST_PROJECT,
                                   name='_'.join([EX_M, EX_S, EX_R, EX_CAM]))
    assert data2.extra_attributes == data.extra_attributes
    assert data2.path == data.path
    assert isinstance(data2, CameraData)



def test_camera(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    miniaml, faml = acq_yaml_and_files.get_example_yaml_files()
    data_dir = tmp_path / acq_yaml_and_files.MOUSE / miniaml['session'] / next(
        iter(miniaml['recordings'].keys()))
    ds = CameraData.from_folder(data_dir, verbose=False)
    assert len(ds) == 4
    d = ds['butt_camera']
    assert d.name == 'butt_camera'
    d.project = 'test'
    assert d.is_valid()
    ds = CameraData.from_folder(data_dir, mouse='testmouse', session='testsession',
                                recording='testrecording')
    assert ds['face_camera'].name == 'testmouse_testsession_testrecording_face_camera'
