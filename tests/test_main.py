import pytest
import flexiznam
from flexiznam.utils import PARAMETERS


@pytest.mark.integtest
def test_get_mice():
    mice_df = flexiznam.get_mice(project_id=PARAMETERS['project_ids']['test'])
    assert mice_df.shape == (1, 69)

