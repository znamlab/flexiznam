import pytest
import pathlib
import pandas as pd
import flexiznam
from flexiznam.schema import Dataset, microscopy_data
from flexiznam.config import PARAMETERS
from flexiznam.errors import DatasetError, FlexilimsError, NameNotUniqueError
from tests.tests_resources.data_for_testing import TEST_PROJECT, PROJECT_ID
from tests.test_components.test_main import MOUSE_ID

# Test the generic dataset class.


def test_dataset(flm_sess):
    ds = Dataset(
        project="test",
        dataset_type="camera",
        is_raw=False,
        path="",
        genealogy=("a", "parent", "test"),
    )
    assert ds.full_name == "a_parent_test"
    assert ds.dataset_name == "test"
    ds = Dataset(
        project="demo_project",
        dataset_type="camera",
        is_raw=False,
        path="",
        genealogy=("a", "parent", "test"),
        flexilims_session=flm_sess,
    )
    assert ds.project_id == ds.flexilims_session.project_id
    Dataset(
        project_id=ds.project_id,
        dataset_type="camera",
        is_raw=False,
        path="",
        genealogy=("a", "parent", "test"),
        flexilims_session=flm_sess,
    )
    Dataset(
        project_id=ds.project_id,
        project="demo_project",
        dataset_type="camera",
        is_raw=False,
        path="",
        genealogy=("a", "parent", "test"),
        flexilims_session=flm_sess,
    )
    with pytest.raises(DatasetError) as err:
        Dataset(
            project="test",
            dataset_type="camera",
            is_raw=False,
            path="",
            genealogy=("a", "parent", "test"),
            flexilims_session=flm_sess,
        )
        assert err.value.args[0] == "Project must match that of flexilims_session"
    with pytest.raises(DatasetError) as err:
        Dataset(
            project="test",
            dataset_type="camera",
            is_raw=False,
            path="",
            genealogy=("a", "parent", "test"),
            project_id=ds.project_id,
        )
        assert err.value.args[0] == "project_id does not correspond to project"


def test_constructor():
    """Make sure that all dataset subclass work with the same constructor"""
    constructor = dict(
        path="none",
        is_raw=True,
        genealogy=None,
        extra_attributes=dict(p=2),
        created="random",
        project="demo_project",
        project_id=PARAMETERS["project_ids"]["demo_project"],
        origin_id="anotherthing",
        flexilims_session=None,
    )
    # make sure that mandatory arguments are given
    extra_attributes = dict(camera=dict(video_file=None), harp=dict(binary_file=None))
    for ds_type, ds_subcls in Dataset.SUBCLASSES.items():
        if ds_type in extra_attributes:
            constructor["extra_attributes"] = extra_attributes[ds_type]
        ds_subcls(**constructor)


def test_dataset_flexilims_integration(flm_sess):
    """This test requires the database to be up-to-date for the physio mouse"""
    ds = Dataset(
        project="demo_project",
        path="fake/path",
        is_raw="no",
        dataset_type="camera",
        extra_attributes={},
        created="",
        flexilims_session=flm_sess,
        genealogy=(
            "mouse_physio_2p",
            "S20211102",
            "R165821_SpheresPermTube",
            "wf_camera",
        ),
    )
    st = ds.flexilims_status()
    assert st == "different"
    rep = ds.flexilims_report()
    expected = pd.DataFrame(
        dict(
            offline={
                "is_raw": "no",
                "path": "fake/path",
                "created": "",
                "metadata_file": "NA",
                "timestamp_file": "NA",
                "video_file": "NA",
            },
            flexilims={
                "is_raw": "yes",
                "created": "2021-11-02 17:03:17",
                "path": "demo_project/mouse_physio_2p/"
                "S20211102/R165821_SpheresPermTube",
                "origin_id": "61ebf94120d82a35f724490d",
                "timestamp_file": "wf_camera_timestamps.csv",
                "video_file": "wf_camera_data.bin",
                "metadata_file": "wf_camera_metadata.txt",
            },
        )
    )
    assert all(rep.sort_index() == expected.sort_index())
    ds_name = "mouse_physio_2p_S20211102_R165821_SpheresPermTube_wf_camera"
    fmt = {
        "path": "fake/path",
        "created": "",
        "dataset_type": "camera",
        "is_raw": "no",
        "name": ds_name,
        "project": "610989f9a651ff0b6237e0f6",
        "type": "dataset",
        "genealogy": (
            "mouse_physio_2p",
            "S20211102",
            "R165821_SpheresPermTube",
            "wf_camera",
        ),
    }
    assert ds.format().name == ds_name
    assert all(
        ds.format().drop("origin_id").sort_index()
        == pd.Series(data=fmt, name=ds_name).sort_index()
    )

    # same with yaml mode
    fmt["extra_attributes"] = {}
    fmt["genealogy"] = list(fmt["genealogy"])
    ds_yaml = ds.format(mode="yaml")
    try:
        del ds_yaml["origin_id"]
    except KeyError:
        pass
    assert ds_yaml == fmt

    ds = Dataset(
        path="fake/path",
        is_raw="no",
        dataset_type="camera",
        extra_attributes={},
        created="",
    )
    assert ds.project_id is None
    # check that updating project change id
    ds.project = "3d_vision"
    assert ds.project_id == PARAMETERS["project_ids"]["3d_vision"]
    # and conversely
    ds.project_id = PARAMETERS["project_ids"]["test"]
    assert ds.project == "test"


