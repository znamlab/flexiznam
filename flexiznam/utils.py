import pathlib
from pathlib import Path, PurePosixPath
import re
import numpy as np
import pandas as pd
import warnings

SPECIAL_CHARACTERS = re.compile(r'[\',@"+=\-!#$%^&*<>?/\|}{~:]')

import flexiznam as flz
from flexiznam.errors import FlexilimsError, DatasetError
from flexiznam.schema import Dataset


def compare_series(
    first_series, second_series, series_name=("first", "second"), tuples_as_list=True
):
    """Compare two series and return a dataframe of differences

    Args:
        first_series: first :py:class:`pandas.Series`
        second_series: second :py:class:`pandas.Series`
        series_name: tuple of name for the two series.
        tuples_as_list (bool): should tuples be compared as string (True by
                               default, useful as flexilims does not allow for tuples)

    Returns:
        :py:class:`pandas.DataFrame`: DataFrame of differences
    """
    if tuples_as_list:
        first_series = pd.Series(
            data={
                k: v if not isinstance(v, tuple) else list(v)
                for k, v in first_series.items()
            },
            name=first_series.name,
        )
        second_series = pd.Series(
            data={
                k: v if not isinstance(v, tuple) else list(v)
                for k, v in second_series.items()
            },
            name=second_series.name,
        )
    second_index = set(second_series.index)
    first_index = set(first_series.index)
    intersection = list(second_index.intersection(first_index))
    differences = first_series[intersection].compare(second_series[intersection])
    differences.columns = series_name
    only_in_first = list(first_index - second_index)
    first_s = pd.DataFrame(
        [
            pd.Series(
                {k: "NA" for k in only_in_first}, name=series_name[1], dtype="object"
            ),
            first_series[only_in_first].rename(series_name[0], axis=0),
        ]
    )
    differences = pd.concat((differences, first_s.T))
    only_in_second = list(second_index - first_index)
    second_s = pd.DataFrame(
        [
            second_series[only_in_second].rename(series_name[1], axis=0),
            pd.Series(
                {k: "NA" for k in only_in_second}, name=series_name[0], dtype="object"
            ),
        ]
    )
    differences = pd.concat((differences, second_s.T))
    return differences


def compare_dictionaries_recursively(first_dict, second_dict, output=None):
    """Compare two dictionnaries recursively

    Will return a dictionnary with only fields that have are different

    Args:
        first_dict (dict): First dictionary
        second_dict (dict): Second dictionary
        output (dict, optional): Output used for recursion. Defaults to None.
    """
    if output is None:
        output = dict()

    if first_dict == second_dict:
        return output

    diff_keys = [k for k in second_dict if k not in first_dict]
    for k in diff_keys:
        output[k] = ("NOT PRESENT", second_dict[k])
    diff_keys = [k for k in first_dict if k not in second_dict]
    for k in diff_keys:
        output[k] = (first_dict[k], "NOT PRESENT")

    for k in first_dict:
        if k in diff_keys:
            continue
        elif first_dict[k] == second_dict[k]:
            continue
        fv = first_dict[k]
        sv = second_dict[k]
        if isinstance(fv, dict) and isinstance(sv, dict):
            output[k] = dict()
            compare_dictionaries_recursively(fv, sv, output[k])
        else:
            output[k] = (fv, sv)

    return output


