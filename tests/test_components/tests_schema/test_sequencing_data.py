import pytest
from flexiznam.schema.sequencing_data import SequencingData
from tests.tests_resources.data_for_testing import DATA_ROOT

# Test creation of all dataset types.
#
# For each dataset type we want to test:
# - Creating by direct call
# - Creating from_flexilims
# - Creating from_origin
# - Creating from_folder


def test_from_folder():
    raw_folder = DATA_ROOT / "mouse_mapseq_lcm" / "Raw_sequencing"
    ds = SequencingData.from_folder(raw_folder, verbose=False)
    assert len(ds) == 2
    d = ds["TUR675_S896_l769_R2_001"]
    assert d.full_name == "Raw_sequencing_TUR675_S896_l769_R2_001"
    assert d.dataset_name == "TUR675_S896_l769_R2_001"
    assert d.is_valid()

