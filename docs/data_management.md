# Data Management

Flexiznam provides utilities to detect data and create the corresponding flexilims entities. 

## Usage

### Acquisition

This will work only if the acquisition pipeline works as predicted, that means that at acquisition:

*  files are named automatically
*  scanimage creates a directory for each recording
*  file names are: `MOUSE_SESSION_RECORDING_PROTOCOL`
*  all path are relative to `DATAROOT`: `<DATAROOT>/<MOUSE>/<SESSION>/<RECORDING_PROTOCOL>/...`

### YAML file

The starting point is a YAML file. An example minimal file is in `flexiznam/flexiznam/camp/minimal_acquisition_yaml_example.yml`. A detailed example showing all
optional features called `acquisition_yaml_example.yml` can be found in the same folder.

Briefly the YAML file format is:

```
project: <PROJECT>
mouse: <MOUSE>
session: <SESSION>
notes: "optional notes"
recordings:
  <RECORDING>:
    protocol: protocol_name
    timestamp: [optional, in HHMMSS]
    notes: [optional]
    datasets: [optional]
      <DATASET>: [optional]
        type: dataset type (scanimage for instance)
        path: path to the folder containing the dataset
```

This YAML file must be saved in the session folder. The mouse folder must be named like the mouse, the session folder like the session and the 
recording folder like the recording.

### File transfer

File transfer is not handled by flexiznam. You should transfer all the data to CAMP first. We will just check that it is available. The path to the camp folder containing the projects must be set in the config file


### Validating the YAML

The first step is to validate and autopopulate the YAML. 

`flexiznam process-yaml --source_yaml "path_to_the_yaml.yml"`

File transfer:
*  copy everything
*  parse YAML and populate flexilims


