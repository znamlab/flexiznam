import pathlib
import yaml
from click.testing import CliRunner
from flexiznam import cli
from flexiznam.config import utils


def test_config(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli.config, ['--config-folder', tmp_path])
    assert result.exit_code == 0
    assert result.output.startswith('No configuration file. Creating one.')
    assert pathlib.Path.exists(tmp_path / 'config.yml')
    prm = utils.load_param(param_folder=tmp_path)
    assert prm['camp']['raw_data_source'] == r'D:\Data'
    result = runner.invoke(cli.config, ['--config-folder', tmp_path])
    assert result.exit_code == 0
    assert result.output.startswith('Configuration file currently used is:')
    str_cfg = yaml.dump(utils.DEFAULT_CONFIG) + '\n'
    assert result.output.endswith(str_cfg)


def test_add_password(tmp_path):
    runner = CliRunner()
    pwd_file = tmp_path / 'pass.yml'
    result = runner.invoke(cli.add_password, ['--password-file', pwd_file,
                                              '--app', 'test_app', '--username', 'noone',
                                              '--password', '1234'])
    assert result.exit_code == 0
    assert result.output.startswith('Password added in')
    p = utils.get_password(username='noone', app='test_app', password_file=pwd_file)
    assert p == '1234'
