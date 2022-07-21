import pathlib
from pathlib import Path, PurePosixPath

import pandas as pd
import flexiznam as flz
from flexiznam.schema import Dataset
from flexiznam.errors import FlexilimsError
from flexilims.main import SPECIAL_CHARACTERS


def compare_series(first_series, second_series, series_name=('first', 'second'),
                   tuples_as_list=True):
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
        first_series = pd.Series(data={k: v if not isinstance(v, tuple) else list(v) 
                                       for k, v in first_series.items()},
                                 name=first_series.name)
        second_series = pd.Series(data={k: v if not isinstance(v, tuple) else list(v)
                                       for k, v in second_series.items()},
                                  name=second_series.name)
    second_index = set(second_series.index)
    first_index = set(first_series.index)
    intersection = list(second_index.intersection(first_index))
    differences = first_series[intersection].compare(second_series[intersection])
    differences.columns = series_name
    only_in_first = list(first_index - second_index)
    first_s = pd.DataFrame([pd.Series({k: 'NA' for k in only_in_first},
                                      name=series_name[1], dtype='object'),
                           first_series[only_in_first].rename(series_name[0], axis=0)])
    differences = pd.concat((differences, first_s.T))
    only_in_second = list(second_index - first_index)
    second_s = pd.DataFrame([second_series[only_in_second].rename(series_name[1], axis=0),
                             pd.Series({k: 'NA' for k in only_in_second},
                                       name=series_name[0], dtype='object')])
    differences = pd.concat((differences, second_s.T))
    return differences


def clean_dictionary_recursively(dictionary, keys=(), path2string=True,
                                 format_dataset=False, tuple_as_list=False):
    """Recursively clean a dictionary inplace

    Args:
        dictionary: dict (of dict)
        keys (list): list of keys to pop from the dictionary
        path2string (bool): replace :py:class:`pathlib.Path` object by their
            string representation (default True)
        format_dataset (bool): replace :py:class:`flexiznam.schema.Dataset`
            instances by their yaml representation (default False)
        tuple_as_list (bool): replace tuples by list (default False)
    """

    if isinstance(keys, str):
        keys = [keys]
    for k in keys:
        dictionary.pop(k, None)
    if format_dataset:
        ds_classes = set(Dataset.SUBCLASSES.values())
        ds_classes.add(Dataset)
    for k, v in dictionary.items():
        if isinstance(v, dict):
            clean_dictionary_recursively(v, keys, path2string, format_dataset,
                                         tuple_as_list)
        if path2string and isinstance(v, pathlib.Path):
            dictionary[k] = str(PurePosixPath(v))
        if tuple_as_list and isinstance(v, tuple):
            dictionary[k] = list(v)
        if format_dataset:
            if any([isinstance(v, cls) for cls in ds_classes]):
                ds_dict = v.format(mode='yaml')
                # we have now a dictionary with a flat structure. Reshape it to match
                # what acquisition yaml are supposed to look like
                for field in ['name', 'project', 'type']:
                    ds_dict.pop(field, None)

                # rename extra_attributes to match acquisition yaml.
                # Making a copy with dict is required to write yaml later on. If I keep
                # the reference the output file has `*id001` instead of `{}`
                ds_dict['attributes'] = dict(ds_dict.pop('extra_attributes', {}))
                ds_dict['path'] = str(PurePosixPath(Path(ds_dict['path'])))
                clean_dictionary_recursively(ds_dict, path2string=path2string,
                                             tuple_as_list=tuple_as_list)
                dictionary[k] = ds_dict


def check_flexilims_paths(flexilims_session, root_name=None, recursive=True,
                          error_only=True):
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
        to_check = flz.get_entities(flexilims_session=flexilims_session, datatype='mouse')
        to_check = [c for _, c in to_check.iterrows()]  # make a list to match get_entity
    else:
        to_check = [flz.get_entity(name=root_name, flexilims_session=flexilims_session)]
    output = []
    for element in to_check:
        _check_path(output, element, flexilims_session=flexilims_session,
                    recursive=recursive, error_only=error_only)
    # format output
    output = pd.DataFrame(columns=['name', 'datatype', 'msg', 'info', 'is_error'],
                          data=output)
    if error_only:
        output = output[['name', 'datatype', 'msg', 'info']]
    return output


