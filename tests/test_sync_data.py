import pytest
import pathlib
import yaml
from flexiznam.camp import sync_data
from flexiznam.config import PARAMETERS
from tests.tests_resources import acq_yaml_and_files

def test_clean_yaml(tmp_path):
    path_to_full_yaml = tmp_path / 'full_yaml.yml'
    path_to_mini_yaml = tmp_path / 'mini_yaml.yml'
    with open(path_to_mini_yaml, 'w') as minifile:
        yaml.dump(acq_yaml_and_files.MINIAML, minifile)
    with open(path_to_full_yaml, 'w') as fullfile:
        yaml.dump(acq_yaml_and_files.FAML, fullfile)

    sync_data.clean_yaml(path_to_mini_yaml)
    sync_data.clean_yaml(path_to_full_yaml)


def test_parse_yaml(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    path_to_full_yaml = tmp_path / 'full_yaml.yml'
    path_to_mini_yaml = tmp_path / 'mini_yaml.yml'
    with open(path_to_mini_yaml, 'w') as minifile:
        yaml.dump(acq_yaml_and_files.MINIAML, minifile)
    with open(path_to_full_yaml, 'w') as fullfile:
        yaml.dump(acq_yaml_and_files.FAML, fullfile)

    m = sync_data.parse_yaml(path_to_mini_yaml, raw_data_folder=tmp_path, verbose=False)
    assert len(m) == 10
    # there should not be any error
    errs = sync_data.find_xxerrorxx(yml_data=m)
    assert not errs
    sess_data = sync_data.parse_yaml(path_to_full_yaml, raw_data_folder=tmp_path, verbose=False)
    errs = sync_data.find_xxerrorxx(yml_data=sess_data)
    assert len(errs) == 3

def test_write_yaml(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    path_to_full_yaml = tmp_path / 'full_yaml.yml'
    with open(path_to_full_yaml, 'w') as fullfile:
        yaml.dump(acq_yaml_and_files.FAML, fullfile)
    sess_data = sync_data.parse_yaml(path_to_full_yaml, raw_data_folder=tmp_path, verbose=False)
    target = tmp_path / 'target_out.yml'
    pure_yaml = sync_data.write_session_data_as_yaml(session_data=sess_data, target_file=target)
    def rec_test(d):
        for k,v in d.items():
            if isinstance(v, dict):
                rec_test(v)
            elif not isinstance(v, str):
                if v is None:
                    continue
                raise IOError('Potentially unvalid yaml. It contains: %s' % v)
    rec_test(pure_yaml)
    with open(target, 'r') as reader:
        reload = yaml.safe_load(reader)
    assert reload == pure_yaml


@pytest.mark.integtest
def test_upload(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    path_to_mini_yaml = tmp_path / 'mini_yaml.yml'
    with open(path_to_mini_yaml, 'w') as fullfile:
        yaml.dump(acq_yaml_and_files.MINIAML, fullfile)

    sync_data.upload_yaml(source_yaml=path_to_mini_yaml, raw_data_folder=tmp_path)
