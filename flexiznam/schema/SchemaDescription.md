# Data schema

## Presentation

This module handles all the different types of dataset we can have. 
The main functions common to all datasets are implemented in the main
`dataset.Dataset` class. 

Each type of dataset will have a subclass, such as `camera.Camera` that
inherits the main `Dataset` class and can re-implement any methods if needed.

For convenience, all these dataset classes are imported in the
`__init__.py`. You can therefore just do `schema.Camera`. The init also 
populate the `Dataset` class property `Dataset.SUBCLASSES` which lists all
the existing subclasses. It is a dictionary with flexilims datatype name as
keys and the corresponding class object as reference.

## Usage

The simpler entry points are the class methods: `Dataset.from_folder` and
`Dataset.from_flexilims`.