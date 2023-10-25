"""File to handle acquisition yaml file and create datasets on flexilims"""
import os
import pathlib
from pathlib import Path, PurePosixPath
import re
import copy
import warnings
import pandas as pd
import yaml
from yaml.parser import ParserError

import flexiznam as flz
from flexiznam.errors import SyncYmlError, FlexilimsError
from flexiznam.schema import Dataset
from flexiznam.config import PARAMETERS
from flexiznam.utils import clean_recursively


def create_yaml(folder_to_parse, project, origin_name, output_file, overwrite=False):
    """Create a yaml file from a folder

    Args:
        folder_to_parse (str): Folder to parse
        project (str): Name of the project
        origin_name (str): Name of the origin on flexilims
        output_file (str): Full path to output yaml.
        overwrite (bool, optional): Overwrite output file if it exists. Defaults to False.
    """
    output_file = pathlib.Path(output_file)
    if (not overwrite) and output_file.exists():
        s = input("File %s already exists. Overwrite (yes/[no])? " % output_file)
        if s == "yes":
            overwrite = True
        else:
            raise (
                FileExistsError(
                    "File %s already exists and overwrite is not allowed" % output_file
                )
            )
    folder_to_parse = pathlib.Path(folder_to_parse)
    if not folder_to_parse.is_dir():
        raise FileNotFoundError("source_dir %s is not a directory" % folder_to_parse)

    data = create_yaml_dict(folder_to_parse, project, origin_name)
    with open(output_file, "w") as f:
        yaml.dump(data, f)


def create_yaml_dict(
    folder_to_parse,
    project,
    origin_name,
    format_yaml=True,
):
    """Create a yaml dict from a folder

    Recursively parse a folder and create a yaml dict with the structure of the folder.

    Args:
        folder_to_parse (str): Path to the folder to parse
        project (str): Name of the project, used as root of the path in the output
        origin_name (str): Name of the origin on flexilims. Must be online and have
            genealogy set.
        format_yaml (bool, optional): Format the output to be yaml compatible if True,
            otherwise keep dataset as Dataset object and path as pathlib.Path. Defaults
            to True.

    Returns:
        dict: Dictionary with the structure of the folder and automatically detected
            datasets
    """
    flm_sess = flz.get_flexilims_session(project_id=project)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        origin = flz.get_entity(name=origin_name, flexilims_session=flm_sess)
    assert origin is not None, f"Origin {origin_name} not found in project {project}"
    assert "genealogy" in origin, f"Origin {origin_name} has no genealogy"
    genealogy = origin["genealogy"]
    folder_to_parse = Path(folder_to_parse)
    assert folder_to_parse.is_dir(), f"Folder {folder_to_parse} does not exist"

    data = _create_yaml_dict(
        level_folder=folder_to_parse,
        project=project,
        genealogy=genealogy,
        format_yaml=format_yaml,
        parent_dict=dict(),
    )
    if format_yaml:
        root_folder = str(folder_to_parse.parent)
    else:
        root_folder = folder_to_parse.parent
    out = dict(
        root_folder=root_folder,
        origin_name=origin_name,
        children=data,
        project=project,
    )
    return out


