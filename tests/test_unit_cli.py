from pathlib import Path

import yaml
from click.testing import CliRunner

from flexiznam import cli
from flexiznam.errors import SyncYmlError


def test_create_yaml_command_delegates_to_parser(monkeypatch, tmp_path):
    called = {}

    def fake_create_yaml(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr("flexiznam.camp.sync_data.create_yaml", fake_create_yaml)
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "skeleton.yml"

    result = CliRunner().invoke(
        cli.create_yaml,
        [
            "--source_dir",
            str(source),
            "--target_yaml",
            str(target),
            "--project",
            "project",
            "--origin",
            "origin",
            "--overwrite",
        ],
    )

    assert result.exit_code == 0
    assert "Created yml skeleton" in result.output
    assert called == {
        "folder_to_parse": str(source),
        "output_file": str(target),
        "origin_name": "origin",
        "project": "project",
        "overwrite": True,
    }


def test_process_yaml_command_writes_parsed_data(monkeypatch, tmp_path):
    source = tmp_path / "source.yml"
    source.write_text("root_folder: /raw\n")
    target = tmp_path / "processed.yml"
    parsed = {"children": {"session": {}}, "root_folder": "/raw"}
    monkeypatch.setattr("flexiznam.camp.sync_data.parse_yaml", lambda *_, **__: parsed)

    result = CliRunner().invoke(
        cli.process_yaml,
        ["--source_yaml", str(source), "--target_yaml", str(target), "--overwrite"],
    )

    assert result.exit_code == 0
    assert yaml.safe_load(target.read_text()) == parsed
    assert f"Processed yaml saved to `{target}`" in result.output


def test_process_yaml_command_reports_missing_data(monkeypatch, tmp_path):
    source = tmp_path / "source.yml"
    source.write_text("root_folder: /raw\n")
    monkeypatch.setattr(
        "flexiznam.camp.sync_data.parse_yaml",
        lambda *_, **__: (_ for _ in ()).throw(FileNotFoundError("/raw/data")),
    )

    result = CliRunner().invoke(cli.process_yaml, ["--source_yaml", str(source)])

    assert result.exit_code != 0
    assert "Could not access the data" in result.output


def test_yaml_to_flexilims_command_converts_sync_errors(monkeypatch, tmp_path):
    source = tmp_path / "source.yml"
    source.write_text("children: {}\n")
    called = {}

    def fake_upload_yaml(*args, **kwargs):
        called["args"] = args
        called["kwargs"] = kwargs
        raise SyncYmlError("invalid yaml")

    monkeypatch.setattr("flexiznam.camp.sync_data.upload_yaml", fake_upload_yaml)

    result = CliRunner().invoke(
        cli.yaml_to_flexilims,
        [
            "--source_yaml",
            str(source),
            "--raw_data_folder",
            "/raw",
            "--conflicts",
            "skip",
        ],
    )

    assert result.exit_code != 0
    assert "invalid yaml" in result.output
    assert called == {
        "args": (Path(source), "/raw"),
        "kwargs": {"conflicts": "skip", "verbose": False},
    }
