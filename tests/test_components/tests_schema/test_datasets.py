import pytest
import pathlib
import pandas as pd
from flexiznam.schema import Dataset
from flexiznam.config import PARAMETERS
from flexiznam.errors import DatasetError, FlexilimsError

# Test the generic dataset class.


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
             # dict(mouse='mo_use', session='S12345678_123456',
             #      recording='R123456wihttext',
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


def test_constructor():
    """Make sure that all dataset subclass work with the same constructor"""
    constructor = dict(path='none', is_raw=True, name=None,
                       extra_attributes=dict(p=2), created='random',
                       project='demo_project',
                       project_id=PARAMETERS['project_ids']['demo_project'],
                       origin_id='anotherthing',
                       flm_session=None)
    # make sure that mandatory arguments are given
    extra_attributes = dict(camera=dict(video_file=None),
                            harp=dict(binary_file=None))
    for ds_type, ds_subcls in Dataset.SUBCLASSES.items():
        if ds_type in extra_attributes:
            constructor['extra_attributes'] = extra_attributes[ds_type]
        ds_subcls(**constructor)


@pytest.mark.integtest
def test_dataset_flexilims_integration(flm_sess):
    """This test requires the database to be up-to-date for the physio mouse"""
    ds = Dataset(project='demo_project', path='fake/path', is_raw='no',
                 dataset_type='camera', extra_attributes={}, created='',
                 flexilims_session=flm_sess)
    ds.dataset_name = 'mouse_physio_2p_S20211102_R165821_SpheresPermTube_wf_camera'
    st = ds.flexilims_status()
    assert st == 'different'
    rep = ds.flexilims_report()
    expected = pd.DataFrame(dict(offline={'is_raw': 'no',
                                          'path': 'fake/path',
                                          'created': '',
                                          'metadata_file': 'NA',
                                          'timestamp_file': 'NA',
                                          'video_file': 'NA',
                                          },
                                 flexilims={'is_raw': 'yes',
                                            'created': '2021-11-02 17:03:17',
                                            'path': 'demo_project/mouse_physio_2p/'
                                                    'S20211102/R165821_SpheresPermTube',
                                            'origin_id': '61ebf94120d82a35f724490d',
                                            'timestamp_file': 'wf_camera_timestamps.csv',
                                            'video_file': 'wf_camera_data.bin',
                                            'metadata_file': 'wf_camera_metadata.txt'
                                            }))
    assert all(rep.sort_index() == expected.sort_index())
    ds_name = 'mouse_physio_2p_S20211102_R165821_SpheresPermTube_wf_camera'
    fmt = {'path': 'fake/path', 'created': '', 'dataset_type': 'camera', 'is_raw': 'no',
           'name': ds_name, 'project': '610989f9a651ff0b6237e0f6', 'type': 'dataset'}
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
def test_from_flexilims(flm_sess):
    """This test requires the database to be up-to-date for the physio mouse"""
    project = 'demo_project'
    ds = Dataset.from_flexilims(project, flm_session=flm_sess,
                                name='mouse_physio_2p_S20211102_R165821_'
                                     'SpheresPermTube_wf_camera')
    assert ds.name == 'mouse_physio_2p_S20211102_R165821_SpheresPermTube_wf_camera'
    assert ds.flexilims_status() == 'up-to-date'


@pytest.mark.integtest
def test_from_origin(flm_sess):
    """This test requires the database to be up-to-date for the physio mouse"""
    project = 'demo_project'
    origin_name = 'mouse_physio_2p_S20211102_R165821_SpheresPermTube'
    ds = Dataset.from_origin(
        project,
        origin_type='recording',
        origin_name=origin_name,
        dataset_type='suite2p_rois',
        conflicts='skip',
        flm_session=flm_sess
    )


@pytest.mark.integtest
def test_update_flexilims(flm_sess):
    """This test requires the database to be up-to-date for the physio mouse"""
    project = 'demo_project'
    ds_name = 'mouse_physio_2p_S20211102_R165821_SpheresPermTube_wf_camera'
    ds = Dataset.from_flexilims(project, name=ds_name, flm_session=flm_sess)
    original_path = ds.path
    ds.path = 'new/test/path'
    with pytest.raises(FlexilimsError) as err:
        ds.update_flexilims()
    assert err.value.args[0].startswith("Cannot change existing flexilims entry with")
    ds.update_flexilims(mode='overwrite')
    reloaded_ds = Dataset.from_flexilims(project, name=ds_name, flm_session=flm_sess)
    assert str(reloaded_ds.path) == ds.path
    # undo changes:
    ds.path = original_path
    ds.update_flexilims(mode='overwrite')

    # try to change the origin_id
    original_origin_id = ds.origin_id
    ds.origin_id = '61b4c65d068a8561a85ae891'
    ds.update_flexilims(mode='overwrite')
    assert ds.get_flexilims_entry()['origin_id'] == '61b4c65d068a8561a85ae891'
    ds.origin_id = original_origin_id
    ds.update_flexilims(mode='overwrite')
    assert ds.get_flexilims_entry()['origin_id'] == original_origin_id
    with pytest.raises(FlexilimsError) as err:
        ds.origin_id = None
        ds.update_flexilims(mode='overwrite')
    assert err.value.args[0] == 'Cannot set origin_id to null'


@pytest.mark.integtest
def test_dataset_paths(flm_sess):
    """This test requires the database to be up-to-date for the physio mouse"""
    project = 'demo_project'
    ds_name = 'mouse_physio_2p_S20211102_R165821_SpheresPermTube_wf_camera'
    ds = Dataset.from_flexilims(project, name=ds_name, flm_session=flm_sess)
    path_root = pathlib.Path(PARAMETERS['data_root']['raw'])
    assert ds.path_root == path_root
    assert str(ds.path_full) == \
        str(pathlib.Path(PARAMETERS['data_root']['raw'] / ds.path))


