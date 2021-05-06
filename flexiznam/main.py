import pandas as pd
import flexilims as flm
from flexiznam import mcms
from flexiznam.utils import PARAMETERS, get_password
from flexiznam.errors import NameNotUniqueException


def _format_project(project_id, prm):
    if project_id in prm['project_ids']:
        return prm['project_ids'][project_id]
    if project_id is None or len(project_id) != 24:
        raise AttributeError('Invalid project: "%s"' % project_id)
    return project_id


def get_session(project_id, username, password):
    project_id = _format_project(project_id, PARAMETERS)
    if username is None:
        username = PARAMETERS['flexilims_username']
    if password is None:
        password = get_password(username, 'flexilims')
    session = flm.Flexilims(username, password, project_id=project_id)
    return session


def add_mouse(mouse_name, project_id, session=None, mcms_animal_name=None,
              flexilims_username=None, mcms_username=None,
              flexilims_password=None):
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


def get_entities(datatype='mouse', query_key=None, query_value=None,
        project_id=None, username=None, session=None, password=None):
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
    if query_key is None:
        results = format_results(session.get(datatype))
    else:
        results = format_results(session.get(
                        datatype,
                        query_key=query_key,
                        query_value=query_value
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
                            query_key='name',
                            query_value=name)
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

    if mouse is None:
        expts = format_results(session.get('session'))
    else:
        mouse_id = get_id(mouse, datatype='mouse', session=session)
        expts = format_results(session.get(
                    'session',
                    query_key=origin,
                    query_value=mouse_id
                    ))
    return expts


def get_children(parent_id, children_type, project_id=None, username=None,
        session=None, password=None):
    """Get all entries belonging to a particular parent entity"""
    assert (project_id is not None) or (session is not None)
    if session is None:
        session = get_session(project_id, username, password)

    results = format_results(session.get(
                    children_type,
                    query_key='origin',
                    query_value=parent_id))
    return results