def clean_recursively(
    element,
    keys=(),
    json_compatible=True,
    format_dataset=False,
):
    """Recursively clean inplace to make json compatible

    Args:
        element (any): Typically a dict of dict to clean, but can be any object that
            needs to be made json compatible
        keys (list): list of keys to pop from the dictionary
        json_compatible (bool): make the dictionary json compatible (default True)
        format_dataset (bool): replace :py:class:`flexiznam.schema.Dataset`
            instances by their yaml representation (default False)
    """
    if isinstance(keys, str):
        keys = [keys]

    # handle dictionaries and first recursion
    if isinstance(element, dict):
        for k in keys:
            element.pop(k, None)
        for k in list(element.keys()):
            v = element[k]
            if json_compatible:
                if SPECIAL_CHARACTERS.search(k) is not None:
                    new_key = re.sub(SPECIAL_CHARACTERS, "_", k)
                    print(
                        f"Warning: key `{k}` contains special characters and is "
                        + f"unvalid JSON. Will use {new_key} instead"
                    )
                    element[new_key] = element.pop(k)
                    k = new_key
            element[k] = clean_recursively(v, keys, json_compatible, format_dataset)
        return element

    if json_compatible:
        # we don't have a dictionary
        ds_classes = set(Dataset.SUBCLASSES.values())
        ds_classes.add(Dataset)
        floats = (float, np.float32, np.float64)
        ints = (int, np.int32, np.int64)
        if (
            (element is None)
            or isinstance(element, str)
            or isinstance(element, int)
            or isinstance(element, bool)
            or isinstance(element, list)
            or any([isinstance(element, cls) for cls in ds_classes])
        ):
            pass
        elif isinstance(element, tuple):
            element = list(element)
        elif isinstance(element, np.ndarray):
            element = element.tolist()
        elif isinstance(element, pathlib.Path):
            element = str(PurePosixPath(element))
        elif isinstance(element, floats):
            if not np.isfinite(element):
                # nan and inf must be uploaded as string
                element = str(element)
            else:
                element = float(element)
        elif isinstance(element, ints):
            element = int(element)
        elif isinstance(element, pd.Series or pd.DataFrame):
            raise IOError("Cannot make a pandas object json compatible")
        else:
            warnings.warn(
                f"{element} has unknown type ({type(element)}). Will save as string"
            )
            element = str(element)

    if isinstance(element, list):
        for i, v in enumerate(element):
            element[i] = clean_recursively(v, keys, json_compatible, format_dataset)

    if format_dataset:
        ds_classes = set(Dataset.SUBCLASSES.values())
        ds_classes.add(Dataset)
        if any([isinstance(element, cls) for cls in ds_classes]):
            ds_dict = element.format(mode="yaml")
            # we have now a dictionary with a flat structure. Reshape it to match
            # what acquisition yaml are supposed to look like
            for field in ["name", "project", "type"]:
                ds_dict.pop(field, None)

            # rename extra_attributes to match acquisition yaml.
            # Making a copy with dict is required to write yaml later on. If I keep
            # the reference the output file has `*id001` instead of `{}`
            ds_dict["attributes"] = dict(ds_dict.pop("extra_attributes", {}))
            ds_dict["path"] = str(PurePosixPath(Path(ds_dict["path"])))
            ds_dict = clean_recursively(ds_dict, keys, json_compatible, format_dataset)
            element = ds_dict
    return element


def check_flexilims_paths(
    flexilims_session, root_name=None, recursive=True, error_only=True
):
    """Check that paths defined on flexilims exist

    For datasets, check that the exact path exists, for the rest check if either `raw` or
    `process` path exist (as mouse, sample etc can be found in both or either folder).

    Args:
        flexilims_session (flm.Session): flexilims session object, must define project
        root_name (str): optional, name of entity to check. If not provided, will check
                         all mice.
        recursive (bool): Check recursively all children (default True)
        error_only (bool): Return only issue (default True). Otherwise list valid paths

    Returns:
        error_df (pd.DataFrame): list of unvalid paths

    """

    if root_name is None:
        to_check = flz.get_entities(
            flexilims_session=flexilims_session, datatype="mouse"
        )
        to_check = [
            c for _, c in to_check.iterrows()
        ]  # make a list to match get_entity
    else:
        to_check = [flz.get_entity(name=root_name, flexilims_session=flexilims_session)]
    output = []
    for element in to_check:
        _check_path(
            output,
            element,
            flexilims_session=flexilims_session,
            recursive=recursive,
            error_only=error_only,
        )
    # format output
    output = pd.DataFrame(
        columns=["name", "datatype", "msg", "info", "is_error"], data=output
    )
    if error_only:
        output = output[["name", "datatype", "msg", "info"]]
    return output


