import os
import pytest
import numpy as np
from pathlib import Path
import pandas as pd
import tempfile
from flexiznam.config import config_tools, DEFAULT_CONFIG
from flexiznam import utils


def test_create_config():
    with tempfile.TemporaryDirectory() as tmp:
        config_tools.create_config(
            overwrite=True, config_folder=tmp, favorite_colour="dark"
        )
        # reload and check one random field
        prm = config_tools.load_param(tmp)
        assert prm["mcms_username"] == "yourusername"
        assert prm["favorite_colour"] == "dark"
        # check that I load it if the cwd is the local path
        prm = config_tools.load_param()
        assert "favorite_colour" not in prm
        cwd = os.getcwd()
        os.chdir(tmp)
        prm = config_tools.load_param()
        assert prm["favorite_colour"] == "dark"
        os.chdir(cwd)


def test_update_config():
    with tempfile.TemporaryDirectory() as tmp:
        config_tools.create_config(
            overwrite=True, config_folder=tmp, favorite_colour="dark"
        )
        prm = config_tools.load_param(tmp)
        assert len(prm["project_ids"]) == len(DEFAULT_CONFIG["project_ids"])
        config_tools.update_config(
            param_file="config.yml",
            config_folder=tmp,
            skip_checks=False,
            mcms_username="alfred",
            project_ids=dict(new_project="test_id"),
            add_all_projects=False,
        )
        prm = config_tools.load_param(tmp)
        assert prm["mcms_username"] == "alfred"
        assert prm["favorite_colour"] == "dark"
        assert prm["project_ids"]["new_project"] == "test_id"
        assert prm["project_ids"]["test"] == DEFAULT_CONFIG["project_ids"]["test"]
        n_projs = len(prm["project_ids"])
        assert n_projs == (len(DEFAULT_CONFIG["project_ids"]) + 1)
        prm = config_tools.load_param()
        assert "favorite_colour" not in prm
        config_tools.update_config(
            param_file="config.yml", config_folder=tmp, add_all_projects=True
        )
        prm = config_tools.load_param(tmp)
        if n_projs != 5:
            print(n_projs)
        print(prm["project_ids"])
        assert len(prm["project_ids"]) > n_projs
        assert "new_project" in prm["project_ids"]
        config_tools.update_config(
            param_file="config.yml",
            config_folder=tmp,
            add_all_projects=True,
            project_ids=dict(new_project="update_id"),
        )
        prm = config_tools.load_param(tmp)
        assert prm["project_ids"]["new_project"] == "update_id"


def test_passwd_creation():
    with tempfile.NamedTemporaryFile() as tmp:
        config_tools.add_password(
            "my_app", "username1", "password1", password_file=tmp.name
        )
        config_tools.add_password(
            "my_app", "username2", "password2", password_file=tmp.name
        )
        config_tools.add_password(
            "my_otherapp", "username", "password", password_file=tmp.name
        )

        pwd = config_tools.get_password("username1", "my_app", tmp.name)
        assert pwd == "password1"


def test_check_flexilims_paths(flm_sess):
    df = utils.check_flexilims_paths(flm_sess)
    df2 = utils.check_flexilims_paths(flm_sess, error_only=False)
    assert df.shape[1] == df2.shape[1] - 1
    assert df2.shape[0] > df.shape[0]
    df = utils.check_flexilims_paths(
        flm_sess, root_name="mouse_physio_2p", recursive=False, error_only=False
    )
    assert len(df) == 1
    df = utils.check_flexilims_paths(
        flm_sess, root_name="mouse_physio_2p", recursive=True, error_only=False
    )
    assert len(df) > 1


def test_check_flexilims_names(flm_sess):
    df = utils.check_flexilims_names(flm_sess, root_name="mouse_physio_2p")
    assert df is None
    df = utils.check_flexilims_names(flm_sess)
    assert df is None
    df = utils.check_flexilims_names(flm_sess, recursive=True)
    assert df is None


@pytest.mark.slow
def test_add_genealogy(flm_sess):
    added = utils.add_genealogy(flm_sess)
    assert added == []
    added = utils.add_genealogy(flm_sess, recursive=True)
    assert added == []


def test_clean_recursively():
    out = utils.clean_recursively(
        {
            "a": (1, 2),
            "b": np.array([1, 2]),
            "c": [1, (1, 2)],
            "d": Path("/this/is/a/path"),
        }
    )
    assert out["a"] == [1, 2]
    assert out["b"] == [1, 2]
    assert out["c"] == [1, [1, 2]]
    assert out["d"] == "/this/is/a/path"

    out = utils.clean_recursively(dict(nested=[dict(a=[np.inf])]))
    assert out["nested"][0]["a"][0] == "inf"

    out = {"Invalid.Name": "Valid-Value:", "ValidName": {"I+nvalid*Key": "Valid-Value"}}
    utils.clean_recursively(out)
    assert "Invalid_Name" in out
    assert "I_nvalid_Key" in out["ValidName"]


def test_add_missing_paths(flm_sess):
    utils.add_missing_paths(flm_sess)


@pytest.mark.slow
def test_check_attribute(flm_sess):
    attr = utils._check_attribute_case(flm_sess)
    for att in attr.attribute.unique():
        assert att.lower() != att
