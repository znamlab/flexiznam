import datetime
import re
import warnings
import pandas as pd
import flexilims as flm
from pathlib import Path
import flexiznam
from flexiznam import mcms
from flexiznam.config import PARAMETERS, get_password, add_password
from flexiznam.errors import NameNotUniqueError, FlexilimsError, ConfigurationError


warnings.simplefilter("always", DeprecationWarning)


def _format_project(project_id, prm):
    if project_id in prm["project_ids"]:
        return prm["project_ids"][project_id]
    if project_id is None or len(project_id) != 24:
        raise AttributeError('Invalid project: "%s"' % project_id)
    return project_id


def lookup_project(project_id, prm=None):
    """
    Look up project name by hexadecimal id
    """
    if prm is None:
        prm = PARAMETERS
    try:
        proj = next(proj for proj, id in prm["project_ids"].items() if id == project_id)
        return proj
    except StopIteration:
        return None


def get_flexilims_session(
    project_id=None, username=None, password=None, reuse_token=True
):
    """Open a new flexilims session by creating a new authentication token.

    Args:
        project_id (str): name of the project. Automatically converted to the
            corresponding hexadecimal ID by looking up the config file.
        username (str): (optional) flexilims username. If not provided, it is
            read from the config file.
        password (str): (optional) flexilims password. If not provided, it is
            read from the secrets file, or failing that triggers an input prompt.
        reuse_token (bool): (optional) if True, try to reuse an existing token

    Returns:
        :py:class:`flexilims.Flexilims`: Flexilims session object.
    """

    if project_id is not None:
        project_id = _format_project(project_id, PARAMETERS)
    else:
        warnings.warn("Starting flexilims session without setting project_id.")
    if username is None:
        username = PARAMETERS["flexilims_username"]
    if password is None:
        password = get_password("flexilims", username)

    if reuse_token:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            token = get_password(app="flexilims", username="token", allow_input=False)
            token, date = token.split("_")
            if date != today:
                token = None
            else:
                token = dict(Authorization=f"Bearer {token}")
        except ConfigurationError:
            token = None
    else:
        token = None
    session = flm.Flexilims(username, password, project_id=project_id, token=token)
    if reuse_token:
        token = session.session.headers["Authorization"].split(" ")[-1]
        add_password("flexilims", "token", f"{token}_{today}")
    return session


