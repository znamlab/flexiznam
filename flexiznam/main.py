import pandas as pd
import flexilims as flm
from flexiznam import mcms
from flexiznam.config.utils import PARAMETERS, get_password
from flexiznam.errors import NameNotUniqueException


def _format_project(project_id, prm):
    if project_id in prm['project_ids']:
        return prm['project_ids'][project_id]
    if project_id is None or len(project_id) != 24:
        raise AttributeError('Invalid project: "%s"' % project_id)
    return project_id


def get_session(project_id, username=None, password=None):
    project_id = _format_project(project_id, PARAMETERS)
    if username is None:
        username = PARAMETERS['flexilims_username']
    if password is None:
        password = get_password(username, 'flexilims')
    session = flm.Flexilims(username, password, project_id=project_id)
    return session


def add_mouse(mouse_name, project_id, session=None, mcms_animal_name=None,
              flexilims_username=None, mcms_username=None, flexilims_password=None):
    """Check if a mouse is already in the database and add it if it isn't"""

    if session is None:
        session = get_session(project_id, flexilims_username, flexilims_password)
    mice_df = get_mice(session=session)
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
    resp = session.post(datatype='mouse', name=mouse_name, attributes=dict(mouse_info))
    return resp


def add_experimental_session(mouse_name, date, project_id=None, session=None,
                password=None, username=None):
    """
    Add a new session as a child entity of a mouse
    """
    if session is None:
        session = get_session(project_id, username, password)

    mouse_id = get_id(mouse_name, datatype='mouse', session=session)

    sessions_num = 0
    while len(get_entities(
        session=session,
        datatype='session',
        name=mouse_name + '_' + date + '_' + str(session_num))):
        # session with this name already exists, increment the number
        sessions_num += 1

    session_name = mouse_name + '_' + date + '_' + str(session_num)

    session_info = { 'date': date, }
    resp = session.post(
        datatype='session',
        name=session_name,
        origin_id=mouse_id,
        attributes=session_info)
    return resp


def add_recording(session_id, recording_type, protocol,
                  project_id=None, session=None, password=None, username=None):
    """
    Add a recording as a child of an experimental session
    """
    if session is None:
        session = get_session(project_id, username, password)

    recording_num = 0
    while len(get_entities(
        session=session,
        datatype='recording',
        name=mouse_name + '_' + date + '_' + protocol + '_' + str(recording_num))):
        # session with this name already exists, increment the number
        recording_num += 1

    recording_name = mouse_name + '_' + date + '_' + protocol + '_' + str(recording_num)))

    recording_info = { 'recording_type': recording_type, 'protocol': protocol }
    resp = session.post(
        datatype='recording',
        name=recording_name,
        origin_id=session_id,
        attributes=recording_info)
    return resp


def get_entities(datatype='mouse', query_key=None, query_value=None,
                 project_id=None, username=None, session=None, password=None,
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
        session (Flexilims): Flexylims session object
        password (str): Flexylims password

    Returns:
        DataFrame: containing all matching entities
    """
    assert (project_id is not None) or (session is not None)
    if session is None:
        session = get_session(project_id, username, password)
    results = format_results(session.get(
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


def format_results(results):
    """make request output a nice df"""
    reserved_keywords = ['id', 'type', 'name', 'incrementalId']
    for result in results:
        for attr_name, attr_value in result['attributes'].items():
            assert attr_name not in reserved_keywords
            result[attr_name] = attr_value
        result.pop('attributes')
    df = pd.DataFrame(results)
    return df


def get_id(name, datatype='mouse', project_id=None, username=None, session=None, password=None):
    """Get database ID for entity by name"""
    assert (project_id is not None) or (session is not None)
    if session is None:
        session = get_session(project_id, username, password)

    entities = get_entities(datatype=datatype,
                            session=session,
                            name=name)
    if len(entities) != 1:
        raise NameNotUniqueException(
            'ERROR: Found {num} entities of type {datatype} with name {name}!'
            .format(num=len(entities), datatype=datatype, name=name))
        return None
    else:
        return entities['id'][0]


def get_experimental_sessions(project_id=None, username=None, session=None, password=None,
                              mouse=None):
    """Get all sessions from a given mouse"""
    assert (project_id is not None) or (session is not None)
    if session is None:
        session = get_session(project_id, username, password)

    expts = format_results(session.get(datatype='session'))

    if mouse is None:
        return expts
    else:
        mouse_id = get_id(mouse, session=session)
        return expts[expts['origin'] == mouse_id]


def get_children(parent_id, children_datatype, project_id=None, username=None,
                 session=None, password=None):
    """
    Get all entries belonging to a particular parent entity

    Args:
        parent_id (str): hexadecimal id of the parent entity
        children_datatype (str): type of child entities to fetch
        project_id (str): text name of the project
        username (str): Flexylims username
        session (Flexilims): Flexylims session object
        password (str): Flexylims password

    Returns:
        DataFrame: containing all the relevant child entitites
    """
    assert (project_id is not None) or (session is not None)
    if session is None:
        session = get_session(project_id, username, password)

    results = format_results(session.get(
                    children_datatype,
                    origin_id=parent_id))
    return results
