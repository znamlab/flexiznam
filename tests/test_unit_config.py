import pytest
import yaml

from flexiznam.config import DEFAULT_CONFIG, config_tools
from flexiznam.errors import ConfigurationError


def test_create_load_and_update_config_without_network(tmp_path):
    config_tools.create_config(
        config_folder=tmp_path,
        overwrite=True,
        favorite_colour="dark",
    )

    parameters = config_tools.load_param(tmp_path)
    assert parameters["favorite_colour"] == "dark"
    assert parameters["mcms_username"] == DEFAULT_CONFIG["mcms_username"]

    config_tools.update_config(
        config_folder=tmp_path,
        add_all_projects=False,
        mcms_username="alfred",
        project_ids={"new_project": "new-id"},
    )
    updated = config_tools.load_param(tmp_path)
    assert updated["mcms_username"] == "alfred"
    assert updated["favorite_colour"] == "dark"
    assert updated["project_ids"]["new_project"] == "new-id"


def test_config_file_lookup_and_passwords(tmp_path):
    missing = tmp_path / "missing"
    with pytest.raises(ConfigurationError, match="Cannot find"):
        config_tools._find_file("config.yml", config_folder=missing)

    token_file = config_tools._find_file(
        "token.yml", config_folder=tmp_path, create_if_missing=True
    )
    assert token_file.read_text() == ""

    password_file = tmp_path / "passwords.yml"
    config_tools.add_password("service", "user", "secret", password_file)
    config_tools.add_password("service", "second", "other", password_file)
    assert config_tools.get_password("service", "user", password_file) == "secret"
    with pytest.raises(ConfigurationError, match="No password"):
        config_tools.get_password("missing", "user", password_file, allow_input=False)


def test_recursive_update_preserves_nested_values_and_checks_types():
    source = {"nested": {"kept": 1}, "value": 1}

    assert config_tools._recursive_update(
        source, {"nested": {"new": 2}, "value": 3}
    ) == {
        "nested": {"kept": 1, "new": 2},
        "value": 3,
    }
    with pytest.raises(AssertionError):
        config_tools._recursive_update({"nested": {}}, {"nested": 1})
    assert config_tools._recursive_update(
        {"nested": {}}, {"nested": 1}, skip_checks=True
    ) == {"nested": 1}


def test_create_config_uses_yaml_template_and_prevents_accidental_overwrite(tmp_path):
    template = tmp_path / "template.yml"
    template.write_text(yaml.safe_dump({"project_ids": {"project": "id"}, "value": 1}))

    config_tools.create_config(config_folder=tmp_path, template=template, value=2)
    assert config_tools.load_param(tmp_path)["value"] == 2
    with pytest.raises(IOError, match="already exists"):
        config_tools.create_config(config_folder=tmp_path, template=template)
