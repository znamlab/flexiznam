# flexiznam
Znam lab tool to interact with flexilims. Detailed documentation at https://flexiznam.znamlab.org/. Recent updates to the main branch of the repo are described in the [CHANGELOG](CHANGELOG.md).

# Getting started

In brief, you can follow the `setup.sh`. For clarifications see below.

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

You can also install the develop branch:
```
pip install git+ssh://git@github.com/znamlab/flexiznam.git@dev
```

Once flexiznam is installed, you can also use pip to keep the package updated:
```
pip install --upgrade git+ssh://git@github.com/znamlab/flexiznam.git
```
This will update the package as long as the version of the repository is higher than the one you have installed.

## Configuration

The default configuration settings can be created simply by running: `flexiznam config`. This will create a `~/.flexiznam` directory with a `config.yml` file.

To add newly defined configuration field and set them to their default value, you can run  `flexiznam config --update`. This will not change any existing field or remove any obsolete fields.

The configuration file can be edited manually or using `flexiznam.config.update_config`. The option should be self explaining but in doubt, see the comments in `flexiznam.config.default_config.py`.

## Password management

To simplify the interaction with MCSM and flexilims, you can store a copy of you passwords in `~/.flexiznam/secret_password.yml`. This file can be created and edited manualy. It needs to be a yml file formatted like the template in `flexiznam.config`. Alternatively on can use the CLI:

`flexiznam add-password --app mcms --username myname --password uniquepassword`
