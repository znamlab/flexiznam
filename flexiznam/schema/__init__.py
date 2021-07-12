"""
This module handles all the different types of dataset we can have.
The main functions common to all datasets are implemented in the main
:py:class:`flexiznam.schema.datasets.Dataset` class.

Each type of dataset will have a subclass, such as
:py:class:`flexiznam.schema.datasets.camera_data.CameraData` that
inherits the main `Dataset` class and can re-implement any methods if needed.

For convenience, all these dataset classes are imported in the
`__init__.py`. You can therefore just use `schema.Camera`. The init also
populate the `Dataset` class property `Dataset.SUBCLASSES` which lists all
the existing subclasses. It is a dictionary with flexilims datatype name as
keys and the corresponding class object as reference.

Usage
-----

The simpler entry points are the class methods:
:py:class:`flexiznam.schema.datasets.Dataset.from_folder` and
:py:class:`flexiznam.schema.datasets.Dataset.from_flexilims`.

"""

from .datasets import Dataset
from .camera_data import CameraData
from .harp_data import HarpData
from .scanimage_data import ScanimageData
from .microscopy_data import MicroscopyData

Dataset.SUBCLASSES['camera'] = CameraData
Dataset.SUBCLASSES['harp'] = HarpData
Dataset.SUBCLASSES['scanimage'] = ScanimageData
Dataset.SUBCLASSES['microscopy'] = MicroscopyData
