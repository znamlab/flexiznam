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
    """ Open a new flexilims session by creating a new authentication token.

    Args:
        project_id (str): name of the project. Automatically converted to the
            corresponding hexadecimal ID by looking up the config file.
        username (str): (optional) flexilims username. If not provided, it is
            read from the config file.
        password (str): (optional) flexilims password. If not provided, it is
            read from the secrets file, or failing that triggers an input prompt.

    Returns:
        :py:class:`flexilims.Flexilims`: Flexilims session object.
    """
    project_id = _format_project(project_id, PARAMETERS)
    if username is None:
        username = PARAMETERS['flexilims_username']
    if password is None:
        password = get_password(username, 'flexilims')
    session = flm.Flexilims(username, password, project_id=project_id)
    return session


def add_mouse(mouse_name, project_id, flexilims_session=None, mcms_animal_name=None,
              flexilims_username=None, mcms_username=None, flexilims_password=None):
    """Check if a mouse is already in the database and add it if it isn't

    Args:
        mouse_name:
        project_id:
        flexilims_session (:py:class:`flexilims.Flexilims`):
        mcms_animal_name:
        mcms_username:

    Returns:
        flexilims reply

    """

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


def add_experimental_session(mouse_name, date, attributes={}, session_name=None,
                             other_relations=None, flexilims_session=None,
                             project_id=None, conflicts='abort'):
    """Add a new session as a child entity of a mouse

    Args:
        mouse_name (str): name of the mouse. Must exist on flexilims
        date (str): date of the session. If `session_name` is not provided, will be used as name
        attributes (dict): dictionary of additional attributes (on top of date)
        session_name (str or None): name of the session, usually in the shape `S20210420`.
        conflicts (str): What to do if a session with that name already exists? Can be `skip`
            for skiping creation and returning the session from flexilims or
            `abort` to crash
        other_relations: ID(s) of custom entities related to the session
        flexilims_session (:py:class:`flexilims.Flexilims`): flexilims session
        project_id (str): name of the project or hexadecimal project id (needed if session is not provided)

    Returns:
        flexilims reply

    """
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    if conflicts.lower() not in ('skip', 'abort'):
        raise AttributeError('conflicts must be `skip` or `abort`')

    mouse_id = get_id(mouse_name, datatype='mouse', flexilims_session=flexilims_session)
    if session_name is None:
        session_name = mouse_name + '_' + date + '_0'
    online_session = get_entity(datatype='session', name=session_name,
                                flexilims_session=flexilims_session)
    if online_session is not None:
        if conflicts.lower() == 'skip':
            print('A session named %s already exists' % session_name)
            return online_session
        else:
            raise FlexilimsError('A session named %s already exists' % session_name)

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
                  recording_name=None, conflicts='abort', other_relations=None,
                  flexilims_session=None, project_id=None):
    """Add a recording as a child of an experimental session

    Args:
        session_id (str): hexadecimal ID of the session. Must exist on flexilims
        recording_type (str): one of [two_photon, widefield, intrinsic, ephys, behaviour]
        protocol (str): experimental protocol (`retinotopy` for instance)
        attributes (dict):  dictionary of additional attributes (on top of protocol and recording_type)
        recording_name (str or None): name of the recording, usually in the shape `R152356`.
        conflicts (str): `skip` or `abort`: how to handle conflicts
        other_relations: ID(s) of custom entities related to the session
        flexilims_session (:py:class:`flexilims.Flexilims`): flexilims session
        project_id (str): name of the project or hexadecimal project id (needed if session is not provided)

    Returns:
        flexilims reply

    """

    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    if conflicts.lower() not in ('skip', 'abort'):
        raise AttributeError('conflicts must be `skip` or `abort`')

    experimental_session = get_entity(datatype='session',
                                      flexilims_session=flexilims_session,
                                      id=session_id)
    if recording_name is None:
        recording_name = experimental_session['name'] + '_' + protocol + '_0'
    online_recording = get_entity(datatype='recording', name=recording_name,
                                flexilims_session=flexilims_session)
    if online_recording is not None:
        if conflicts.lower() == 'skip':
            print('A recording named %s already exists' % (recording_name))
            return online_recording
        else:
            raise FlexilimsError('A recording named %s already exists' %
                                 recording_name)

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


