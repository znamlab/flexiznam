import datetime
import os
import pathlib
import re

from flexiznam.schema.datasets import Dataset


class HarpData(Dataset):
    DATASET_TYPE = 'harp'

    @classmethod
    def from_folder(cls, folder, verbose=True, flm_session=None):
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
            output[bin_file[:-4]] = HarpData(name=bin_file[:-4],
                                             path=folder,
                                             binary_file=bin_file,
                                             csv_files=associated_csv,
                                             created=created.strftime(
                                                 '%Y-%m-%d %H:%M:%S'),
                                             flm_session=flm_session)
        if verbose:
            unmatched = set(csv_files) - matched_files
            if unmatched and verbose:
                print('%d csv files did not match any binary file:' % len(unmatched))
                for m in unmatched:
                    print('    %s' % m)
        return output

    @classmethod
    def from_flexilims(cls, project=None, name=None, data_series=None, flm_session=None):
        """Create a harp dataset from flexilims entry"""
        raise NotImplementedError

    def __init__(self, name, path, binary_file, csv_files=None, extra_attributes=None,
                 created=None, project=None, is_raw=True, flm_session=None):
        """Create a Harp dataset

        Args:
            name: Identifier. Unique name on flexilims. Import default to the file name of
                  the binary file without the extension
            path: Path to the folder containing all the files
            binary_file: File name of the binary file.
            csv_files: Dictionary of csv files associated to the binary file. Keys are
                       identifier provided for convenience, values are the full file name
            extra_attributes: Other optional attributes (from or for flexilims)
            created: Date of creation. Default to the creation date of the binary file
            project: name of hexadecimal id of the project to which the dataset belongs
            is_raw: default to True. Is it processed data or raw data?
            flm_session: authentication session for connecting to flexilims
        """
        super().__init__(name=name, path=path, is_raw=is_raw,
                         dataset_type=HarpData.DATASET_TYPE,
                         extra_attributes=extra_attributes, created=created,
                         project=project, flm_session=flm_session)
        self.binary_file = binary_file
        self.csv_files = csv_files if csv_files is not None else {}

    def is_valid(self):
        """Check that video, metadata and timestamps files exist"""
        if not (pathlib.Path(self.path) / self.binary_file).exists():
            return False
        for _, file_path in self.csv_files.items():
            if not (pathlib.Path(self.path) / file_path).exists():
                return False
        return True
