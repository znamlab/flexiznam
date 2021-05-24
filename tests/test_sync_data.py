import pytest
import pathlib
from flexiznam.camp import sync_data

znm_folder = pathlib.Path(__file__).parent.absolute()
PATH_TO_FULL_YAML = znm_folder / '..' / 'flexiznam' / 'camp' / 'example_acquisition_yaml.yml'
PATH_TO_MINI_YAML = znm_folder / '..' / 'flexiznam' / 'camp' / 'minimal_example_acquisition_yaml.yml'


def test_clean_yaml():
    sync_data.clean_yaml(PATH_TO_MINI_YAML)
    sync_data.clean_yaml(PATH_TO_FULL_YAML)


def test_parse_yaml(tmpdir):
    sync_data.parse_yaml(PATH_TO_MINI_YAML)
    sess_data = sync_data.parse_yaml(PATH_TO_FULL_YAML, verbose=False)