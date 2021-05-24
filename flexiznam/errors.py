class NameNotUniqueException(Exception):
    """
    Mouse name does not correspond to exactly 1 entry
    """
    pass


class ConfigurationError(Exception):
    """
    The configuration file cannot be loaded
    """
    pass


class SyncYmlError(Exception):
    """
    The YAML file used for synchronisation is invalid
    """
    pass


class DatasetError(Exception):
    """
    Cannot automatically deal with this dataset
    """

class FlexilimsError(Exception):
    """
    I cannot do that on flexilims
    """