# Change log

##v0.2.3

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
