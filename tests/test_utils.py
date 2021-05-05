import pytest
import os
import pathlib
import shutil
import tempfile
from flexiznam import utils


def test_create_config():
    with tempfile.NamedTemporaryFile() as tmp:
        utils.create_config(overwrite=True, target=tmp.name, favorite_colour='dark')
        # reload and check one random field
        prm = utils.load_param(tmp.name)
        assert prm['mcms_username'] == 'ab8'
        assert prm['favorite_colour'] == 'dark'
        # check that I load it if the cwd is the local path
        tmp_path = pathlib.Path(tmp.name)
        os.chdir(tmp_path.parent)
        target = pathlib.Path(tmp_path.parent / 'config.yml')
        assert not target.is_file()
        shutil.copy(tmp_path, target)
        prm = utils.load_param()
        assert prm['favorite_colour'] == 'dark'
        # remove temporary config file
        shutil.move(target, tmp_path)


def test_passwd_creation():
    with tempfile.NamedTemporaryFile() as tmp:
        utils.add_password('my_app', 'username1', 'password1', password_file=tmp.name)
        utils.add_password('my_app', 'username2', 'password2', password_file=tmp.name)
        utils.add_password('my_otherapp', 'username', 'password', password_file=tmp.name)

        pwd = utils.get_password('username1', 'my_app', tmp.name)
        assert pwd == 'password1'
