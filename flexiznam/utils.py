import pathlib
import yaml


def load_param(param_file=None):
    """Read parameter file from config folder"""
    if param_file is None:
        param_file = pathlib.Path(__file__).parent.absolute() / 'config' / 'config.yml'
    with open(param_file, 'r') as yml_file:
        prm = yaml.safe_load(yml_file)
    return prm


def get_password(username, app, password_file=None):
    """Read the password yaml"""
    if password_file is None:
        password_file = pathlib.Path(__file__).parent.absolute() / 'config' / 'secret_password.yml'
    with open(password_file, 'r') as yml_file:
        pwd = yaml.safe_load(yml_file)
    if app not in pwd:
        raise IOError('No password for %s' % app)
    pwd = pwd[app]
    if username not in pwd:
        raise IOError('No %s password for user %s' % (app, username))
    return pwd[username]


PARAMETERS = load_param()
# expanduser for file paths:
PARAMETERS['download_folder'] = pathlib.Path(PARAMETERS['download_folder']).expanduser()

