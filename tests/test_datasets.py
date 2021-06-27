import pytest
import pathlib
import pandas as pd
from flexiznam.schema import Dataset, CameraData, HarpData, ScanimageData
from flexiznam.config import PARAMETERS
from flexiznam.errors import DatasetError, NameNotUniqueError, FlexilimsError
from tests.tests_resources import acq_yaml_and_files


def test_dataset():
    ds = Dataset(project='test', dataset_type='camera', is_raw=False, path='')
    # test a bunch of names and check we have what expected
    parts_label = ['mouse', 'session', 'recording', 'dataset_name']
    names = [dict(mouse='mouse', session='S12345678', recording='R123456',
                  dataset_name='name_with_underscore'),
             dict(mouse='mouse', session='S12345678_00', recording='R123456_00',
                  dataset_name='name_with_underscore'),
             dict(mouse='mo_use', session='S12345678', recording='R123456',
                  dataset_name='name_with_underscore'),
             dict(mouse='mo_use', session='S12345678_123456', recording=None,
                  dataset_name='name_with_underscore'),
             # dict(mouse='mo_use', session='S12345678_123456', recording='R123456wihttext',
             #      dataset_name='name_with_underscore'),
             # dict(mouse='mo_use', session='S12345678_123456',
             #      recording='R123456_recording_with_underscore',
             #      dataset_name='name_with_underscore'),
             # dict(mouse='mo_use', session='S12345678_1',
             #      recording='R123456_recording_with_underscore_12',
             #      dataset_name='name_with_underscore'),
             ]

    for n in names:
        parts = [n[k] for k in parts_label]
        ds.name = '_'.join([p for p in parts if p is not None])
        for p in parts_label:
            assert getattr(ds, p) == n[p]

    # test also a few unvalid datasets
    bad_names = ['hopeles',
                 'mo_use_S12345678_123456_000_norec',
                 'mo_use_000_R123456_000_nosess']
    msgs = [('Cannot parse dataset name. No match in: `hopeles`. Must be '
             '`<MOUSE>_SXXXXXX[...]_<DATASET>`.\nSet self.mouse, self.session, '
             'self.recording, and self.dataset_name individually'),
            ('Cannot parse dataset name. Found recording number but not recording name '
             'in `mo_use_S12345678_123456_000_norec`\nSet self.mouse, self.session, '
             'self.recording, and self.dataset_name individually'),
            ('Cannot parse dataset name. No match in: `mo_use_000_R123456_000_nosess`. '
             'Must be `<MOUSE>_SXXXXXX[...]_<DATASET>`.\nSet self.mouse, self.session, '
             'self.recording, and self.dataset_name individually')]
    for name, err_msg in zip(bad_names, msgs):
        with pytest.raises(DatasetError) as exc:
            ds.name = name
        assert exc.value.args[0] == err_msg


@pytest.mark.integtest
def test_dataset_flexilims_integration():
    ds = Dataset(project='test', path='fake/path', is_raw='no',
                 dataset_type='camera', extra_attributes={}, created='')
    ds.dataset_name = 'test_ran_on_20210513_113928_dataset'
    st = ds.flexilims_status()
    assert st == 'different'
    rep = ds.flexilims_report()
    expected = pd.DataFrame(dict(offline={'created': '',
                                          'is_raw': 'no',
                                          'path': 'fake/path',
                                          'only_online': 'NA',
                                          },
                                 flexilims={'created': None,
                                            'is_raw': None,
                                            'path': 'random',
                                            'only_online': 'this attribute is only on '
                                                           'flexilims',
                                            }))
    assert all(rep.sort_index() == expected.sort_index())
    ds_name = 'test_ran_on_20210513_113928_dataset'
    fmt = {'path': 'fake/path', 'created': '', 'dataset_type': 'camera', 'is_raw': 'no',
           'name': ds_name, 'project': '606df1ac08df4d77c72c9aa4', 'type': 'dataset'}
    assert ds.format().name == ds_name
    assert all(ds.format().drop('origin_id') == pd.Series(data=fmt, name=ds_name))

    # same with yaml mode
    fmt['extra_attributes'] = {}
    ds_yaml = ds.format(mode='yaml')
    try:
        del ds_yaml['origin_id']
    except KeyError:
        pass
    assert ds_yaml == fmt

    # check that updating project change id
    ds.project = '3d_vision'
    assert ds.project_id == PARAMETERS['project_ids']['3d_vision']
    # and conversely
    ds.project_id = PARAMETERS['project_ids']['test']
    assert ds.project == 'test'
    ds = Dataset(path='fake/path', is_raw='no',
                 dataset_type='camera', extra_attributes={}, created='')
    assert ds.project_id is None


