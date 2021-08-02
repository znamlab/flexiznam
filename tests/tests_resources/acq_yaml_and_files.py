"""A list of file coming from one experiment"""
from pathlib import Path
import datetime


def get_example_yaml_files(session_name='S20210513'):
    """Help for testing: generates a yaml-like dictionary

    Args:
        session_name: str name of the session

    Returns:
        miniaml: minimal example of yaml compatible with flexilims update
        faml: full example of yaml, which includes things that need to be corrected
    """
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
           target_folder: str temporary folder to write the data. Must not exist
           session_name: str name of the session

    Returns:
           session_name: str the name of the session
    """

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
              target_folder: str temporary folder to write the data. Must not exist

       Returns:
              None
    """
    target_folder = Path(target_folder)
    root = target_folder / MOUSE
    if root.exists():
           raise IOError('Target folder exists')

    for file in ACQ:
           file_path = root / file
           file_path.parent.mkdir(parents=True, exist_ok=True)
           file_path.touch()


MOUSE = 'PZAH4.1c'

ACQ = ['overview_00001_00001.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00037.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00004.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00034.tif',
       'R193432_Retinotopy/right_eye_camera_metadata.txt',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00019.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00005.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_Motion_00001.csv',
       'R193432_Retinotopy/left_eye_camera_metadata.txt',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00011.tif',
       'R193432_Retinotopy/butt_camera_data.avi',
       'R193432_Retinotopy/left_eye_camera_timestamps.csv',
       'R193432_Retinotopy/face_camera_data.avi',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00036.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00015.tif',
       'R193432_Retinotopy/face_camera_timestamps.csv',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00012.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00010.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00020.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00032.tif',
       'R193432_Retinotopy/butt_camera_timestamps.csv',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00006.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00022.tif',
       'R193432_Retinotopy/right_eye_camera_timestamps.csv',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00003.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00002.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00016.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00017.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00009.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00025.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00001.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00023.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00026.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00007.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00018.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00027.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00031.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00029.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00021.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00024.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00030.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00008.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00039.tif',
       'R193432_Retinotopy/butt_camera_metadata.txt',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00035.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00033.tif',
       'R193432_Retinotopy/face_camera_metadata.txt',
       'R193432_Retinotopy/left_eye_camera_data.avi',
       'R193432_Retinotopy/right_eye_camera_data.avi',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00038.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00028.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00013.tif',
       'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_00001_00014.tif',
       'Ref/ref_00002.tif', 'Ref/ref_00004.tif', 'Ref/ref_Motion_00004.csv',
       'Ref/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00005.tif',
       'Ref/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00004.tif',
       'Ref/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00002.tif',
       'Ref/ref_00003.tif',
       'Ref/PZAH4.1c_S20210513_R181858_SphereCylinder_Motion_00001.csv',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00006.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00012.tif',
       'Ref/PZAH4.1c_S20210513_R181858_SphereCylinder_00001_00001.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00013.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00007.tif',
       'Ref/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00001.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00001.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00010.tif',
       'Ref/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00007.tif',
       'Ref/ref_00001.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00005.tif',
       'Ref/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00003.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00002.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00003.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00008.tif',
       'Ref/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00008.tif',
       'Ref/ref_Motion_00003.csv',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00009.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00004.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_00001_00011.tif',
       'Ref/PZAH4.1c_S20210513_R182025_SphereCylinder_Motion_00001.csv',
       'Ref/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00006.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00063.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00034.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00080.tif',
       'R182758_SphereCylinder/right_eye_camera_metadata.txt',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00055.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00030.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00037.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00026.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00081.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00089.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00045.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00070.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00077.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00017.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00097.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00020.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00035.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00096.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00068.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00067.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00066.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00028.tif',
       'R182758_SphereCylinder/left_eye_camera_metadata.txt',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00048.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00056.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00100.tif',
       'R182758_SphereCylinder/butt_camera_data.avi',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00038.tif',
       'R182758_SphereCylinder/left_eye_camera_timestamps.csv',
       'R182758_SphereCylinder/face_camera_data.avi',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00032.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00094.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00090.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00084.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00029.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00104.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00036.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00073.tif',
       'R182758_SphereCylinder/face_camera_timestamps.csv',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00061.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00014.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00102.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00101.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00099.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00074.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00023.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00107.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00039.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00113.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00086.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00106.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00109.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00044.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00046.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00079.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00041.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00062.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00088.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00085.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00058.tif',
       'R182758_SphereCylinder/butt_camera_timestamps.csv',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00092.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00013.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00050.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00019.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00075.tif',
       'R182758_SphereCylinder/right_eye_camera_timestamps.csv',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00057.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00025.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00091.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00054.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00012.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00049.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00051.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00047.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00042.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00072.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00069.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00076.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00024.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00093.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00103.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00060.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00098.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00083.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00022.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00021.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00043.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00105.tif',
       'R182758_SphereCylinder/butt_camera_metadata.txt',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00009.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00015.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00112.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00018.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00011.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00052.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00040.tif',
       'R182758_SphereCylinder/face_camera_metadata.txt',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00078.tif',
       'R182758_SphereCylinder/left_eye_camera_data.avi',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00095.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00033.tif',
       'R182758_SphereCylinder/right_eye_camera_data.avi',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00071.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00010.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00064.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00027.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00108.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00082.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00016.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00111.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00065.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00087.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00031.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00110.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00053.tif',
       'R182758_SphereCylinder/PZAH4.1c_S20210513_R182758_SphereCylinder_00001_00059.tif',
       'overview_00002_00001.tif', 'overview_Motion_00001.csv',
       ]

