import pytest
import pathlib
from flexiznam.schema import CameraData
from tests.tests_resources import data_for_testing as test_data
from flexiznam.config import PARAMETERS


import pandas as pd
from flexiznam.schema import CameraData
from flexiznam.config import PARAMETERS
from flexiznam.errors import DatasetError, NameNotUniqueError, FlexilimsError
from tests.tests_resources import acq_yaml_and_files

# Test creation of all dataset types.
#
# For each dataset type we want to test:
# - Creating by direct call
# - Creating from_flexilims
# - Creating from_origin
# - Creating from_folder


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

