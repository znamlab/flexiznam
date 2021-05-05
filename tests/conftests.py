import os
from flexiznam import utils
import pytest


@pytest.fixture(scope="session")
def create_config(tmp_path_factory):
    config_file = tmp_path_factory.mktemp('config.yaml')
    utils.create_config(target=config_file)
    return config_file