def add_mouse(
    mouse_name,
    project_id=None,
    mouse_info=None,
    flexilims_session=None,
    get_mcms_data=True,
    mcms_animal_name=None,
    mcms_username=None,
    mcms_password=None,
    flexilims_username=None,
    flexilims_password=None,
):
    """Check if a mouse is already in the database and add it if it isn't

    Args:
        mouse_name (str): name of the mouse for flexilims
        project_id (str): hexadecimal project id or project name (used only if
                          flexilims_session is None)
        mouse_info (dict): a dictionary of mouse info that will be uploaded as
                           attributes. It will be used to update info from MCMS.
        flexilims_session (:py:class:`flexilims.Flexilims`): [optional] a flexilims
                          session to reuse identification token
        get_mcms_data (bool): Get the data from MCMS and add it to `mouse_info`? (
                              default True)
        mcms_animal_name (str): [optional] name of the mouse on MCMS if different from
                                flexilims name (not advised)
        mcms_username (str): [optional] username for MCMS. Will try to get it from
                             config if not provided
        mcms_password (str): [optional] password for MCMS. Will try to get it from
                             config if not provided
        flexilims_username (str): [optional] username for flexilims, used only if
                                  flexilims session is not provided
        flexilims_password (str): [optional] password for flexilims, used only if
                                  flexilims session is not provided

    Returns (dict):
        flexilims reply

    """

    if flexilims_session is None:
        flexilims_session = get_flexilims_session(
            project_id, flexilims_username, flexilims_password
        )

    mice_df = get_entities(flexilims_session=flexilims_session, datatype="mouse")
    if mouse_name in mice_df.index:
        print("Mouse already online")
        return mice_df.loc[mouse_name]

    if mouse_info is None:
        mouse_info = {}
    else:
        mouse_info = dict(mouse_info)

    if get_mcms_data:
        if mcms_username is None:
            mcms_username = PARAMETERS["mcms_username"]
        if mcms_animal_name is None:
            mcms_animal_name = mouse_name
        mcms_info = mcms.get_mouse_info(
            mouse_name=mcms_animal_name,
            username=mcms_username,
            password=mcms_password,
        )
        # flatten alleles and colony
        alleles = mcms_info.pop("alleles")
        for gene in alleles:
            gene_name = gene["allele"]["shortAlleleSymbol"].replace(" ", "_")
            mcms_info[gene_name] = gene["genotype"]["name"]
        colony = mcms_info.pop("colony")
        mcms_info["colony_prefix"] = colony["colonyPrefix"]
        if not mcms_info:
            raise IOError(f"Could not get info for mouse {mouse_name} from MCMS")
        # update mouse_info with mcms_info but prioritise mouse_info for conflicts
        mouse_info = dict(mcms_info, **mouse_info)

    # add the genealogy info, which is just [mouse_name]
    mouse_info["genealogy"] = [mouse_name]
    project_name = lookup_project(flexilims_session.project_id, PARAMETERS)
    mouse_info["path"] = str(Path(project_name) / mouse_name)
    resp = flexilims_session.post(
        datatype="mouse",
        name=mouse_name,
        attributes=mouse_info,
        strict_validation=False,
    )
    return resp


def add_experimental_session(
    date,
    flexilims_session,
    parent_name=None,
    parent_id=None,
    attributes={},
    session_name=None,
    other_relations=None,
    conflicts="abort",
):
    """Add a new session as a child entity of a mouse

    Args:
        date (str): date of the session. If `session_name` is not provided, will be
                    used as name
        flexilims_session (flexilims.Flexilims): flexilims session. Must contain project
            information.
        parent_name (str, optional): name of the parent, usually a mouse. Must exist on
            flexilims. Ignored and optional if parent_id is provided.
        parent_id (str, optional): hexadecimal id of the parent, usually a mouse. Must
            exist on flexilims. If provided, parent_name is ignored.
        attributes (dict, optional): dictionary of additional attributes
        session_name (str, optional): name of the session, usually in the shape `S20210420`.
        conflicts (str, optional): What to do if a session with that name already exists? Can be
                        `skip`, `abort`, `update` or `overwrite` (see update_entity for
                        detailed description)
        other_relations (list, optional): ID(s) of custom entities related to the session


    Returns:
        flexilims reply

    """

    if conflicts.lower() not in ("skip", "abort", "overwrite", "update"):
        raise AttributeError("conflicts must be `skip` or `abort`")

    if parent_id is None:
        assert parent_name is not None, "Must provide either parent_name or parent_id"
        parent_df = get_entity(name=parent_name, flexilims_session=flexilims_session)
        parent_id = parent_df["id"]
    else:
        parent_df = get_entity(id=parent_id, flexilims_session=flexilims_session)

    if session_name is None:
        parsed_date = re.fullmatch(r"(\d\d\d\d)-(\d\d)-(\d\d)", date)
        if parsed_date:
            session_name = "S" + "".join(parsed_date.groups())
        else:
            session_name = "S%s" % date
            warnings.warn(
                "Cannot parse date `%s`. Session name will be: `%s`"
                % (date, session_name)
            )

    session_info = {"date": date}
    if attributes is None:
        attributes = {}
    if "genealogy" in attributes:
        warnings.warn(
            "Cannot set genealogy using attributes. Will be generated from " "parent",
            stacklevel=3,
        )

    attributes["genealogy"] = list(parent_df["genealogy"]) + [session_name]

    if ("date" in attributes) and (date != attributes["date"]):
        raise FlexilimsError(
            "Got two values for date: %s and %s" % (date, attributes["date"])
        )
    if "path" not in attributes:
        attributes["path"] = str(Path(parent_df.path) / session_name)
    session_info.update(attributes)
    session_full_name = "_".join(attributes["genealogy"])
    online_session = get_entity(
        datatype="session",
        name=session_full_name,
        flexilims_session=flexilims_session,
        format_reply=False,
    )
    if online_session is not None:
        if conflicts.lower() == "skip":
            print("A session named %s already exists" % session_full_name)
            return online_session
        elif conflicts.lower() == "abort":
            raise FlexilimsError(
                "A session named %s already exists" % session_full_name
            )
        else:
            resp = update_entity(
                datatype="session",
                name=session_full_name,
                id=online_session["id"],
                origin_id=parent_id,
                mode=conflicts,
                attributes=session_info,
                other_relations=None,
                flexilims_session=flexilims_session,
            )
            return resp

    resp = flexilims_session.post(
        datatype="session",
        name=session_full_name,
        attributes=session_info,
        origin_id=parent_id,
        other_relations=other_relations,
        strict_validation=False,
    )
    return resp


