import pytest
from flexiznam.schema.scanimage_data import ScanimageData
from tests.tests_resources.data_for_testing import DATA_ROOT


def test_scanimage(tmp_path):
    data_dir = DATA_ROOT / "mouse_physio_2p" / "S20211102" / "Ref"
    ds = ScanimageData.from_folder(data_dir, verbose=False)
    assert len(ds) == 1
    d = next(iter(ds.values()))
    assert d.full_name == "Ref_Ref_00001"
    assert d.dataset_name == "Ref_00001"
    assert d.is_valid()
    assert len(d) == 5