def check_flexilims_names(flexilims_session, root_name=None, recursive=True):
    """Check that names defined on flexilims match the hierarchy

    This will verify that the name of each entity starts with the names of all its
    parent separated by underscores.

    Args:
        flexilims_session (flm.Session): flexilims session object, must define project
        root_name (str): optional, name of entity to check. If not provided, will check
                         all mice.
        recursive (bool): test recursively on children (default True)

    Returns:
        error_df (pd.DataFrame): list of invalid paths

    """
    if root_name is None:
        to_check = flz.get_entities(
            flexilims_session=flexilims_session, datatype="mouse"
        )
        to_check = [
            c for _, c in to_check.iterrows()
        ]  # make a list to match get_entity
    else:
        to_check = [flz.get_entity(name=root_name, flexilims_session=flexilims_session)]
    output = []
    for element in to_check:
        _check_name(
            output, element, flexilims_session, parent_name=None, recursive=recursive
        )
    if not len(output):
        return None
    return pd.DataFrame(data=output, columns=["name", "parent_name"])


def add_genealogy(
    flexilims_session, root_name=None, recursive=False, added=None, verbose=True
):
    """Add genealogy info to properly named sections of database

    If the names of all entries are as expected (check_flexilims_names return None),
    one can get the hierarchy (mouse, session, recording for instance) from the names.
    This function does that and add it to flexilims in the "genealogy" attribute

    Args:
        flexilims_session (flm.Session): flexilims session object, must define project
        root_name (str): optional, name of entity to check. If not provided, will check
                         all mice.
        recursive (bool): do recursively on children (default False)
        added (None): holder for recursion. Do not use
        verbose (bool,optional): show progress. Default True.
    Returns:
        list of entity names for which genealogy was added
    """
    if added is None:
        added = []
        ok = check_flexilims_names(
            flexilims_session=flexilims_session,
            root_name=root_name,
            recursive=recursive,
        )
        if ok is not None:
            raise IOError("check_flexilims_names must return None to add genealogy")

    if root_name is None:
        to_check = flz.get_entities(
            flexilims_session=flexilims_session, datatype="mouse"
        )
        to_check = [
            c for _, c in to_check.iterrows()
        ]  # make a list to match get_entity
    else:
        to_check = [flz.get_entity(name=root_name, flexilims_session=flexilims_session)]

    for element in to_check:
        entity = flz.get_entity(
            datatype=element.type,
            name=element["name"],
            flexilims_session=flexilims_session,
        )
        parent = entity
        parts = [parent["name"]]
        while ("origin_id" in parent) and (parent.origin_id is not None):
            parent = flz.get_entity(
                id=parent.origin_id, flexilims_session=flexilims_session
            )
            parts.append(parent["name"])
        parts = parts[::-1]
        cut = ""
        # transform parts in genealogy by cutting begining
        for i, part in enumerate(parts):
            parts[i] = part[len(cut) :]
            cut = part + "_"

        if "genealogy" in entity and isinstance(entity.genealogy, list):
            if entity.genealogy != parts:
                raise FlexilimsError(
                    '%s genealogy does not match database: "%s" vs '
                    '"%s"' % (entity.name, parts, entity.genealogy)
                )
            else:
                pass
        else:
            if verbose:
                print(f"Updating {entity.name}", flush=True)
            flz.update_entity(
                entity.type,
                flexilims_session=flexilims_session,
                id=entity.id,
                mode="update",
                attributes=dict(genealogy=parts),
            )
            added.append(entity.name)
        if recursive:
            children = flz.get_children(entity.id, flexilims_session=flexilims_session)
            for _, child in children.iterrows():
                add_genealogy(
                    flexilims_session,
                    root_name=child.name,
                    recursive=recursive,
                    added=added,
                )
    return added


