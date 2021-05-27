import pandas as pd
import flexilims as flm
from pathlib import Path
from flexiznam import mcms
from flexiznam.config import PARAMETERS, get_password
from flexiznam.errors import NameNotUniqueException, FlexilimsError


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
    resp = flexilims_session.post(datatype='mouse', name=mouse_name, attributes=dict(mouse_info), strict_validation=False)
    return resp


def add_experimental_session(mouse_name, date, attributes={}, session_name=None, mode='abort',
                             other_relations=None, flexilims_session=None, project_id=None, username=None, password=None):
    """Add a new session as a child entity of a mouse

    Args:
        mouse_name: str, name of the mouse. Must exist on flexilims
        date: str, date of the session. If `session_name` is not provided, will be used as name
        attributes: dict, dictionary of additional attributes (on top of date)
        session_name: str or None, name of the session, usually in the shape `S20210420`.
        mode: `abort`, `append`, or `overwrite`: how to handle conflicts
        other_relations: ID(s) of custom entities related to the session
        flexilims_session: flexilims session
        project_id: name of the project or hexadecimal project id (needed if session is not provided)
        username: flexilims username (needed if session is not provided)
        password: flexilims password (needed if session is not provided)


    Returns: flexilims reply
    """

    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id, username, password)

    mouse_id = get_id(mouse_name, datatype='mouse', flexilims_session=flexilims_session)
    if session_name is None:
        session_name = date
    name = mouse_name + '_' + session_name + '_0'

    session_info = {'date': date}
    if attributes is None:
        attributes = {}
    if ('date' in attributes) and (date != attributes['date']):
        raise FlexilimsError('Got two values for date: %s and %s' % (date, attributes['date']))
    session_info.update(attributes)
    resp = update_by_name(name=name, datatype='session', origin_id=mouse_id, attributes=session_info, flexilims_session=flexilims_session,
                          mode=mode, other_relations=other_relations)
    return resp


def add_recording(session_id, recording_type, protocol, attributes=None, recording_name=None, mode=None,
                  other_relations=None, flexilims_session=None, project_id=None, password=None, username=None):
    """Add a recording as a child of an experimental session

    Args:
        session_id: str, hexadecimal ID of the session. Must exist on flexilims
        recording_type: str, one of [two_photon, widefield, intrinsic, ephys, behaviour]
        protocol: str, experimental protocol (`retinotopy` for instance)
        attributes: dict, dictionary of additional attributes (on top of protocol and recording_type)
        recording_name: str or None, name of the recording, usually in the shape `R152356`.
        mode: `abort`, `append`, or `overwrite`: how to handle conflicts
        other_relations: ID(s) of custom entities related to the session
        flexilims_session: flexilims session
        project_id: name of the project or hexadecimal project id (needed if session is not provided)
        username: flexilims username (needed if session is not provided)
        password: flexilims password (needed if session is not provided)


    Returns: flexilims reply
    """

    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id, username, password)

    experimental_session = get_entity(datatype=flexilims_session, id=session_id)
    if recording_name is None:
        recording_name = experimental_session['name'] + '_' + protocol + '_0'
    else:
        recording_name = experimental_session['name'] + recording_name

    recording_info = {'recording_type': recording_type, 'protocol': protocol}
    if attributes is None:
        attributes = {}
    for key in recording_info.keys():
        if (key in attributes) and (attributes[key] != locals()[key]):
            raise FlexilimsError('Got two values for %s: `%s` and `%s`' % (key, attributes[key], locals()[key]))
    recording_info.update(attributes)
    resp = update_by_name(name=recording_name, datatype='recording', origin_id=session_id, attributes=recording_info,
                          flexilims_session=flexilims_session, mode=mode, other_relations=other_relations)
    return resp


