"""
Example file to upload a barseq dataset

The example data is found in demo_project
"""
import copy

import pandas as pd
import yaml

from flexiznam.camp.sync_data import upload_yaml, create_yaml, parse_yaml
from flexiznam.utils import clean_dictionary_recursively
from tests.tests_resources import flexilims_session
from tests.tests_resources.data_for_testing import (
    DATA_ROOT,
    PROCESSED_ROOT,
    TEST_PROJECT,
)
import flexiznam as fzn
from flexiznam import camp

MOUSE = "mouse_barseq"
YAML = "yaml_automatic_skeleton.yml"
FLM_IS_WIPED = False  # switch this flag to True if you deleted everything on flexilims

# An acquisition yaml file must be written by hand
# The format is quite simple, you must specify the project, mouse and session name
# An example is in: `shared/projects/demo_project/mouse_barseq/barseq_yaml.yml`


def test_create_yaml():
    """Test automatic yaml creation

    We check that the acquisition yaml can also be created automatically
    """
    saved_skeleton = PROCESSED_ROOT / MOUSE / "yaml_automatic_skeleton.yml"
    # To save the yaml the first time we add outfile:
    automat = create_yaml(DATA_ROOT / MOUSE, mouse=MOUSE, project=TEST_PROJECT)
    #                      outfile=saved_skeleton, overwrite=True)

    with open(saved_skeleton, "r") as fopen:
        saved = yaml.safe_load(fopen)
    assert saved == automat


def test_parse_yaml():
    """Test that we can parse the acq yaml

    We check that we can parse the yaml and that the output is similar to a known copy
    """
    parsed = parse_yaml(
        path_to_yaml=PROCESSED_ROOT / MOUSE / YAML,
        raw_data_folder=DATA_ROOT,
        verbose=False,
    )

    saved_parsed_yaml = PROCESSED_ROOT / MOUSE / YAML.replace(".yml", "_parsed.yml")
    # If the parsed has changed and you want to overwrite it, you can do:
    # fzn.camp.sync_data.write_session_data_as_yaml(parsed, target_file=saved_parsed_yaml,
    #                                               overwrite=True)
    # parsed contains datasets, we need to make them  into str to compare with saved data
    parsed_str = copy.deepcopy(parsed)
    clean_dictionary_recursively(
        parsed_str, keys=["name"], format_dataset=True, tuple_as_list=True
    )

    with open(saved_parsed_yaml, "r") as fopen:
        saved = yaml.safe_load(fopen)
    assert saved == parsed_str


def test_flm():
    """Check that we can upload to flexilims if the database is wiped"""
    if FLM_IS_WIPED:
        # there shouldn't be anything in the way, if there is we have an issue
        conflicts = "abort"
    else:
        # entries already exist, just skip them. Will still crash if there is dataset
        # that has changed.
        conflicts = "skip"
    # make sure we have the mouse
    barseq_mouse_exists()
    saved_parsed_yaml = PROCESSED_ROOT / MOUSE / YAML.replace(".yml", "_parsed.yml")
    created = upload_yaml(
        saved_parsed_yaml,
        raw_data_folder=None,
        verbose=False,
        log_func=print,
        flexilims_session=flexilims_session,
        conflicts=conflicts,
    )
    # check that I do not duplicate any part of the name (except for SI datasets)
    for c in created:
        parts = c.split("_")
        v = pd.value_counts(parts)
        if v.max() > 1:
            if "czi" in c:
                continue
            if c in [
                "mouse_barseq_brain_slide_001_slide_001_overview.tif",
                "mouse_barseq_brain_slide_001_section_01_cycle_01",
                "mouse_barseq_brain_slide_006_section_02_cycle_02",
            ]:
                continue
            raise ValueError("Name is weird: %s" % c)


def barseq_mouse_exists():
    mouse = fzn.get_entity(
        datatype="mouse", name=MOUSE, flexilims_session=flexilims_session
    )
    if FLM_IS_WIPED:
        assert mouse is None
        # we need to add the mouse. If it was a real MCMS mouse we could do:
        # `fzn.add_mouse(project=test_data.TEST_PROJECT, mouse_name=MOUSE)`
        # but since it's a dummy mouse, I'll just add it manually:
        mouse = fzn.add_mouse(
            flexilims_session=flexilims_session,
            mouse_info=dict(birth_date="01-Mar-2021", sex="Female", animal_name=MOUSE),
            mouse_name=MOUSE,
            get_mcms_data=False,
        )
    else:
        assert mouse is not None
