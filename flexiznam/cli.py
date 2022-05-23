import click

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
    from flexiznam import main

    """Add a single mouse to a project."""
    click.echo('Trying to add %s in %s' % (mouse_name, project_id))
    main.add_mouse(mouse_name=mouse_name, project_id=project_id,
                   mcms_animal_name=mcms_animal_name, mcms_username=mcms_username,
                   flexilims_username=flexilims_username,)


@cli.command()
@click.option('-t', '--template', default=None, help='Template config file.')
@click.option('--config_folder', default=None, help='Folder containing the config file.')
@click.option('--update/--no-update', default=False,
              help='Update the config file to include all fields present in the default '
                   'config. Will not change already defined fields.')
def config(template=None, config_folder=None, update=False):
    """Create a configuration file if none exists."""
    from flexiznam.config import config_tools
    from flexiznam import errors
    import yaml

    try:
        fname = config_tools._find_file('config.yml', config_folder=config_folder)
        click.echo('Configuration file currently used is:\n%s' % fname)
        if update:
            click.echo('Updating file')
            prm = config_tools.load_param(param_folder=config_folder)
            config_tools.create_config(overwrite=True, template=template,
                                       config_folder=config_folder,
                                       **prm)
    except errors.ConfigurationError:
        click.echo('No configuration file. Creating one.')
        config_tools.create_config(template=template, config_folder=config_folder)
        fname = config_tools._find_file('config.yml', config_folder=config_folder)
        click.echo('Configuration file created here:\n%s' % fname)
    click.echo('\nCurrent configuration is:')
    prm = config_tools.load_param(param_folder=config_folder)
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
    from flexiznam.config import config_tools

    pass_file = config_tools.add_password(app.lower(), username, password, password_file)
    click.echo('Password added in %s' % pass_file)


@cli.command()
@click.option('-s', '--source_dir', required=True,
              help='Base directory for this yaml file. Usually a session directory')
@click.option('-t', '--target_yaml', required=True, help='Path to output YAML file.')
@click.option('-p', '--project', default='NOT SPECIFIED', help='Project name on flexilims.')
@click.option('-m', '--mouse', default='NOT SPECIFIED', help='Mouse name on flexilims.')
@click.option('--overwrite/--no-overwrite', default=False,
              help='If target yaml exist, should I replace it?.')
@click.option('--process/--no-process', default=False,
              help='After creating the yaml skeleton, should I also parse it?')
@click.option('-r', '--raw_data_folder', default=None,
              help='Path to the root folder containing raw data. Only used with '
                   '`--process`')
def create_yaml(source_dir, target_yaml, project, mouse, overwrite, process,
                raw_data_folder):
    """Create a yaml file by looking recursively in `root_dir`"""
    from flexiznam import camp
    import pathlib

    target_yaml = pathlib.Path(target_yaml)
    if (not overwrite) and target_yaml.exists():
        s = input('File %s already exists. Overwrite (yes/[no])? ' % target_yaml)
        if s == 'yes':
            overwrite = True
        else:
            raise(FileExistsError('File %s already exists and overwrite is not allowed'
                                  % target_yaml))
    source_dir = pathlib.Path(source_dir)
    if not source_dir.is_dir():
        raise FileNotFoundError('source_dir %s is not a directory' % source_dir)
    yml_content = camp.sync_data.create_yaml(root_folder=source_dir,
                                             outfile=target_yaml,
                                             project=project,
                                             mouse=mouse,
                                             overwrite=overwrite)
    click.echo('Created yml skeleton in %s' % target_yaml)


