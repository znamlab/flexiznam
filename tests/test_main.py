import pytest
import flexiznam
from flexiznam.resources.projects import PROJECT_IDS


def test_get_mice():
    mice_df = flexiznam.get_mice(project_id=PROJECT_IDS['test'])
    assert mice_df.shape == (1, 69)
