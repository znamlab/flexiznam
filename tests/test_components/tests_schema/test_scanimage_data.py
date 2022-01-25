import pytest
from flexiznam.schema.scanimage_data import ScanimageData
from tests.tests_resources.data_for_testing import DATA_ROOT


@pytest.mark.integtest
def test_scanimage(tmp_path):
    data_dir = DATA_ROOT / 'mouse_physio_2p' / 'S20211102' / 'Ref'
    ds = ScanimageData.from_folder(data_dir, verbose=False)
    assert len(ds) == 1
    d = next(iter(ds.values()))
    assert d.name == 'Ref_00001'
    assert d.name == next(iter(ds.keys()))
    assert d.is_valid()
    assert len(d) == 5