def add_sample(parent_id, attributes=None, sample_name=None,
               conflicts='skip', other_relations=None, flexilims_session=None,
               project_id=None):
    """Add a sample as a child of a mouse or another sample

    Default conflict behaviour for samples is `skip`, as we will often add from
    the same sample multiple occasions.

    Args:
        parent_id (str): hexadecimal ID of the parent entity. Must exist on flexilims.
        attributes (dict): dictionary of additional attributes.
        sample_name (str or None): name of the sample.
        conflicts (str): `skip` or `abort`: how to handle conflicts.
        other_relations: ID(s) of custom entities related to the sample.
        flexilims_session (:py:class:`flexilims.Flexilims`): flexilims session.
        project_id (str): name of the project or hexadecimal project id
            (required if session is not provided).

    Returns:
        flexilims reply

    """
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    if conflicts.lower() not in ('skip', 'abort'):
        raise AttributeError('conflicts must be `skip` or `abort`')

    if sample_name is None:
        parent_name = pd.concat([
            get_entities(flexilims_session=flexilims_session,
                         datatype='mouse',
                         id=parent_id),
            get_entities(flexilims_session=flexilims_session,
                         datatype='sample',
                         id=parent_id)
        ])['name'][0]
        sample_name = parent_name + '_sample_0'
        sample_name = generate_name('sample', sample_name,
                                    flexilims_session=flexilims_session)
    online_sample = get_entity(
        datatype='sample',
        name=sample_name,
        flexilims_session=flexilims_session
    )
    if online_sample is not None:
        if conflicts.lower() == 'skip':
            print('A sample named %s already exists' % (sample_name))
            return online_sample
        else:
            raise FlexilimsError('A sample named %s already exists' %
                                 sample_name)

    if attributes is None:
        attributes = {}
    resp = flexilims_session.post(
        datatype='sample',
        name=sample_name,
        attributes=attributes,
        origin_id=parent_id,
        other_relations=other_relations,
        strict_validation=False
    )
    return resp