def test_from_flexilims(flm_sess):
    """This test requires the database to be up-to-date for the physio mouse"""
    project = "demo_project"
    ds = Dataset.from_flexilims(
        project,
        flexilims_session=flm_sess,
        name="mouse_physio_2p_S20211102_R165821_" "SpheresPermTube_wf_camera",
    )
    assert ds.flexilims_session == flm_sess
    assert ds.full_name == "mouse_physio_2p_S20211102_R165821_SpheresPermTube_wf_camera"
    assert ds.flexilims_status() == "up-to-date"
    assert ds.project == project
    ds_by_id = Dataset.from_flexilims(flexilims_session=flm_sess, id=ds.id)
    assert ds_by_id.full_name == ds.full_name
    assert ds_by_id.project == project


def test_from_dataseries(flm_sess):
    """This test requires the config file to include demo_project"""
    series = pd.Series(
        name="minimal_series",
        data=dict(
            genealogy=("minimal_series",),
            path="/fake/path",
            id="hexidonflexilims",
            project=PROJECT_ID,
            is_raw="no",
            dataset_type="suite2p_rois",
        ),
    )
    ds = Dataset.from_dataseries(
        dataseries=series,
        flexilims_session=flm_sess,
    )
    assert ds.flexilims_session == flm_sess
    assert ds.full_name == "minimal_series"
    assert type(ds) == Dataset
    series = pd.Series(
        name="test_microscopy",
        data=dict(
            genealogy=(
                "test",
                "microscopy",
            ),
            path="/fake/path",
            id="hexidonflexilims",
            project=PROJECT_ID,
            is_raw="no",
            dataset_type="microscopy",
        ),
    )

    ds = Dataset.from_dataseries(
        dataseries=series,
        flexilims_session=flm_sess,
    )
    assert ds.flexilims_session == flm_sess
    assert ds.full_name == "test_microscopy"
    assert ds.dataset_name == "microscopy"
    assert type(ds) == microscopy_data.MicroscopyData


def test_from_origin(flm_sess):
    """This test requires the database to be up-to-date for the physio mouse"""
    origin_name = "mouse_physio_2p_S20211102_R165821_SpheresPermTube"
    ds0 = Dataset.from_origin(
        origin_type="recording",
        origin_name=origin_name,
        dataset_type="suite2p_rois",
        conflicts="abort",
        flexilims_session=flm_sess,
    )
    assert ds0.flexilims_session == flm_sess
    assert ds0.genealogy[-1].startswith("suite2p_rois")
    assert ds0.dataset_name == "suite2p_rois_0"
    ds0.update_flexilims()
    # now from_origin should raise an error if abort
    with pytest.raises(DatasetError) as err:
        Dataset.from_origin(
            origin_type="recording",
            origin_name=origin_name,
            dataset_type="suite2p_rois",
            conflicts="abort",
            flexilims_session=flm_sess,
        )
    ds0_bis = Dataset.from_origin(
        origin_type="recording",
        origin_name=origin_name,
        dataset_type="suite2p_rois",
        conflicts="overwrite",
        flexilims_session=flm_sess,
    )
    assert ds0.id == ds0_bis.id

    ds1 = Dataset.from_origin(
        origin_type="recording",
        origin_name=origin_name,
        dataset_type="suite2p_rois",
        conflicts="append",
        flexilims_session=flm_sess,
    )
    assert ds1.id is None
    assert ds1.flexilims_session == flm_sess
    assert ds1.dataset_name == "suite2p_rois_1"
    ds1.update_flexilims()
    assert ds1.id is not None
    assert ds1.id != ds0.id
    # now we have 2 datasets, skip and overwrite should raise an error
    with pytest.raises(NameNotUniqueError) as err:
        Dataset.from_origin(
            origin_type="recording",
            origin_name=origin_name,
            dataset_type="suite2p_rois",
            conflicts="skip",
            flexilims_session=flm_sess,
        )
    with pytest.raises(NameNotUniqueError) as err:
        Dataset.from_origin(
            origin_type="recording",
            origin_name=origin_name,
            dataset_type="suite2p_rois",
            conflicts="overwrite",
            flexilims_session=flm_sess,
        )
    # clean up
    for ds in (ds0, ds1):
        flm_sess.delete(ds.id)


