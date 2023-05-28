# Change log

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
- `add_dataset` can add a dataset to a mouse.

### Bugfixes
- Fix [#68](https://github.com/znamlab/flexiznam/issues/68). Dataset.format returns 
  always the path in posix format.
- Fix [#88](https://github.com/znamlab/flexiznam/issues/88). Now make attributes JSON
  compatible before uploading to flexilims. This will replace special characters in
  attribute names by `_` in the database.

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
