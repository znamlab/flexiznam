import os
import warnings
# Default values


FLEXILIMS_USERNAME = 'blota'
MCMS_USERNAME = 'ab8'


# Config
DOWNLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'Downloads')
if not os.path.isdir(DOWNLOAD_FOLDER):
    warnings.warn('Download folder does not exist. Check you parameter file')
