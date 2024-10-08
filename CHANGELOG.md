# Change log

## v0.4

### Main changes

- New `SequencingData` class to handle sequencing data
- GUI can now be used to add data to flexilims with `flexiznam gui`
- Add a `conda_envs` field in the config file to use in conjuction with `znamutils`
- `get_children` can work with name or id (instead of id only)
- `check_flexilims_issues` can now add missing paths
- `Dataset.from_origin` has a new `extra_attributes` argument to match online datasets
  with specific attributes only.
- `delete_recursively` can delete all children of an entity
- Offline mode using downloaded copy of the database

### Minor
- `add_mouse` uploads birth and death dates in a human readable format instead.
- Add `conflicts` argument to `add_mouse` to overwrite existing mice
- `get_entities` does not raise warnings anymore if `name` is specified and `datatype`
is not. This is now supported upstream by `flexilims`
- Clearer error message when mouse info cannot be found in MCMS
- `load_param` can print the file used to read config with the `verbose` flag.

### Bugfixes

- `update_config` actually adds the new fields (i.e. fields that are in the default
config but not the local config) to the config file

## v0.3.11

### Bugfixes

- Fix bugs related to raw_data for projects not in main folder
- Add mouse works with alive animals


## v0.3.10

### Main changes

- Make `update_entity` safer by crashing if reserved fields are used as attributes.

## v0.3.9

### Main changes

- Replace crash for conflicting attributes by a warning

## v0.3.8

### Main changes

- Add `get_data_root` function to get `raw` or `processed` root for a project
- `get_children` can filter children by attributes before returning results
- refactor `get_datasets` to be non recursive and add filtering options. Also add
  multiple options to filter datasets and format output
- add `get_datasets_recursively` to get all datasets below a given entity

### Bugfixes

- return empty dataframe if `filter` in `get_children` filters out everything (instead
  of crashing)
- `update_flexilims` correctly uploads tuples parameters
- `update_flexilims` correctly uploads floats and np.float/np.int parameters
- `update_flexilims` can overwrite existing datasets (if `conflicts='overwrite'`)
- Add filelock for token creation to avoid concurrent access and move token to their own
  file

### Minor

- `harp_dataset.from_folder` will now match csv even if there is nothing before or after
  `harpmessage` in the file name (i.e. the file is `harpmessage.bin`, and all csvs in
  the folder will be matched)
- private function `config_tools._find_files` has now  a `create_if_missing` argument to
  create the file if it does not exist

## v0.3.7

### Main changes

- Separate `Dataset.from_dataseries` and `Dataset.from_flexilims` to avoid confusion

### Minor

- `get_children` output is filtered to contain only relevant columns when   `children_datatype` is not None

### Bugfixes
## v0.3.6

### Main changes

- New `SequencingData` class to handle sequencing data
- Add a `conda_envs` field in the config file to use in conjuction with `znamutils`
- `get_children` can work with name or id (instead of id only)

### Minor
- `add_mouse` uploads birth and death dates in a human readable format instead.
- `get_entities` does not raise warnings anymore if `name` is specified and `datatype`
is not. This is now supported upstream by `flexilims`

### Bugfixes

- `update_config` actually adds the new fields (i.e. fields that are in the default
config but not the local config) to the config file

## v0.3.5

### Main changes
- `flz.get_datasets` can return `Dataset` objects instead of path strings if
  `return_paths=False`
- New `OnixData` class to handle Onix data
- `get_flexilims_session` can now re-use token from a previous session
- Add a GUI module.

### Minor
- More generic `clean_recursively` replaces the `clean_dictionary_recursively`. It
  handle more complex nesting and replaces non finite float by their string repr.
- `CameraDataset` metadata can also be `.yml`, not only `.txt`.
- `Dataset.format(mode='yaml')` ensure yaml compatibility. (path to str, tuple to list,
  etc...)
- `add_experimental_session` can be done with `parent_id` (or `parent_name`).
- `add_dataset` can add a dataset to a mouse and does not require genealogy.


