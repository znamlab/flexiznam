# Testing flexiznam

To test the MCMS part, you need a graphical interface and a browser. 
For interaction with flexilims, you need to be connected via the crick network 
(vpn or from the crick). Neither is easily doable on github workflow.

To make things simpler, the tests requiring flexilims or mcms are marked as integration 
tests. They can be skipped by running `pytest -m "not integtest"`.

Example datasets are available in the 
raw data folder on camp `data/instruments/raw_data/projects/demo_project/`.
A corresponding preprocessed folder is also used by tests. 