# Testing flexiznam

## Organisation

Tests are separated in two:

- Main use cases found in the main test folder 
- Test of individual components found in `test_components`
 
The `test_components` should cover most of the code but are not user friendly. The 
main use cases are example scripts that could be use for a real experiment.

## Data

Example datasets are available in the 
raw data folder on camp `data/instruments/raw_data/projects/demo_project/`.
A corresponding preprocessed folder is also used by tests.

## Notes:

### MCMS
To test the MCMS part, you need a graphical interface and a browser. It is also 
particularly slow.

To avoid having to run it every time, the tests are marked as slow and require the 
`--runslow` flag to be executed. This is False by default

### Flexilims
For interaction with flexilims, you need to be connected via the crick network 
(vpn or from the crick). Neither is easily doable on github workflow. Furthermore 
flexilims does not have an API to delete entries. You will have clean it manually 
before running the tests

To make things simpler, the tests requiring flexilims or mcms are marked as integration 
tests. They can be skipped by running `pytest -m "not integtest"`.

To run the tests, you need to clear flexilims yourself (as there is no API to delete 
stuff).  