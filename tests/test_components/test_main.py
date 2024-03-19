import datetime
import pathlib
from pathlib import Path
import pandas as pd
import portalocker
import pytest
import flexiznam as flz
import yaml
from flexiznam.config import PARAMETERS, get_password
from flexiznam.errors import FlexilimsError, NameNotUniqueError
from tests.tests_resources.data_for_testing import MOUSE_ID, SESSION

# Test functions from main.py
from flexiznam.schema import Dataset, HarpData, ScanimageData

# this needs to change every time I reset flexlilims


def test_get_path():
    p = flz.get_data_root(which="raw", project="test", flexilims_session=None)
    assert p == Path(PARAMETERS["data_root"]["raw"])
    p = flz.get_data_root(which="processed", project="test", flexilims_session=None)
    assert p == Path(PARAMETERS["data_root"]["processed"])
    sess = flz.get_flexilims_session(
        project_id=PARAMETERS["project_ids"]["test"], reuse_token=False
    )
    p = flz.get_data_root(which="processed", project=None, flexilims_session=sess)
    assert p == Path(PARAMETERS["data_root"]["processed"])
    p = flz.get_data_root(which="raw", project="example", flexilims_session=None)
    assert p == Path("/camp/project/example_project/raw")
    with pytest.raises(AssertionError):
        flz.get_data_root(which="processed", project=None, flexilims_session=None)
    with pytest.raises(ValueError):
        flz.get_data_root(which="crap", project="test", flexilims_session=None)
    with pytest.raises(AssertionError):
        p = flz.get_data_root(which="raw", project="random", flexilims_session=None)


def test_get_flexilims_session():
    sess = flz.get_flexilims_session(
        project_id=PARAMETERS["project_ids"]["test"], reuse_token=False
    )
    assert sess.username == PARAMETERS["flexilims_username"]
    sess = flz.get_flexilims_session(project_id=None, reuse_token=True)
    assert sess.username == PARAMETERS["flexilims_username"]
    token_file = flz.config.config_tools._find_file("flexilims_token.yml")
    tokinfo = yaml.safe_load(token_file.read_text())
    token = tokinfo.get("token", None)
    date = tokinfo.get("date", None)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    assert date == today
    assert sess.session.headers["Authorization"].split(" ")[1] == token
    sess = flz.get_flexilims_session(project_id=None, reuse_token=True)
    assert sess.session.headers["Authorization"].split(" ")[1] == token

    # manualy lock the token file to test timeout
    with portalocker.Lock(token_file, "r+", timeout=10) as file_handle:
        with pytest.raises(portalocker.exceptions.LockException):
            sess = flz.get_flexilims_session(
                project_id=None, reuse_token=True, timeout=0.1
            )
        # but fine without the reuse_token flag
        sess = flz.get_flexilims_session(project_id=None, reuse_token=False)
        assert sess.session.headers["Authorization"].split(" ")[1] != token
    sess = flz.get_flexilims_session(project_id=None, reuse_token=True, timeout=0.1)
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
    ds = flz.get_datasets(
        origin_id=MOUSE_ID,
        flexilims_session=flm_sess,
    )
    assert len(ds) == 0
    ds = flz.get_datasets(
        origin_name=SESSION,
        flexilims_session=flm_sess,
        return_paths=True,
    )
    assert len(ds) == 3
    assert all([isinstance(d, pathlib.PosixPath) for d in ds])
    ds = flz.get_datasets(
        origin_name=SESSION,
        flexilims_session=flm_sess,
        return_paths=False,
    )
    assert len(ds) == 3
    assert all([hasattr(d, "path_full") for d in ds])
    ds = flz.get_datasets(
        origin_name=SESSION,
        flexilims_session=flm_sess,
        return_paths=False,
        filter_datasets=dict(acq_uid="overview_zoom1_00001"),
    )
    assert len(ds) == 1
    ds = flz.get_datasets(
        origin_name=SESSION,
        flexilims_session=flm_sess,
        return_paths=False,
        filter_datasets=dict(acq_uid="overview_zoom1_00001"),
        allow_multiple=False,
    )
    assert isinstance(ds, ScanimageData)
    ds = flz.get_datasets(
        origin_name=SESSION,
        flexilims_session=flm_sess,
        return_paths=True,
        filter_datasets=dict(acq_uid="overview_zoom1_00001"),
        allow_multiple=False,
    )
    assert isinstance(ds, pathlib.PosixPath)
    ds = flz.get_datasets(
        origin_name=SESSION,
        flexilims_session=flm_sess,
        return_dataseries=True,
        filter_datasets=dict(acq_uid="overview_zoom1_00001"),
        allow_multiple=True,
    )
    assert isinstance(ds, pd.DataFrame)
    ds = flz.get_datasets(
        origin_name=SESSION,
        flexilims_session=flm_sess,
        return_dataseries=True,
        filter_datasets=dict(acq_uid="overview_zoom1_00001"),
        allow_multiple=False,
    )
    assert isinstance(ds, pd.Series)

    rec = flz.get_children(
        parent_name=SESSION, flexilims_session=flm_sess, children_datatype="recording"
    ).iloc[0]
    ds_all = flz.get_datasets(
        origin_id=rec.id,
        flexilims_session=flm_sess,
        return_paths=False,
    )
    ds_cam = flz.get_datasets(
        origin_id=rec.id,
        dataset_type="camera",
        flexilims_session=flm_sess,
        return_paths=False,
    )
    assert len(ds_all) > len(ds_cam)
    ds = flz.get_datasets(
        origin_id=rec.id,
        dataset_type="camera",
        filter_datasets=dict(timestamp_file="face_camera_timestamps.csv"),
        flexilims_session=flm_sess,
        return_paths=True,
    )
    assert len(ds) == 1
    ds2 = flz.get_datasets(
        origin_id=rec.id,
        dataset_type="camera",
        filter_datasets=dict(timestamp_file="face_camera_timestamps.csv"),
        project_id=flm_sess.project_id,
        return_paths=True,
    )
    assert ds == ds2
    with pytest.raises(AssertionError):
        flz.get_datasets(
            origin_id=rec.id,
            project_id=flm_sess.project_id,
            allow_multiple=False,
        )


