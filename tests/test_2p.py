"""
Example file to upload a 2P dataset

The example data is found in demo_project
"""
from tests.tests_resources import flm_session
from tests.tests_resources import data_for_testing as test_data
import flexiznam as fzn
from flexiznam import camp

MOUSE = 'mouse_physio_2p'
SESSION = 'S20211102'
RECORDINGS = dict(R165821_SpheresPermTube='SphereCylinder',
                  R173617_SpheresPermTube='SphereCylinder')
YAML = 'physio_acq_yaml.yml'

# First check that mouse exists:
mouse = fzn.get_entity(datatype='mouse', name=MOUSE, flexilims_session=flm_session)
if mouse is None:
    # we need to add the mouse. If it was a real MCMS mouse we could do:
    # `fzn.add_mouse(project=test_data.TEST_PROJECT, mouse_name=MOUSE)`
    # but since it's a dummy mouse, I'll just add it manually:
    resp = flm_session.post(datatype='mouse', name=MOUSE, strict_validation=False,
                            attributes=dict(birth_date='01-Mar-2021',
                                            sex='Female',
                                            animal_name=MOUSE),
                            )
# Now write an acquisition yaml file
# The format is quite simple, you must specify the project, mouse and session name
acq_yml = """
mouse: {0}
project: {1}
session: {2}
recordings:
""".format(MOUSE, test_data.TEST_PROJECT, SESSION)

# Then, for each recording, give the recording name and the protocol
for rec, prot in RECORDINGS.items():
    acq_yml += "  {0}:\n    protocol:{1}\n".format(rec, prot)

# Datasets belonging to one dataset will be automatically detected.
# If you want to add dataset to the session, you need to add them manually (for now)
acq_yml += r"""
datasets:
  Ref:
    dataset_type: 'scanimage'
    notes: 'Motion correction refrence
    path: 'mouse_physio_2p/S20211102/Ref'
"""


# parse the yaml file.
out = fzn.camp.sync_data.parse_yaml(path_to_yaml=test_data.DATA_ROOT / MOUSE / YAML,
                                    raw_data_folder=test_data.DATA_ROOT)
print('done')