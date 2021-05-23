"""File to handle acquisition yaml file and create datasets on flexilims"""
import pathlib
import re
import warnings

import yaml
from flexiznam.errors import SyncYmlError, ConfigurationError
from flexiznam.schema import Dataset
from flexiznam.config import PARAMETERS


def parse_yaml(path_to_yaml, raw_data_folder=None, verbose=True):
    if raw_data_folder is None:
        if ('camp' not in PARAMETERS) or ('raw_data_source' not in PARAMETERS['camp']):
            raise ConfigurationError('camp/raw_data_source not found in configuration file')
        raw_data_folder = PARAMETERS['camp']['raw_data_source']

    session_data = clean_yaml(path_to_yaml)

    if session_data['path'] is not None:
        home_folder = pathlib.Path(raw_data_folder) / session_data['path']
    else:
        home_folder = pathlib.Path(raw_data_folder) / session_data['mouse'] / session_data['session']
        # first load datasets in the session level
    if not home_folder.is_dir():
        raise FileNotFoundError('Session directory %s does not exist' % home_folder)
    session_data['full_path'] = home_folder
    sess_ds = create_dataset(dataset_infos=session_data['datasets'],verbose=verbose,
                             parent=session_data, raw_data_folder=raw_data_folder)

    for ds_name, ds in sess_ds.items():
        ds = dict(ds.format().loc[['path', 'created', 'dataset_type', 'is_raw', 'name']])
        assert ds_name not in session_data['datasets']
        session_data['datasets'][ds_name] = ds

    for rec_name, recording in session_data['recordings'].items():
        recording['full_path'] = home_folder / rec_name
        rec_ds = create_dataset(dataset_infos=recording['datasets'], parent=recording, raw_data_folder=raw_data_folder,
                                verbose=verbose)
        for ds_name, ds in rec_ds.items():
            ds = dict(ds.format().loc[['path', 'created', 'dataset_type', 'is_raw', 'name']])
            assert ds_name not in recording['datasets']
            recording['datasets'][ds_name] = ds

    # remove the full path that are not needed
    _clean_dictionary_recursively(session_data, ['full_path'])
    return session_data


def _clean_dictionary_recursively(dictionary, keys):
    """Recursively pop keys from a dictionary inplace

    Args:
        dictionary: dict (of dict)
        keys: list of keys to pop
    """
    if isinstance(keys, str):
        keys = [keys]
    for k in keys:
        dictionary.pop(k, None)
    for v in dictionary.values():
        if isinstance(v, dict):
            _clean_dictionary_recursively(v, keys)


def create_dataset(dataset_infos, parent, raw_data_folder, verbose=True):

    # autoload datasets
    datasets = Dataset.from_folder(parent['full_path'])

    # check dataset_infos for extra datasets
    for ds_name, ds_data in dataset_infos.items():
        ds_path = pathlib.Path(raw_data_folder) / ds_data['path']
        # first deal with dataset that are not in parent['full_path']
        ds_class = Dataset.SUBCLASSES.get(ds_data['type'], Dataset)
        if ds_path.is_dir() and (ds_path != parent['full_path']):
            ds = ds_class.from_folder(ds_path, verbose=verbose)
        elif ds_path.is_file() and (ds_path.parent != parent['full_path']):
            ds = ds_class.from_folder(ds_path.parent, verbose=verbose)
        elif not ds_path.exists():
            raise FileNotFoundError('Dataset not found. Path %s does not exist' % ds_path)
        else:
            # if it is in the parent['full_path'] folder, I already loaded it.
            ds = {k: v for k, v in datasets.items() if v.dataset_type == ds_data['type']}
        if not ds:
            raise SyncYmlError('Dataset "%s" not found' % ds_name)
        # match by name
        if ds_name in ds:
            ds = ds[ds_name]
        else:             # now we're in trouble.
            raise SyncYmlError('Could not find dataset "%s". Found %s instead' % (ds_name, ', '.join(ds.keys())))
        if ds_data['attributes'] is not None:
            ds.extra_attributes.update(ds_data['attributes'])
        if ds_data['notes'] is not None:
            ds.extra_attributes['notes'] = ds_data['notes']
        datasets[ds_name] = ds

    return datasets


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
    recording, datasets = read_level(data, mandatory_args=('protocol',),
                                     optional_args=('notes', 'attributes', 'path', 'recording_type', 'timestamp'),
                                     nested_levels=('datasets',))
    recording['name'] = name
    recording['full_name'] = '_'.join([name, session['full_name']])

    # if timestamps is None, the name must start with RHHMMSS
    if recording['timestamp'] is None:
        m = re.match('R(\d\d\d\d\d\d)', recording['name'])
        if not m:
            raise SyncYmlError('Timestamp must be provided if recording name is not properly formatted')
        recording['timestamp'] = m.groups()[0]
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
