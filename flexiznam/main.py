import pandas as pd
import flexilims as flm
from pathlib import Path
from flexiznam import mcms
from flexiznam.config import PARAMETERS, get_password
from flexiznam.errors import NameNotUniqueError, FlexilimsError


def _format_project(project_id, prm):
    if project_id in prm['project_ids']:
        return prm['project_ids'][project_id]
    if project_id is None or len(project_id) != 24:
        raise AttributeError('Invalid project: "%s"' % project_id)
    return project_id


def _lookup_project(project_id, prm):
    """
    Look up project name by hexadecimal id
    """
    try:
        proj = next(proj for proj, id in prm['project_ids'].items() if id == project_id)
        return proj
    except StopIteration:
        return None


def get_flexilims_session(project_id, username=None, password=None):
    project_id = _format_project(project_id, PARAMETERS)
    if username is None:
        username = PARAMETERS['flexilims_username']
    if password is None:
        password = get_password(username, 'flexilims')
    session = flm.Flexilims(username, password, project_id=project_id)
    return session


def add_mouse(mouse_name, project_id, flexilims_session=None, mcms_animal_name=None,
              flexilims_username=None, mcms_username=None, flexilims_password=None):
    """Check if a mouse is already in the database and add it if it isn't"""

    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id, flexilims_username, flexilims_password)
    mice_df = get_entities(flexilims_session=flexilims_session, datatype='mouse')
    if mouse_name in mice_df.index:
        return mice_df.loc[mouse_name]

    if mcms_username is None:
        mcms_username = PARAMETERS['mcms_username']
    if mcms_animal_name is None:
        mcms_animal_name = mouse_name
    mouse_info = mcms.get_mouse_df(mouse_name=mcms_animal_name, username=mcms_username)

    # add the data in flexilims, which requires a directory
    mouse_info = dict(mouse_info)
    for k, v in mouse_info.items():
        if type(v) != str:
            mouse_info[k] = float(v)
        else:
            mouse_info[k] = v.strip()
    resp = flexilims_session.post(
        datatype='mouse',
        name=mouse_name,
        attributes=dict(mouse_info),
        strict_validation=False
    )
    return resp


def add_experimental_session(mouse_name, date, attributes={}, session_name=None, other_relations=None,
                             flexilims_session=None, project_id=None):
    """Add a new session as a child entity of a mouse

    Args:
        mouse_name: str, name of the mouse. Must exist on flexilims
        date: str, date of the session. If `session_name` is not provided, will be used as name
        attributes: dict, dictionary of additional attributes (on top of date)
        session_name: str or None, name of the session, usually in the shape `S20210420`.
        conflicts: `abort`, `append`, or `overwrite`: how to handle conflicts
        other_relations: ID(s) of custom entities related to the session
        flexilims_session: flexilims session
        project_id: name of the project or hexadecimal project id (needed if session is not provided)


    Returns: flexilims reply
    """
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    mouse_id = get_id(mouse_name, datatype='mouse', flexilims_session=flexilims_session)
    if session_name is None:
        session_name = mouse_name + '_' + date + '_0'
    session_name = generate_name('session', session_name, flexilims_session=flexilims_session)

    session_info = {'date': date}
    if attributes is None:
        attributes = {}
    if ('date' in attributes) and (date != attributes['date']):
        raise FlexilimsError('Got two values for date: %s and %s' % (date, attributes['date']))
    if ('path' not in attributes):
        attributes['path'] = str(Path(mouse_name) / session_name)
    session_info.update(attributes)
    resp = flexilims_session.post(
        datatype='session',
        name=session_name,
        attributes=session_info,
        origin_id=mouse_id,
        other_relations=other_relations,
        strict_validation=False
    )
    return resp


