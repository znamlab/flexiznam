import datetime
import os
import pathlib
import re

from flexiznam.schema.datasets import Dataset


class HarpData(Dataset):
    DATASET_TYPE = 'harp'

    @classmethod
    def from_folder(cls, folder, verbose=True, flm_session=None, project=None):
        """Create a harp dataset by loading info from folder"""
        fnames = [f for f in os.listdir(folder) if f.endswith(('.csv', '.bin'))]
        bin_files = [f for f in fnames if f.endswith('.bin')]
        csv_files = [f for f in fnames if f.endswith('.csv')]
        if not bin_files:
            raise IOError('Cannot find binary file')

        output = {}
        matched_files = set()
        for bin_file in bin_files:
            m = re.match(r'(.*?)_?harpmessage_?(.*?).bin', bin_file)
            if not m:
                if verbose:
                    print('%s is not a binary harp file: `_harpmessage_` is not in '
                          'file name.' % bin_file)
                continue

            pattern = '(.*)'.join(m.groups()) + '.csv'
            matches = [re.match(pattern, f) for f in csv_files]
            associated_csv = {m.groups()[0].strip('_'): f for f, m in
                              zip(csv_files, matches) if m}
            if matched_files.intersection(associated_csv.values()):
                raise IOError('A csv file matched with multiple binary files.')
            matched_files.update(associated_csv.values())

            bin_path = pathlib.Path(folder) / bin_file
            created = datetime.datetime.fromtimestamp(bin_path.stat().st_mtime)
            extra_attributes = dict(binary_file=bin_file,
                                    csv_files=associated_csv,
                                    )
            output[bin_file[:-4]] = HarpData(name=bin_file[:-4],
                                             path=folder,
                                             extra_attributes=extra_attributes,
                                             created=created.strftime(
                                                 '%Y-%m-%d %H:%M:%S'),
                                             flm_session=flm_session,
                                             project=project)
        if verbose:
            unmatched = set(csv_files) - matched_files
            if unmatched and verbose:
                print('%d csv files did not match any binary file:' % len(unmatched))
                for m in unmatched:
                    print('    %s' % m)
        return output

    def __init__(self, path, is_raw=None, name=None, extra_attributes=None,
                 created=None, project=None, project_id=None, origin_id=None,
                 flm_session=None):
        """Create a Harp dataset

        Args:
            path: folder containing the dataset or path to file (valid only for single
                  file datasets)
            is_raw: bool, used to sort in raw and processed subfolders
            name: name of the dataset as on flexilims. Is expected to include mouse,
                  session etc...
            extra_attributes: dict, optional attributes.
            created: Creation date, in "YYYY-MM-DD HH:mm:SS"
            project: name of the project. Must be in config, can be guessed from
                     project_id
            project_id: hexadecimal code for the project. Must be in config, can be
                        guessed from project
            origin_id: hexadecimal code for the origin on flexilims.
            flm_session: authentication session to connect to flexilims

        Expected extra_attributes:
            binary_file: File name of the binary file.
            csv_files (optional): Dictionary of csv files associated to the binary file.
                                  Keys are identifier provided for convenience,
                                  values are the full file name
        """
        if 'binary_file' not in extra_attributes:
            raise IOError('Harp dataset require `binary_file` in their extra_attributes')

        super().__init__(name=name, path=path, is_raw=is_raw,
                         dataset_type=HarpData.DATASET_TYPE,
                         extra_attributes=extra_attributes, created=created,
                         project=project, project_id=project_id,
                         origin_id=origin_id, flm_session=flm_session)

    @property
    def binary_file(self):
        return self.extra_attributes.get('binary_file', None)
    
    @binary_file.setter
    def binary_file(self, value):
        self.extra_attributes['binary_file'] = str(value)
        
    @property
    def csv_files(self):
        return self.extra_attributes.get('csv_files', None)
    
    @csv_files.setter
    def csv_files(self, value):
        self.extra_attributes['csv_files'] = str(value)
        
    def is_valid(self):
        """Check that video, metadata and timestamps files exist"""
        if not (pathlib.Path(self.path) / self.binary_file).exists():
            return False
        for _, file_path in self.csv_files.items():
            if not (pathlib.Path(self.path) / file_path).exists():
                return False
        return True
