"""A list of file coming from one experiment"""

from pathlib import Path

from flexiznam.config import PARAMETERS
from flexiznam.main import get_flexilims_session

MOUSE_ID = "6437dcb13ded9c65df142a12"  # actual physio2p mouse
MOUSE_TEMP = "647a1aec7ddb34517470d3e6"  # mouse PZAA15.1a where I can change data
TEST_PROJECT = "demo_project"
PROJECT_ID = "610989f9a651ff0b6237e0f6"
TEST_PROJECT_ID = "606df1ac08df4d77c72c9aa4"  # <- test_api project
SESSION = "PZAA15.1a_S20201225"
DATA_ROOT = Path(PARAMETERS["data_root"]["raw"]) / TEST_PROJECT
PROCESSED_ROOT = Path(PARAMETERS["data_root"]["processed"]) / TEST_PROJECT

if not DATA_ROOT.is_dir():
    print("WARNING: cannot find test data, most tests will fail\n")


# Clear the database
if True:
    id_to_keep = dict(mouse=[MOUSE_ID, MOUSE_TEMP])
    name_to_keep = "mouse_physio_2p_S20211102_R173917_SpheresPermTube_face_camera"
    datatype_to_remove = ["mouse", "recording", "session", "sample", "dataset"]

    session = get_flexilims_session(project_id=PROJECT_ID)
    for datatype in datatype_to_remove:
        entities = session.get(datatype=datatype)
        to_keep = id_to_keep.get(datatype, [])
        for entity in entities:
            if entity["id"] in to_keep:
                print(f"Keeping {entity['name']}")
            elif entity["name"] in name_to_keep:
                print(f"Keeping `{entity['name']}")
            else:
                print(f"Deleting `{entity['name']}`, id: {entity['id']}")
                print(session.delete(entity["id"]))
    # Add back the session
    mouse, sess = SESSION.split("_")
    sess_entity = session.post(
        datatype="session",
        origin_id=MOUSE_TEMP,
        name=SESSION,
        attributes={"path": f"{TEST_PROJECT}/{mouse}/{sess}"},
    )
    # A recording
    rec_entity = session.post(
        datatype="recording",
        origin_id=sess_entity["id"],
        name=sess_entity["name"] + "_example_recording",
        attributes={
            "path": f"{sess_entity['attributes']['path']}/example_recording",
            "genealogy": (sess_entity["name"], "example_recording"),
            "protocol": "smart_experiment",
        },
        strict_validation=False,
    )
    # Two dataset on session
    for ds_id in range(2):
        session.post(
            datatype="dataset",
            origin_id=sess_entity["id"],
            name=sess_entity["name"] + f"_overview_ds_{ds_id}",
            attributes={
                "path": f"{sess_entity['attributes']['path']}/overview_{ds_id}.tif",
                "dataset_type": "scanimage",
                "is_raw": "yes",
                "genealogy": (sess_entity["name"], f"overview_ds_{ds_id}"),
                "acq_uid": f"overview_zoom1_0000{ds_id}",
                "acq_num": f"0000{ds_id}",
            },
            strict_validation=False,
        )

    # Three datasets below recording
    datasets_type = ["suite2_traces", "scanimage", "camera"]
    for ds_id in range(3):
        attr = {
            "path": f"{rec_entity['attributes']['path']}/ds_{ds_id}.npy",
            "dataset_type": datasets_type[ds_id],
            "is_raw": "yes",
            "genealogy": (
                sess_entity["name"],
                "example_recording",
                f"dataset_{ds_id}",
            ),
            "example_attribute": f"some_number_{ds_id}",
        }
        if datasets_type[ds_id] == "camera":
            attr.update(
                dict(
                    acq_uid=f"overview_zoom1_0000{ds_id}",
                    timestamp_file="face_camera_timestamps.csv",
                    video_file="face_camera.mp4",
                )
            )
        session.post(
            datatype="dataset",
            origin_id=rec_entity["id"],
            name=rec_entity["name"] + f"_dataset_{ds_id}",
            attributes=attr,
            strict_validation=False,
        )
