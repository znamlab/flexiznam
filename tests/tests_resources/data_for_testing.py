"""A list of file coming from one experiment"""
from pathlib import Path
import datetime
from flexiznam.config import PARAMETERS


MOUSE_ID = '628f8cf4527421769cdd4bfb'
TEST_PROJECT = 'demo_project'
DATA_ROOT = Path(PARAMETERS['data_root']['raw']) / TEST_PROJECT
PROCESSED_ROOT = Path(PARAMETERS['data_root']['processed']) / TEST_PROJECT

if not DATA_ROOT.is_dir():
    print('WARNING: cannot find test data, most tests will fail\n')
