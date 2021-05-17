"""Creating and modifying the config file used for file transfer"""
from flexiznam import PARAMETERS

DEFAULT_CAMP_CONFIG = dict(data_source='path/to/raw/data/',  # where to read the data, should contain a folder per mouse
                           data_target=PARAMETERS['projects_root'],  # where to copy the data, default to 'projects_root'
                           target_subfolder='raw',  # subfolder created inside each project folder to copy data
                           )

