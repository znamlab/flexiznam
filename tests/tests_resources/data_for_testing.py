"""A list of file coming from one experiment"""
from pathlib import Path
import datetime
from flexiznam.config import PARAMETERS


TEST_PROJECT = 'demo_project'
MOUSE_PHYSIO = 'PZAD9.4d'
MOUSE_SAMPLE = 'PZAJ5.1a'

DATA_ROOT = Path(PARAMETERS['data_root']['raw']) / TEST_PROJECT
if not DATA_ROOT.is_dir():
    print('WARNING: cannot find test data, most tests will fail\n')


def get_example_yaml_files(session_name='S20210513'):
    """Help for testing: generates a yaml-like dictionary

    Args:
        session_name (str): name of the session

    Returns:
        miniaml (dict): minimal example of yaml compatible with flexilims update
        faml (dict): full example of yaml, which includes things that need to be corrected
    """
    raise DeprecationWarning
    miniaml = {"project": "test",
               "mouse": "PZAH4.1c",
               "session": session_name,
               "recordings": {
                   "R182758_SphereCylinder": {"protocol": "SphereCylinder"},
                   "R193432_Retinotopy": {"protocol": "Retinotopy"}
               }
               }
    ds_rec = dict(harp_data_csv=dict(dataset_type='harp',
                                     path='./PZAH4.1c/%s/ParamLog/R193432_Retinotopy' %
                                          session_name,
                                     notes="Here too you can add notes"))
    rec_dict = dict(R182758_SphereCylinder=dict(protocol="SphereCylinder",
                                                timestamp="182758",
                                                recording_type="two_photon",
                                                notes="note or the recording level"),
                    R193432_Retinotopy=dict(protocol="Retinotopy",
                                            timestamp="182758",
                                            datasets=ds_rec))
    ds_sess = dict(ref_for_motion=dict(dataset_type='scanimage',
                                       path='./PZAH4.1c/%s/Ref' % session_name),
                   overview00001=dict(dataset_type='scanimage',
                                      path='./PZAH4.1c/%s/overview_00001_00001.tif' %
                                           session_name),
                   overview_picture_02=dict(dataset_type='scanimage',
                                            path='./PZAH4.1c/%s/overview_00002_00001.tif'
                                                 % session_name,
                                            notes="at any point you can add notes or "
                                                  "attributes as below",
                                            attributes=dict(
                                                channels=['red', 'blue'],
                                                led_knob=12, )
                                            )
                   )
    faml = dict(project="test", mouse="PZAH4.1c", session=session_name,
                path="./PZAH4.1c/%s" % session_name,
                notes="Notes can be added at any level of the hierarchy in this yaml "
                      "file.",
                attributes=dict(quality='test data'),
                recordings=rec_dict,
                datasets=ds_sess
                )

    return miniaml, faml


def create_acq_files(target_folder, session_name='S20210513'):
    """Create empty files mimicking acq file structure

    Args:
           target_folder (str): temporary folder to write the data. Must not exist
           session_name (str): name of the session

    Returns:
           session_name (str): the name of the session
    """
    raise DeprecationWarning
    if session_name == 'unique':
        # create a unique session name
        session_name = 'S' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    target_folder = Path(target_folder)
    root = target_folder / MOUSE / session_name
    if root.exists():
        raise IOError('Target folder exists')

    for file in ACQ:
        file_path = root / file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
    return session_name


def create_sample_file(target_folder):
    """Create empty files mimicking sample imaging file structure

       Args:
              target_folder (str): temporary folder to write the data. Must not exist

       Returns:
              None
    """
    raise DeprecationWarning
    target_folder = Path(target_folder)
    root = target_folder / MOUSE
    if root.exists():
        raise IOError('Target folder exists')

    for file in SPL:
        file_path = root / file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
