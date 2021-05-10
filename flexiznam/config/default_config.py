"""
This file is used to generate the initial config file
"""

config = dict(
    # MCMS configuration:
    download_folder='~/Downloads',
    mcms_username='ab8',
    # Flexilims configuration
    # If you want to access projects by name, add their hexadecimal ID here:
    project_ids={"3d_vision": "606df5af08df4d77c72c9b05",
                 "virus_tests": "607f145d25d64b66227b00be",
                 "test": "606df1ac08df4d77c72c9aa4",
                 },
    # a default username can be specified
    flexilims_username='blota',
)