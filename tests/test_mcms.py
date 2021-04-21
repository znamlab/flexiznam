import pytest
import datetime
from flexiznam import mcms
from flexiznam.resources.secret_password import mcms_passwords

username = 'ab8'
password = mcms_passwords[username]


pytestmark = pytest.mark.skip("Do not test slow MCMS download for now")
def test_download_mouse():
    mcms.download_mouse_info(username=username, mouse_name='PZAJ2.1c')


def test_get_mouse_df():
    mcms.get_mouse_df(mouse_name='PZAJ2.1c', username=username)