def add_missing_paths(flexilims_session, root_name=None):
    """Add paths to non dataset entities

    Datasets MUST have a path. If they don't, it needs to be fixed manually. Other
    entities can have a path. This function will add it if it is not defined and if the
    genealogy is already set (see add_genealogy)
    The path will be set to parent_path/entity_name if this folder exists either in the
    raw or processed folder

    Args:
        flexilims_session (flm.Session): flexilims session object, must define project
        root_name (str): optional, name of entity to check. If not provided, will check
                         all mice.
    """

    df = check_flexilims_paths(flexilims_session, root_name)
    # exclude datasets
    df = df.loc[df.datatype != "dataset", :]
    df = df.loc[df.msg == "path not defined", :]

    for _, element in df.iterrows():
        entity = flz.get_entity(
            datatype=element.datatype,
            name=element["name"],
            flexilims_session=flexilims_session,
        )
        project = flz.main.lookup_project(prm=flz.PARAMETERS, project_id=entity.project)
        if "genealogy" not in entity:
            raise FlexilimsError(
                "Attribute genealogy not defined for %s", entity["name"]
            )
        path = Path(project, *entity.genealogy)
        exist = any([Path(p) / path for p in flz.PARAMETERS["data_root"].values()])
        if not exist:
            raise IOError("No folder corresponding to path exists: %s" % path)
        flz.update_entity(
            datatype=entity.type,
            mode="update",
            id=entity.id,
            flexilims_session=flexilims_session,
            attributes=dict(path=str(path)),
        )


def _check_attribute_case(flexilims_session):
    """House cleaning function

    Iterates on projects and check that all attributes are lower case

    Args:
        flexilims_session: a flexilims session for authentication

    Returns:
        bad_attr (pd.DataFrame): a dataframe of bad attributes and their parent name
    """
    projects = flexilims_session.get_project_info()
    report = []
    for project in projects:
        proj_id = project["id"]
        proj_name = project["name"]
        flexilims_session.project_id = proj_id
        for datatype in flz.PARAMETERS["datatypes"]:
            data = flexilims_session.get(datatype=datatype, project_id=proj_id)
            for d in data:
                for attr in d["attributes"]:
                    if (
                        (not attr.islower())
                        or (r"\s" in attr)
                        or (SPECIAL_CHARACTERS.search(attr) is not None)
                    ):
                        report.append([proj_name, d["name"], attr])

    return pd.DataFrame(data=report, columns=["project", "entity", "attribute"])


def _check_path(output, element, flexilims_session, recursive, error_only):
    """Subfunction to recurse path checking"""
    if "path" not in element:
        output.append([element.name, element.type, "path not defined", "", 1])
    elif not isinstance(element.path, str):
        output.append(
            [element.name, element.type, "Path is not a string!", element.path, 1]
        )
    elif element.type != "dataset":
        ok = []
        for k, v in flz.PARAMETERS["data_root"].items():
            if (Path(v) / element.path).is_dir():
                ok.append(v)
        if not len(ok):
            output.append([element.name, element.type, "folder does not exist", "", 1])
        elif not error_only:
            output.append([element.name, element.type, "Folder found", " ".join(ok), 0])
    else:
        try:
            ds = Dataset.from_dataseries(
                flexilims_session=flexilims_session, dataseries=element
            )
            if not ds.path_full.exists():
                output.append(
                    [
                        element.name,
                        element.type,
                        "dataset path unvalid",
                        ds.path_full,
                        1,
                    ]
                )
            elif not error_only:
                output.append(
                    [element.name, element.type, "Data found", ds.path_full, 0]
                )
        except OSError as err:
            output.append(
                [
                    element.name,
                    element.type,
                    "Cannot create dataset from flexilims",
                    str(err),
                    0,
                ]
            )
        except DatasetError as err:
            output.append(
                [
                    element.name,
                    element.type,
                    "Genealogy might not be set",
                    str(err),
                    0,
                ]
            )
    if recursive:
        children = flz.get_children(element.id, flexilims_session=flexilims_session)
        for _, child in children.iterrows():
            _check_path(output, child, flexilims_session, recursive, error_only)


def _check_name(output, element, flexilims_session, parent_name, recursive):
    if (parent_name is not None) and not element.name.startswith(parent_name):
        output.append([element.name, parent_name])
    parent_name = element.name
    if recursive:
        children = flz.get_children(element.id, flexilims_session=flexilims_session)
        for _, child in children.iterrows():
            _check_name(output, child, flexilims_session, parent_name, recursive)
