Acquisition:
*  files named automatically
*  scanimage creates a directory for each recording
*  file name: `MOUSE_SESSION_RECORDING_PROTOCOL`
*  path: `<DATAROOT>/<MOUSE>/<SESSION>/<RECORDING_PROTOCOL>/...`

YAML file:
*  saved in session folder

File transfer:
*  copy everything
*  parse YAML and populate flexilims

YAML file format:
```
project: <PROJECT>
mouse: <MOUSE>
session: <SESSION>
notes: ""
recordings:
  - protocol:
    timestamp:
    notes:
  - protocol:
    timestamp:
    notes:
datasets:
  - type:
    path:
    notes:
```
