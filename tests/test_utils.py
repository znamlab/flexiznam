import pytest
import flexiznam
import tempfile
from flexiznam import utils


def test_create_config():
    with tempfile.NamedTemporaryFile() as tmp:
        utils.create_config(overwrite=True, target=tmp.name)
        # reload and check one random field
        prm = utils.load_param(tmp.name)
        assert prm['mcms_username'] == 'ab8'


def test_passwd_creation():
    with tempfile.NamedTemporaryFile() as tmp:
        utils.add_password('my_app', 'username1', 'password1', password_file=tmp.name)
        utils.add_password('my_app', 'username2', 'password2', password_file=tmp.name)
        utils.add_password('my_otherapp', 'username', 'password', password_file=tmp.name)

        pwd = utils.get_password('username1', 'my_app', tmp.name)
        assert pwd == 'password1'