@pytest.mark.integtest
def test_from_flexilims():
    project = 'test'
    ds = Dataset.from_flexilims(project, name='test_from_flexi')
    assert ds.name == 'test_from_flexi'
    assert ds.flexilims_status() == 'up-to-date'


@pytest.mark.integtest
def test_from_origin():
    project = 'test'
    origin_name = 'PZAH4.1c_S20210513_0_R150615_0'
    ds = Dataset.from_origin(
        project,
        origin_type='recording',
        origin_name=origin_name,
        dataset_type='suite2p_rois',
        conflicts='skip')
    assert ds.name == 'PZAH4.1c_S20210513_0_R150615_0_suite2p_rois_0'
    ds = Dataset.from_origin(
        project,
        origin_type='recording',
        origin_name=origin_name,
        dataset_type='suite2p_rois',
        conflicts='append')
    assert ds.name == 'PZAH4.1c_S20210513_0_R150615_0_suite2p_rois_1'
    with pytest.raises(NameNotUniqueError) as err:
        ds = Dataset.from_origin(
            project,
            origin_type='recording',
            origin_name=origin_name,
            dataset_type='suite2p_rois',
            conflicts='abort')
    assert 'already processed' in err.value.args[0]


@pytest.mark.integtest
def test_update_flexilims():
    project = 'test'
    ds = Dataset.from_flexilims(project, name='test_from_flexi')
    original_path = ds.path
    ds.path = 'new/test/path'
    with pytest.raises(FlexilimsError) as err:
        ds.update_flexilims()
    assert err.value.args[0] == "Cannot change existing flexilims entry with mode=`safe`"
    ds.update_flexilims(mode='overwrite')
    reloaded_ds = Dataset.from_flexilims(project, name='test_from_flexi')
    assert str(reloaded_ds.path) == ds.path
    ds.path = original_path
    ds.update_flexilims(mode='overwrite')

    # try to change the origin_id
    ds.origin_id = '60c1fd7a5c6930620e4a4bc4'
    ds.update_flexilims(mode='overwrite')
    assert ds.get_flexilims_entry()['origin_id'] == '60c1fd7a5c6930620e4a4bc4'
    ds.origin_id = '60c1fc875c6930620e4a4bc1'
    ds.update_flexilims(mode='overwrite')
    assert ds.get_flexilims_entry()['origin_id'] == '60c1fc875c6930620e4a4bc1'
    with pytest.raises(FlexilimsError) as err:
        ds.origin_id = None
        ds.update_flexilims(mode='overwrite')
    assert err.value.args[0] == 'Cannot set origin_id to null'



def test_camera(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    data_dir = tmp_path / acq_yaml_and_files.MOUSE / acq_yaml_and_files.SESSION / next(
        iter(acq_yaml_and_files.MINIAML['recordings'].keys()))
    ds = CameraData.from_folder(data_dir, verbose=False)
    assert len(ds) == 4
    d = ds['butt_camera']
    assert d.name == 'butt_camera'
    d.project = 'test'
    assert d.is_valid()
    ds = CameraData.from_folder(data_dir, mouse='testmouse', session='testsession', recording='testrecording',
                                verbose=False)
    assert ds['face_camera'].name == 'testmouse_testsession_testrecording_face_camera'


def test_harp(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    data_dir = tmp_path / 'PZAH4.1c/S20210513/ParamLog/R193432_Retinotopy'
    ds = HarpData.from_folder(data_dir, verbose=False)
    assert len(ds) == 1
    d = next(iter(ds.values()))
    assert d.name == next(iter(ds.keys()))
    assert d.is_valid()
    assert len(d.csv_files) == 5


@pytest.mark.integtest
def test_scanimage(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    data_dir = tmp_path / 'PZAH4.1c/S20210513/R193432_Retinotopy'
    ds = ScanimageData.from_folder(data_dir, verbose=False)
    assert len(ds) == 1
    d = next(iter(ds.values()))
    assert d.name == 'PZAH4.1c_S20210513_R193432_Retinotopy00001'
    assert d.name == next(iter(ds.keys()))
    assert d.is_valid()
    assert len(d) == 39


@pytest.mark.integtest
def test_dataset_paths():
    project = 'test'
    ds = Dataset.from_flexilims(project, name='test_from_flexi')
    assert str(ds.path_root) == PARAMETERS['data_root']['processed']
    assert str(ds.path_full) == \
        str(pathlib.Path(PARAMETERS['data_root']['processed'] / ds.path))