def add_recording(
    session_id,
    recording_type,
    protocol,
    attributes=None,
    recording_name=None,
    conflicts="abort",
    other_relations=None,
    flexilims_session=None,
    project_id=None,
):
    """Add a recording as a child of an experimental session

    Args:
        session_id (str): hexadecimal ID of the session. Must exist on flexilims
        recording_type (str): one of [two_photon, widefield, intrinsic, ephys, behaviour]
        protocol (str): experimental protocol (`retinotopy` for instance)
        attributes (dict):  dictionary of additional attributes (on top of protocol and recording_type)
        recording_name (str or None): name of the recording, usually in the shape `R152356`.
        conflicts (str): `skip`, `abort`, `update` or `overwrite` (see update_entity for
                        detailed description)
        other_relations: ID(s) of custom entities related to the session
        flexilims_session (:py:class:`flexilims.Flexilims`): flexilims session
        project_id (str): name of the project or hexadecimal project id (needed if session is not provided)

    Returns:
        flexilims reply

    """

    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    if conflicts.lower() not in ("skip", "abort", "overwrite", "update"):
        raise AttributeError(
            "conflicts must be `skip`, `abort`, `overwrite` or `update`"
        )

    experimental_session = get_entity(
        datatype="session", flexilims_session=flexilims_session, id=session_id
    )
    recording_info = {"recording_type": recording_type, "protocol": protocol}
    if attributes is None:
        attributes = {}
    if "path" not in attributes:
        attributes["path"] = str(
            Path(
                get_path(
                    experimental_session["path"],
                    datatype="session",
                    flexilims_session=flexilims_session,
                )
            )
            / recording_name
        )
    for key in recording_info.keys():
        if (key in attributes) and (attributes[key] != locals()[key]):
            raise FlexilimsError(
                "Got two values for %s: "
                "`%s` and `%s`" % (key, attributes[key], locals()[key])
            )
    recording_info.update(attributes)

    if recording_name is None:
        recording_name = experimental_session["name"] + "_" + protocol + "_0"
    online_recording = get_entity(
        datatype="recording", name=recording_name, flexilims_session=flexilims_session
    )
    if online_recording is not None:
        if conflicts.lower() == "skip":
            print("A recording named %s already exists" % (recording_name))
            return online_recording
        elif conflicts.lower() == "abort":
            raise FlexilimsError("A recording named %s already exists" % recording_name)
        else:
            resp = update_entity(
                datatype="recording",
                name=recording_name,
                id=online_recording["id"],
                origin_id=session_id,
                mode=conflicts,
                attributes=recording_info,
                other_relations=None,
                flexilims_session=flexilims_session,
            )
            return resp

    resp = flexilims_session.post(
        datatype="recording",
        name=recording_name,
        attributes=recording_info,
        origin_id=session_id,
        other_relations=other_relations,
        strict_validation=False,
    )
    return resp