def parse_yaml(
    yaml_data,
    root_folder=None,
    origin_name=None,
    project=None,
    format_yaml=True,
):
    """Parse a yaml file and check validity

    This will add datasets to each existing levels of the yaml, but won't create
    nested levels

    Args:
        yaml_file (str): path to the yaml file (or data as dict)
        root_folder (str): path to the root folder. If not provided, will be read from
            the yaml file. This is the folder that contains the main folder, so "mouse"
            for a  "session".
        origin_name (str): name of the origin on flexilims. If not provided, will be
            read from the yaml file
        project (str): name of the project. If not provided, will be read from the yaml
            file
        format_yaml (bool, optional): Format the output to be yaml compatible if True,
            otherwise keep dataset as Dataset object and path as pathlib.Path. Defaults
            to True.
    Returns
        dict: yaml dict with datasets added
    """
    if isinstance(yaml_data, str) or isinstance(yaml_data, Path):
        with open(yaml_data, "r") as f:
            yaml_data = yaml.safe_load(f)

    if root_folder is None:
        root_folder = Path(yaml_data["root_folder"])
    assert root_folder.is_dir(), f"Folder {root_folder} does not exist"

    if project is None:
        project = yaml_data["project"]
    flm_sess = flz.get_flexilims_session(project_id=project)

    if origin_name is None:
        origin_name = yaml_data["origin_name"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        origin = flz.get_entity(name=origin_name, flexilims_session=flm_sess)
    assert origin is not None, f"Origin {origin_name} not found in project {project}"
    assert "genealogy" in origin, f"Origin {origin_name} has no genealogy"
    genealogy = origin["genealogy"]

    assert len(yaml_data["children"]) == 1, "Parsing only one folder is allowed"
    child = list(yaml_data["children"].keys())[0]
    data = _create_yaml_dict(
        level_folder=root_folder / child,
        project=project,
        genealogy=genealogy,
        format_yaml=format_yaml,
        parent_dict=yaml_data["children"],
        only_datasets=True,
    )
    if format_yaml:
        root_folder = str(root_folder)
    out = dict(
        root_folder=root_folder,
        origin_name=origin_name,
        children=data,
        project=project,
    )
    yaml_data, errors = check_yaml_validity(
        yaml_data, root_folder, origin_name, project
    )

    return out


def check_yaml_validity(yaml_data, root_folder=None, origin_name=None, project=None):
    """Check that a yaml file is valid

    This will check that the genealogy is correct, that the datasets are valid and
    that the folder structure is correct

    Args:
        yaml_file (str): path to the yaml file (or data as dict)
        root_folder (str): path to the root folder. If not provided, will be read from
            the yaml file. This is the folder that contains the main folder, so "mouse"
            for a  "session".
        origin_name (str): name of the origin on flexilims. If not provided, will be
            read from the yaml file
        project (str): name of the project. If not provided, will be read from the yaml
            file

    Returns:
        dict: same as input yaml_data, but with errors added
    """
    if isinstance(yaml_data, str) or isinstance(yaml_data, Path):
        with open(yaml_data, "r") as f:
            yaml_data = yaml.safe_load(f)
    if root_folder is not None:
        assert yaml_data["root_folder"] == str(
            root_folder
        ), f"root_folder is {yaml_data['root_folder']}. Expected {root_folder}"
    else:
        root_folder = yaml_data["root_folder"]

    if project is not None:
        assert (
            yaml_data["project"] == project
        ), f"project is {yaml_data['project']}. Expected {project}"
    else:
        project = yaml_data["project"]

    if origin_name is not None:
        assert (
            yaml_data["origin_name"] == origin_name
        ), f"origin_name is {yaml_data['origin_name']}. Expected {origin_name}"
    else:
        origin_name = yaml_data["origin_name"]

    flm_sess = flz.get_flexilims_session(project_id=project)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        origin = flz.get_entity(name=origin_name, flexilims_session=flm_sess)
    assert hasattr(origin, "genealogy"), f"Origin {origin_name} has no genealogy"

    errors = _check_recursively(
        yaml_data["children"],
        origin_genealogy=origin["genealogy"],
        root_folder=root_folder,
        project=project,
        genealogy=[],
    )
    return yaml_data, errors


def upload_yaml(
    source_yaml,
    raw_data_folder=None,
    verbose=False,
    log_func=print,
    flexilims_session=None,
    conflicts="abort",
):
    """Upload data from one yaml to flexilims

    Args:
        source_yaml (dict or str): path to clean yaml or yaml dict
        raw_data_folder (str): path to the folder containing the data. Default to
            data_root['raw']
        verbose (bool): print progress information
        log_func: function to deal with warnings and messages
        flexilims_session (Flexilims): session to avoid recreating a token
        conflicts (str): `abort` to crash if there is already a session or recording
                         existing on flexilims, `skip` to ignore and proceed. Samples
                         are always updated with `skip` and datasets always have
                         mode=`safe`

    Returns:
        list of names of entities created/updated

    """
    if isinstance(source_yaml, str) or isinstance(source_yaml, Path):
        source_yaml = Path(source_yaml)
        with open(source_yaml, "r") as f:
            yaml_data = yaml.safe_load(f)
    else:
        assert isinstance(source_yaml, dict), "source_yaml must be a dict or a path"
        yaml_data = source_yaml

    # first find the origin

    if flexilims_session is None:
        flexilims_session = flz.get_flexilims_session(project_id=yaml_data["project"])

    origin_name = yaml_data["origin_name"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        origin = flz.get_entity(name=origin_name, flexilims_session=flexilims_session)
    assert origin is not None, f"`{origin_name}` not found on flexilims"
    if verbose:
        print(f"Found origin `{origin_name}` with id `{origin.id}`")
    # then upload the data recursively
    _upload_yaml_dict(
        yaml_data["children"],
        origin=origin,
        raw_data_folder=raw_data_folder,
        log_func=log_func,
        flexilims_session=flexilims_session,
        conflicts=conflicts,
        verbose=verbose,
    )


def _create_yaml_dict(
    level_folder,
    project,
    genealogy,
    format_yaml,
    parent_dict,
    only_datasets=False,
):
    """Private function to create a yaml dict from a folder

    Add a private function to hide the arguments that are used only for recursion
    (parent_dict)

    See `create_yaml_dict` for documentation

    Args:
        level_folder (Path): folder to parse
        project (str): name of the project
        genealogy (tuple): genealogy of the current folder
        format_yaml (bool): format results to be yaml compatible or keep Dataset
            and pathlib.Path objects
        parent_dict (dict): dict of the parent folder. Used for recursion
        only_datasets (bool): only parse datasets, not folders
    """

    level_folder = Path(level_folder)
    assert level_folder.is_dir(), "root_folder must be a directory"
    level_name = level_folder.name
    if level_name in parent_dict:
        level_dict = parent_dict[level_name]
        if level_dict is None:
            level_dict = dict()
    else:
        level_dict = dict()
    genealogy = list(genealogy)

    m = re.fullmatch(r"R\d\d\d\d\d\d_?(.*)?", level_name)
    if m:
        if "type" in level_dict:
            assert (
                level_dict["type"] == "recording"
            ), "Conflicting types, expected recording"
        else:
            level_dict["type"] = "recording"
        if "protocol" not in level_dict:
            level_dict["protocol"] = (
                m[1] if m[1] is not None else "XXERRORXX PROTOCOL NOT SPECIFIED"
            )
        if "recording_type" not in level_dict:
            if "camera" in level_dict["protocol"]:
                level_dict["recording_type"] = "camera"
            elif "onix" in level_dict["protocol"]:
                level_dict["recording_type"] = "ephys"
            elif "harp" in level_dict["protocol"]:
                level_dict["recording_type"] = "behaviour"
            else:
                level_dict["recording_type"] = "NOT SPECIFIED"
    elif re.fullmatch(r"S\d*", level_name):
        if "type" in level_dict:
            assert (
                level_dict["type"] == "session"
            ), "Conflicting types, expected session"
        else:
            level_dict["type"] = "session"
    else:
        if "type" not in level_dict:
            level_dict["type"] = "sample"
    if "genealogy" in level_dict:
        assert level_dict["genealogy"] == genealogy + [
            level_name
        ], f"Conflicting genealogy for {level_name}"
    else:
        level_dict["genealogy"] = genealogy + [level_name]
    if "path" not in level_dict:
        level_dict["path"] = Path(project, *level_dict["genealogy"])
    if format_yaml:
        level_dict["path"] = str(PurePosixPath(level_dict["path"]))
    children = dict() if "children" not in level_dict else level_dict["children"]
    datasets = Dataset.from_folder(level_folder)
    if datasets:
        for ds_name, ds in datasets.items():
            if ds_name in children:
                warnings.warn(f"Dataset {ds_name} already exists in {level_name}. Skip")
                continue
            ds.genealogy = genealogy + list(ds.genealogy)
            if format_yaml:
                # find path root
                proot = str(level_folder)[: -len(level_dict["path"])]
                ds.path = ds.path.relative_to(proot)
                children[ds_name] = ds.format(mode="yaml")
                # remove fields that are not needed
                for field in ["origin_id", "project_id", "name"]:
                    children[ds_name].pop(field, None)
                children[ds_name]["path"] = str(
                    PurePosixPath(children[ds_name]["path"])
                )
            else:
                children[ds_name] = ds

    if only_datasets:
        subfolders = [
            level_folder / n
            for n, c in children.items()
            if (c is None) or (c.get("type", "unknown") != "dataset")
        ]
    else:
        subfolders = level_folder.glob("*")

    for child in subfolders:
        if child.is_dir():
            _create_yaml_dict(
                child,
                project=project,
                genealogy=genealogy + [level_name],
                format_yaml=format_yaml,
                parent_dict=children,
            )
    level_dict["children"] = children
    parent_dict[level_name] = level_dict
    return parent_dict


def _upload_yaml_dict(
    yaml_dict, origin, raw_data_folder, log_func, flexilims_session, conflicts, verbose
):
    for entity, entity_data in yaml_dict.items():
        entity_data = entity_data.copy()
        children = entity_data.pop("children", {})
        datatype = entity_data.pop("type")
        if datatype == "session":
            if verbose:
                print(f"Adding session `{entity}`")
            new_entity = flz.add_experimental_session(
                date=entity[1:],
                flexilims_session=flexilims_session,
                parent_id=origin["id"],
                attributes=entity_data,
                session_name=entity,
                conflicts=conflicts,
            )
        elif datatype == "recording":
            rec_type = entity_data.pop("recording_type", "Not specified")
            prot = entity_data.pop("protocol", "Not specified")
            if verbose:
                print(
                    f"Adding recording `{entity}`, type `{rec_type}`, protocol `{prot}`"
                )
            new_entity = flz.add_recording(
                session_id=origin["id"],
                recording_type=rec_type,
                protocol=prot,
                attributes=entity_data,
                recording_name=entity,
                conflicts=conflicts,
                flexilims_session=flexilims_session,
            )
        elif datatype == "sample":
            if verbose:
                print(f"Adding sample `{entity}`")
            new_entity = flz.add_sample(
                parent_id=origin["id"],
                attributes=entity_data,
                sample_name=entity,
                conflicts=conflicts,
                flexilims_session=flexilims_session,
            )
        elif datatype == "dataset":
            created = entity_data.pop("created")
            dataset_type = entity_data.pop("dataset_type")
            path = entity_data.pop("path")
            is_raw = entity_data.pop("is_raw")

            if verbose:
                print(f"Adding dataset `{entity}`, type `{dataset_type}`")
            new_entity = flz.add_dataset(
                parent_id=origin["id"],
                dataset_type=dataset_type,
                created=created,
                path=path,
                is_raw=is_raw,
                flexilims_session=flexilims_session,
                dataset_name=entity,
                attributes=entity_data["extra_attributes"],
                strict_validation=False,
                conflicts=conflicts,
            )

        _upload_yaml_dict(
            yaml_dict=children,
            origin=new_entity,
            raw_data_folder=raw_data_folder,
            log_func=log_func,
            flexilims_session=flexilims_session,
            conflicts=conflicts,
            verbose=verbose,
        )


def _check_recursively(
    yaml_data,
    origin_genealogy,
    root_folder,
    project,
    genealogy,
    fixerrors=False,
    errors=None,
):
    if errors is None:
        errors = dict()
    root_folder = Path(root_folder)

    for child, child_dict in yaml_data.items():
        fname = root_folder / Path(*genealogy) / child
        child_genealogy = genealogy + [child]

        if child_dict["type"] != "dataset":
            if not fname.is_dir():
                child_dict["PATH_ERROR"] = f"XXERRORXX folder {fname} does not exist"
                errors[fname] = child_dict
        else:
            data_series = pd.Series(child_dict)
            for k, v in data_series.pop("extra_attributes").items():
                data_series[k] = v
            data_series.id = None
            data_series.name = "_".join(origin_genealogy + child_genealogy)
            ds = flz.Dataset.from_dataseries(data_series)
            ds.project = project
            msg = ds.is_valid(return_reason=True)
            if msg:
                child_dict["VALIDATION_ERROR"] = f"XXERRORXX {msg}"
                errors[fname] = child_dict

        if child_dict["genealogy"] != origin_genealogy + child_genealogy:
            if fixerrors:
                print(f"Fixing genealogy for {child}")
                child_dict["genealogy"] = origin_genealogy + child_genealogy
            else:
                child_dict["GENEALOGY_ERROR"] = f"XXERRORXX genealogy is not correct"
                errors[fname] = child_dict
        if "children" in child_dict:
            _check_recursively(
                child_dict["children"],
                origin_genealogy,
                root_folder,
                project,
                genealogy=genealogy + [child],
                fixerrors=fixerrors,
                errors=errors,
            )
    return errors


if __name__ == "__main__":
    example_yml = "/Users/blota/Desktop/test_yaml.yml"
    out = parse_yaml(example_yml)
    with open("/Users/blota/Desktop/test_yaml_redump.yml", "w") as f:
        yaml.dump(out, f)

    rel = "blota_onix_pilote/BRAC7448.2d/"
    root_folder = Path(flz.PARAMETERS["data_root"]["raw"]) / rel
    yaml_file = Path(flz.PARAMETERS["data_root"]["processed"]) / rel / "S20230421.yml"
    origin_name = "BRAC7448.2d"
    check_yaml_validity(yaml_file, root_folder, origin_name)
