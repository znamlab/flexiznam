"""File to handle acquisition yaml file and create datasets on flexilims"""


def process_yaml(path_to_yaml):
    """Read a yaml file, check that the data has been transfered and create the flexilims entries"""
    data_structure = parse_yaml(path_to_yaml)
