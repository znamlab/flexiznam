import pytest
import pathlib
from flexiznam import datasets
from flexiznam.config import PARAMETERS


TEST_FOLDER = pathlib.Path(PARAMETERS['projects_root']) / '3d_vision/Data/PZAH4.1c/S20210510/R184337'


@pytest.mark.integtest
def test_dataset():
    ds = datasets.Dataset(project='test', name='test_ran_on_20210513_113928_dataset', path='fake/path', is_raw='no',
                          dataset_type='camera', extra_attributes={}, created='')
    st = ds.flexilims_status()
    assert st == 'different'
    rep = ds.flexilims_report()
    expected = {'created': ('', 'N/A'), 'is_raw': ('no', 'N/A'), 'path': ('fake/path', 'random')}
    assert rep == expected
    fmt = {'attributes': {'path': 'fake/path', 'created': '', 'dataset_type': 'camera', 'is_raw': 'no'},
           'name': 'test_ran_on_20210513_113928_dataset', 'project': '606df1ac08df4d77c72c9aa4', 'type': 'dataset'}
    assert ds.format() == fmt

    # check that updating project change id
    ds.project = '3d_vision'
    assert ds.project_id == PARAMETERS['project_ids']['3d_vision']
    # and conversely
    ds.project_id = PARAMETERS['project_ids']['test']
    assert ds.project == 'test'