def add_dataset(parent_id, dataset_type, created, path, is_raw='yes',
                project_id=None, flexilims_session=None, password=None, username=None,
                dataset_name=None, attributes=None, strict_validation=False):
    """
    Add a dataset as a child of a recording or session
    """
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id, username, password)

    if dataset_name is None:
        parent_name = pd.concat([
            get_entities(flexilims_session=flexilims_session, datatype='recording', id=parent_id),
            get_entities(flexilims_session=flexilims_session, datatype='session', id=parent_id)
        ])['name'][0]
        dataset_num = 0
        while len(get_entities(
                flexilims_session=flexilims_session,
                datatype='dataset',
                name=parent_name + '_' + dataset_type + '_' + str(dataset_num))):
            # session with this name already exists, increment the number
            dataset_num += 1
        dataset_name = parent_name + '_' + dataset_type + '_' + str(dataset_num)

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


def update_dataset(dataset_name=None, dataset_id=None, project_id=None,
                   flexilims_session=None, password=None, username=None, attributes=None,
                   parent_id=None, strict_validation=False):
    """
    Update dataset entry on flexilims selected by name or id

    TODO:
    Check what happens if a previously added attribute value is not provided.
    We probably want to clear those if not explicitly passed in the attributes
    dictionary
    """
    assert (dataset_name is not None) or (dataset_id is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id, username, password)
    dataset_series = get_entity(
        flexilims_session=flexilims_session,
        datatype='dataset',
        name=dataset_name,
        id=dataset_id
    )
    if parent_id is None:
        parent_id = dataset_series['origin_id']
    if dataset_id is None:
        dataset_id = dataset_series['id']
    if dataset_name is None:
        dataset_name = dataset_series['name']
    dataset_info = {}
    if attributes is not None:
        for attribute in attributes:
            dataset_info[attribute] = attributes[attribute]
    resp = flexilims_session.update_one(
        datatype='dataset',
        name=dataset_name,
        id=dataset_id,
        origin_id=parent_id,
        attributes=dataset_info,
        strict_validation=strict_validation
    )
    return resp


def get_entities(datatype='mouse', query_key=None, query_value=None,
                 project_id=None, username=None, flexilims_session=None, password=None,
                 name=None, origin_id=None, id=None):
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
        username (str): Flexylims username
        flexilims_session (Flexilims): Flexylims session object
        password (str): Flexylims password
        name (str): filter by name
        origin_id (str): filter by origin / parent
        id (str): filter by hexadecimal id

    Returns:
        DataFrame: containing all matching entities
    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id, username, password)
    # Awaiting implementation on the flexilims side:
    results = format_results(flexilims_session.get(
        datatype,
        query_key=query_key,
        query_value=query_value,
        name=name,
        origin_id=origin_id,
        id=id
    ))
    if len(results):
        results.set_index('name', drop=False, inplace=True)
    return results


def get_entity(datatype, query_key=None, query_value=None,
               project_id=None, username=None, flexilims_session=None, password=None,
               name=None, origin_id=None, id=None):
    """
    Get one entity and format result.

    If multiple entities on the database match the query, raise a NameNotUniqueException,
    if nothing match, return None

    If an open Flexylims session is provided, the other authentication arguments
    aree not needed (or used)

    Args:
        datatype (str): type of Flexylims entity to fetch, e.g. 'mouse', 'session',
            'recording', or 'dataset'
        query_key (str): attribute to filter by
        query_value (str): attribute value to select
        project_id (str): text name of the project
        username (str): Flexylims username
        flexilims_session (Flexilims): Flexylims session object
        password (str): Flexylims password
        name (str): filter by name
        origin_id (str): filter by origin / parent
        id (str): filter by hexadecimal id

    Returns:
        Series: containing the entity
    """
    entity = get_entities(datatype=datatype, query_key=query_key, query_value=query_value,
                          project_id=project_id, username=username, flexilims_session=flexilims_session,
                          password=password, name=name, origin_id=origin_id, id=id)
    if not len(entity):
        return None
    if len(entity) != 1:
        raise NameNotUniqueException('Found %d entities, not 1' % len(entity))
    return entity.iloc[0]