def add_recording(session_id, recording_type, protocol, attributes=None,
                  recording_name=None, conflicts=None, other_relations=None,
                  flexilims_session=None, project_id=None):
    """Add a recording as a child of an experimental session

    Args:
        session_id: str, hexadecimal ID of the session. Must exist on flexilims
        recording_type: str, one of [two_photon, widefield, intrinsic, ephys, behaviour]
        protocol: str, experimental protocol (`retinotopy` for instance)
        attributes: dict, dictionary of additional attributes (on top of protocol and recording_type)
        recording_name: str or None, name of the recording, usually in the shape `R152356`.
        conflicts: `abort`, `append`, or `overwrite`: how to handle conflicts
        other_relations: ID(s) of custom entities related to the session
        flexilims_session: flexilims session
        project_id: name of the project or hexadecimal project id (needed if session is not provided)


    Returns: flexilims reply
    """

    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    experimental_session = get_entity(datatype='session',
                                      flexilims_session=flexilims_session,
                                      id=session_id)
    if recording_name is None:
        recording_name = experimental_session['name'] + '_' + protocol + '_0'
    recording_name = generate_name('recording',
                                   recording_name,
                                   flexilims_session=flexilims_session)

    recording_info = {'recording_type': recording_type, 'protocol': protocol}
    if attributes is None:
        attributes = {}
    if ('path' not in attributes):
        attributes['path'] = str(Path(get_path(
            experimental_session['path'],
            datatype='session',
            flexilims_session=flexilims_session)) / recording_name)
    for key in recording_info.keys():
        if (key in attributes) and (attributes[key] != locals()[key]):
            raise FlexilimsError('Got two values for %s: '
                                 '`%s` and `%s`' % (key, attributes[key], locals()[key]))
    recording_info.update(attributes)

    resp = flexilims_session.post(
        datatype='recording',
        name=recording_name,
        attributes=recording_info,
        origin_id=session_id,
        other_relations=other_relations,
        strict_validation=False
    )
    return resp


def add_dataset(parent_id, dataset_type, created, path, is_raw='yes', project_id=None,
                flexilims_session=None, dataset_name=None, attributes=None, strict_validation=False):
    """
    Add a dataset as a child of a recording or session
    """
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    if dataset_name is None:
        parent_name = pd.concat([
            get_entities(flexilims_session=flexilims_session, datatype='recording', id=parent_id),
            get_entities(flexilims_session=flexilims_session, datatype='session', id=parent_id)
        ])['name'][0]
        dataset_name = parent_name + '_' + dataset_type + '_0'
    dataset_name = generate_name('dataset', dataset_name, flexilims_session=flexilims_session)

    dataset_info = {
        'dataset_type': dataset_type,
        'created': created,
        'path': path,
        'is_raw': is_raw
    }
    reserved_attributes = ['dataset_type', 'created', 'path', 'is_raw']
    if attributes is not None:
        for attribute in attributes:
            assert attribute not in reserved_attributes
            dataset_info[attribute] = attributes[attribute]

    resp = flexilims_session.post(
        datatype='dataset',
        name=dataset_name,
        origin_id=parent_id,
        attributes=dataset_info,
        strict_validation=strict_validation
    )
    return resp


