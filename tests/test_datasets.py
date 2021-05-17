import pytest
import pathlib
import pandas as pd
from flexiznam.schema import Dataset, Camera, HarpData
from flexiznam.config import PARAMETERS

TEST_FOLDER = pathlib.Path(PARAMETERS['projects_root']) / '3d_vision/Data/PZAH4.1c/S20210513/R193432_Retinotopy'

@pytest.mark.integtest
def test_dataset():
    ds = Dataset(project='test', name='test_ran_on_20210513_113928_dataset', path='fake/path', is_raw='no',
                 dataset_type='camera', extra_attributes={}, created='')
    st = ds.flexilims_status()
    assert st == 'different'
    rep = ds.flexilims_report()
    expected = pd.DataFrame(dict(offline={'created': '', 'is_raw': 'no', 'path': 'fake/path'},
                                 flexilims={'created': 'N/A', 'is_raw': 'N/A', 'path': 'random'}))
    assert all(rep.sort_index() == expected.sort_index())
    fmt = {'path': 'fake/path', 'created': '', 'dataset_type': 'camera', 'is_raw': 'no',
           'name': 'test_ran_on_20210513_113928_dataset', 'project': '606df1ac08df4d77c72c9aa4', 'type': 'dataset'}
    assert ds.format().name == 'test_ran_on_20210513_113928_dataset'
    assert all(ds.format() == pd.Series(data=fmt, name='test_ran_on_20210513_113928_dataset'))

    # check that updating project change id
    ds.project = '3d_vision'
    assert ds.project_id == PARAMETERS['project_ids']['3d_vision']
    # and conversely
    ds.project_id = PARAMETERS['project_ids']['test']
    assert ds.project == 'test'
    ds = Dataset(name='test_ran_on_20210513_113928_dataset', path='fake/path', is_raw='no',
                 dataset_type='camera', extra_attributes={}, created='')
    assert ds.project_id is None


@pytest.mark.integtest
def test_from_flexilims():
    project = 'test'
    ds = Dataset.from_flexilims(project, name='R101501_retinotopy_suite2p_traces')

@pytest.mark.integtest
def test_camera():
    ds = Camera.from_folder(TEST_FOLDER)
    assert len(ds) == 3
    d = ds['butt_camera']
    assert d.name == 'butt_camera'
    d.project = 'test'
    assert d.flexilims_status() == 'not online'
    assert d.is_valid()

@pytest.mark.integtest
def test_harp():

    TEST_FOLDER = pathlib.Path(PARAMETERS['projects_root']) / '3d_vision/Data/PZAH4.1c/S20210510/ParamLog/R184500'
    ds = HarpData.from_folder(TEST_FOLDER)


