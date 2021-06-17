"""File to handle acquisition yaml file and create datasets on flexilims"""
import pathlib
import re
import yaml

import flexiznam as flz
from flexiznam.errors import SyncYmlError
from flexiznam.schema import Dataset
from flexiznam.config import PARAMETERS
from flexiznam.utils import clean_dictionary_recursively


def upload_yaml(source_yaml, conflicts='abort', raw_data_folder=None, verbose=True,
                log_func=print):
    """Upload data from one yaml to flexilims

    Args:
        source_yaml: path to clean yaml
        conflicts: `abort`, `append` or `overwrite`. How to deal with conflicts on
                   flexilims
        raw_data_folder: path to the folder containing the data. Default to
                         project_root/project/raw
        verbose: print progress information
        log_func: function to deal with warnings and messages

    Returns: dictionary or flexilims ID
    """

    errors = find_xxerrorxx(yml_file=source_yaml)
    if errors:
        raise SyncYmlError('The yaml file still contains error. Fix it')
    session_data = parse_yaml(source_yaml, raw_data_folder, verbose)

    # first find the mouse
    flexilims_session = flz.get_flexilims_session(project_id=session_data['project'])
    mouse = flz.get_entity(datatype='mouse', name=session_data['mouse'],
                           flexilims_session=flexilims_session)
    if mouse is None:
        raise SyncYmlError('Mouse not on flexilims. You must add it manually first')

    # deal with the session
    m = re.match(r'S(\d{4})(\d\d)(\d\d)', session_data['session'])
    if m:
        date = '-'.join(m.groups())
    else:
        log_func('Cannot parse date for session %s.' % session_data['session'])
        date = 'N/A'

    attributes = session_data.get('attributes', None)
    if attributes is None:
        attributes = {}
    for field in ('path', 'notes'):
        value = session_data.get(field, None)
        if value is not None:
            attributes[field] = value

    session = flz.add_experimental_session(
        mouse_name=mouse['name'],
        session_name=session_data['session'],
        flexilims_session=flexilims_session,
        date=date,
        attributes=attributes
    )
    # session datasets
    if 'datasets' in session_data:
        for ds_name, ds in session_data['datasets'].items():
            ds.mouse = mouse.name
            ds.session = session['name']
            flz.add_dataset(parent_id=session['id'],
                            dataset_type=ds.dataset_type,
                            created=ds.created,
                            path=str(ds.path),
                            is_raw='yes' if ds.is_raw else 'no',
                            flexilims_session=flexilims_session,
                            dataset_name=ds.name,
                            attributes=ds.extra_attributes,
                            strict_validation=False)
            ds.project_id = session['project']
            ds.update_flexilims()
    # now deal with recordings
    for rec_name, rec_data in session_data['recordings'].items():
        attributes = rec_data.get('attributes', {})
        attributes.update(rec_data.get('notes', ''))
        attributes.update(rec_data.get('path', ''))
        attributes.update(rec_data.get('timestamp', ''))
        flz.add_recording(session_id=session['id'],
                          recording_type=rec_data.get('recording_type', ''),
                          protocol=rec_data.get('protocol', ''),
                          attributes=rec_data.get,
                          recording_name=None, conflicts=None, other_relations=None,
                          flexilims_session=None, project_id=None)
    # now deal with recordings

    return session


def parse_yaml(path_to_yaml, raw_data_folder=None, verbose=True):
    """Read an acquisition yaml and create corresponding datasets

    Args:
        path_to_yaml: path to the file to parse
        raw_data_folder: root folder containing the mice folders
        verbose: print info while looking for datasets

    Returns: A yaml dictionary with dataset classes
    """

    session_data = clean_yaml(path_to_yaml)

    if raw_data_folder is None:
        raw_data_folder = pathlib.Path(PARAMETERS['projects_root'])
        raw_data_folder /= session_data['project']
        raw_data_folder /= PARAMETERS['data_subfolder']['raw']

    if session_data['path'] is not None:
        home_folder = pathlib.Path(raw_data_folder) / session_data['path']
    else:
        home_folder = pathlib.Path(raw_data_folder) / session_data['mouse'] / \
                      session_data['session']
        # first load datasets in the session level
    if not home_folder.is_dir():
        raise FileNotFoundError('Session directory %s does not exist' % home_folder)
    session_data['path'] = home_folder
    session_data['datasets'] = create_dataset(
        dataset_infos=session_data['datasets'],
        verbose=verbose,
        parent=session_data,
        raw_data_folder=raw_data_folder,
        error_handling='report'
    )

    for rec_name, recording in session_data['recordings'].items():
        recording['path'] = home_folder / rec_name
        recording['datasets'] = create_dataset(
            dataset_infos=recording['datasets'],
            parent=recording,
            raw_data_folder=raw_data_folder,
            verbose=verbose,
            error_handling='report'
        )

    # remove the full path that are not needed
    clean_dictionary_recursively(session_data)
    return session_data


