import pathlib
from flexiznam import datasets
from flexiznam.config import PARAMETERS


TEST_FOLDER = pathlib.Path(PARAMETERS['projects_root']) / '3d_vision/Data/PZAH4.1c/S20210510/R184337'


def test_camera():
    ds = datasets.Dataset(project='test', name='R101501_retinotopy_suite2p_traces', path=TEST_FOLDER, is_raw='no',
                          dataset_type='camera', extra_attributes={}, id=None)
    ds.flexilims_status()