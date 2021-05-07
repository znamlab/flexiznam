#!/bin/bash

# Don't forget to activate your virtual environment before running this script

# get the code
git clone git@github.com:znamlab/flexiznam.git
# install dependencies
cd flexiznam
pip install -r requirements.txt
# install flexiznam
pip install -e .
# configure
flexiznam config