### Bugfixes
- Fix [#68](https://github.com/znamlab/flexiznam/issues/68). Dataset.format returns
  always the path in posix format.
- Fix [#88](https://github.com/znamlab/flexiznam/issues/88). Now make attributes JSON
  compatible before uploading to flexilims. This will replace special characters in
  attribute names by `_` in the database.
- Fix [#102](https://github.com/znamlab/flexiznam/issues/102). `add_mouse` now works
  with mice that have special character in their allele.
- `add_recording` and `add_sample` add the value online with the full name (including
  genealogy) rather than the short name.

## v0.3.4

### Main changes

- Use `pymcms` to get mouse data from MCMS
- Make `_lookup_project` non private. It is now `flz.utils.lookup_project`

### Bugfixes

- `clean_dictionary_recursively` replaces ndarray by list, which are JSON-compatible

### Minor

- `flz.lookup_project` uses `PARAMETERS` as default project source.

## v0.3.3

### Main changes
- New entry point: `add_genealogy` to add the genealogy field to existing entries.
- add `enforce_dataset_types` option to `config.yml`. This let the user decide if the
  dataset type must be defined in the config file or can be freely changed.
- `Dataset.from_flexilims` accepts `id` or `name`.

### Bugfixes
- `add_genealogy` now works with scanimage datasets
- `HarpData` does not match csv if the file name is only `harpmessage.bin`.
  See issue #93
- Adapt `add_mouse` to new MCMS page layout
- `config --update` adds fields that are new in the default config to the current config

### Minor
- add `compare_dictionaries_recursively` in `utils`
- switch to `black` formatter
- `Dataset` can now be imported from `flexiznam`

## v0.3.2

### Main changes
- Add CLI function: `check_flexilims_issues` to check for ill-named entity and invalid
  paths
- `update_config` now adds all project_ids to the default config (requires to have
  flexilims access)

### Breaking changes:
- `add_dataset` requires the genealogy argument
- `from_folder` uses a `folder_genealogy` argument instead of the previous `mouse`,
  `session` and ` recording` arguments
- `Dataset` creation requires `genealogy` instead of `name`
- `Dataset` has now a `Dataset.full_name` and `Dataset.short_name` property instead
  of a `Dataset.name`

### Main changes
- `from_origin` has a new `base_name` property to allow multiple datasets of the same
  `dataset_type` below the same origin.

### Minor
- `add_mouse` can be given a dictionary of info instead of reading them from MCMS (to
  allow for manual download)
- `add_experimental_session` uses parent path as base path. It means that parent must
  have a path
- `CameraData.from_folder` has an option to detect partial datasets (i.e. without
  timestamps or metadata)
- Reduce default verbosity of some functions
- `get_flexilims_sessions` can get a session without setting the project_id

## v0.3.0

### Breaking changes:
- All `flm_session` are now `flexilims_session` (harmonise with main functions)

### Main changes
- Compatible with flexilims v0.2. `None` and `''` can both be uploaded.
- Dataset.is_raw can be autodetermined from path. If this fails, it **must** be
  manually set.
- New function and CLI entry: `create_yaml` to create the skeleton of a yaml before
  parsing.
- Extensions for microscopy datasets are now defined in the config file.
- ScanImage datasets have a `stack_type` attribute, default to `calcium`.
- Authorise `overwrite` when adding samples, sessions, recordings, or datasets.
- Add  `flz.utils.check_flexilims_path` to verify that defined paths actually exist.
- Add `flz.utils.check_flexilims_names` to verify that entity names start with their
  parent's name.
- Add `flz.utils.add_genealogy` to add a `genealogy` field to flexilims entries. This
  field contains the list of parents ([mouse, session, recording] for instance) up to
  the short name of the current entity
- Add `flz.utilis.add_missing_paths` to update flexilims to add `path` attribute to
  non-dataset entities that have a genealogy defined. The path is set to `project /
  Path(*genealogy)` if this folder exists in the processed or raw root directory.

### Bugfixes:
  - ScanImage datasets tif files were uploaded as `file_list` instead of `tif_files`
  - ScanImage dataset are recognised as such and not as MicroscopyData


### Misc and minor:
  - `get_entity` and `get_id` can work without specifying `datatype`
  - `get_children` works without specifying datatype
  - Tests are now using real data and require CAMP being mounted and configured.
  - Dataset project is set when setting `Dataset.flexilims_session`


## v0.2.2

- Names of files associated with `CameraData`, `HarpData` and `ScanimageData` datasets are now stored as extra attributes on Flexilims and not passed as separate arguments to the class constructors.
- `ScanimageData` are now detected by checking if TIFFs have metadata consistent with being created by Scanimage. Filenames of `ScanimageData` TIFFs have to follow the SI naming convention (`<acqname>_<acqnumber>_<filenumber>.tif` or `<acqname>_<acqnumber>.tif`, e.g. `zstack_00001_00001.tif`). Files from the same acquisition are grouped in the same dataset and their filenames are stored in the database. The benefit of this is that multiple acquisitions, each with multiple files, can now be stored in the same directory. This could create backward compatibility issues if you are using the `ScanimageData` class to access existing database entries. However, there should be no issues if you are only using it to add new data with `parse_yaml`.
