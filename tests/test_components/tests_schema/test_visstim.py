import pytest
from flexiznam.schema.visstim_data import VisStimData
from tests.tests_resources.data_for_testing import DATA_ROOT


def test_vistim():
    folder_genealogy = ["mouse_onix", "S20230915", "R165222_SpheresPermTubeReward"]
    data_dir = DATA_ROOT.joinpath(*folder_genealogy)
    ds = VisStimData.from_folder(data_dir, verbose=False)
    assert len(ds) == 1
    ds_name = "visstim"
    d = ds[ds_name]
    assert d.full_name == folder_genealogy[-1] + "_" + ds_name
    d.project = "demo_project"
    assert d.is_valid()
    assert len(d.csv_files) == 4
    ds = VisStimData.from_folder(
        data_dir, verbose=False, folder_genealogy=folder_genealogy
    )
    d = ds[ds_name]
    d.project = "demo_project"
    assert d.full_name == "_".join(folder_genealogy + [ds_name])
    assert d.is_valid()
    assert len(d.csv_files) == 4
