# Change log

## v0.2.2

- Names of files associated with `CameraData`, `HarpData` and `ScanimageData` datasets are now stored as extra attributes on Flexilims and not passed as separate arguments to the class constructors.
- `ScanimageData` are now detected by checking if TIFFs have metadata created by Scanimage, which can take a few seconds per dataset. Filenames of `ScanimageData` TIFFs have to follow the SI naming convention (`<acqname>_<acqnumber>_<filenumber>.tif` or `<acqname>_<acqnumber>.tif`, e.g. `zstack_00001_00001.tif`). Files from the same acquisition are grouped in the same datasst and their filenames are stored in the database. The benefit of this is that multiple acquisitions, each with multiple files, can now be stored in the same directory. This could create backward compatibility issues if you are using the `ScanimageData` class to access existing database entries. However, there should be no issues if you are only using it to add new data with `parse_yaml`.