@cli.command()
@click.option('-s', '--source_yaml', required=True, help='Manually generated yaml to seed automatic method.')
@click.option('-t', '--target_yaml', default=None, help='Path to outpout YAML file.')
@click.option('-r', '--raw_data_folder', default=None, help='Path to the root folder containing raw data')
@click.option('--overwrite/--no-overwrite', default=False, help='Overwrite the output if it exists.')
def process_yaml(source_yaml, target_yaml=None, overwrite=False, raw_data_folder=None):
    """Parse source_yaml and autogenerate a full yaml containing all datasets"""
    from flexiznam import camp
    import pathlib

    source_yaml = pathlib.Path(source_yaml)
    if target_yaml is None:
        target_yaml = source_yaml.parent / (source_yaml.with_suffix('').name + '_autogenerated_full_file.yml')
    target_yaml = pathlib.Path(target_yaml)
    if (not overwrite) and target_yaml.exists():
        s = input('File %s already exists. Overwrite (yes/[no])? ' % target_yaml)
        if s == 'yes':
            overwrite = True
        else:
            raise(FileExistsError('File %s already exists and overwrite is not allowed' % target_yaml))

    click.echo('Reading %s' % source_yaml)
    try:
        parsed = camp.sync_data.parse_yaml(source_yaml, raw_data_folder=raw_data_folder,
                                           verbose=False)
    except FileNotFoundError as err:
        msg = 'Cannot process yaml file. Could not access the data.\n%s' % err.args[0]
        raise click.ClickException(msg)
    errors = camp.sync_data.find_xxerrorxx(yml_data=parsed)
    if errors:
        click.echo('\nFound some issues with the yaml:')
        for k, v in errors.items():
            click.echo('    - Dataset: `%s`' % k)
            click.echo('              %s' % v.strip('XXERRRORR!! '))
        click.echo('Fix manually these errors before uploading to flexilims')
    camp.sync_data.write_session_data_as_yaml(parsed, target_file=target_yaml,
                                              overwrite=overwrite)
    click.echo('Processed yaml saved to `%s`' % target_yaml)


@cli.command()
@click.option('-s', '--source_yaml', required=True, help='Clean yaml without any error.')
@click.option('-r', '--raw_data_folder', default=None, help='Path to the root folder containing raw data')
@click.option('-c', '--conflicts', default='abort',
              help='Default is `abort` to crash if there is a conflict, use `skip` to '
                   'ignore and proceed')
def yaml_to_flexilims(source_yaml, raw_data_folder=None, conflicts=None):
    """Create entries on flexilims corresponding to yaml"""
    from flexiznam import camp, errors
    import pathlib

    source_yaml = pathlib.Path(source_yaml)
    try:
        camp.sync_data.upload_yaml(source_yaml, raw_data_folder, conflicts=conflicts,
                                   verbose=False)
    except errors.SyncYmlError as err:
        raise click.ClickException(err.args[0])

@cli.command()
@click.option('-p', '--project_id', prompt='Enter the project ID', help='Project ID.')
@click.option('-t', '--target_file', default=None, help='Path to write csv output.')
@click.option('-r', '--root_name', default=None, help='Root entity to start the check.')
@click.option('--flexilims_username', default=None, help='Your username on flexilims.')
def check_flexilims_issues(project_id, target_file, root_name, flexilims_username):
    """Check that database is properly formatted

    This will check recursively all mice if `root_name` is not provided. Elements that
    are not descendent of mice will NOT be check if root_name is not selected
    appropriately.
    """
    from flexiznam.main import get_flexilims_session
    from flexiznam import utils
    import pathlib
    import pandas as pd
    flexilims_session = get_flexilims_session(project_id=project_id,
                                              username=flexilims_username)
    ndf = utils.check_flexilims_names(flexilims_session, root_name=root_name,
                                      recursive=True)
    pdf = utils.check_flexilims_paths(flexilims_session)
    pdf.set_index('name', inplace=True)
    pdf['error_type'] = 'path'
    if ndf is not None:
        ndf.set_index('name', inplace=True)
        ndf['error_type'] = 'name'
        # check for non-unique names
        bad = ndf.index.value_counts()
        bad = bad[bad > 1].index
        if len(bad):
            ndf['name_is_not_unique'] = 0
            ndf.loc[ndf.index.isin(bad.index), 'name_is_not_unique'] = 1
        df = pd.concat([pdf, ndf], axis=0)
    else:
        df = pdf
    df.to_csv(target_file)