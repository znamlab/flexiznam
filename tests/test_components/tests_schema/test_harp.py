from flexiznam.schema.harp_data import HarpData
from tests.tests_resources.data_for_testing import DATA_ROOT, TEST_PROJECT


def test_harp(flm_sess):
    folder_genealogy = ["mouse_physio_2p", "S20211102", "R165821_SpheresPermTube"]
    data_dir = DATA_ROOT.joinpath(*folder_genealogy)
    ds = HarpData.from_folder(data_dir, verbose=False, flexilims_session=flm_sess)
    assert len(ds) == 1
    ds_name = "PZAD9.4d_S20211102_R165821_SpheresPermTube_harpmessage"
    d = ds[ds_name]
    assert d.full_name == folder_genealogy[-1] + "_" + ds_name
    assert d.is_valid()
    assert len(d.csv_files) == 4
    ds = HarpData.from_folder(
        data_dir, verbose=False, folder_genealogy=folder_genealogy, project=TEST_PROJECT
    )
    d = ds[ds_name]
    assert d.full_name == "_".join(folder_genealogy + [ds_name])
    assert d.is_valid()
    assert len(d.csv_files) == 4
