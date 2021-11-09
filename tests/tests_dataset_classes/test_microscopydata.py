import pytest
import pathlib
import pandas as pd
from flexiznam.schema import MicroscopyData
from flexiznam.config import PARAMETERS
from flexiznam.errors import DatasetError, NameNotUniqueError, FlexilimsError
from tests.tests_resources.acq_yaml_and_files import TEST_PROJECT

# Test creation of all dataset types.
#
# For each dataset type we want to test:
# - Creating by direct call
# - Creating from_flexilims
# - Creating from_origin
# - Creating from_folder


def test_from_folder():
    raw_folder = pathlib.Path(PARAMETERS['data_root']['raw']) / TEST_PROJECT
    ds = MicroscopyData.from_folder(raw_folder / 'PZAJ5.1a',
                                    verbose=False,
                                    mouse=None, flm_session=None)
    assert len(ds) == 6
    d = ds['Stitch_A01_binned.tif']
    assert d.name == 'Stitch_A01_binned.tif'
    assert d.is_valid()
    #/Volumes/lab-znamenskiyp/data/instruments/raw_data/projects/demo_project/PZAJ5.1a