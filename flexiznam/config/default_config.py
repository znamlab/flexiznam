"""
This file is used to generate the initial config file
"""

DEFAULT_CONFIG = dict(
    # MCMS configuration:
    download_folder='~/Downloads',  # folder use to download files by your default web browser
    mcms_username='yourusername',
    # Flexilims configuration
    # If you want to access projects by name, add their hexadecimal ID here:
    project_ids={"3d_vision": "606df5af08df4d77c72c9b05",
                 "virus_tests": "607f145d25d64b66227b00be",
                 "test": "606df1ac08df4d77c72c9aa4",
                 "AAVRKO_retina_hva": "60a7757a8901a2357f29080a",
                 },
    # a default username can be specified
    flexilims_username='yourusername',
    # Use for data dataset detection
    data_root=dict(raw='/camp/lab/znamenskiyp/data/instruments/raw_data/projects',
                   processed='/camp/lab/znamenskiyp/home/shared/projects'),
    # list of all datatypes
    datatypes=['mouse', 'session', 'recording', 'dataset', 'sample'],
    # list of valid dataset type
    dataset_types=['scanimage', 'camera', 'ephys', 'suite2p_rois', 'suite2p_traces',
                     'harp', 'microscopy'],

    # list of extensions accepted as `MicroscopyData`
    microscopy_extensions=['.czi', '.png', '.gif', '.tif', '.tiff']
)