def get_entities(datatype='mouse', query_key=None, query_value=None, project_id=None,
                 flexilims_session=None, name=None, origin_id=None, id=None, format_reply=True):
    """
    Get entities of a given type and format results.

    If an open Flexylims session is provided, the other authentication arguments
    aree not needed (or used)

    Args:
        datatype (str): type of Flexylims entity to fetch, e.g. 'mouse', 'session',
            'recording', or 'dataset'
        query_key (str): attribute to filter by
        query_value (str): attribute value to select
        project_id (str): text name of the project
        flexilims_session (Flexilims): Flexylims session object
        name (str): filter by name
        origin_id (str): filter by origin / parent
        id (str): filter by hexadecimal id
        format_reply (bool, default True): format the reply into a dataframe

    Returns:
        DataFrame: containing all matching entities
    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)
    results = flexilims_session.get(
        datatype,
        query_key=query_key,
        query_value=query_value,
        name=name,
        origin_id=origin_id,
        id=id
    )
    if not format_reply:
        return results
    results = format_results(results)
    if len(results):
        results.set_index('name', drop=False, inplace=True)
    return results


def get_entity(datatype=None, query_key=None, query_value=None, project_id=None, flexilims_session=None,
               name=None, origin_id=None, id=None, format_reply=True):
    """
    Get one entity and format result.

    If multiple entities on the database match the query, raise a NameNotUniqueError,
    if nothing match, return None

    If an open Flexylims session is provided, the other authentication arguments
    aree not needed (or used)

    Args:
        datatype (str): type of Flexylims entity to fetch, e.g. 'mouse', 'session',
            'recording', or 'dataset'
        query_key (str): attribute to filter by
        query_value (str): attribute value to select
        project_id (str): text name of the project
        flexilims_session (Flexilims): Flexylims session object
        name (str): filter by name
        origin_id (str): filter by origin / parent
        id (str): filter by hexadecimal id
        format_reply (bool, default True): format the reply into a dataframe

    Returns:
        Series: containing the entity or dictionary if format_reply is False
    """
    entity = get_entities(
        datatype=datatype,
        query_key=query_key,
        query_value=query_value,
        project_id=project_id,
        flexilims_session=flexilims_session,
        name=name,
        origin_id=origin_id,
        id=id,
        format_reply=format_reply
    )
    if not len(entity):
        return None
    if len(entity) != 1:
        raise NameNotUniqueError('Found %d entities, not 1' % len(entity))
    if format_reply:
        return entity.iloc[0]
    return entity[0]


def generate_name(datatype, name, flexilims_session=None, project_id=None):
    """
    Generate a number for incrementally increasing the numeric suffix
    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)
    parts = name.split('_')
    if not parts[-1].isnumeric():
        root =  name + '_'
        suffix = 0
    else:
        root = '_'.join(parts[:-1])
        if root:
            root += '_'
            suffix = int(parts[-1])
        else:
            root = parts[-1] + '_'
            suffix = 0
    while get_entity(datatype, name='%s%s' % (root, suffix), flexilims_session=flexilims_session) is not None:
        suffix += 1
    name = '%s%s' % (root, suffix)
    return name


