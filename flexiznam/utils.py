import os.path
import pathlib
import sys
import yaml
from flexiznam.errors import ConfigurationError


def _find_file(file_name):
    """Find a file by looking first in the current directory, then in the config folder, then in sys.path"""
    local = pathlib.Path.cwd() / file_name
    if local.is_file():
        return local
    config = pathlib.Path(__file__).parent.absolute() / 'config' / file_name
    if config.is_file():
        return config
    for directory in sys.path:
        fname = pathlib.Path(directory) / file_name
        if fname.is_file():
            return fname
    raise ConfigurationError('Cannot find %s' % file_name)


def load_param(param_file=None):
    """Read parameter file from config folder"""
    if param_file is None:
        param_file = _find_file('config.yml')
    with open(param_file, 'r') as yml_file:
        prm = yaml.safe_load(yml_file)
    return prm


def get_password(username, app, password_file=None):
    """Read the password yaml"""
    if password_file is None:
        password_file = _find_file('secret_password.yml')
    with open(password_file, 'r') as yml_file:
        pwd = yaml.safe_load(yml_file) or {}
    if app not in pwd:
        raise IOError('No password for %s' % app)
    pwd = pwd[app]
    if username not in pwd:
        raise IOError('No %s password for user %s' % (app, username))
    return pwd[username]


def add_password(app, username, password, password_file=None):
    """Add a password to a new or existing password file"""
    if password_file is None:
        password_file = _find_file('secret_password.yml')
    if os.path.isfile(password_file):
        with open(password_file, 'r') as yml_file:
            pwd = yaml.safe_load(yml_file) or {}  # use empty dict if load returns None or False
    else:
        pwd = {}
    # create or copy the app field
    pwd[app] = pwd.get(app, {})
    pwd[app][username] = password
    with open(password_file, 'w') as yml_file:
        yaml.dump(pwd, yml_file)


def create_config(overwrite=False, target=None, template=None, **kwargs):
    """Create a config file based on a template

    If no template is provided, use ./config/config_example.yml

    **kwargs elements are used to update/supplement infos found in the template
    """
    if template is None:
        template = _find_file('config_example.yml')
    if not os.path.isfile(template):
        raise ConfigurationError('Cannot find template example configuration file')
    with open(template, 'r') as tpl_file:
        cfg = yaml.safe_load(tpl_file)
    cfg = _recursive_update(cfg, kwargs)

    if target is None:
        target = pathlib.Path(__file__).parent.absolute() / 'config' / 'config.yml'
    if (not overwrite) and os.path.isfile(target):
        raise IOError('Config file %s already exists.' % target)
    with open(target, 'w') as cfg_yml:
        yaml.dump(cfg, cfg_yml)


def _recursive_update(source, new_values):
    """Update dict of dict recursively"""
    for k, v in new_values.items():
        if isinstance(v, dict):
            source[k] = _recursive_update(source.get(k, {}), v)
        else:
            source[k] = v
    return source


try:
    PARAMETERS = load_param()
    # expanduser for file paths:
    PARAMETERS['download_folder'] = pathlib.Path(PARAMETERS['download_folder']).expanduser()
except ConfigurationError:
    print('Could not load the parameters. Check your configuration file')
    PARAMETERS = {}