import pytest
import flexiznam.main as fzn
from flexiznam.config.utils import PARAMETERS


@pytest.mark.integtest
def test_get_mice():
    mice_df = fzn.get_mice(project_id=PARAMETERS['project_ids']['test'])
    assert mice_df.shape == (2, 70)


@pytest.mark.integtest
def test_get_mouse_id():
    mid = fzn.get_mouse_id(mouse_name='test_mouse', project_id=PARAMETERS['project_ids']['test'])
    assert mid == '6094f7212597df357fa24a8c'