def add_entity(datatype, name, origin_id=None, attributes={}, other_relations=None,
               flexilims_session=None, project_id=None):
    """Add a new entity on flexilims. Name must be unique

    Args:
        datatype (str): flexilims type
        name (str): name on flexilims
        origin_id (str or None): hexadecimal id of the origin
        attributes (dict or None): attributes to update
        other_relations (str or list of str): hexadecimal ID(s) of custom entities
            link to the entry to update
        project_id (str): text name of the project
        flexilims_session (Flexilims): Flexylims session object

    Returns:
        flexilims reply
    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    try:
        rep = flexilims_session.post(
            datatype=datatype,
            name=name,
            attributes=attributes,
            origin_id=origin_id,
            other_relations=other_relations,
            strict_validation=False
        )
    except OSError as err:
        if 'already exist in the project ' in err.args[0]:
            raise NameNotUniqueError(err.args[0])
        raise FlexilimsError(err.args[0])
    return rep


def update_entity(datatype, name=None, id=None, origin_id=None, mode='overwrite',
                  attributes={}, other_relations=None, flexilims_session=None,
                  project_id=None):
    """Update one entity identified with its datatype and name or id

    Args:
        datatype (str): flexilims type
        name (str): name on flexilims
        origin_id (str or None): hexadecimal id of the origin
        mode (str): If `overwrite`, (default) all attributes that already existed on
                                    flexilims but are not specified in the function call
                                    are set to 'null'.
                    If `update`, update the attributes given in this call and do not
                                 change the other
        attributes (dict or None): attributes to update
        project_id (str): text name of the project
        flexilims_session (Flexilims): Flexylims session object

    Returns:
        flexilims reply
    """
    assert (name is not None) or (id is not None)
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)
    entity = get_entity(datatype=datatype,
        name=name,
        id=id,
        flexilims_session=flexilims_session,
        format_reply=False)
    if entity is None:
        err_msg = 'Cannot find an entity of type `%s` named `%s`' % (datatype, name)
        raise FlexilimsError(err_msg)
    if mode.lower() == 'overwrite':
        full_attributes = {k: '' for k in entity['attributes'].keys()}
        full_attributes.update(attributes)
    elif mode.lower() == 'update':
        full_attributes = attributes.copy()
    else:
        raise AttributeError('`mode` must be `overwrite` or `update`')
    if id is None:
        id = entity['id']

    # the update cannot deal with None, set them to ''
    for k, v in full_attributes.items():
        if v is None:
            full_attributes[k] = ''

    rep = flexilims_session.update_one(
        id=id,
        datatype=datatype,
        origin_id=origin_id,
        name=None,
        attributes=full_attributes,
        strict_validation=False
        )
    return rep


def format_results(results):
    """make request output a nice df

    This will crash if any attribute is also present in the flexilims reply,
    i.e. if an attribute is named:
    'id', 'type', 'name', 'incrementalId', 'createdBy', 'dateCreated',
    'origin_id', 'objects', 'customEntities', or 'project'
    """

    for result in results:
        for attr_name, attr_value in result['attributes'].items():
            if attr_name in result:
                raise FlexilimsError('An entity should not have %s as attribute' % attr_name)
            result[attr_name] = attr_value
        result.pop('attributes')
    df = pd.DataFrame(results)
    return df


def get_datatype(name=None, id=None, project_id=None, flexilims_session=None):
    """
    Loop through possible datatypes and return the first with a matching name
    """
    assert (project_id is not None) or (flexilims_session is not None)
    assert (name is not None) or (id is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)
    for datatype in PARAMETERS['datatypes']:
        resp = get_entity(datatype=datatype, name=name, id=id, flexilims_session=flexilims_session)
        if resp: return datatype
    return None


def get_id(name, datatype='mouse', project_id=None, flexilims_session=None):
    """Get database ID for entity by name"""
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    entities = get_entities(datatype=datatype,
                            flexilims_session=flexilims_session,
                            name=name)
    if len(entities) != 1:
        raise NameNotUniqueError(
            'ERROR: Found {num} entities of type {datatype} with name {name}!'
                .format(num=len(entities), datatype=datatype, name=name))
        return None
    else:
        return entities['id'][0]


def get_path(name, datatype='mouse', project_id=None, flexilims_session=None):
    """Get database ID for entity by name"""
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    entities = get_entities(datatype=datatype,
                            flexilims_session=flexilims_session,
                            name=name)
    if len(entities) != 1:
        raise NameNotUniqueError(
            'ERROR: Found {num} entities of type {datatype} with name {name}!'
                .format(num=len(entities), datatype=datatype, name=name))
        return None
    else:
        return entities['path'][0]


def get_experimental_sessions(project_id=None, flexilims_session=None, mouse=None):
    """Get all sessions from a given mouse"""
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    expts = format_results(flexilims_session.get(datatype='session'))

    if mouse is None:
        return expts
    else:
        mouse_id = get_id(mouse, flexilims_session=flexilims_session)
        return expts[expts['origin_id'] == mouse_id]


def get_children(parent_id, children_datatype, project_id=None, flexilims_session=None):
    """
    Get all entries belonging to a particular parent entity

    Args:
        parent_id (str): hexadecimal id of the parent entity
        children_datatype (str): type of child entities to fetch
        project_id (str): text name of the project
        flexilims_session (Flexilims): Flexylims session object

    Returns:
        DataFrame: containing all the relevant child entitites
    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    results = format_results(flexilims_session.get(
        children_datatype,
        origin_id=parent_id))
    return results


def get_datasets(origin_id, recording_type=None, dataset_type=None, project_id=None,
                 flexilims_session=None):
    """
    Recurse into recordings and get paths to child datasets of a given type
    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)
    else:
        project_id = _lookup_project(flexilims_session.project_id, PARAMETERS)
    recordings = get_entities(datatype='recording',
                              origin_id=origin_id,
                              query_key='recording_type',
                              query_value=recording_type,
                              flexilims_session=flexilims_session)
    datapath_dict = {}
    for recording_id in recordings['id']:
        datasets = get_entities(datatype='dataset',
                                origin_id=recording_id,
                                query_key='dataset_type',
                                query_value=dataset_type,
                                flexilims_session=flexilims_session)
        datapaths = []
        for dataset_path in datasets['path']:
            this_path = Path(PARAMETERS['projects_root']) / project_id / dataset_path
            if this_path.exists():
                datapaths.append(str(this_path))
            else:
                raise IOError('Dataset {} not found'.format(this_path))
            datapath_dict[recording_id] = datapaths
    return datapath_dict
