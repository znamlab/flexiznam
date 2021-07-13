"""File to handle acquisition yaml file and create datasets on flexilims"""
from pathlib import Path
import re
import copy
import yaml

import flexiznam as flz
from flexiznam.errors import SyncYmlError
from flexiznam.schema import Dataset
from flexiznam.config import PARAMETERS
from flexiznam.utils import clean_dictionary_recursively


def upload_yaml(source_yaml, raw_data_folder=None, verbose=False,
                log_func=print, flexilims_session=None, conflicts='abort'):
    """Upload data from one yaml to flexilims

    Args:
        source_yaml (str): path to clean yaml
        raw_data_folder (str): path to the folder containing the data. Default to
            data_root['raw']
        verbose (bool): print progress information
        log_func: function to deal with warnings and messages
        flexilims_session (Flexilims): session to avoid recreating a token
        conflicts (str): `abort` to crash if there is a conflict, `skip` to ignore and proceed

    Returns:
        dictionary or flexilims ID

    """
    # if there are errors, I cannot safely parse the yaml
    errors = find_xxerrorxx(yml_file=source_yaml)
    if errors:
        raise SyncYmlError('The yaml file still contains error. Fix it')
    session_data = parse_yaml(source_yaml, raw_data_folder, verbose)
    # parsing can created errors, check again
    errors = find_xxerrorxx(yml_file=source_yaml)
    if errors:
        raise SyncYmlError('Invalid yaml. Use `parse_yaml` and fix errors manually.')

    # first find the mouse
    if flexilims_session is None:
        flexilims_session = flz.get_flexilims_session(project_id=session_data['project'])
    mouse = flz.get_entity(datatype='mouse', name=session_data['mouse'],
                           flexilims_session=flexilims_session)
    if mouse is None:
        raise SyncYmlError('Mouse not on flexilims. You must add it manually first')

    # deal with the session
    if session_data['session'] is not None:
        m = re.match(r'S(\d{4})(\d\d)(\d\d)', session_data['session'])
        if m:
            date = '-'.join(m.groups())
        else:
            log_func('Cannot parse date for session %s.' % session_data['session'])
            date = 'N/A'

    session_data = trim_paths(session_data, raw_data_folder)

    attributes = session_data.get('attributes', None)
    if attributes is None:
        attributes = {}
    for field in ('path', 'notes'):
        value = session_data.get(field, None)
        if value is not None:
            attributes[field] = value
    # if session is not specified, then entries will be added directly as
    # children of the mouse
    if session_data['session'] is not None:
        session = flz.add_experimental_session(
            mouse_name=mouse['name'],
            session_name=mouse['name'] + '_' + session_data['session'],
            flexilims_session=flexilims_session,
            date=date,
            attributes=attributes,
            conflicts=conflicts)
        root_id = session['id']
    else:
        root_id = mouse.id

    # session datasets
    for ds_name, ds in session_data.get('datasets', {}).items():
        ds.mouse = mouse.name
        ds.project = session_data['project']
        ds.session = session_data['session']
        ds.origin_id = root_id
        ds.flm_session = flexilims_session
        ds.update_flexilims(mode='safe')

    # now deal with recordings
    for short_rec_name, rec_data in session_data.get('recordings', {}).items():
        rec_name = session['name'] + '_' + short_rec_name
        attributes = rec_data.get('attributes', None)
        if attributes is None:
            attributes = {}
        for field in ['notes', 'path', 'timestamp']:
            value = rec_data.get(field, '')
            attributes[field] = value if value is not None else ''
        rec_type = rec_data.get('recording_type', 'unspecified')
        if not rec_type:
            rec_type = 'unspecified'
        rec_rep = flz.add_recording(
            session_id=root_id,
            recording_type=rec_type,
            protocol=rec_data.get('protocol', ''),
            attributes=attributes,
            recording_name=rec_name,
            other_relations=None,
            flexilims_session=flexilims_session,
            conflicts=conflicts
        )

        # now deal with recordings' datasets
        for ds_name, ds in rec_data.get('datasets', {}).items():
            ds.mouse = mouse.name
            ds.project = session_data['project']
            ds.session = session_data['session']
            ds.recording = short_rec_name
            ds.origin_id = rec_rep['id']
            ds.flm_session = flexilims_session
            ds.update_flexilims(mode='safe')
    # now deal with samples
    def add_samples(samples, parent, short_parent_name=None):
        # we'll need a utility function to deal with recursion
        for short_sample_name, sample_data in samples.items():
            sample_name = parent['name'] + '_' + short_sample_name
            if short_parent_name is not None:
                short_sample_name = short_parent_name + '_' + short_sample_name
            attributes = sample_data.get('attributes', None)
            if attributes is None:
                attributes = {}
            # we always use `skip` to add samples
            sample_rep = flz.add_sample(
                parent['id'],
                attributes=attributes,
                sample_name=sample_name,
                conflicts='skip',
                flexilims_session=flexilims_session
            )
            # deal with datasets attached to this sample
            for ds_name, ds in sample_data.get('datasets', {}).items():
                ds.mouse = mouse.name
                ds.project = session_data['project']
                ds.sample = short_sample_name
                ds.session = session_data['session']
                ds.origin_id = sample_rep['id']
                ds.flm_session = flexilims_session
                ds.update_flexilims(mode='safe')
            # now add child samples
            add_samples(sample_data['samples'], sample_rep, short_sample_name)
    # samples are attached to mice, not sessions
    add_samples(session_data['samples'], mouse)