def test_get_datasets_recursively(flm_sess):
    ds_dict = flz.get_datasets_recursively(
        flexilims_session=flm_sess, origin_name=SESSION, return_paths=True
    )
    assert len(ds_dict) == 3
    ds_dict = flz.get_datasets_recursively(
        flexilims_session=flm_sess,
        origin_name=SESSION,
        return_paths=False,
        dataset_type="harp",
    )
    assert len(ds_dict) == 2
    ds = []
    for d in ds_dict.values():
        ds.extend(d)
    assert all([isinstance(d, HarpData) for d in ds])
    ds_dict = flz.get_datasets_recursively(
        flexilims_session=flm_sess,
        origin_name=SESSION,
        return_paths=False,
        dataset_type="harp",
        filter_datasets=dict(
            binary_file="PZAD9.4d_S20211102_R173917_SpheresPermTube_harpmessage.bin"
        ),
    )
    assert len(ds_dict) == 1
    ds = ds_dict.values().__iter__().__next__()[0]
    assert isinstance(ds, HarpData)

    ds_dict = flz.get_datasets_recursively(
        flexilims_session=flm_sess,
        origin_name=SESSION,
        return_paths=False,
        filter_parents={"timestamp": "165821"},
    )
    assert len(ds_dict) == 1
    ds_dict = flz.get_datasets_recursively(
        flexilims_session=flm_sess,
        origin_name=SESSION,
        return_paths=False,
        parent_type="recording",
    )
    assert len(ds_dict) == 2


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
    res_all = flz.get_children(parent_name=SESSION, flexilims_session=flm_sess)
    assert (res_all.type != "recording").sum() != 0
    res_part = flz.get_children(
        parent_name=SESSION, flexilims_session=flm_sess, children_datatype="recording"
    )
    assert (res_part.type != "recording").sum() == 0
    assert res_all.shape[1] > res_part.shape[1]
    single_res = flz.get_children(
        parent_name=SESSION,
        flexilims_session=flm_sess,
        children_datatype="dataset",
        filter=dict(notes="Motion correction reference"),
    )
    assert single_res.shape[0] == 1


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
    with pytest.raises(FlexilimsError) as err:
        flz.update_entity(
            "dataset",
            name=dataset_name,
            flexilims_session=flm_sess,
            attributes={
                "path": "new/path",
                "dataset_type": "scanimage",
                "project": "random",
                "createdBy": "BAD",
            },
        )
