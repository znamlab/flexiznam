import pandas as pd
import pytest
import flexiznam.main as fzn
from flexiznam.config import PARAMETERS
from flexiznam.errors import FlexilimsError


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
def test_update_by_name():
    # test the three mode
    name = 'test_update'
    # first in append to create a new entity
    mouse = fzn.get_entities(datatype='mouse', project_id=PARAMETERS['project_ids']['test']).iloc[0]
    rep = fzn.update_entity(name=name, datatype='sample', origin_id=None, mode='append', attributes={'old_attr': 'bad'},
                             other_relations=None, project_id=PARAMETERS['project_ids']['test'])
    assert 'origin_id' not in rep
    # then in abort, which should crash
    name = rep['name']
    with pytest.raises(FlexilimsError) as err:
        rep = fzn.update_entity(name=name, datatype='sample', origin_id=None, mode='abort', attributes={},
                                 other_relations=None, project_id=PARAMETERS['project_ids']['test'])
    assert err.value.args[0] == 'An entry named `%s` already exist. Use `overwrite` flag to replace' % name
    # then in overwrite, which should get rid of old_attr
    rep = fzn.update_entity(name=name, datatype='sample', origin_id=mouse['id'], mode='overwrite', attributes={},
                             other_relations=None, project_id=PARAMETERS['project_ids']['test'])
    assert rep['origin_id'] == mouse['id']
    assert rep['attributes']['old_attr'] == 'null'
    rep = fzn.update_entity(id=rep['id'], datatype='sample', origin_id=None, mode='overwrite',
                            attributes=dict(new_attr='test'), other_relations=None,
                            project_id=PARAMETERS['project_ids']['test'])
    assert rep['attributes']['old_attr'] == 'null'
    assert rep['attributes']['new_attr'] == 'test'