def update_entity(datatype, name=None, id=None,
                   origin_id=None, mode='overwrite', attributes={}, other_relations=None,
                   flexilims_session=None, project_id=None, username=None, password=None):
    """Update one entity identified with its datatype and name

    Args:
        name (str): name on flexilims
        datatype (str): flexilims type
        origin_id (str or None): hexadecimal id of the origin
        mode (`abort`=None, `append`, `overwrite`): How to handle conflicts
        attributes (dict or None): attributes to update
        other_relations (str or list of str): hexadecimal ID(s) of custom entities
            link to the entry to update
        project_id (str): text name of the project
        username (str): Flexylims username
        flexilims_session (Flexilims): Flexylims session object
        password (str): Flexylims password


    Returns:

    """
    assert (name is not None) or (id is not None)
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id, username, password)
    entity = get_entity(datatype=datatype, name=name, id=id, flexilims_session=flexilims_session)
    if entity is not None:
        if (mode is None) or (mode.lower() == 'abort'):
            raise FlexilimsError('An entry named `%s` already exist. Use `overwrite` flag to replace' % name)
        if mode.lower() == 'overwrite':
            if attributes:
                full_attributes = {k: '' for k in entity['attributes'].keys()}
                full_attributes.update(attributes)
            else:
                full_attributes = {}
            if (origin_id is None) and ('origin_id' in entity.keys()):
                origin_id = entity['origin_id']
            if id is None:
                id = entity['id']
            rep = flexilims_session.update_one(
                id=id,
                datatype=datatype,
                origin_id=origin_id,
                name=None,
                attributes=full_attributes,
                strict_validation=False
            )
            return rep
        if mode.lower() == 'append':
            # I need to generate a new name
            suffix = name.split('_')[-1]
            root = name[:-len(suffix) - 1]
            if not suffix.isnumeric():
                root += suffix
                suffix = 0
            else:
                suffix = int(suffix)
            while get_entity(datatype, name='%s_%s' % (root, suffix), flexilims_session=flexilims_session) is not None:
                suffix += 1
            name = '%s_%s' % (root, suffix)

    # new name, will create one entry
    rep = flexilims_session.post(
        datatype=datatype,
        name=name,
        attributes=attributes,
        origin_id=origin_id,
        other_relations=other_relations,
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


def get_id(name, datatype='mouse', project_id=None, username=None, flexilims_session=None, password=None):
    """Get database ID for entity by name"""
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id, username, password)

    entities = get_entities(datatype=datatype,
                            flexilims_session=flexilims_session,
                            name=name)
    if len(entities) != 1:
        raise NameNotUniqueException(
            'ERROR: Found {num} entities of type {datatype} with name {name}!'
                .format(num=len(entities), datatype=datatype, name=name))
        return None
    else:
        return entities['id'][0]


def get_experimental_sessions(project_id=None, username=None, flexilims_session=None, password=None,
                              mouse=None):
    """Get all sessions from a given mouse"""
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id, username, password)

    expts = format_results(flexilims_session.get(datatype='session'))

    if mouse is None:
        return expts
    else:
        mouse_id = get_id(mouse, flexilims_session=flexilims_session)
        return expts[expts['origin_id'] == mouse_id]


def get_children(parent_id, children_datatype, project_id=None, username=None,
                 flexilims_session=None, password=None):
    """
    Get all entries belonging to a particular parent entity

    Args:
        parent_id (str): hexadecimal id of the parent entity
        children_datatype (str): type of child entities to fetch
        project_id (str): text name of the project
        username (str): Flexylims username
        flexilims_session (Flexilims): Flexylims session object
        password (str): Flexylims password

    Returns:
        DataFrame: containing all the relevant child entitites
    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id, username, password)

    results = format_results(flexilims_session.get(
        children_datatype,
        origin_id=parent_id))
    return results


def get_datasets(origin_id, recording_type=None, dataset_type=None,
                 project_id=None, username=None, flexilims_session=None, password=None):
    """
    Recurse into recordings and get paths to child datasets of a given type
    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id, username, password)
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
