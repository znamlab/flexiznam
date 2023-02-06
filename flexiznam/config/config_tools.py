import os.path
from pathlib import Path
import sys
import yaml
from copy import deepcopy
import flexiznam
from flexiznam.errors import ConfigurationError
from flexiznam.config.default_config import DEFAULT_CONFIG
from getpass import getpass


def _find_file(file_name, config_folder=None):
    """Find a file by looking at various places

    Only in config_folder (if provided)
    Otherwise look:
    - in the current directory
    - then in the ~/.config folder
    - then in the folder contain the file defining this function
    - then in sys.path
    """
    if config_folder is not None:
        in_config_folder = Path(config_folder) / file_name
        if in_config_folder.is_file():
            return in_config_folder
        raise ConfigurationError("Cannot find %s in %s" % (file_name, config_folder))
    local = Path.cwd() / file_name
    if local.is_file():
        return local
    config = Path(__file__).parent.absolute() / "config" / file_name
    home = Path.home() / ".flexiznam"
    if home.is_dir() and (home / file_name).is_file():
        return home / file_name
    if config.is_file():
        return config
    for directory in sys.path:
        fname = Path(directory) / file_name
        if fname.is_file():
            return fname
    raise ConfigurationError("Cannot find %s" % file_name)


def load_param(param_folder=None, config_file="config.yml"):
    """Read parameter file from config folder"""
    if param_folder is None:
        param_file = _find_file(config_file)
    else:
        param_file = Path(param_folder) / config_file
    with open(param_file, "r") as yml_file:
        prm = yaml.safe_load(yml_file)
    return prm


def get_password(username, app, password_file=None):
    """Read the password yaml"""
    if password_file is None:
        password_file = _find_file("secret_password.yml")
    with open(password_file, "r") as yml_file:
        pwd = yaml.safe_load(yml_file) or {}
    try:
        if app not in pwd:
            raise IOError("No password for %s" % app)
        pwd = pwd[app]
        if username not in pwd:
            raise IOError("No %s password for user %s" % (app, username))
        return pwd[username]
    except IOError:
        return getpass(prompt=f"Enter {app} password: ")


def add_password(app, username, password, password_file=None):
    """Add a password to a new or existing password file"""
    if password_file is None:
        try:
            password_file = _find_file("secret_password.yml")
        except ConfigurationError:
            home = Path.home() / ".flexiznam"
            if not home.is_dir():
                os.mkdir(home)
            password_file = home / "secret_password.yml"
    if os.path.isfile(password_file):
        with open(password_file, "r") as yml_file:
            pwd = yaml.safe_load(yml_file) or {}  # use empty dict if load returns None
    else:
        pwd = {}
    # create or copy the app field
    pwd[app] = pwd.get(app, {})
    pwd[app][username] = password
    with open(password_file, "w") as yml_file:
        yaml.dump(pwd, yml_file)
    return password_file


def update_config(
    param_file="config.yml",
    config_folder=None,
    add_all_projects=True,
    skip_checks=False,
    **kwargs,
):
    """Update the current configuration

    You can give any keyword arguments. For nested levels, provide a dictionary (of
    dictionaries). For instance:
    update_config(project_ids=dict(my_project='its_id'))

    will add the new project into the project_ids dictionary without removing existing
    projects.

    If you want

    Args:
        param_file (str): name of the param file.
        config_folder (str): folder to save config. Usually `~/.flexiznam`
        add_all_projects (bool): If True, will connect to flexilims to download project
                                 IDs
        skip_checks (bool): If True allow to replace a nested field by a flat structure
        **kwargs: Parameters to change (see description above)

    Returns:
        None
    """

    if config_folder is None:
        config_folder = Path.home() / ".flexiznam"

    full_param_path = Path(config_folder) / param_file

    # get all existing params and add the kwargs
    prm = load_param(config_file=full_param_path)
    kwargs = _recursive_update(prm, kwargs, skip_checks=skip_checks)

    if add_all_projects:
        flm_sess = flexiznam.get_flexilims_session()
        projects = flm_sess.get_project_info()
        project_ids = {}
        for project in projects:
            project_ids[project["name"]] = project["id"]
        if "project_ids" in kwargs:
            project_ids.update(kwargs["project_ids"])
        kwargs["project_ids"] = project_ids

    # run create_config with template=None to append new keys
    create_config(
        config_folder=config_folder,
        config_file=param_file,
        overwrite=True,
        template=None,
        skip_checks=skip_checks,
        **kwargs,
    )


def create_config(
    overwrite=False,
    config_folder=None,
    template=None,
    skip_checks=False,
    config_file="config.yml",
    **kwargs,
):
    """Create a config file based on a template

    If no template is provided, use ./config/default_config.py to generate a new config
    file

    **kwargs elements are used to update/supplement info found in the template
    """
    if template is not None:
        if isinstance(template, dict):
            cfg = template
        else:  # we don't have a preloaded config, must be path to a file
            with open(template, "r") as tpl_file:
                cfg = yaml.safe_load(tpl_file)
    else:
        cfg = deepcopy(DEFAULT_CONFIG)
    cfg = _recursive_update(cfg, kwargs, skip_checks=skip_checks)

    if config_folder is None:
        config_folder = Path.home() / ".flexiznam"
        if not config_folder.is_dir():
            os.mkdir(config_folder)
    else:
        config_folder = Path(config_folder)
        assert config_folder.is_dir()
    target_file = config_folder / config_file
    if (not overwrite) and os.path.isfile(target_file):
        raise IOError("Config file %s already exists." % target_file)
    with open(target_file, "w") as cfg_yml:
        yaml.dump(cfg, cfg_yml)


def _recursive_update(source, new_values, skip_checks=False):
    """Update dict of dict recursively"""
    for k, v in new_values.items():
        if isinstance(v, dict):
            source[k] = _recursive_update(source.get(k, {}), v)
        else:
            if not skip_checks:
                assert not isinstance(source.get(k, None), dict)
            source[k] = v
    return source


try:
    PARAMETERS = load_param()
    # expanduser for file paths:
    PARAMETERS["download_folder"] = Path(PARAMETERS["download_folder"]).expanduser()
except ConfigurationError:
    print("Could not load the parameters. Check your configuration file")
    PARAMETERS = {}

__all__ = [
    "load_param",
    "get_password",
    "add_password",
    "update_config",
    "create_config",
    "PARAMETERS",
]
