import pytest
from requests.exceptions import InvalidURL
from flexiznam import mcms


USERNAME = "ab8"


def test_get_mouse_df():
    md = mcms.get_mouse_info(mouse_name="PZAJ2.1c", username=USERNAME)
    assert md["mcms_id"] == 1431106
    with pytest.raises(InvalidURL):
        mcms.get_mouse_info(mouse_name="wrongname", username=USERNAME)


def test_get_procedures():
    proc = mcms.get_procedures(mouse_name="BRAC7437.6d", username=USERNAME)
