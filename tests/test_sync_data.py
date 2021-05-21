import pytest
import pathlib
from flexiznam.camp import sync_data

PATH_TO_YAML = pathlib.Path(__file__).parent.absolute() / '..' / 'flexiznam' / 'camp' / 'example_acquisition_yaml.yml'


def test_parse_yaml():
    sync_data.clean_yaml(PATH_TO_YAML)