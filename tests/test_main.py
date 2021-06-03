import pandas as pd
import pytest
import flexiznam.main as fzn
from flexiznam.config import PARAMETERS
from flexiznam.errors import FlexilimsError, NameNotUniqueException


@pytest.mark.integtest
def test_get_session():
    sess = fzn.get_flexilims_session(project_id=PARAMETERS['project_ids']['test'])
    assert sess.username == PARAMETERS['flexilims_username']


def test_format_results():
    exmple_res = {'id': 'randomid', 'type': 'flmdatatype', 'name': 'fake_results', 'incrementalId': 'SOMETHING0000001',
                  'attributes': {'exmpl_attr': 'this will be flattened'}, 'createdBy': 'Antonin Blot',
                  'dateCreated': 1620375329769, 'objects': {}, 'customEntities': '[]',
                  'project': '606df1ac08df4d77c72c9aa4'}
    exmple_res = [exmple_res, exmple_res.copy()]
    res = fzn.format_results(exmple_res)
    assert res.shape == (2, 10)
    assert 'exmpl_attr' in res.columns


@pytest.mark.integtest
def test_get_experimental_sessions():
    exp_sess = fzn.get_experimental_sessions(project_id=PARAMETERS['project_ids']['test'])
    assert all(exp_sess.type == 'session')
    assert all(exp_sess.project == PARAMETERS['project_ids']['test'])
    assert len(exp_sess.origin.unique()) > 1
    exp_sess_mouse = fzn.get_experimental_sessions(project_id=PARAMETERS['project_ids']['test'], mouse='test_mouse')
    assert len(exp_sess) > len(exp_sess_mouse)
    assert len(exp_sess_mouse.origin.unique()) == 1


@pytest.mark.integtest
def test_get_entities():
    mice_df = fzn.get_entities(project_id=PARAMETERS['project_ids']['test'], datatype='mouse')
    assert mice_df.shape == (3, 70)
    mice_df = fzn.get_entities(project_id=PARAMETERS['project_ids']['test'], datatype='mouse', format_reply=False)
    assert isinstance(mice_df, list)
    assert len(mice_df) == 3


@pytest.mark.integtest
def test_get_entity():
    mouse = fzn.get_entity(id='6094f7212597df357fa24a8c', project_id=PARAMETERS['project_ids']['test'],
                           datatype='mouse')
    assert isinstance(mouse, pd.Series)
    assert mouse.shape == (12,)
    mouse = fzn.get_entity(id='6094f7212597df357fa24a8c', project_id=PARAMETERS['project_ids']['test'],
                           datatype='mouse', format_reply=False)
    assert isinstance(mouse, dict)
    assert len(mouse) == 10


@pytest.mark.integtest
def test_get_mouse_id():
    mid = fzn.get_id(name='test_mouse', project_id=PARAMETERS['project_ids']['test'])
    assert mid == '6094f7212597df357fa24a8c'


@pytest.mark.integtest
def test_generate_name():
    flm_sess = fzn.get_flexilims_session('test')
    name = fzn.generate_name(datatype='dataset', name='test_iter', flexilims_session=flm_sess)
    assert name.startswith('test_iter')
    assert fzn.get_entity(datatype='dataset', name='test_iter', flexilims_session=flm_sess) is None


@pytest.mark.integtest
def test_add_entity():
    flm_sess = fzn.get_flexilims_session('test')
    dataset_name = 'test_ran_on_20210524_162613_dataset'
    with pytest.raises(FlexilimsError) as err:
        fzn.add_entity(datatype='dataset', name=dataset_name, flexilims_session=flm_sess)
    assert err
    with pytest.raises(NameNotUniqueException) as err:
        fzn.add_entity(datatype='dataset', name=dataset_name, flexilims_session=flm_sess,
                       attributes=dict(path='random'))
    new_name = fzn.generate_name(datatype='dataset', name='test_iter', flexilims_session=flm_sess)
    rep = fzn.add_entity(datatype='dataset', name=new_name, flexilims_session=flm_sess,
                       attributes=dict(path='random'))
    assert rep['name'] == new_name
    assert len(rep) == 9


@pytest.mark.integtest
def test_update_entity():
    session = fzn.get_flexilims_session('test')
    dataset_name = 'test_ran_on_20210524_162613_dataset'
    res = fzn.update_entity(
        'dataset',
        name=dataset_name,
        flexilims_session=session,
        attributes={'path': 'old/path'}
    )
    assert (res['attributes']['path'] == 'old/path')
    res = fzn.update_entity(
        'dataset',
        name=dataset_name,
        flexilims_session=session,
        attributes={'path': 'new/path', 'test': 'test value'}
    )
    assert (res['attributes']['path'] == 'new/path')
    assert (res['attributes']['test'] == 'test value')
    res = fzn.update_entity(
        'dataset',
        name=dataset_name,
        flexilims_session=session,
        attributes={'path': 'test/path'}
    )
    assert (res['attributes']['test'] == 'null')
