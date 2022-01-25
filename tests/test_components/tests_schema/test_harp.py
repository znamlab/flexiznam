import pytest
from flexiznam.schema.harp_data import HarpData
from tests.tests_resources.data_for_testing import DATA_ROOT


@pytest.mark.integtest
def test_harp():
    data_dir = DATA_ROOT / 'mouse_physio_2p' / 'S20211102' / 'R165821_SpheresPermTube'
    ds = HarpData.from_folder(data_dir, verbose=False)
    assert len(ds) == 1
    d = next(iter(ds.values()))
    assert d.name == next(iter(ds.keys()))
    assert d.is_valid()
    assert len(d.csv_files) == 4