def add_entity(
    datatype,
    name,
    origin_id=None,
    attributes={},
    other_relations=None,
    flexilims_session=None,
    project_id=None,
):
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
            strict_validation=False,
        )
    except OSError as err:
        if "already exist in the project " in err.args[0]:
            raise NameNotUniqueError(err.args[0])
        raise FlexilimsError(err.args[0])
    return rep


def add_sample(
    parent_id,
    attributes=None,
    sample_name=None,
    conflicts="skip",
    other_relations=None,
    flexilims_session=None,
    project_id=None,
):
    """Add a sample as a child of a mouse or another sample

    Default conflict behaviour for samples is `skip`, as we will often add from
    the same sample multiple occasions.

    Args:
        parent_id (str): hexadecimal ID of the parent entity. Must exist on flexilims.
        attributes (dict): dictionary of additional attributes.
        sample_name (str or None): name of the sample.
        conflicts (str): `skip`, `abort`, `update` or `overwrite`: how to handle
                         conflicts.
        other_relations: ID(s) of custom entities related to the sample.
        flexilims_session (:py:class:`flexilims.Flexilims`): flexilims session.
        project_id (str): name of the project or hexadecimal project id
            (required if session is not provided).

    Returns:
        flexilims reply

    """
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    if conflicts.lower() not in ("skip", "abort", "update", "overwrite"):
        raise AttributeError("conflicts must be `skip` or `abort`")
    if attributes is None:
        attributes = {}

    parent_df = get_entity(id=parent_id, flexilims_session=flexilims_session)
    genealogy = list(parent_df["genealogy"])

    if sample_name is None:
        sample_full_name = generate_name(
            "sample",
            "_".join(genealogy + ["sample_0"]),
            flexilims_session=flexilims_session,
        )
        sample_name = sample_full_name[len(parent_df["name"]) + 1 :]

    genealogy.append(sample_name)

    if "genealogy" in attributes:
        warnings.warn(
            "Cannot set genealogy in add_sample `attributes`. It will be "
            "generated from parent genealogy",
            stacklevel=3,
        )
    attributes["genealogy"] = genealogy
    sample_full_name = "_".join(genealogy)

    if "path" not in attributes:
        attributes["path"] = str(Path(parent_df["path"]) / sample_name)

    online_sample = get_entity(
        datatype="sample",
        name=sample_full_name,
        flexilims_session=flexilims_session,
        format_reply=False,
    )
    if online_sample is not None:
        if conflicts.lower() == "skip":
            print("A sample named %s already exists" % (sample_full_name))
            return online_sample
        elif conflicts.lower() == "abort":
            raise FlexilimsError("A sample named %s already exists" % sample_full_name)
        else:
            resp = update_entity(
                datatype="sample",
                name=sample_full_name,
                id=online_sample["id"],
                origin_id=parent_df["id"],
                mode=conflicts,
                attributes=attributes,
                other_relations=None,
                flexilims_session=flexilims_session,
            )
            return resp

    resp = flexilims_session.post(
        datatype="sample",
        name=sample_full_name,
        attributes=attributes,
        origin_id=parent_df["id"],
        other_relations=other_relations,
        strict_validation=False,
    )
    return resp


