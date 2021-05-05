import click
import yaml
from flexiznam import utils, errors, main

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
def config(template=None):
    """Create a configuration file if none exists."""
    try:
        fname = utils._find_file('config.yml')
        click.echo('Configuration file currently used is:\n%s' % fname)
    except errors.ConfigurationError:
        click.echo('No configuration file. Creating one.')
        utils.create_config(template=template)
    click.echo('\nCurrent configuration is:')
    prm = utils.load_param()
    click.echo(yaml.dump(prm))


@cli.command()
@click.option('-a', '--app', prompt='Enter the name of the app',
              help='Name of the service requiring the password (flexilims or mcms for instance).')
@click.option('-u', '--username', prompt='Enter the username', help='Username as required by the app.')
@click.option('-p', '--password', prompt='Enter the password (no text will appear)', help='Password to add.',
              hide_input=True)
@click.option('--password-file', default=None,
              help='File to edit or create to add if not using the config folder')
def add_password(app, username, password, password_file):
    """Edit or create password file"""
    pass_file = utils.add_password(app, username, password, password_file)
    click.echo('Password added in %s' % pass_file)


if __name__ == '__main__':
    main.add_mouse(mouse_name='PZAJ2.1c', project_id='test')