def add_dataset(parent_id, dataset_type, created, path, is_raw='yes', project_id=None,
                flexilims_session=None, dataset_name=None, attributes=None,
                strict_validation=False, conflicts='append'):
    """Add a dataset as a child of a recording, session, or sample

    Args:
        parent_id (str): hexadecimal ID of the parent (session or recording)
        dataset_type (str): dataset_type, must be a type define in the config file
        created (str): date of creation as text, usually in this format: '2021-05-24 14:56:41'
        path (str): path to the data relative to the project folder
        is_raw (str): `yes` or `no`, used to find the root directory
        project_id (str): hexadecimal ID or name of the project
        flexilims_session (:py:class:`flexilims.Flexilims`): authentication
            session for flexilims
        dataset_name (str): name of the dataset, will be autogenerated if not provided
        attributes (dict): optional attributes
        strict_validation (bool): default False, if True, only attributes in lab settings are
            allowed
        conflicts (str): `abort`, `skip`, `append`, what to do if a dataset with this name
            already exists? `abort` to crash, `skip` to ignore and return the
            online version, `append` to increment name and create a new dataset.

    Returns:
        the flexilims response

    """
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)
    valid_conflicts = ('abort', 'skip', 'append')
    if conflicts.lower() not in valid_conflicts:
        raise AttributeError('`conflicts` must be in [%s]' % ', '.join(valid_conflicts))

    if dataset_name is None:
        parent_name = pd.concat([
            get_entities(flexilims_session=flexilims_session,
                         datatype='recording',
                         id=parent_id),
            get_entities(flexilims_session=flexilims_session,
                         datatype='session',
                         id=parent_id),
            get_entities(flexilims_session=flexilims_session,
                         datatype='sample',
                         id=parent_id)
        ])['name'][0]
        dataset_name = parent_name + '_' + dataset_type + '_0'
    if conflicts.lower() == 'append':
        dataset_name = generate_name('dataset', dataset_name,
                                     flexilims_session=flexilims_session)
    else:
        online_version = get_entity('dataset', name=dataset_name,
                                    flexilims_session=flexilims_session)
        if online_version is not None:
            if conflicts.lower() == 'abort':
                raise FlexilimsError('A dataset named %s already exists' % (dataset_name))
            else:
                print('A dataset named %s already exists' % (dataset_name))
                return online_version

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

    Entities can be filtered by name, id, origin, or attribute (using the
    `query_key` / `query_value` arguments).

    Args:
        datatype (str): type of Flexylims entity to fetch, e.g. 'mouse', 'session',
            'recording', or 'dataset'. This is the only mandatory argument.
        query_key (str): attribute to filter by.
        query_value (str): attribute value to select
        project_id (str): text name of the project. Either `project_id` or
            `flexilims_session` must be provided.
        flexilims_session (:py:class:`flexilims.Flexilims`): Flexylims session
            object. This is preferred to providing `project_id` as it avoids
            creating new authentication tokens.
        name (str): filter by name
        origin_id (str): filter by origin / parent
        id (str): filter by hexadecimal id
        format_reply (bool): (default True) whether to format the reply into a
            `Dataframe`. If this is set to false, a list of dictionaries will be
            returned instead.

    Returns:
        :py:class:`pandas.DataFrame`: containing all matching entities

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

    Calls :py:meth:`flexiznam.main.get_entities` but expects only one result and
    returns a :py:class:`pandas.Series` instead of a :py:class:`pandas.DataFrame`.
    If multiple entities on the database match the query, raise a
    :py:class:`flexiznam.errors.NameNotUniqueError`, if nothing matches returns `None`.

    Args:
        datatype (str): type of Flexylims entity to fetch, e.g. 'mouse', 'session',
            'recording', or 'dataset'. This is the only mandatory argument.
        query_key (str): attribute to filter by.
        query_value (str): attribute value to select
        project_id (str): text name of the project. Either `project_id` or
            `flexilims_session` must be provided.
        flexilims_session (:py:class:`flexilims.Flexilims`): Flexylims session
            object. This is preferred to providing `project_id` as it avoids
            creating new authentication tokens.
        name (str): filter by name
        origin_id (str): filter by origin / parent
        id (str): filter by hexadecimal id
        format_reply (bool): (default True) whether to format the reply into a
            `Dataframe`. If this is set to false, a list of dictionaries will be
            returned instead.

    Returns:
        :py:class:`pandas.Series`: containing the entity or dictionary if
        format_reply is False

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
        other_relations (str or :obj:`list` of :obj:`str`): hexadecimal ID(s)
            of custom entities link to the entry to update
        project_id (str): text name of the project
        flexilims_session (:py:class:`flexilims.Flexilims`): Flexylims session object

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
        mode (str): what to do with attributes that are not explicitly specified.

            `overwrite`
                (default) all attributes that already exist on
                flexilims but are not specified in the function call are set to 'null'.
            `update`
                update the attributes given in this call and do not change the
                others.

        attributes (dict or None): attributes to update
        project_id (str): text name of the project
        flexilims_session (:py:class:`flexilims.Flexilims`): Flexylims session object

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
    """Make request output a nice DataFrame

    This will crash if any attribute is also present in the flexilims reply,
    i.e. if an attribute is named:
    'id', 'type', 'name', 'incrementalId', 'createdBy', 'dateCreated',
    'origin_id', 'objects', 'customEntities', or 'project'

    Args:
        results (:obj:`list` of :obj:`dict`): Flexilims reply

    Returns:
        :py:class:`pandas.DataFrame`: Reply formatted as a DataFrame

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
    Loop through possible datatypes and return the first with a matching name.

    .. warning::
      If there are multiple matches, will return only the first one found!

    Args:
        name (str): (optional, if `id` is provided) name of the entity
        id (str): (optional, if `name` is provided) hexadecimal id of the entity
        project_id (str): (optional, if `flexilims_session` is provided)
            text name of the project
        flexilims_session (:py:class:`flexilims.Flexilims`): (optional, if
            `project_id` is provided) Flexylims session object

    Returns:
        str: datatype of the matching entity.

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
        flexilims_session (:py:class:`flexilims.Flexilims`): Flexylims session object

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
    Recurse into recordings and get paths to child datasets of a given type.

    For example, this is useful if you want to retrieve paths to all *scanimage*
    datasets associated with a given session.

    Args:
        origin_id (str): hexadecimal ID of the origin session.
        recording_type (str): type of the recording to filter by. If `None`,
            will return datasets for all recordings.
        dataset_type (str): type of the dataseet to filter by. If `None`,
            will return all datasets.
        project_id (str): text name of the project. Not required if
            `flexilims_session` is provided.
        flexilims_session (:py:class:`flexilims.Flexilims`): Flexylims session object

    Returns:
        dict: Dictionary with recording names as keys containing lists of associated dataset paths.

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
    if len(recordings)<1:
        return datapath_dict
    for recording_id in recordings['id']:
        datasets = get_entities(datatype='dataset',
                                origin_id=recording_id,
                                query_key='dataset_type',
                                query_value=dataset_type,
                                flexilims_session=flexilims_session)
        datapaths = []
        for (dataset_path, is_raw) in zip(datasets['path'], datasets['is_raw']):
            prefix = PARAMETERS['data_root']['raw'] if is_raw=='yes' else PARAMETERS['data_root']['processed']
            this_path = Path(prefix) / dataset_path
            if this_path.exists():
                datapaths.append(str(this_path))
            else:
                raise IOError('Dataset {} not found'.format(this_path))
            datapath_dict[recording_id] = datapaths
    return datapath_dict
