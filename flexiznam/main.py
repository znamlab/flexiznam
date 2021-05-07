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


def add_mouse(mouse_name, project_id, session=None, mcms_animal_name=None, flexilims_username=None, mcms_username=None,
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


def get_mice(project_id=None, username=None, session=None, password=None):
    """Get mouse info and format it"""

    assert (project_id is not None) or (session is not None)
    if session is None:
        session = get_session(project_id, username, password)

    mice = format_results(session.get(datatype='mouse'))
    if len(mice):
        mice.set_index('name', drop=False, inplace=True)
    return mice


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


def get_mouse_id(mouse_name, project_id=None, username=None, session=None, password=None):
    """Get database ID for mouse by name"""
    assert (project_id is not None) or (session is not None)
    if session is None:
        session = get_session(project_id, username, password)

    mice = get_mice(session=session)
    matching_mice = mice[mice['name'] == mouse_name]
    if len(matching_mice) != 1:
        raise NameNotUniqueException(
            'ERROR: Found {num} mice with name {name}!'
            .format(num=len(matching_mice), name=mouse_name))
    return matching_mice['id'][0]


def get_experimental_sessions(project_id=None, username=None, session=None, password=None,
                              mouse=None):
    """Get all sessions from a given mouse"""
    assert (project_id is not None) or (session is not None)
    if session is None:
        session = get_session(project_id, username, password)

    expts = format_results(session.get({'type': 'session'}))

    if mouse is None:
        return expts
    else:
        mouse_id = get_mouse_id(mouse, session=session)
        return expts[expts['origin'] == mouse_id]
