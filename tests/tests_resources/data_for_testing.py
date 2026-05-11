"""A list of file coming from one experiment"""

from pathlib import Path

from flexiznam.config import PARAMETERS

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


def populate_test_data(session):
    # Clear the database
    if True:
        id_to_keep = dict(mouse=[MOUSE_ID, MOUSE_TEMP])
        name_to_keep = "mouse_physio_2p_S20211102_R173917_SpheresPermTube_face_camera"
        datatype_to_remove = ["mouse", "recording", "session", "sample", "dataset"]

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
        # Create mice
        session.post(
            datatype="mouse",
            name="PZAA15.1a",
            attributes={"genealogy": ["PZAA15.1a"]},
            id=MOUSE_TEMP,
        )
        session.post(
            datatype="mouse",
            name="mouse_physio_2p",
            attributes={"genealogy": ["mouse_physio_2p"]},
            id=MOUSE_ID,
        )

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

        # Add mouse_physio_2p data
        physio_sess = session.post(
            datatype="session",
            origin_id=MOUSE_ID,
            name="mouse_physio_2p_S20211102",
            attributes={
                "path": f"{TEST_PROJECT}/mouse_physio_2p/S20211102",
                "genealogy": ["mouse_physio_2p", "S20211102"],
            },
        )
        physio_rec = session.post(
            datatype="recording",
            origin_id=physio_sess["id"],
            name="mouse_physio_2p_S20211102_R165821_SpheresPermTube",
            attributes={
                "path": f"{physio_sess['attributes']['path']}/R165821_SpheresPermTube",
                "genealogy": (
                    "mouse_physio_2p",
                    "S20211102",
                    "R165821_SpheresPermTube",
                ),
                "protocol": "SpheresPermTube",
            },
        )
        session.post(
            datatype="dataset",
            origin_id=physio_rec["id"],
            name="mouse_physio_2p_S20211102_R165821_SpheresPermTube_wf_camera",
            attributes={
                "path": f"{physio_rec['attributes']['path']}/wf_camera",
                "dataset_type": "camera",
                "is_raw": "yes",
                "genealogy": (
                    "mouse_physio_2p",
                    "S20211102",
                    "R165821_SpheresPermTube",
                    "wf_camera",
                ),
                "video_file": "face_camera.mp4",
            },
        )

        # Add a recording named "mouse_physio_2p" to satisfy test_from_origin
        # This seems to be what the test expects, even if weird.
        session.post(
            datatype="recording",
            name="mouse_physio_2p",
            attributes={"genealogy": ["mouse_physio_2p"], "path": "fake/path/to/rec"},
            origin_id=MOUSE_ID,
        )