def add_dataset(
    parent_id,
    dataset_type,
    created,
    path,
    genealogy,
    is_raw="yes",
    project_id=None,
    flexilims_session=None,
    dataset_name=None,
    attributes=None,
    strict_validation=False,
    conflicts="append",
):
    """Add a dataset as a child of a recording, session, or sample

    Args:
        parent_id (str): hexadecimal ID of the parent (session or recording)
        dataset_type (str): dataset_type, must be a type define in the config file
        created (str): date of creation as text, usually in this format: '2021-05-24 14:56:41'
        path (str): path to the data relative to the project folder
        genealogy (tuple): parents of this dataset from the project (excluded) down to
                           the dataset name itself (included)
        is_raw (str): `yes` or `no`, used to find the root directory
        project_id (str): hexadecimal ID or name of the project
        flexilims_session (:py:class:`flexilims.Flexilims`): authentication
            session for flexilims
        dataset_name (str): name of the dataset, will be autogenerated if not provided
        attributes (dict): optional attributes
        strict_validation (bool): default False, if True, only attributes in lab settings are
            allowed
        conflicts (str): `abort`, `skip`, `append`, `overwrite`, `update`, what to do
                         if a dataset with this name already exists? `abort` to crash,
                         `skip` to ignore and return the online version, `append` to
                         increment name and create a new dataset. `overwrite` will
                         set all existing attributes to None before updating, `update`
                         will update without clearing pre-existing attributes

    Returns:
        the flexilims response

    """
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)
    valid_conflicts = ("abort", "skip", "append", "overwrite", "update")
    if conflicts.lower() not in valid_conflicts:
        raise AttributeError("`conflicts` must be in [%s]" % ", ".join(valid_conflicts))

    if dataset_name is None:
        parent_name = get_entity(
            flexilims_session=flexilims_session,
            id=parent_id,
        )["name"]
        dataset_name = parent_name + "_" + dataset_type + "_0"

    dataset_info = {
        "dataset_type": dataset_type,
        "created": created,
        "path": path,
        "is_raw": is_raw,
        "genealogy": genealogy,
    }
    reserved_attributes = ["dataset_type", "created", "path", "is_raw", "genealogy"]
    if attributes is not None:
        for attribute in attributes:
            assert attribute not in reserved_attributes
            dataset_info[attribute] = attributes[attribute]

    if conflicts.lower() == "append":
        dataset_name = generate_name(
            "dataset", dataset_name, flexilims_session=flexilims_session
        )
    else:
        online_version = get_entity(
            "dataset", name=dataset_name, flexilims_session=flexilims_session
        )
        if online_version is not None:
            if conflicts.lower() == "abort":
                raise FlexilimsError("A dataset named %s already exists" % dataset_name)
            elif conflicts.lower() == "skip":
                print("A dataset named %s already exists" % dataset_name)
                return online_version
            else:
                resp = update_entity(
                    datatype="dataset",
                    name=dataset_name,
                    id=online_version["id"],
                    origin_id=parent_id,
                    mode=conflicts,
                    attributes=dataset_info,
                    other_relations=None,
                    flexilims_session=flexilims_session,
                )
                return resp

    resp = flexilims_session.post(
        datatype="dataset",
        name=dataset_name,
        origin_id=parent_id,
        attributes=dataset_info,
        strict_validation=strict_validation,
    )
    return resp


def update_entity(
    datatype,
    name=None,
    id=None,
    origin_id=None,
    mode="overwrite",
    attributes=None,
    other_relations=None,
    flexilims_session=None,
    project_id=None,
):
    """Update one entity identified with its datatype and name or id

    Args:
        datatype (str): flexilims type
        name (str or None): name on flexilims
        id (str or None): id of the entity on flexilims
        origin_id (str or None): hexadecimal id of the origin
        mode (str): what to do with attributes that are not explicitly specified.

            `overwrite`
                (default) all attributes that already exist on flexilims but are not
                specified in the function call are set to 'null'.
            `update`
                update the attributes given in this call and do not change the
                others.

        attributes (dict or None): attributes to update
        project_id (str): text name of the project
        flexilims_session (:py:class:`flexilims.Flexilims`): Flexylims session object

    Returns:
        flexilims reply

    """
    if attributes is None:
        attributes = {}
    assert (name is not None) or (id is not None)
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)
    entity = get_entity(
        datatype=datatype,
        name=name,
        id=id,
        flexilims_session=flexilims_session,
        format_reply=False,
    )
    if entity is None:
        err_msg = "Cannot find an entity of type `%s` named `%s`" % (datatype, name)
        raise FlexilimsError(err_msg)
    if mode.lower() == "overwrite":
        full_attributes = {k: None for k in entity["attributes"].keys()}
        full_attributes.update(attributes)
    elif mode.lower() == "update":
        full_attributes = attributes.copy()
    else:
        raise AttributeError("`mode` must be `overwrite` or `update`")
    if id is None:
        id = entity["id"]

    rep = flexilims_session.update_one(
        id=id,
        datatype=datatype,
        origin_id=origin_id,
        name=None,
        attributes=full_attributes,
        strict_validation=False,
    )
    return rep


