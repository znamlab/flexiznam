# flexiznam
Znam lab tool to interact with flexilims

# Getting started

In brief, you can follow the `setup.sh`. For clarifications see below

## Installation

To create a standalone installation, in you favorite `conda` or `venv`, clone the repository and `pip` install:

```
git clone git@github.com:znamlab/flexiznam.git
cd flexiznam
pip install -r requirements.txt
pip install -e .
```

Don't forget to use the `-e` flag when installing flexiznam if you want to be able to edit the code.

To check that the install is successful you can type `flexiznam --help` in a terminal. You can also start python and `import flexiznam`.

If you want to install flexiznam to use it in another repository, then run the following with the corresponding virtual environment active:
```
pip install git+ssh://git@github.com/znamlab/flexiznam.git
```

Once flexiznam is install, you can also use pip to keep the package updated:
```
pip install --upgrade git+ssh://git@github.com/znamlab/flexiznam.git
```

## Configuration

The default configuration settings can be created simply by running: `flexiznam config`. This will create a `~/.flexiznam` directory with a `config.yml` file. 

To add newly defined configuration field and set them to their default value, you can run  `flexiznam config --update`. This will not change any existing field or remove any obsolete fields.

The configuration file can be edited manually or using `flexiznam.config.update_config`. The option should be self explaining but in doubt, see the comments in `flexiznam.config.default_config.py`.

## Password management

To simplify the interaction with MCSM and flexilims, you can store a copy of you passwords in `~/.flexiznam/secret_password.yml`. This file can be created and edited manualy. It needs to be a yml file formatted like the template in `flexiznam.config`. Alternatively on can use the CLI:

`flexiznam add-password --app mcms --username myname --password uniquepassword`

# Usage

## Creating and logging data
See the [data management](docs/data_management.md) guide.

## mcms

This package handle semi-automatic import of data from mcms. It is based on code from Tom Childs.

### Requirements

To use mcms, you need to specify what is your download folder in the flexiznam config file (see configuration). You also require to run the code in a system with a graphical interface and a web browser. There is no API for MCMS, so we will "automanually" click the relevant menus to download data.

### Getting mice

For now a single function exist: `get_mouse_df`. It will log in to mcms, look for a mouse based on it's name and download a one-line csv with the info about that mouse. It will then read the downloaded file, load it in a pandas dataframe and delete the file (to make sure it can be redownloaded without naming issue).

This can also be ran from the CLI using `flexiznam add-mouse`. See `flexiznam add-mouse --help` for documentation.

## Interaction with flexilims

TODO
