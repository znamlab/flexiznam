from pathlib import Path

import pandas as pd
import pytest
import yaml

from flexiznam.camp import sync_data


def test_create_yaml_writes_generated_structure(monkeypatch, tmp_path):
    source = tmp_path / "session"
    source.mkdir()
    target = tmp_path / "acquisition.yml"
    generated = {"project": "project", "children": {"session": {}}}
    monkeypatch.setattr(sync_data, "create_yaml_dict", lambda *_, **__: generated)

    sync_data.create_yaml(source, "project", "origin", target)

    assert yaml.safe_load(target.read_text()) == generated
    monkeypatch.setattr("builtins.input", lambda _: "no")
    with pytest.raises(FileExistsError, match="overwrite"):
        sync_data.create_yaml(source, "project", "origin", target)


def test_create_yaml_dict_uses_origin_and_formats_output(monkeypatch, tmp_path):
    session_folder = tmp_path / "session"
    session_folder.mkdir()
    origin = pd.Series({"genealogy": ["mouse", "session"]})
    captured = {}
    monkeypatch.setattr(sync_data.flz, "get_flexilims_session", lambda **_: "session")
    monkeypatch.setattr(sync_data.flz, "get_entity", lambda **_: origin)
    monkeypatch.setattr(
        sync_data,
        "_create_yaml_dict",
        lambda **kwargs: captured.update(kwargs) or {"recording": {}},
    )

    result = sync_data.create_yaml_dict(session_folder, "project", "origin")

    assert result == {
        "root_folder": str(tmp_path),
        "origin_name": "origin",
        "children": {"recording": {}},
        "project": "project",
    }
    assert captured["genealogy"] == ["mouse", "session"]
    assert captured["level_folder"] == session_folder


def test_parse_yaml_uses_yaml_metadata_and_checks_result(monkeypatch, tmp_path):
    root = tmp_path / "raw"
    session_folder = root / "session"
    session_folder.mkdir(parents=True)
    source = {
        "root_folder": str(root),
        "origin_name": "origin",
        "project": "project",
        "children": {"session": {}},
    }
    origin = pd.Series({"genealogy": ["mouse", "session"]})
    captured = {}
    monkeypatch.setattr(sync_data.flz, "get_flexilims_session", lambda **_: "session")
    monkeypatch.setattr(sync_data.flz, "get_entity", lambda **_: origin)
    monkeypatch.setattr(
        sync_data,
        "_create_yaml_dict",
        lambda **kwargs: captured.update(kwargs) or {"session": {"datasets": []}},
    )
    monkeypatch.setattr(sync_data, "check_yaml_validity", lambda *args: (args[0], []))

    result = sync_data.parse_yaml(source)

    assert result["root_folder"] == str(root)
    assert result["children"] == {"session": {"datasets": []}}
    assert captured["only_datasets"] is True
    assert captured["level_folder"] == session_folder


def test_check_yaml_validity_checks_metadata_and_descendants(monkeypatch):
    yaml_data = {
        "root_folder": "/raw",
        "origin_name": "origin",
        "project": "project",
        "children": {"session": {}},
    }
    origin = pd.Series({"genealogy": ["mouse", "session"]})
    monkeypatch.setattr(sync_data.flz, "get_flexilims_session", lambda **_: "session")
    monkeypatch.setattr(sync_data.flz, "get_entity", lambda **_: origin)
    monkeypatch.setattr(
        sync_data, "_check_recursively", lambda children, **kwargs: [kwargs]
    )

    result, errors = sync_data.check_yaml_validity(
        yaml_data,
        root_folder=Path("/raw"),
        origin_name="origin",
        project="project",
    )

    assert result is yaml_data
    assert errors[0]["origin_genealogy"] == ["mouse", "session"]
    with pytest.raises(AssertionError, match="project is"):
        sync_data.check_yaml_validity(yaml_data, project="other")