def get_entities(
    datatype,
    query_key=None,
    query_value=None,
    project_id=None,
    flexilims_session=None,
    name=None,
    origin_id=None,
    id=None,
    format_reply=True,
):
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
        id=id,
    )
    if not format_reply:
        return results
    results = format_results(results)
    if len(results):
        results.set_index("name", drop=False, inplace=True)
    return results


def get_entity(
    datatype=None,
    query_key=None,
    query_value=None,
    project_id=None,
    flexilims_session=None,
    name=None,
    origin_id=None,
    id=None,
    format_reply=True,
):
    """
    Get one entity and format result.

    Calls :py:meth:`flexiznam.main.get_entities` but expects only one result and
    returns a :py:class:`pandas.Series` instead of a :py:class:`pandas.DataFrame`.
    If multiple entities on the database match the query, raise a
    :py:class:`flexiznam.errors.NameNotUniqueError`, if nothing matches returns `None`.

    For best performance, provide the `id` of the entity and/or the `datatype`.
    Args:
        datatype (str): type of Flexylims entity to fetch, e.g. 'mouse', 'session',
            'recording', or 'dataset'. If None, will iterate on all datatype until the
            entity is found.
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

    if datatype is None:
        if id is None:
            warnings.warn(
                "No datatype specified, trying everything. Will be slow", UserWarning
            )
        # datatype is not specify, try everything
        args = [
            datatype,
            query_key,
            query_value,
            project_id,
            flexilims_session,
            name,
            origin_id,
            id,
            format_reply,
        ]
        for dt in ("mouse", "session", "sample", "recording", "dataset"):
            args[0] = dt
            entity = get_entity(*args)
            if entity is not None:
                return entity
        return None

    entity = get_entities(
        datatype=datatype,
        query_key=query_key,
        query_value=query_value,
        project_id=project_id,
        flexilims_session=flexilims_session,
        name=name,
        origin_id=origin_id,
        id=id,
        format_reply=format_reply,
    )
    if not len(entity):
        return None
    if len(entity) != 1:
        raise NameNotUniqueError("Found %d entities, not 1" % len(entity))
    if format_reply:
        return entity.iloc[0]
    return entity[0]


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
    for datatype in PARAMETERS["datatypes"]:
        resp = get_entity(
            datatype=datatype, name=name, id=id, flexilims_session=flexilims_session
        )
        if resp:
            return datatype
    return None


def get_id(name, datatype=None, project_id=None, flexilims_session=None):
    """Get database ID for entity by name"""
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    entity = get_entity(
        datatype=datatype, flexilims_session=flexilims_session, name=name
    )
    return entity["id"]


def get_path(name, datatype="dataset", project_id=None, flexilims_session=None):
    """Get path for entity by name

    Parameters
    ----------
    name (str): name of the entity on flexilims
    datatype (str): datatype, 'mouse' or 'dataset' for instance
    project_id (str): hexadecimal project id
    flexilims_session (flm.Session): flexilims session object

    Returns
    -------
    path (str): path to the entity

    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    entity = get_entity(
        datatype=datatype, flexilims_session=flexilims_session, name=name
    )
    return entity["path"]


