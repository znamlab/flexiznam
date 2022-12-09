import pytest
from flexiznam.schema.harp_data import HarpData
from tests.tests_resources.data_for_testing import DATA_ROOT
from pathlib import Path



def test_harp():
    folder_genealogy = ['mouse_physio_2p', 'S20211102', 'R165821_SpheresPermTube']
    data_dir = DATA_ROOT.joinpath(*folder_genealogy)
    ds = HarpData.from_folder(data_dir, verbose=False)
    assert len(ds) == 1
    d = next(iter(ds.values()))
    assert d.full_name == folder_genealogy[-1] + '_' + next(iter(ds.keys()))
    assert d.is_valid()
    assert len(d.csv_files) == 4
    ds = HarpData.from_folder(data_dir, verbose=False, folder_genealogy=folder_genealogy)
    d = next(iter(ds.values()))
    assert d.full_name == '_'.join(folder_genealogy + [next(iter(ds.keys()))])
    assert d.is_valid()
    assert len(d.csv_files) == 4