def _check_path(output, element, flexilims_session, recursive, error_only):
    """Subfunction to recurse path checking"""
    if 'path' not in element:
        output.append([element.name, element.type, 'path not defined', '', 1])
    elif not isinstance(element.path, str):
        output.append([element.name, element.type, 'Path is not a string!', element.path,
                       1])
    elif element.type != 'dataset':
        ok = []
        for k, v in flz.PARAMETERS['data_root'].items():
            if (Path(v) / element.path).is_dir():
                ok.append(v)
        if not len(ok):
            output.append([element.name, element.type, 'folder does not exist', '', 1])
        elif not error_only:
            output.append([element.name, element.type, 'Folder found', ' '.join(ok), 0])
    else:
        ds = Dataset.from_flexilims(flexilims_session=flexilims_session,
                                    data_series=element)
        if not ds.path_full.exists():
            output.append([element.name, element.type, 'dataset path unvalid',
                           ds.path_full, 1])
        elif not error_only:
            output.append([element.name, element.type, 'Data found', ds.path_full, 0])
    if recursive:
        children = flz.get_children(element.id, flexilims_session=flexilims_session)
        for _, child in children.iterrows():
            _check_path(output, child, flexilims_session, recursive, error_only)


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
        to_check = flz.get_entities(flexilims_session=flexilims_session, datatype='mouse')
        to_check = [c for _, c in to_check.iterrows()]  # make a list to match get_entity
    else:
        to_check = [flz.get_entity(name=root_name, flexilims_session=flexilims_session)]
    output = []
    for element in to_check:
        _check_name(output, element, flexilims_session, parent_name=None,
                    recursive=recursive)
    if not len(output):
        return None
    return pd.DataFrame(data=output, columns=['name', 'parent_name'])


def _check_name(output, element, flexilims_session, parent_name, recursive):
    if (parent_name is not None) and not element.name.startswith(parent_name):
        output.append([element.name, parent_name])
    parent_name = element.name
    if recursive:
        children = flz.get_children(element.id, flexilims_session=flexilims_session)
        for _, child in children.iterrows():
            _check_name(output, child, flexilims_session, parent_name, recursive)


def add_genealogy(flexilims_session, root_name=None, recursive=False, added=None):
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
    Returns:
        list of entity names for which genealogy was added
    """
    if added is None:
        added = []
    ok = check_flexilims_names(flexilims_session=flexilims_session, root_name=root_name,
                               recursive=recursive)
    if ok is not None:
        raise IOError('check_flexilims_names must return None to add genealogy')

    if root_name is None:
        to_check = flz.get_entities(flexilims_session=flexilims_session, datatype='mouse')
        to_check = [c for _, c in to_check.iterrows()]  # make a list to match get_entity
    else:
        to_check = [flz.get_entity(name=root_name, flexilims_session=flexilims_session)]

    for element in to_check:
        entity = flz.get_entity(datatype=element.type, name=element['name'],
                                flexilims_session=flexilims_session)
        parent = entity
        parts = [parent['name']]
        while ('origin_id' in parent) and (parent.origin_id is not None):
            parent = flz.get_entity(id=parent.origin_id,
                                    flexilims_session=flexilims_session)
            parts.append(parent['name'])
        # transform parts in genealogy by cutting begining
        parts = parts[::-1]
        cut = ''
        for i, part in enumerate(parts):
            parts[i] = part.replace(cut, '')
            cut = part + '_'

        if 'genealogy' in entity:
            if entity.genealogy != parts:
                raise FlexilimsError('%s genealogy does not match database: "%s" vs '
                                     '"%s"' % (entity.name, parts, entity.genealogy))
            else:
                pass
        else:
            flz.update_entity(entity.type, flexilims_session=flexilims_session,
                              id=entity.id, mode='update',
                              attributes=dict(genealogy=parts))
            added.append(entity.name)
        if recursive:
            children = flz.get_children(entity.id, flexilims_session=flexilims_session)
            for _, child in children.iterrows():
                add_genealogy(flexilims_session, root_name=child.name,
                              recursive=recursive, added=added)
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
    df = df.loc[df.datatype != 'dataset', :]
    df = df.loc[df.msg == 'path not defined', :]

    for _, element in df.iterrows():
        entity = flz.get_entity(datatype=element.datatype, name=element['name'],
                                flexilims_session=flexilims_session)
        project = flz.main._lookup_project(prm=flz.PARAMETERS, project_id=entity.project)
        if 'genealogy' not in entity:
            raise FlexilimsError('Attribute genealogy not defined for %s', entity['name'])
        path = Path(project, *entity.genealogy)
        exist = any([Path(p) / path for p in flz.PARAMETERS['data_root'].values()])
        if not exist:
            raise IOError('No folder corresponding to path exists: %s' % path)
        flz.update_entity(datatype=entity.type, mode='update', id=entity.id,
                          flexilims_session=flexilims_session,
                          attributes=dict(path=str(path)))


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
        proj_id = project['id']
        proj_name = project['name']
        flexilims_session.project_id = proj_id
        for datatype in flz.PARAMETERS['datatypes']:
            data = flexilims_session.get(datatype=datatype, project_id=proj_id)
            for d in data:
                for attr in d['attributes']:
                    if (not attr.islower()) or (r'\s' in attr) or \
                            (SPECIAL_CHARACTERS.search(attr) is not None):
                        report.append([proj_name, d['name'], attr])

    return pd.DataFrame(data=report, columns=['project', 'entity', 'attribute'])
