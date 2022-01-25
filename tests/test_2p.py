"""
Example file to upload a 2P dataset

The example data is found in demo_project
"""
import copy
import yaml

from flexiznam.camp.sync_data import upload_yaml
from flexiznam.utils import clean_dictionary_recursively
from tests.tests_resources import flm_session
from tests.tests_resources.data_for_testing import DATA_ROOT, PROCESSED_ROOT
import flexiznam as fzn
from flexiznam import camp

MOUSE = 'mouse_physio_2p'
YAML = 'physio_acq_yaml.yml'
FLM_IS_WIPED = False  # switch this flag to True if you deleted everything on flexilims

# An acquisition yaml file must be written by hand
# The format is quite simple, you must specify the project, mouse and session name
# An example is in: `shared/projects/demo_project/mouse_physio_2p/physio_acq_yaml.yml`


def physio_mouse_exists():
    mouse = fzn.get_entity(datatype='mouse', name=MOUSE, flexilims_session=flm_session)
    if FLM_IS_WIPED:
        assert mouse is None
        # we need to add the mouse. If it was a real MCMS mouse we could do:
        # `fzn.add_mouse(project=test_data.TEST_PROJECT, mouse_name=MOUSE)`
        # but since it's a dummy mouse, I'll just add it manually:
        resp = flm_session.post(datatype='mouse',
                                name=MOUSE,
                                strict_validation=False,
                                attributes=dict(birth_date='01-Mar-2021',
                                                sex='Female',
                                                animal_name=MOUSE),
                                )
    else:
        assert mouse is not None


def test_parse_yaml():
    """Test that we can parse the acq yaml

    We check that we can parse the yaml and that the output is similar to a known copy
    """
    parsed = fzn.camp.sync_data.parse_yaml(path_to_yaml=PROCESSED_ROOT / MOUSE / YAML,
                                           raw_data_folder=DATA_ROOT)

    saved_parsed_yaml = PROCESSED_ROOT / MOUSE / YAML.replace('.yml', '_parsed.yml')
    # parsed contains datasets, we need to make them  into str to compare with saved data
    parsed_str = copy.deepcopy(parsed)
    clean_dictionary_recursively(parsed_str, keys=['name'], format_dataset=True)

    with open(saved_parsed_yaml, 'r') as fopen:
        saved = yaml.safe_load(fopen)
    assert saved == parsed_str


def test_flm():
    """Check that we can upload to flexilims if the database is wiped"""
    if FLM_IS_WIPED:
        conflicts = 'abort'
    else:
        conflicts = 'skip'

    saved_parsed_yaml = PROCESSED_ROOT / MOUSE / YAML.replace('.yml', '_parsed.yml')
    upload_yaml(saved_parsed_yaml, raw_data_folder=None, verbose=False,
                log_func=print, flexilims_session=flm_session, conflicts=conflicts)
