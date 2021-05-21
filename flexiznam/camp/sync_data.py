"""File to handle acquisition yaml file and create datasets on flexilims"""
import yaml
from flexiznam.errors import SyncYmlError
from flexiznam.config import PARAMETERS


def parse_yaml(path_to_yaml):

    session_data = clean_yaml(path_to_yaml)


def clean_yaml(path_to_yaml):
    """Read a yaml file and check that it is correctly formatted

    This does not do any processing, just make sure that I can read the whole yaml and generate dictionary will
    all expected fields
    """
    with open(path_to_yaml, 'r') as yml_file:
        yml_data = yaml.safe_load(yml_file)

    session, nested_levels = read_level(yml_data)
    session['parent'] = session['mouse']  # duplicate info to format as nested layers
    session['full_name'] = '_'.join([session['session'], session['mouse']])
    session['datasets'] = {}
    for dataset_name, dataset_dict in nested_levels['datasets'].items():
        ds = read_dataset(name=dataset_name, data=dataset_dict, parent=session)
        session['datasets'][dataset_name] = ds

    session['recordings'] = {}
    for rec_name, rec_dict in nested_levels['recordings'].items():
        ds = read_recording(name=rec_name, data=rec_dict, session=session)
        session['recordings'][rec_name] = ds
    return session


def read_recording(name, data, session):
    """Read YAML information corresponding to a recording

    Args:
        name: str the name of the dataset, will be composed with parent names to generate an identifier
        data: dict data for this dataset only
        session: a dictionary of the parent session

    Returns:

    """
    recording, datasets = read_level(data, mandatory_args=('protocol', 'timestamp'),
                                     optional_args=('notes', 'attributes', 'path', 'recording_type'),
                                     nested_levels=('datasets',))
    recording['name'] = name
    recording['full_name'] = '_'.join([name, session['full_name']])
    recording['datasets'] = dict()
    for ds_name, ds_data in datasets['datasets'].items():
        ds = read_dataset(name=ds_name, data=ds_data, parent=recording)
        recording['datasets'][ds_name] = ds
    return recording


def read_dataset(name, data, parent):
    """Read YAML information corresponding to a dataset

    Args:
        name: str the name of the dataset, will be composed with parent names to generate an identifier
        data: dict data for this dataset only
        parent: a dictionary of the parent level. Can have a parent itself

    Returns:
        a formatted dictionary including 'full_name', 'type', 'path', 'notes', 'attributes' and 'name'
    """
    level, _ = read_level(data, mandatory_args=('type', 'path'), optional_args=('notes', 'attributes'),
                          nested_levels=())
    level['name'] = name
    level['full_name'] = '_'.join([name, parent['full_name']])
    return level


def read_level(yml_level, mandatory_args=('project', 'mouse', 'session'), optional_args=('path', 'notes', 'attributes'),
               nested_levels=('recordings', 'datasets')):
    """Read one layer of the yml file (i.e. a dictionnary)

    Args:
        yml_level: a dictionary containing the yml level to analyse (and all sublevels)
        mandatory_args: arguments that must be in this level
        optional_args: arguments that are expected but not mandatory, will be `None` if absent
        nested_levels: name of any nested level that should not be parsed

    Returns: (level, nested_levels) two dictionary
    """
    # make a copy to not change original version
    yml_level = yml_level.copy()
    is_absent = [m not in yml_level for m in mandatory_args]
    if any(is_absent):
        absents = ', '.join(["%s" % a for a, m in zip(mandatory_args, is_absent) if m])
        raise SyncYmlError('%s must be provided in the YAML file.' % absents)
    level = {m: yml_level.pop(m) for m in mandatory_args}

    for opt in optional_args:
        level[opt] = yml_level.pop(opt, None)

    nested_levels = {n: yml_level.pop(n, {}) for n in nested_levels}

    # the rest is unexpected
    if len(yml_level):
        raise SyncYmlError('Got unexpected attribute(s): %s' % (', '.join(yml_level.keys())))
    return level, nested_levels