def test_update_flexilims(flm_sess):
    """This test requires the database to be up-to-date for the physio mouse"""
    project = "demo_project"
    ds_name = "mouse_physio_2p_S20211102_R165821_SpheresPermTube_wf_camera"
    ds = Dataset.from_flexilims(project, name=ds_name, flexilims_session=flm_sess)
    original_path = ds.path
    ds.path = "new/test/path"
    with pytest.raises(FlexilimsError) as err:
        ds.update_flexilims()
    assert err.value.args[0].startswith("Cannot change existing flexilims entry with")
    ds.update_flexilims(mode="overwrite")
    reloaded_ds = Dataset.from_flexilims(
        project, name=ds_name, flexilims_session=flm_sess
    )
    assert str(reloaded_ds.path) == ds.path
    # undo changes:
    ds.path = original_path
    ds.update_flexilims(mode="overwrite")

    # try to change the origin_id
    original_origin_id = ds.origin_id
    ds.origin_id = MOUSE_ID
    ds.update_flexilims(mode="overwrite")
    assert ds.get_flexilims_entry()["origin_id"] == MOUSE_ID
    ds.origin_id = original_origin_id
    ds.update_flexilims(mode="overwrite")
    assert ds.get_flexilims_entry()["origin_id"] == original_origin_id
    with pytest.raises(FlexilimsError) as err:
        ds.origin_id = None
        ds.update_flexilims(mode="overwrite")
    assert err.value.args[0] == "Cannot set origin_id to null"


def test_dataset_paths(flm_sess):
    """This test requires the database to be up-to-date for the physio mouse"""
    project = "demo_project"
    ds_name = "mouse_physio_2p_S20211102_R165821_SpheresPermTube_wf_camera"
    ds = Dataset.from_flexilims(project, name=ds_name, flexilims_session=flm_sess)
    path_root = pathlib.Path(PARAMETERS["data_root"]["raw"])
    assert ds.path_root == path_root
    assert str(ds.path_full) == str(
        pathlib.Path(PARAMETERS["data_root"]["raw"] / ds.path)
    )
    ds = Dataset(
        path="test_project",
        is_raw="no",
        dataset_type="camera",
        extra_attributes={},
        created="",
        project="example",
    )
    assert ds.path_root != pathlib.Path(PARAMETERS["data_root"]["processed"])
    assert ds.path_root == flexiznam.get_data_root(which="processed", project="example")


def test_project_project_id(flm_sess):
    """Check that project, project_id and flm_sess.project are linked"""
    with pytest.raises(DatasetError) as err:
        Dataset(
            path="fake/path",
            is_raw="no",
            dataset_type="camera",
            extra_attributes={},
            created="",
            project="test",
            flexilims_session=flm_sess,
        )
    assert err.value.args[0] == "Project must match that of flexilims_session"
    ds = Dataset(
        path="fake/path",
        is_raw="no",
        dataset_type="camera",
        extra_attributes={},
        created="",
        project="test",
        flexilims_session=None,
    )
    with pytest.raises(DatasetError) as err:
        ds.flexilims_session = flm_sess
    assert (
        err.value.args[0] == "Cannot use a flexilims_session from a different project"
    )
    ds.project_id = PARAMETERS["project_ids"][TEST_PROJECT]
    # that changes project too
    assert ds.project == TEST_PROJECT
    # now I can change flm_sess
    ds.flexilims_session = flm_sess


def test_dataset_type_enforcer():
    orignal_value = PARAMETERS["enforce_dataset_types"]
    PARAMETERS["enforce_dataset_types"] = True
    valid_dstype = PARAMETERS["dataset_types"][0]
    ds = Dataset(
        path="fake/path",
        is_raw="no",
        dataset_type=valid_dstype,
        extra_attributes={},
        created="",
        project="test",
        flexilims_session=None,
    )
    with pytest.raises(DatasetError) as err:
        ds = Dataset(
            path="fake/path",
            is_raw="no",
            dataset_type="badtypeJJJJJ",
            extra_attributes={},
            created="",
            project="test",
            flexilims_session=None,
        )
    assert err.value.args[0].startswith(
        'dataset_type "badtypeJJJJJ" not valid. Valid types are:'
    )
    PARAMETERS["enforce_dataset_types"] = False
    ds = Dataset(
        path="fake/path",
        is_raw="no",
        dataset_type="badtypeJJJJJ",
        extra_attributes={},
        created="",
        project="test",
        flexilims_session=None,
    )
    PARAMETERS["enforce_dataset_types"] = orignal_value
