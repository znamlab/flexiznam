# flexiznam
Znam lab tool to interact with flexilims. Detailed documentation at https://flexiznam.znamlab.org/. Recent updates to the main branch of the repo are described in the [CHANGELOG](CHANGELOG.md).

# Getting started

## Installation

To create a standalone installation, in you favorite `conda` or `venv`, clone the repository and `pip` install:

```
git clone git@github.com:znamlab/flexiznam.git
cd flexiznam
pip install -r requirements.txt
pip install -e .
```

When installing `flexiznam` requirments, `flexilims` will be installed from our Crick github page. Make sure you have access to this repository by setting ssh keys as advised on the github [help page](https://docs.github.com/en/enterprise-server@3.0/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account).

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

## Initial configuration

To set up the flexilims and mcms integration, the config file must be edited. First create the default config by running:

```
flexiznam config
```

This should create a `~/.flexiznam/config.yml` file. Edit it with your favorite text editor to change `flexilims_username`, `mcms_username` and,
if neeed `data_root`.

You can then add passwords to make it simpler by running (one by one):

```
flexiznam add-password -a mcms
flexiznam add-password -a flexilims
```

This will prompt you for a username and a password and create a `~/.flexiznam/secret_password.yml` file. This is not very secure. You can marginally
improve that by running:

```
chmod 700 ~/.flexiznam/secret_password.yml
```

Then you can run:

```
flexiznam config --update
```

Flexiznam should now be able to log in to flexilims automatically and find the project ids to add them to the config file.
## Updating

Once flexiznam is installed, you can also use pip to keep the package updated:
```
pip install --upgrade git+ssh://git@github.com/znamlab/flexiznam.git
```
This will update the package as long as the version of the repository is higher than the one you have installed. After the update, it is advised to update the config file to create potentially new entries. This can be done with:

```
flexiznam config --update
```

If you used `pip -e .` to install, updating can be done with:

```
cd flexiznam
git pull
pip install -e . --upgrade
flexiznam config --update
```

## Configuration

The default configuration settings can be created simply by running: `flexiznam config`. This will create a `~/.flexiznam` directory with a `config.yml` file.

To add newly defined configuration field and set them to their default value, you can run  `flexiznam config --update`. This will not change any existing field or remove any obsolete fields.

The configuration file can be edited manually or using `flexiznam.config.update_config`. The option should be self explaining but in doubt, see the comments in `flexiznam.config.default_config.py`.

## Password management

To simplify the interaction with MCSM and flexilims, you can store a copy of you passwords in `~/.flexiznam/secret_password.yml`. This file can be created and edited manualy. It needs to be a yml file formatted like the template in `flexiznam.config`. Alternatively on can use the CLI:

`flexiznam add-password --app mcms --username myname --password uniquepassword`

# Known issues

## Selenium drivers do not update

When updating chromium, `get_mouse_df` and `add_mouse` can stop working. Updating `webbot` does not solve the issue. The selenirum drivers must manually be [downloaded](https://chromedriver.chromium.org/downloads) and put in the `webbot` install folder. You can `import webbot` and check `webbot.__file__` to find where is that folder. See https://github.com/nateshmbhat/webbot/issues/87
