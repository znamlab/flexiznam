import datetime
import pandas as pd
import pytest
import flexiznam.main as flz
from flexiznam.config import PARAMETERS, get_password
from flexiznam.errors import FlexilimsError, NameNotUniqueError
from tests.tests_resources.data_for_testing import MOUSE_ID

# Test functions from main.py
from flexiznam.schema import Dataset

# this needs to change every time I reset flexlilims


def test_get_flexilims_session():
    sess = flz.get_flexilims_session(
        project_id=PARAMETERS["project_ids"]["test"], reuse_token=False
    )
    assert sess.username == PARAMETERS["flexilims_username"]
    sess = flz.get_flexilims_session(project_id=None, reuse_token=True)
    assert sess.username == PARAMETERS["flexilims_username"]
    token, date = get_password("flexilims", "token").split("_")
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    assert date == today
    assert sess.session.headers["Authorization"].split(" ")[1] == token
    sess = flz.get_flexilims_session(project_id=None, reuse_token=True)
    assert sess.session.headers["Authorization"].split(" ")[1] == token


def test_format_results():
    exmple_res = {
        "id": "randomid",
        "type": "flmdatatype",
        "name": "fake_results",
        "incrementalId": "SOMETHING0000001",
        "attributes": {"exmpl_attr": "this will be flattened"},
        "createdBy": "Antonin Blot",
        "dateCreated": 1620375329769,
        "objects": {},
        "customEntities": "[]",
        "project": "606df1ac08df4d77c72c9aa4",
    }
    exmple_res = [exmple_res, exmple_res.copy()]
    res = flz.format_results(exmple_res)
    assert res.shape == (2, 10)
    assert "exmpl_attr" in res.columns


def test_get_experimental_sessions(flm_sess):
    proj_id = PARAMETERS["project_ids"]["demo_project"]
    exp_sess = flz.get_experimental_sessions(
        project_id=proj_id, flexilims_session=flm_sess
    )
    assert all(exp_sess.type == "session")
    assert all(exp_sess.project == proj_id)
    assert len(exp_sess.origin_id.unique()) == 1


def test_get_entities(flm_sess):
    mice_df = flz.get_entities(
        project_id=PARAMETERS["project_ids"]["demo_project"],
        datatype="mouse",
        flexilims_session=flm_sess,
    )
    assert mice_df.shape[0] > 1
    assert hasattr(mice_df, "birth_date")
    mice_df = flz.get_entities(
        project_id=PARAMETERS["project_ids"]["demo_project"],
        datatype="mouse",
        format_reply=False,
        flexilims_session=flm_sess,
    )
    assert isinstance(mice_df, list)
    assert all(["sex" in m["attributes"] for m in mice_df])


def test_get_entity(flm_sess):
    mouse = flz.get_entity(
        id=MOUSE_ID,
        project_id=PARAMETERS["project_ids"]["demo_project"],
        datatype="mouse",
        flexilims_session=flm_sess,
    )
    assert isinstance(mouse, pd.Series)
    for k in ("sex", "birth_date", "id", "dateCreated"):
        assert hasattr(mouse, k)
    mouse = flz.get_entity(
        id=MOUSE_ID,
        project_id=PARAMETERS["project_ids"]["demo_project"],
        datatype="mouse",
        format_reply=False,
        flexilims_session=flm_sess,
    )
    assert isinstance(mouse, dict)
    assert "id" in mouse
    assert "birth_date" in mouse["attributes"]


def test_get_mouse_id(flm_sess):
    mid = flz.get_id(
        name="mouse_physio_2p",
        project_id=PARAMETERS["project_ids"]["demo_project"],
        flexilims_session=flm_sess,
    )
    assert mid == MOUSE_ID


def test_get_datasets(flm_sess):
    sess = flz.get_entity(
        name="mouse_physio_2p_S20211102", datatype="session", flexilims_session=flm_sess
    )
    ds = flz.get_datasets(
        flexilims_session=flm_sess, origin_id=sess.id, return_paths=True
    )
    assert len(ds) == 2
    for v in ds.values():
        assert isinstance(v, list)
        assert all([isinstance(d, str) for d in v])

    ds2 = flz.get_datasets(
        flexilims_session=flm_sess, origin_id=sess.id, return_paths=False
    )
    assert len(ds2) == 2
    assert all([k in ds2 for k in ds])
    for k in ds2:
        ds_paths = ds[k]
        ds_ds = ds2[k]
        assert len(ds_ds) == len(ds_paths)
        assert all([isinstance(d, Dataset) for d in ds_ds])
        assert all([str(d.path_full) in ds_paths for d in ds_ds])


