import pytest
from flexiznam import mcms

USERNAME = 'ab8'
pytestmark = pytest.mark.skip("Do not test slow MCMS download for now")


def test_download_mouse():
    ret = mcms.main.download_mouse_info(username=USERNAME, mouse_name='PZAJ2.1c')
    assert ret


def test_get_mouse_df():
    mcms.get_mouse_df(mouse_name='PZAJ2.1c', username=USERNAME)

