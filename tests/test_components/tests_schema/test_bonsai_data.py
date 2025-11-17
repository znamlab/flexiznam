from flexiznam.schema.bonsai_data import BonsaiData


def test_bonsai_data_from_folder_no_files(tmp_path):
    """
    Test that from_folder returns an empty dict when no .bonsai files are present.
    """
    (tmp_path / "some_other_file.txt").touch()
    datasets = BonsaiData.from_folder(tmp_path)
    assert isinstance(datasets, dict)
    assert not datasets


def test_bonsai_data_from_folder_single_file(tmp_path):
    """
    Test detection of a single .bonsai file.
    """
    bonsai_file = tmp_path / "workflow1.bonsai"
    bonsai_file.touch()

    datasets = BonsaiData.from_folder(tmp_path, is_raw=True)

    assert len(datasets) == 1
    dataset_name = "workflow1"
    assert dataset_name in datasets

    ds = datasets[dataset_name]
    assert isinstance(ds, BonsaiData)
    assert ds.dataset_type == "bonsai"
    assert ds.dataset_name == dataset_name
    assert ds.path == tmp_path
    assert ds.extra_attributes == {"file": "workflow1.bonsai"}
    assert ds.genealogy == (tmp_path.name, dataset_name)
    assert ds.created is not None


def test_bonsai_data_from_folder_multiple_files(tmp_path):
    """
    Test detection of multiple .bonsai files.
    """
    (tmp_path / "workflow1.bonsai").touch()
    (tmp_path / "workflow2.bonsai").touch()
    (tmp_path / "other.txt").touch()

    datasets = BonsaiData.from_folder(tmp_path, is_raw=True)

    assert len(datasets) == 2
    assert "workflow1" in datasets
    assert "workflow2" in datasets

    assert datasets["workflow1"].extra_attributes["file"] == "workflow1.bonsai"
    assert datasets["workflow2"].extra_attributes["file"] == "workflow2.bonsai"


def test_bonsai_data_from_folder_with_directory_ending_in_bonsai(tmp_path):
    """
    Test that a directory with a .bonsai extension is ignored.
    """
    (tmp_path / "real_workflow.bonsai").touch()
    (tmp_path / "fake_workflow.bonsai").mkdir()

    datasets = BonsaiData.from_folder(tmp_path, is_raw=True)

    assert len(datasets) == 1
    assert "real_workflow" in datasets
    assert "fake_workflow" not in datasets


def test_bonsai_data_from_folder_with_genealogy(tmp_path):
    """
    Test that folder_genealogy is correctly used.
    """
    (tmp_path / "my_workflow.bonsai").touch()
    folder_genealogy = ("mouse1", "session1")
    datasets = BonsaiData.from_folder(
        tmp_path, folder_genealogy=folder_genealogy, is_raw=True
    )

    assert "my_workflow" in datasets
    ds = datasets["my_workflow"]
    assert ds.genealogy == ("mouse1", "session1", "my_workflow")


def test_bonsai_data_is_valid(tmp_path):
    """
    Test the is_valid() method of BonsaiData.
    """
    bonsai_file = tmp_path / "valid_workflow.bonsai"
    bonsai_file.touch()

    # Create a valid dataset
    datasets = BonsaiData.from_folder(tmp_path, is_raw=True)
    valid_ds = datasets["valid_workflow"]
    valid_ds.project = "test"  # Needed for path_full

    assert valid_ds.is_valid() is True
    assert valid_ds.is_valid(return_reason=True) == ""


def test_bonsai_data_is_invalid_missing_file(tmp_path):
    """
    Test is_valid() when the associated file is missing.
    """
    bonsai_file = tmp_path / "workflow.bonsai"
    bonsai_file.touch()

    datasets = BonsaiData.from_folder(tmp_path, is_raw=True)
    ds = datasets["workflow"]
    ds.project = "test"

    # Manually make it invalid by pointing to a non-existent file
    ds.extra_attributes["file"] = "non_existent.bonsai"

    assert ds.is_valid() is False
    reason = ds.is_valid(return_reason=True)
    assert "does not exist" in reason


def test_bonsai_data_is_invalid_no_extra_attributes(tmp_path):
    """
    Test is_valid() when extra_attributes is missing 'file'.
    """
    bonsai_file = tmp_path / "workflow.bonsai"
    bonsai_file.touch()

    datasets = BonsaiData.from_folder(tmp_path, is_raw=True)
    ds = datasets["workflow"]
    ds.project = "test"

    ds.extra_attributes = {}

    assert ds.is_valid() is False
    assert ds.is_valid(return_reason=True) == "No file found in dataset"
