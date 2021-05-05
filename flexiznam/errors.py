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