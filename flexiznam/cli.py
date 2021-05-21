import pathlib

import click
import yaml
from flexiznam import errors, main, camp
from flexiznam.config import utils


@click.group()
def cli():
    pass


@cli.command()
@click.option('-p', '--project_id', prompt='Enter the project ID', help='Project ID.')
@click.option('-m', '--mouse_name', prompt='Enter the name of the mouse you want to add',
              help='Name of the mouse for flexilims.')
@click.option('--mcms_animal_name', default=None, help='Name of the mouse on MCMS (if different from mouse_name).')
@click.option('--flexilims_username', default=None, help='Your username on flexilims.')
@click.option('--mcms_username', default=None, help='Your username on mcms.')
def add_mouse(project_id, mouse_name, mcms_animal_name=None, flexilims_username=None, mcms_username=None):
    """Add a single mouse to a project."""
    click.echo('Trying to add %s in %s' % (mouse_name, project_id))
    main.add_mouse(mouse_name, project_id, mcms_animal_name, flexilims_username, mcms_username)


@cli.command()
@click.option('-t', '--template', default=None, help='Template config file.')
@click.option('--config_folder', default=None, help='Folder containing the config file.')
def config(template=None, config_folder=None):
    """Create a configuration file if none exists."""
    try:
        fname = utils._find_file('config.yml', config_folder=config_folder)
        click.echo('Configuration file currently used is:\n%s' % fname)
    except errors.ConfigurationError:
        click.echo('No configuration file. Creating one.')
        utils.create_config(template=template, config_folder=config_folder)
    click.echo('\nCurrent configuration is:')
    prm = utils.load_param(param_folder=config_folder)
    click.echo(yaml.dump(prm))


@cli.command()
@click.option('-a', '--app', prompt='Enter the name of the app',
              help='Name of the service requiring the password (flexilims or mcms for instance).')
@click.option('-u', '--username', prompt='Enter the username', help='Username as required by the app.')
@click.option('-p', '--password', prompt='Enter the password (no text will appear)', help='Password to add.',
              hide_input=True)
@click.option('--password_file', default=None,
              help='File to edit or create to add if not using the config folder')
def add_password(app, username, password, password_file):
    """Edit or create password file"""
    pass_file = utils.add_password(app.lower(), username, password, password_file)
    click.echo('Password added in %s' % pass_file)


@cli.command()
@click.option('-s', '--source_yaml', help='Manually generated yaml to seed automatic method.')
@click.option('-t', '--target_yaml', default=None, help='Path to outpout YAML file.')
@click.option('--overwrite', default=False, help='Overwrite the output if it exists.')
def make_full_yaml(source_yaml, target_yaml=None, overwrite=False):
    """Parse source_yaml and autogenerate a full yaml containing all datasets"""
    if target_yaml is None:
        target_yaml = source_yaml.strip('.yml') + 'autogenerated_full_file.yml'
    target_yaml = pathlib.Path(target_yaml)
    if (not overwrite) and target_yaml.exists():
        raise FileExistsError('File %s already exists. Use --overwrite to replace' % target_yaml)
    parsed = camp.sync_data.parse_yaml(source_yaml, raw_data_folder=None, verbose=False)
    with open(target_yaml, 'w') as writer:
        yaml.dump(parsed, writer)
