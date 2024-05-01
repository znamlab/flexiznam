from flexiznam.config import config_tools

ymlfile = "/camp/home/blota/home/users/blota/temp/s20230605_valid.yml"
from flexiznam.camp import sync_data as sd

o = sd.parse_yaml(ymlfile)


config_folder = None
fname = config_tools._find_file("config.yml", config_folder=config_folder)
prm = config_tools.load_param(param_folder=config_folder)
config_tools.update_config(
    param_file="config.yml", config_folder=config_folder, add_all_projects=True, **prm
)
