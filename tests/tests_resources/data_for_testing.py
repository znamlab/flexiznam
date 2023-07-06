"""A list of file coming from one experiment"""
from pathlib import Path
import datetime
from flexiznam.config import PARAMETERS


MOUSE_ID = "6437dcb13ded9c65df142a12"
TEST_PROJECT = "demo_project"
PROJECT_ID = "610989f9a651ff0b6237e0f6"
DATA_ROOT = Path(PARAMETERS["data_root"]["raw"]) / TEST_PROJECT
PROCESSED_ROOT = Path(PARAMETERS["data_root"]["processed"]) / TEST_PROJECT

if not DATA_ROOT.is_dir():
    print("WARNING: cannot find test data, most tests will fail\n")