def get_experimental_sessions(project_id=None, flexilims_session=None, mouse=None):
    """Get all sessions from a given mouse"""
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)

    expts = format_results(flexilims_session.get(datatype="session"))

    if mouse is None:
        return expts
    else:
        mouse_id = get_id(mouse, flexilims_session=flexilims_session)
        return expts[expts["origin_id"] == mouse_id]


def get_children(
    parent_id, children_datatype=None, project_id=None, flexilims_session=None
):
    """
    Get all entries belonging to a particular parent entity

    Args:
        parent_id (str): hexadecimal id of the parent entity
        children_datatype (str or None): type of child entities to fetch (return all
                                         types if None)
        project_id (str): text name of the project
        flexilims_session (:py:class:`flexilims.Flexilims`): Flexylims session object

    Returns:
        DataFrame: containing all the relevant child entitites

    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)
    results = format_results(flexilims_session.get_children(parent_id))
    if not len(results):
        return results
    if children_datatype is not None:
        results = results.loc[results.type == children_datatype, :]
    results.set_index("name", drop=False, inplace=True)
    return results


def get_datasets(
    origin_id,
    recording_type=None,
    dataset_type=None,
    project_id=None,
    flexilims_session=None,
    return_paths=True,
):
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
        return_paths (bool): if True, return a list of paths. If False, return the
            dataset objects.

    Returns:
        dict: Dictionary with recording names as keys containing lists of associated dataset paths.

    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)
    else:
        project_id = lookup_project(flexilims_session.project_id, PARAMETERS)
    recordings = get_entities(
        datatype="recording",
        origin_id=origin_id,
        query_key="recording_type",
        query_value=recording_type,
        flexilims_session=flexilims_session,
    )
    datapath_dict = {}
    if len(recordings) < 1:
        return datapath_dict
    for recording_id in recordings["id"]:
        datasets = get_entities(
            datatype="dataset",
            origin_id=recording_id,
            query_key="dataset_type",
            query_value=dataset_type,
            flexilims_session=flexilims_session,
        )
        if return_paths:
            datapaths = []
            for dataset_path, is_raw in zip(datasets["path"], datasets["is_raw"]):
                prefix = (
                    PARAMETERS["data_root"]["raw"]
                    if is_raw == "yes"
                    else PARAMETERS["data_root"]["processed"]
                )
                this_path = Path(prefix) / dataset_path
                if this_path.exists():
                    datapaths.append(str(this_path))
                else:
                    raise IOError("Dataset {} not found".format(this_path))
                datapath_dict[recording_id] = datapaths
        else:
            datapath_dict[recording_id] = [
                flexiznam.Dataset.from_flexilims(
                    data_series=ds, flexilims_session=flexilims_session
                )
                for _, ds in datasets.iterrows()
            ]
    return datapath_dict


def generate_name(datatype, name, flexilims_session=None, project_id=None):
    """
    Generate a number for incrementally increasing the numeric suffix

    """
    assert (project_id is not None) or (flexilims_session is not None)
    if flexilims_session is None:
        flexilims_session = get_flexilims_session(project_id)
    parts = name.split("_")
    if not parts[-1].isnumeric():
        root = name + "_"
        suffix = 0
    else:
        root = "_".join(parts[:-1])
        if root:
            root += "_"
            suffix = int(parts[-1])
        else:
            root = parts[-1] + "_"
            suffix = 0
    while (
        get_entity(
            datatype, name="%s%s" % (root, suffix), flexilims_session=flexilims_session
        )
        is not None
    ):
        suffix += 1
    name = "%s%s" % (root, suffix)
    return name


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
        for attr_name, attr_value in result["attributes"].items():
            if attr_name in result:
                raise FlexilimsError(
                    "An entity should not have %s as attribute" % attr_name
                )
            result[attr_name] = attr_value
        result.pop("attributes")
    df = pd.DataFrame(results)
    return df
