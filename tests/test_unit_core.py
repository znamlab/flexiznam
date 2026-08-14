from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from flexiznam import main, utils
from flexiznam.errors import FlexilimsError, NameNotUniqueError


class FakeSession:
    def __init__(self, results, project_id="project-id"):
        self.results = results
        self.project_id = project_id
        self.calls = []

    def get(self, datatype, **kwargs):
        self.calls.append((datatype, kwargs))
        return [
            {**result, "attributes": dict(result["attributes"])}
            for result in self.results.get(datatype, [])
        ]


def test_project_paths_and_lookup(monkeypatch):
    parameters = {
        "project_ids": {"project": "project-id"},
        "project_paths": {
            "project": {"raw": "/project/raw", "processed": "/project/out"}
        },
        "data_root": {"raw": "/raw", "processed": "/out"},
    }
    monkeypatch.setattr(main, "PARAMETERS", parameters)

    assert main._format_project("project", parameters) == "project-id"
    assert main._format_project("a" * 24, parameters) == "a" * 24
    with pytest.raises(AttributeError, match="Invalid project"):
        main._format_project("unknown", parameters)

    assert main.lookup_project("project-id") == "project"
    assert main.lookup_project("missing") is None
    assert main.get_data_root("raw", project="project") == Path("/project/raw")
    assert main.get_data_root("processed", project="project-id") == Path("/project/out")
    assert main.get_data_root("raw", flexilims_session=FakeSession({})) == Path(
        "/project/raw"
    )
    assert main.get_raw_path("project/a/file") == Path("/project/raw/project/a/file")
    assert main.get_processed_path("project/a/file") == Path(
        "/project/out/project/a/file"
    )
    with pytest.raises(ValueError, match="which"):
        main.get_data_root("archive", project="project")
    with pytest.raises(AssertionError, match="flexilims_session"):
        main.get_data_root("raw")


def test_get_entities_and_entity_formatting():
    results = {
        "mouse": [
            {
                "id": "mouse-id",
                "name": "mouse-1",
                "type": "mouse",
                "attributes": {"sex": "F"},
            }
        ]
    }
    session = FakeSession(results)

    entities = main.get_entities("mouse", name="mouse-1", flexilims_session=session)
    assert entities.loc["mouse-1", "sex"] == "F"
    assert session.calls == [
        (
            "mouse",
            {
                "query_key": None,
                "query_value": None,
                "name": "mouse-1",
                "origin_id": None,
                "id": None,
            },
        )
    ]

    entity = main.get_entity("mouse", name="mouse-1", flexilims_session=session)
    assert entity["id"] == "mouse-id"
    assert (
        main.get_entity("mouse", name="missing", flexilims_session=FakeSession({}))
        is None
    )


def test_get_entity_rejects_non_unique_results():
    session = FakeSession(
        {
            "mouse": [
                {"id": "one", "name": "one", "type": "mouse", "attributes": {}},
                {"id": "two", "name": "two", "type": "mouse", "attributes": {}},
            ]
        }
    )

    with pytest.raises(NameNotUniqueError, match="not 1"):
        main.get_entity("mouse", flexilims_session=session)


def test_entity_helpers_find_ids_paths_and_datatypes(monkeypatch):
    session = FakeSession({})
    responses = {"mouse": None, "session": pd.Series({"id": "session-id", "path": "p"})}

    def fake_get_entity(datatype=None, **_):
        return responses.get(datatype)

    monkeypatch.setattr(main, "get_entity", fake_get_entity)
    monkeypatch.setattr(main, "PARAMETERS", {"datatypes": ["mouse", "session"]})

    assert main.get_datatype(name="session", flexilims_session=session) == "session"
    assert (
        main.get_id("session", datatype="session", flexilims_session=session)
        == "session-id"
    )
    assert (
        main.get_path("session", datatype="session", flexilims_session=session) == "p"
    )

    responses["session"] = None
    assert main.get_datatype(name="missing", flexilims_session=session) is None
    with pytest.raises(FlexilimsError, match="Cannot find"):
        main.get_id("missing", flexilims_session=session)


def test_get_experimental_sessions_filters_by_mouse(monkeypatch):
    session = FakeSession(
        {
            "session": [
                {
                    "id": "one",
                    "name": "one",
                    "type": "session",
                    "origin_id": "mouse-id",
                    "attributes": {},
                },
                {
                    "id": "two",
                    "name": "two",
                    "type": "session",
                    "origin_id": "other-id",
                    "attributes": {},
                },
            ]
        }
    )
    monkeypatch.setattr(main, "get_id", lambda *_, **__: "mouse-id")

    sessions = main.get_experimental_sessions(flexilims_session=session, mouse="mouse")
    assert list(sessions["id"]) == ["one"]


def test_generate_name_increments_until_available(monkeypatch):
    existing = {"sample_2", "sample_3"}
    monkeypatch.setattr(
        main,
        "get_entity",
        lambda _, name, **__: {"name": name} if name in existing else None,
    )

    assert (
        main.generate_name("sample", "sample_2", flexilims_session=FakeSession({}))
        == "sample_4"
    )
    assert (
        main.generate_name("sample", "sample", flexilims_session=FakeSession({}))
        == "sample_0"
    )


def test_format_results_flattens_attributes_and_warns_on_reserved_name():
    results = [
        {"id": "one", "name": "mouse", "attributes": {"sex": "F", "id": "duplicate"}}
    ]

    with pytest.warns(UserWarning, match="should not have id"):
        formatted = main.format_results(results)

    assert formatted.loc[0, "sex"] == "F"
    assert formatted.loc[0, "id"] == "one"


def test_compare_series_and_nested_dictionaries():
    differences = utils.compare_series(
        pd.Series({"same": 1, "changed": (1, 2), "left": "left"}),
        pd.Series({"same": 1, "changed": [2, 1], "right": "right"}),
        series_name=("before", "after"),
    )

    assert differences.loc["changed"].to_dict() == {"before": [1, 2], "after": [2, 1]}
    assert differences.loc["left"].to_dict() == {"before": "left", "after": "NA"}
    assert differences.loc["right"].to_dict() == {"before": "NA", "after": "right"}
    assert utils.compare_dictionaries_recursively(
        {"same": 1, "nested": {"old": 1}, "left": 1},
        {"same": 1, "nested": {"old": 2, "new": 3}, "right": 4},
    ) == {
        "right": ("NOT PRESENT", 4),
        "left": (1, "NOT PRESENT"),
        "nested": {"new": ("NOT PRESENT", 3), "old": (1, 2)},
    }


def test_clean_recursively_handles_json_values_and_errors():
    cleaned = utils.clean_recursively(
        {
            "bad?key": (np.int64(2), np.inf),
            "path": Path("project/data"),
            "nested": [{"keep": np.bool_(True), "remove": "x"}],
        },
        keys="remove",
    )

    assert cleaned == {
        "bad_key": [2, "inf"],
        "path": "project/data",
        "nested": [{"keep": True}],
    }
    with pytest.raises(IOError, match="pandas"):
        utils.clean_recursively(pd.Series([1]))
    unknown = object()
    with pytest.warns(UserWarning, match="unknown type"):
        assert utils.clean_recursively(unknown) == str(unknown)
