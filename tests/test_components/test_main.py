import pandas as pd
import pytest
import flexiznam.main as flz
from flexiznam.config import PARAMETERS
from flexiznam.errors import FlexilimsError, NameNotUniqueError

# Test functions from main.py
from flexiznam.schema import Dataset


@pytest.mark.integtest
def test_get_flm_session():
    sess = flz.get_flexilims_session(project_id=PARAMETERS['project_ids']['test'])
    assert sess.username == PARAMETERS['flexilims_username']


def test_format_results():
    exmple_res = {'id': 'randomid', 'type': 'flmdatatype', 'name': 'fake_results',
                  'incrementalId': 'SOMETHING0000001',
                  'attributes': {'exmpl_attr': 'this will be flattened'},
                  'createdBy': 'Antonin Blot',
                  'dateCreated': 1620375329769, 'objects': {}, 'customEntities': '[]',
                  'project': '606df1ac08df4d77c72c9aa4'}
    exmple_res = [exmple_res, exmple_res.copy()]
    res = flz.format_results(exmple_res)
    assert res.shape == (2, 10)
    assert 'exmpl_attr' in res.columns


@pytest.mark.integtest
def test_get_experimental_sessions(flm_sess):
    proj_id = PARAMETERS['project_ids']['demo_project']
    exp_sess = flz.get_experimental_sessions(project_id=proj_id,
                                             flexilims_session=flm_sess)
    assert all(exp_sess.type == 'session')
    assert all(exp_sess.project == proj_id)
    assert len(exp_sess.origin_id.unique()) == 1


@pytest.mark.integtest
def test_get_entities(flm_sess):
    mice_df = flz.get_entities(project_id=PARAMETERS['project_ids']['demo_project'],
                               datatype='mouse', flexilims_session=flm_sess)
    assert mice_df.shape == (2, 12)
    mice_df = flz.get_entities(project_id=PARAMETERS['project_ids']['demo_project'],
                               datatype='mouse', format_reply=False,
                               flexilims_session=flm_sess)
    assert isinstance(mice_df, list)
    assert len(mice_df) == 2


@pytest.mark.integtest
def test_get_entity(flm_sess):
    mouse = flz.get_entity(id='61b4c65d068a8561a85ae891',
                           project_id=PARAMETERS['project_ids']['demo_project'],
                           datatype='mouse', flexilims_session=flm_sess)
    assert isinstance(mouse, pd.Series)
    assert mouse.shape == (12,)
    mouse = flz.get_entity(id='61b4c65d068a8561a85ae891',
                           project_id=PARAMETERS['project_ids']['demo_project'],
                           datatype='mouse',
                           format_reply=False,
                           flexilims_session=flm_sess)
    assert isinstance(mouse, dict)
    assert len(mouse) == 10


@pytest.mark.integtest
def test_get_mouse_id(flm_sess):
    mid = flz.get_id(name='mouse_physio_2p',
                     project_id=PARAMETERS['project_ids']['demo_project'],
                     flexilims_session=flm_sess)
    assert mid == '61b4c65d068a8561a85ae891'


@pytest.mark.integtest
def test_generate_name(flm_sess):
    name = flz.generate_name(datatype='dataset', name='test_iter',
                             flexilims_session=flm_sess)
    assert name.startswith('test_iter')
    assert flz.get_entity(datatype='dataset', name=name,
                          flexilims_session=flm_sess) is None
    name = flz.generate_name(datatype='dataset', name='nounderscore',
                             flexilims_session=flm_sess)
    assert name.startswith('nounderscore')
    assert name.endswith('_0')
    name = flz.generate_name(datatype='dataset', name='suffix_already_01',
                             flexilims_session=flm_sess)
    assert name == 'suffix_already_1'
    name = flz.generate_name(datatype='dataset', name='134241',
                             flexilims_session=flm_sess)
    assert name == '134241_0'


@pytest.mark.integtest
def test_get_children(flm_sess):
    parent_id = '6094f7212597df357fa24a8c'
    res = flz.get_children(parent_id, flexilims_session=flm_sess)
    assert len(res) > 1


@pytest.mark.integtest
def test_add_entity(flm_sess):
    dataset_name = 'mouse_physio_2p_S20211102_overview_zoom2_00001'
    with pytest.raises(FlexilimsError) as err:
        flz.add_entity(datatype='dataset', name=dataset_name, flexilims_session=flm_sess)
    assert err.value.args[0] == 'Error 400:  Save failed. &#39;path&#39; is a necessary attribute for dataset. If you have &#39;null&#39; values please substitute (null) with empty string (&#39;&#39;) '
    with pytest.raises(NameNotUniqueError) as err:
        flz.add_entity(datatype='dataset', name=dataset_name, flexilims_session=flm_sess,
                       attributes=dict(path='random', dataset_type='scanimage'))
    new_name = flz.generate_name(datatype='dataset', name=dataset_name,
                                 flexilims_session=flm_sess)
    assert flz.get_entity(datatype='dataset', name=new_name,
                          flexilims_session=flm_sess) is None


@pytest.mark.integtest
def test_update_entity(flm_sess):
    with pytest.raises(FlexilimsError) as err:
        flz.update_entity('dataset', name='gibberish', flexilims_session=flm_sess)
    assert err.value.args[0] == 'Cannot find an entity of type `dataset` named ' \
                                '`gibberish`'
    dataset_name = 'mouse_physio_2p_S20211102_overview_zoom2_00001'
    original_entity = flz.get_entity(datatype='dataset', name=dataset_name,
                                     flexilims_session=flm_sess)
    res = flz.update_entity('dataset',
                            name=dataset_name,
                            flexilims_session=flm_sess,
                            attributes={
                                'path': 'old/path',
                                'dataset_type': 'scanimage'},
                            mode='update'
                            )
    assert (res['attributes']['path'] == 'old/path')
    assert (res['attributes']['acq_num'] == '00001')  # existing attribute is unchanged
    # now in overwrite mode
    res = flz.update_entity('dataset',
                            name=dataset_name,
                            flexilims_session=flm_sess,
                            attributes={'path': 'new/path',
                                        'dataset_type': 'scanimage',
                                        'is_raw': res['attributes']['is_raw']},
                            )
    # in the reply the null values are []
    assert (res['attributes']['path'] == 'new/path')
    assert (res['attributes']['acq_num'] == [])
    # but in the database they are null
    dbval = flz.get_entity('dataset', name=dataset_name, flexilims_session=flm_sess,
                           format_reply=False)
    assert (dbval['attributes']['acq_num'] is None)

    # restore database state
    ds = Dataset.from_flexilims(data_series=original_entity, flm_session=flm_sess)
    ds.update_flexilims(mode='overwrite')
    new_entity = flz.get_entity(datatype='dataset', name=dataset_name,
                                flexilims_session=flm_sess)
    assert repr(new_entity) == repr(original_entity)
