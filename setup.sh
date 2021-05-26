#!/bin/bash

# Don't forget to activate your virtual environment before running this script
# install dependencies
pip install -r requirements.txt
# install flexiznam
pip install -e .
# configure
flexiznam config
