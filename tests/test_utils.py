import os
import pathlib
import shutil
import tempfile
from flexiznam.config import utils, DEFAULT_CONFIG


def test_create_config():
    with tempfile.TemporaryDirectory() as tmp:
        utils.create_config(overwrite=True, config_folder=tmp, favorite_colour='dark')
        # reload and check one random field
        prm = utils.load_param(tmp)
        assert prm['mcms_username'] == 'ab8'
        assert prm['favorite_colour'] == 'dark'
        # check that I load it if the cwd is the local path
        prm = utils.load_param()
        assert 'favorite_colour' not in prm
        cwd = os.getcwd()
        os.chdir(tmp)
        prm = utils.load_param()
        assert prm['favorite_colour'] == 'dark'
        os.chdir(cwd)


def test_update_config():
    with tempfile.TemporaryDirectory() as tmp:
        utils.create_config(overwrite=True, config_folder=tmp, favorite_colour='dark')
        utils.update_config(param_file='config.yml', config_folder=tmp, skip_checks=False, mcms_username='alfred',
                            project_ids=dict(new_project='test_id'))
        prm = utils.load_param(tmp)
        assert prm['mcms_username'] == 'alfred'
        assert prm['favorite_colour'] == 'dark'
        assert prm['project_ids']['new_project'] == 'test_id'
        assert prm['project_ids']['test'] == DEFAULT_CONFIG['project_ids']['test']
        prm = utils.load_param()
        assert 'favorite_colour' not in prm


def test_passwd_creation():
    with tempfile.NamedTemporaryFile() as tmp:
        utils.add_password('my_app', 'username1', 'password1', password_file=tmp.name)
        utils.add_password('my_app', 'username2', 'password2', password_file=tmp.name)
        utils.add_password('my_otherapp', 'username', 'password', password_file=tmp.name)

        pwd = utils.get_password('username1', 'my_app', tmp.name)
        assert pwd == 'password1'