# add some example data that would be in a weird folder
_p = ['R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_RotaryEncoder.csv',
      'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_PhotodiodeLog.csv',
      'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_NewParams.csv',
      'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_harpmessage.csv',
      'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_FrameLog.csv',
      'R193432_Retinotopy/PZAH4.1c_S20210513_R193432_Retinotopy_harpmessage.bin'
      ]
for txt in _p:
    ACQ.append('ParamLog/' + txt)

# also give some histology path
SPL = ['brain/Slide1/example_SC_cell_snap.czi',
       'brain/Slide3/conv_fluo_overview_10X_raw.czi',
       'brain/Slide3/conv_fluo_overview_10X_stitched.czi',
       'brain/BeforeStaining/Lateral_cortex_hop_10x_snap.czi',
       'brain/BeforeStaining/LGN_5x_snap.czi',
       'brain/BeforeStaining/LGN_20x_zstack_conventional_fluor.czi',
       'brain/BeforeStaining/2_starters_20x_zstack_conventional_fluor.czi',
       'brain/BeforeStaining/LGN_20x_zstack_apotomed.czi',
       'brain/BeforeStaining/2_starters_20x_zstack_apotomed.czi',
       'brain/Slide4/epifluo_10x_overview_raw.czi',
       'brain/Slide4/epifluo_10x_overview_stitched.czi',
       'left_retina/MAX_Reslice of Stitch_A01_binned.png',
       'left_retina/overview_single_plane.jpg',
       'left_retina/Stitch_A01_S2_IPL_layer.png',
       'left_retina/Stitch_A01_binned.gif',
       'left_retina/Stitch_A01_S4_IPL_layer.png',
       'left_retina/Stitch_A01_RGC_layer.png',
       'left_retina/Stitch_A01_maybe_INL.png',
       'left_retina/Stitch_A01_binned.tif',
       'right_retina/snap_40X_green_cells_and_chat.jpg',
       'right_retina/tile_zstack_20x_Cycle_01',
       'right_retina/tile_zstack_20x_Cycle_01/Map_A01.hdf5',
       'right_retina/tile_zstack_20x_Cycle_01/Map_A01.oir',
       'right_retina/tile_zstack_20x_Cycle_01/tile_zstack_20x_A01_G001_0003.oir',
       'right_retina/tile_zstack_20x_Cycle_01/tile_zstack_20x_A01_G001_0001.oir',
       'right_retina/tile_zstack_20x_Cycle_01/tile_zstack_20x_A01_G001_0002.oir',
       'right_retina/tile_zstack_20x_Cycle_01/matl.omp2info',
       'right_retina/tile_zstack_20x_Cycle_01/tile_zstack_20x_A01_G001_0004.oir',
       'right_retina/tile_zstack_20x_Cycle_01/matl_forVSIimages.omp2info',
       'right_retina/tile_zstack_20x_Cycle/Map_A01.hdf5',
       'right_retina/tile_zstack_20x_Cycle/Map_A01.oir',
       'right_retina/tile_zstack_20x_Cycle/tile_zstack_20x_A01_G001_0006.oir',
       'right_retina/tile_zstack_20x_Cycle/tile_zstack_20x_A01_G001_0007.oir',
       'right_retina/tile_zstack_20x_Cycle/tile_zstack_20x_A01_G001_0003.oir',
       'right_retina/tile_zstack_20x_Cycle/tile_zstack_20x_A01_G001_0001.oir',
       'right_retina/tile_zstack_20x_Cycle/tile_zstack_20x_A01_G001_0002.oir',
       'right_retina/tile_zstack_20x_Cycle/matl.omp2info',
       'right_retina/tile_zstack_20x_Cycle/tile_zstack_20x_A01_G001_0004.oir',
       'right_retina/tile_zstack_20x_Cycle/matl_forVSIimages.omp2info',
       'right_retina/tile_zstack_20x_Cycle/tile_zstack_20x_A01_G001_0005.oir',
       'right_retina/overview_Cycle',
       'right_retina/overview_Cycle/Map_A01.hdf5',
       'right_retina/overview_Cycle/overview_A01_G001_0001.oir',
       'right_retina/overview_Cycle/Map_A01.oir',
       'right_retina/overview_Cycle/matl.omp2info',
       'right_retina/overview_Cycle/matl_forVSIimages.omp2info',
       'right_retina/MAX_Reslice of tile_zstack_30x_A01_G001_0005.png',
       'right_retina/snap_40X_green_cells_and_chat.czi']
