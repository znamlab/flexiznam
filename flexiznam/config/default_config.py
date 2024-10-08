"""
This file is used to generate the initial config file
"""

DEFAULT_CONFIG = dict(
    # MCMS configuration:
    download_folder="~/Downloads",  # folder use to download files by your default web browser
    mcms_username="yourusername",
    # Flexilims configuration
    # If you want to access projects by name, add their hexadecimal ID here:
    project_ids={
        "3d_vision": "606df5af08df4d77c72c9b05",
        "virus_tests": "607f145d25d64b66227b00be",
        "test": "606df1ac08df4d77c72c9aa4",
        "AAVRKO_retina_hva": "60a7757a8901a2357f29080a",
    },
    project_paths={
        "example": dict(
            raw="/camp/project/example_project/raw",
            processed="/camp/project/example_project/processed",
        )
    },
    # a default username can be specified
    flexilims_username="yourusername",
    # Use for data dataset detection
    data_root=dict(
        raw="/camp/lab/znamenskiyp/data/instruments/raw_data/projects",
        processed="/camp/lab/znamenskiyp/home/shared/projects",
    ),
    # list of all datatypes
    datatypes=["mouse", "session", "recording", "dataset", "sample"],
    # should we limit the valid dataset types?
    enforce_dataset_types=False,
    # if we enforce, what is the list of valid dataset type
    dataset_types=[
        "scanimage",
        "camera",
        "ephys",
        "suite2p_rois",
        "suite2p_traces",
        "harp",
        "microscopy",
        "sequencing",
        "onix",
    ],
    # list of extensions accepted as `MicroscopyData`
    microscopy_extensions=[".czi", ".png", ".gif", ".tif", ".tiff"],
    # list of extensions accepted as `SequencingData`
    sequencing_extensions=[".fastq.gz", ".fastq", ".fq.gz", ".fq", ".bam", ".sam"],
    conda_envs=dict(
        dlc="dlc_nogui",
        cottage_analysis="cottage_analysis",
        suite2p="suite2p",
    ),
)