def write_session_data_as_yaml(session_data, target_file=None, overwrite=False):
    """Write a session_data dictionary into a yaml

    Args:
        session_data: dictionary with Dataset instances, as returned by parse_yaml
        target_file: path to the output file (if None, does not write to disk)
        overwrite: replace target file if it already exists (default False)

    Returns: the pure yaml dictionary
    """
    out_dict = session_data.copy()
    clean_dictionary_recursively(out_dict, keys=['name'], format_dataset=True)
    if target_file is not None:
        target_file = pathlib.Path(target_file)
        if target_file.exists() and not overwrite:
            raise IOError('Target file %s already exists' % target_file)
        with open(target_file, 'w') as writer:
            yaml.dump(out_dict, writer)
    return out_dict


def create_dataset(dataset_infos, parent, raw_data_folder, verbose=True,
                   error_handling='crash'):
    """ Create dictionary of datasets

    Args:
        dataset_infos: extra information for reading dataset outside of raw_data_folder
                       or adding optional arguments
        parent: yaml dictionary of the parent level
        raw_data_folder: folder where to look for data
        verbose: (True) Print info about dataset found
        error_handling: `crash` or `report`. When something goes wrong, raise an error if
                        `crash` otherwise replace the dataset instance by the error
                        message in the output dictionary

    Returns: dictionary of dataset instances

    """

    # autoload datasets
    datasets = Dataset.from_folder(parent['path'], verbose=verbose)
    error_handling = error_handling.lower()
    if error_handling not in ('crash', 'report'):
        raise IOError('error_handling must be `crash` or `report`')

    # check dataset_infos for extra datasets
    for ds_name, ds_data in dataset_infos.items():
        ds_path = pathlib.Path(raw_data_folder) / ds_data['path']
        # first deal with dataset that are not in parent path']
        ds_class = Dataset.SUBCLASSES.get(ds_data['dataset_type'], Dataset)
        if ds_path.is_dir() and (ds_path != parent['path']):
            ds = ds_class.from_folder(ds_path, verbose=verbose)
        elif ds_path.is_file() and (ds_path.parent != parent['path']):
            ds = ds_class.from_folder(ds_path.parent, verbose=verbose)
        elif not ds_path.exists():
            err_msg = 'Dataset not found. Path %s does not exist' % ds_path
            if error_handling == 'crash':
                raise FileNotFoundError(err_msg)
            datasets[ds_name] = 'XXERRORXX!! ' + err_msg
            continue
        else:
            # if it is in the parent['path'] folder, I already loaded it.
            ds = {k: v for k, v in datasets.items() if isinstance(v, ds_class)}
        if not ds:
            err_msg = 'Dataset "%s" not found in %s' % (ds_name, ds_path)
            if error_handling == 'crash':
                raise SyncYmlError(err_msg)
            datasets[ds_name] = 'XXERRORXX!! ' + err_msg

        # match by name
        if ds_name in ds:
            ds = ds[ds_name]
        else:      # now we're in trouble.
            err_msg = 'Could not find dataset "%s". Found "%s" instead' % (
                       ds_name, ', '.join(ds.keys()))
            if error_handling == 'crash':
                raise SyncYmlError(err_msg)
            datasets[ds_name] = 'XXERRORXX!! ' + err_msg
            continue
        if ds_data['attributes'] is not None:
            ds.extra_attributes.update(ds_data['attributes'])
        if ds_data['notes'] is not None:
            ds.extra_attributes['notes'] = ds_data['notes']
        datasets[ds_name] = ds
    return datasets


