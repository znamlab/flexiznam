"""Lab specific code. Depends of on our schema"""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("flexiznam")
except PackageNotFoundError:
    # package is not installed
    pass

from .main import *
from . import utils
from .schema import Dataset
