from flexiznam.schema.microscopy_data import MicroscopyData
from tests.tests_resources.data_for_testing import DATA_ROOT

# Test creation of all dataset types.
#
# For each dataset type we want to test:
# - Creating by direct call
# - Creating from_flexilims
# - Creating from_origin
# - Creating from_folder


def test_from_folder():
    raw_folder = DATA_ROOT / "mouse_physio_2p"
    ds = MicroscopyData.from_folder(raw_folder, verbose=False)
    assert len(ds) == 1
    d = ds["wf_overview.PNG"]
    assert d.full_name == "mouse_physio_2p_wf_overview.PNG"
    assert d.dataset_name == "wf_overview.PNG"
    assert d.is_valid()