def test_add_mouse(flm_sess):
    mouse_name = "BRAC7449.2a"
    rep = flm_sess.get(datatype="mouse", name=mouse_name)
    if rep:
        flm_sess.delete(rep[0]["id"])
    rep = flz.add_mouse(
        mouse_name,
        project_id=None,
        mouse_info=None,
        flexilims_session=flm_sess,
        get_mcms_data=True,
        mcms_animal_name=None,
    )
    assert rep["name"] == mouse_name


def test_generate_name(flm_sess):
    name = flz.generate_name(
        datatype="dataset", name="test_iter", flexilims_session=flm_sess
    )
    assert name.startswith("test_iter")
    assert (
        flz.get_entity(datatype="dataset", name=name, flexilims_session=flm_sess)
        is None
    )
    name = flz.generate_name(
        datatype="dataset", name="nounderscore", flexilims_session=flm_sess
    )
    assert name.startswith("nounderscore")
    assert name.endswith("_0")
    name = flz.generate_name(
        datatype="dataset", name="suffix_already_01", flexilims_session=flm_sess
    )
    assert name == "suffix_already_1"
    name = flz.generate_name(
        datatype="dataset", name="134241", flexilims_session=flm_sess
    )
    assert name == "134241_0"


def test_get_children(flm_sess):
    parent_id = MOUSE_ID
    res = flz.get_children(parent_id, flexilims_session=flm_sess)
    assert len(res) == 1
    # test that it works also when there are no children
    while len(res):
        res = flz.get_children(parent_id=res.iloc[0].id, flexilims_session=flm_sess)
    assert isinstance(res, pd.DataFrame)
    res = flz.get_children(parent_name="mouse_physio_2p", flexilims_session=flm_sess)
    assert len(res) == 1


def test_add_entity(flm_sess):
    dataset_name = "mouse_physio_2p_S20211102_overview_zoom2_00001"
    with pytest.raises(FlexilimsError) as err:
        flz.add_entity(
            datatype="dataset", name=dataset_name, flexilims_session=flm_sess
        )
    msg = (
        "Error 400:  Save failed. &#39;path&#39; is a necessary attribute for "
        "dataset. If you have &#39;null&#39; values please substitute (null) with "
        "empty string (&#39;&#39;) "
    )
    assert err.value.args[0] == msg
    with pytest.raises(NameNotUniqueError) as err:
        flz.add_entity(
            datatype="dataset",
            name=dataset_name,
            flexilims_session=flm_sess,
            attributes=dict(path="random", dataset_type="scanimage"),
        )
    new_name = flz.generate_name(
        datatype="dataset", name=dataset_name, flexilims_session=flm_sess
    )
    assert (
        flz.get_entity(datatype="dataset", name=new_name, flexilims_session=flm_sess)
        is None
    )


def test_update_entity(flm_sess):
    with pytest.raises(FlexilimsError) as err:
        flz.update_entity("dataset", name="gibberish", flexilims_session=flm_sess)
    assert (
        err.value.args[0] == "Cannot find an entity of type `dataset` named "
        "`gibberish`"
    )
    dataset_name = "mouse_physio_2p_S20211102_overview_zoom2_00001"
    original_entity = flz.get_entity(
        datatype="dataset", name=dataset_name, flexilims_session=flm_sess
    )
    res = flz.update_entity(
        "dataset",
        name=dataset_name,
        flexilims_session=flm_sess,
        attributes={"path": "old/path", "dataset_type": "scanimage"},
        mode="update",
    )
    assert res["attributes"]["path"] == "old/path"
    assert res["attributes"]["acq_num"] == "00001"  # existing attribute is unchanged
    # now in overwrite mode
    res = flz.update_entity(
        "dataset",
        name=dataset_name,
        flexilims_session=flm_sess,
        attributes={
            "path": "new/path",
            "dataset_type": "scanimage",
            "is_raw": res["attributes"]["is_raw"],
        },
    )
    # in the reply the null values are []
    assert res["attributes"]["path"] == "new/path"
    assert res["attributes"]["acq_num"] == []
    # but in the database they are null
    dbval = flz.get_entity(
        "dataset", name=dataset_name, flexilims_session=flm_sess, format_reply=False
    )
    assert dbval["attributes"]["acq_num"] is None

    # restore database state
    ds = Dataset.from_dataseries(dataseries=original_entity, flexilims_session=flm_sess)
    ds.update_flexilims(mode="overwrite")
    new_entity = flz.get_entity(
        datatype="dataset", name=dataset_name, flexilims_session=flm_sess
    )
    assert repr(new_entity) == repr(original_entity)
