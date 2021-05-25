import pytest
import pathlib
import yaml
from click.testing import CliRunner
from flexiznam import cli
from flexiznam.config import config_tools
from tests.tests_resources import acq_yaml_and_files


def test_config(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli.config, ['--config_folder', tmp_path])
    assert result.exit_code == 0
    assert result.output.startswith('No configuration file. Creating one.')
    assert pathlib.Path.exists(tmp_path / 'config.yml')
    prm = config_tools.load_param(param_folder=tmp_path)
    assert prm['data_subfolder']['raw'] == r'raw'
    result = runner.invoke(cli.config, ['--config_folder', tmp_path])
    assert result.exit_code == 0
    assert result.output.startswith('Configuration file currently used is:')
    str_cfg = yaml.dump(config_tools.DEFAULT_CONFIG) + '\n'
    assert result.output.endswith(str_cfg)


def test_add_password(tmp_path):
    runner = CliRunner()
    pwd_file = tmp_path / 'pass.yml'
    result = runner.invoke(cli.add_password, ['--password_file', pwd_file,
                                              '--app', 'test_app', '--username', 'noone',
                                              '--password', '1234'])
    assert result.exit_code == 0
    assert result.output.startswith('Password added in')
    p = config_tools.get_password(username='noone', app='test_app', password_file=pwd_file)
    assert p == '1234'


def test_make_full_yaml(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    path_to_full_yaml = tmp_path / 'full_yaml.yml'
    path_to_mini_yaml = tmp_path / 'mini_yaml.yml'
    with open(path_to_mini_yaml, 'w') as minifile:
        yaml.dump(acq_yaml_and_files.MINIAML, minifile)
    with open(path_to_full_yaml, 'w') as fullfile:
        yaml.dump(acq_yaml_and_files.FAML, fullfile)

    runner = CliRunner()
    out_yml = tmp_path / 'autogenerated.yml'
    result = runner.invoke(cli.process_yaml, ['-s', path_to_mini_yaml, '-t', out_yml, '-r', tmp_path])
    assert result.exit_code == 0
    # read auto yaml
    with open(out_yml, 'r') as reader:
        auto_out = yaml.safe_load(reader)
    assert len(auto_out) == 10
    result = runner.invoke(cli.process_yaml, ['-s', path_to_full_yaml, '-t', out_yml])
    assert result.exit_code == 1
    assert result.exception.args[0].endswith('autogenerated.yml already exists. Use --overwrite to replace')
    result = runner.invoke(cli.process_yaml, ['-s', path_to_full_yaml, '-t', out_yml, '-r', tmp_path,
                                              '--overwrite'])
    assert result.exit_code == 0
    # read auto yaml
    with open(out_yml, 'r') as reader:
        auto_out = yaml.safe_load(reader)
    assert len(auto_out) == 10


@pytest.mark.integtest
def test_upload(tmp_path):
    # first generate a yaml with and without error:
    acq_yaml_and_files.create_acq_files(tmp_path)
    path_to_full_yaml = tmp_path / 'full_yaml.yml'
    path_to_mini_yaml = tmp_path / 'mini_yaml.yml'
    with open(path_to_mini_yaml, 'w') as minifile:
        yaml.dump(acq_yaml_and_files.MINIAML, minifile)
    with open(path_to_full_yaml, 'w') as fullfile:
        yaml.dump(acq_yaml_and_files.FAML, fullfile)

    runner = CliRunner()
    err_yml = tmp_path / 'with_error.yml'
    result = runner.invoke(cli.process_yaml, ['-s', path_to_full_yaml, '-t', err_yml, '-r', tmp_path])
    assert result.exit_code == 0
    out_yml = tmp_path / 'without_error.yml'
    result = runner.invoke(cli.process_yaml, ['-s', path_to_mini_yaml, '-t', out_yml, '-r', tmp_path])
    assert result.exit_code == 0

    # now do the actual test
    result = runner.invoke(cli.yaml_to_flexilims, ['-s', err_yml, '-r', tmp_path])
    assert result.exit_code == 1
    assert result.output == 'Error: The yaml file still contains error. Fix it\n'

    result = runner.invoke(cli.yaml_to_flexilims, ['-s', out_yml, '-r', tmp_path])
    assert result.exit_code == 0