def trim_paths(session_data, raw_data_folder):
    """Parses paths to make them relative to `raw_data_folder`

    Args:
        session_data (dict): dictionary containing children of the session
        raw_data_folder (str): part of the path to be omitted from on flexilims

    Returns:
        dict: `session_data` after trimming the paths

    """

    def trim_sample_paths(samples):
        # utility function to recurse into samples
        for sample_name, sample_data in samples.items():
            samples[sample_name]['path'] = \
                str(Path(samples[sample_name]['path'])
                    .relative_to(raw_data_folder))
            for ds_name, ds in sample_data.get('datasets', {}).items():
                ds.path = ds.path.relative_to(raw_data_folder)
            trim_sample_paths(sample_data['samples'])

    if raw_data_folder is None:
        raw_data_folder = Path(PARAMETERS['data_root']['raw'])
    if 'path' in session_data.keys():
        session_data['path'] = \
            str(Path(session_data['path']).relative_to(raw_data_folder))
    for ds_name, ds in session_data.get('datasets', {}).items():
        ds.path = ds.path.relative_to(raw_data_folder)
    for rec_name, rec_data in session_data['recordings'].items():
        session_data['recordings'][rec_name]['path'] = \
            str(Path(session_data['recordings'][rec_name]['path'])
                .relative_to(raw_data_folder))
        for ds_name, ds in rec_data.get('datasets', {}).items():
            ds.path = ds.path.relative_to(raw_data_folder)
    trim_sample_paths(session_data['samples'])
    return session_data


def parse_yaml(path_to_yaml, raw_data_folder=None, verbose=True):
    """Read an acquisition yaml and create corresponding datasets

    Args:
        path_to_yaml (str): path to the file to parse
        raw_data_folder (str): root folder containing the mice folders
        verbose (bool): print info while looking for datasets

    Returns:
        dict: A yaml dictionary with dataset classes

    """
    session_data = clean_yaml(path_to_yaml)

    if raw_data_folder is None:
        raw_data_folder = Path(PARAMETERS['data_root']['raw'])
        raw_data_folder /= session_data['project']

    if session_data['path'] is not None:
        home_folder = Path(raw_data_folder) / session_data['path']
    elif session_data['session'] is not None:
        home_folder = Path(raw_data_folder) / session_data['mouse'] / \
                      session_data['session']
    else:
        home_folder = Path(raw_data_folder) / session_data['mouse']
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

    session_data['samples'] = create_sample_datasets(
        session_data,
        raw_data_folder
    )

    # remove the full path that are not needed
    clean_dictionary_recursively(session_data)
    return session_data


def create_sample_datasets(parent, raw_data_folder):
    """Recursively index samples creating a nested dictionary and generate
    corresponding datasets

    Args:
        parent (dict): Dictonary corresponding to the parent entity

    Return:
        dict: dictonary of child samples

    """
    if 'samples' not in parent:
        return dict()
    for sample_name, sample in parent['samples'].items():
        sample['path'] = parent['path'] / sample_name
        sample['datasets'] = create_dataset(
            dataset_infos=sample['datasets'],
            parent=sample,
            raw_data_folder=raw_data_folder,
            error_handling='report'
        )

        # recurse into child samples
        sample['samples'] = create_sample_datasets(sample, raw_data_folder)
    # we update in place but we also return the dictionary of samples to make
    # for more readable code
    return parent['samples']

def write_session_data_as_yaml(session_data, target_file=None, overwrite=False):
    """Write a session_data dictionary into a yaml

    Args:
        session_data (dict): dictionary with Dataset instances, as returned by parse_yaml
        target_file (str): path to the output file (if None, does not write to disk)
        overwrite (bool): replace target file if it already exists (default False)

    Returns:
        dict: the pure yaml dictionary

    """
    out_dict = copy.deepcopy(session_data)
    clean_dictionary_recursively(out_dict, keys=['name'], format_dataset=True)
    if target_file is not None:
        target_file = Path(target_file)
        if target_file.exists() and not overwrite:
            raise IOError('Target file %s already exists' % target_file)
        with open(target_file, 'w') as writer:
            yaml.dump(out_dict, writer)
        # temp check:
        with open(target_file, 'r') as reader:
            writen = yaml.safe_load(reader)
    return out_dict