def clean_yaml(path_to_yaml):
    """Read a yaml file and check that it is correctly formatted

    This does not do any processing, just make sure that I can read the whole yaml and
    generate dictionary will all expected fields
    """
    with open(path_to_yaml, 'r') as yml_file:
        yml_data = yaml.safe_load(yml_file)

    session, nested_levels = read_level(yml_data)
    # session['parent'] = session['mouse']  # duplicate info to format as nested layers
    # session['full_name'] = '_'.join([session['mouse'], session['session']])
    session['datasets'] = {}
    for dataset_name, dataset_dict in nested_levels['datasets'].items():
        ds = read_dataset(name=dataset_name, data=dataset_dict)
        session['datasets'][dataset_name] = ds

    session['recordings'] = {}
    for rec_name, rec_dict in nested_levels['recordings'].items():
        ds = read_recording(name=rec_name, data=rec_dict)
        session['recordings'][rec_name] = ds
    return session


def read_recording(name, data):
    """Read YAML information corresponding to a recording

    Args:
        name: str the name of the recording
        data: dict data for this dataset only

    Returns:
        recording: dict, the dictionary read from the yaml
    """
    recording, datasets = read_level(data, mandatory_args=('protocol',),
                                     optional_args=('notes', 'attributes', 'path',
                                                    'recording_type', 'timestamp'),
                                     nested_levels=('datasets',))
    recording['name'] = name

    # if timestamps is None, the name must start with RHHMMSS
    if recording['timestamp'] is None:
        m = re.match(r'R(\d\d\d\d\d\d)', recording['name'])
        if not m:
            raise SyncYmlError('Timestamp must be provided if recording name is not '
                               'properly formatted')
        recording['timestamp'] = m.groups()[0]
    recording['datasets'] = dict()
    for ds_name, ds_data in datasets['datasets'].items():
        ds = read_dataset(name=ds_name, data=ds_data)
        recording['datasets'][ds_name] = ds

    return recording


def read_dataset(name, data):
    """Read YAML information corresponding to a dataset

    Args:
        name: str the name of the dataset, will be composed with parent names to
        generate an identifier
        data: dict data for this dataset only

    Returns:
        a formatted dictionary including,  'dataset_type', 'path', 'notes',
        'attributes' and 'name'
    """
    level, _ = read_level(data, mandatory_args=('dataset_type', 'path'),
                          optional_args=('notes', 'attributes', 'autogen_name', 'origin_id'),
                          nested_levels=())
    level['name'] = name
    return level


def read_level(yml_level, mandatory_args=('project', 'mouse', 'session'),
               optional_args=('path', 'notes', 'attributes'),
               nested_levels=('recordings', 'datasets')):
    """Read one layer of the yml file (i.e. a dictionary)

    Args:
        yml_level: a dictionary containing the yml level to analyse (and all sublevels)
        mandatory_args: arguments that must be in this level
        optional_args: arguments that are expected but not mandatory, will be `None` if
                       absent
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
        raise SyncYmlError('Got unexpected attribute(s): %s' % (
                           ', '.join(yml_level.keys())))
    return level, nested_levels


def find_xxerrorxx(yml_file=None, yml_data=None, pattern='XXERRORXX', _output=None):
    """Utility to find where things went wrong

    Look through a `yml_file` or the corresponding `yml_Data` dictionary recursively.
    Returns a dictionary with all entries containing the error `pattern`

    _output is used for recursive calling.
    """
    if yml_file is not None:
        if yml_data is not None:
            raise IOError('Set either yml_file OR yml_data')
        with open(yml_file, 'r') as reader:
            yml_data = yaml.safe_load(reader)

    if _output is None:
        _output = dict()
    for k, v in yml_data.items():
        if isinstance(v, dict):
            _output = find_xxerrorxx(yml_data=v, pattern=pattern, _output=_output)
        elif isinstance(v, str) and (pattern in v):
            _output[k] = v
    return _output