def create_dataset(dataset_infos, parent, raw_data_folder, verbose=True,
                   error_handling='crash'):
    """ Create dictionary of datasets

    Args:
        dataset_infos: extra information for reading dataset outside of raw_data_folder
          or adding optional arguments
        parent (dict): yaml dictionary of the parent level
        raw_data_folder (str): folder where to look for data
        verbose (bool): (True) Print info about dataset found
        error_handling (str) `crash` or `report`. When something goes wrong, raise an
            error if `crash` otherwise replace the dataset instance by the error
            message in the output dictionary

    Returns:
        dict: dictionary of dataset instances

    """

    # autoload datasets
    datasets = Dataset.from_folder(parent['path'], verbose=verbose)
    error_handling = error_handling.lower()
    if error_handling not in ('crash', 'report'):
        raise IOError('error_handling must be `crash` or `report`')

    # check dataset_infos for extra datasets
    for ds_name, ds_data in dataset_infos.items():
        ds_path = Path(raw_data_folder) / ds_data['path']
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

    Args:
        path_to_yaml (str): path to the YAML file

    Returns:
        dict: nested dictonary containing entries in the YAML file

    """
    with open(path_to_yaml, 'r') as yml_file:
        yml_data = yaml.safe_load(yml_file)

    session, nested_levels = read_level(yml_data)

    session['datasets'] = {}
    for dataset_name, dataset_dict in nested_levels['datasets'].items():
        session['datasets'][dataset_name] = read_dataset(name=dataset_name, data=dataset_dict)

    session['recordings'] = {}
    for rec_name, rec_dict in nested_levels['recordings'].items():
        session['recordings'][rec_name] = read_recording(name=rec_name, data=rec_dict)

    session['samples'] = {}
    for sample_name, sample_dict in nested_levels['samples'].items():
        session['samples'][sample_name] = read_sample(name=sample_name, data=sample_dict)

    return session


def read_sample(name, data):
    """Read YAML information corresponding to a sample

    Args:
        name (str): the name of the sample
        data (dict): data for this sample only

    Returns:
        dict: the sample read from the yaml

    """
    if data is None:
        data = {}
    sample, nested_levels = read_level(
        data,
        mandatory_args=(),
        optional_args=('notes', 'attributes', 'path'),
        nested_levels=('datasets','samples')
    )
    sample['name'] = name

    sample['datasets'] = dict()
    for ds_name, ds_data in nested_levels['datasets'].items():
        sample['datasets'][ds_name] = read_dataset(name=ds_name, data=ds_data)
    sample['samples'] = dict()
    for sample_name, sample_data in nested_levels['samples'].items():
        sample['samples'][sample_name] = read_sample(name=sample_name, data=sample_data)
    return sample


def read_recording(name, data):
    """Read YAML information corresponding to a recording

    Args:
        name (str): the name of the recording
        data (dict): data for this dataset only

    Returns:
        dict: the recording read from the yaml

    """
    recording, datasets = read_level(
        data,
        mandatory_args=('protocol',),
        optional_args=('notes', 'attributes', 'path', 'recording_type', 'timestamp'),
        nested_levels=('datasets',)
    )
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
        recording['datasets'][ds_name] = read_dataset(name=ds_name, data=ds_data)

    return recording


def read_dataset(name, data):
    """Read YAML information corresponding to a dataset

    Args:
        name (str): the name of the dataset, will be composed with parent names to
        generate an identifier
        data (dict): data for this dataset only

    Returns:
        dict: a formatted dictionary including,  'dataset_type', 'path', 'notes',
        'attributes' and 'name'

    """
    level, _ = read_level(
        data,
        mandatory_args=('dataset_type', 'path'),
        optional_args=('notes', 'attributes', 'created', 'is_raw', 'origin_id'),
        nested_levels=()
    )
    level['name'] = name
    return level


def read_level(yml_level, mandatory_args=('project', 'mouse', 'session'),
               optional_args=('path', 'notes', 'attributes'),
               nested_levels=('recordings', 'datasets', 'samples')):
    """Read one layer of the yml file (i.e. a dictionary)

    Args:
        yml_level (dict): a dictionary containing the yml level to analyse (and all sublevels)
        mandatory_args: arguments that must be in this level
        optional_args: arguments that are expected but not mandatory, will be `None` if
            absent
        nested_levels: name of any nested level that should not be parsed

    Returns:
        (tuple): a tuple containing two dictionaries:
            level (dict): dictonary of top level attributes
            nested_levels (dict): dictionary of nested dictonaries
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
