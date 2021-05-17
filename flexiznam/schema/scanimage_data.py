import datetime
import os
import pathlib
import re

import pandas as pd
from flexiznam.schema.datasets import Dataset


class ScanimageData(Dataset):
    DATASET_TYPE = 'scanimage'

    @staticmethod
    def from_folder(folder, verbose=True):
        """Create a scanimage dataset by loading info from folder"""
        fnames = [f for f in os.listdir(folder) if f.endswith(('.csv', '.tiff', '.tif'))]
        tif_files = [f for f in fnames if f.endswith(('.tif', '.tiff'))]
        csv_files = [f for f in fnames if f.endswith('.csv')]
        if not tif_files:
            raise IOError('Cannot find any tif file')

        # scanimage files finish with _acqnum_filenum.tif. All files with the same filename until acqnum are grouped
        # together
        pattern = '(.*)_(\d*)_(\d*).tiff?'
        matches = [re.match(pattern, f) for f in tif_files]
        tif_df = [dict(filename=f, fname=m.groups()[0], acq_num=m.groups()[1], file_num=m.groups()[2])
                     for f,m in zip(tif_files, matches) if m]
        tif_df = pd.DataFrame(tif_df)
        tif_df['acq_identifier'] = tif_df.fname + tif_df.acq_num

        output = {}
        matched_csv = set()
        for acq_id, acq_df in tif_df.groupby('acq_identifier'):
            # find if there is any corresponding csv
            fname = acq_df.fname.iloc[0]
            acq_num = acq_df.acq_num.iloc[0]
            associated_csv = {f for f in csv_files if f.startswith(fname) and f.endswith(acq_num + '.csv')}
            if associated_csv in matched_csv:
                raise IOError('A csv file matched with 2 scanimage tif datasets')
            matched_csv.update(associated_csv)

            example_tif = pathlib.Path(folder) / acq_df.filename.iloc[0]
            created = datetime.datetime.fromtimestamp(example_tif.stat().st_mtime)
            output[bin_file[:-4]] = ScanimageData(name=bin_file[:-4], path=folder,
                                         tif_files=list(acq_df.filename.values),
                                         csv_files=associated_csv,
                                         created=created.strftime('%Y-%m-%d %H:%M:%S'))


        if verbose:
            unmatched = set(csv_files) - matched_csv
            if unmatched and verbose:
                print('%d csv files did not match any binary file:')
                for m in unmatched:
                    print('    %s' % m)
        return output

    def from_flexilims(project=None, name=None, flm_rep=None):
        """Create a camera dataset from flexilims entry"""
        raise NotImplementedError


    def __init__(self, name, path, tif_files, csv_files={}, extra_attributes={}, created=None, project=None,
                 is_raw=True):
        """Create a Scanimage dataset

        Args:
            name: Identifier. Unique name on flexilims. Import default to the file name of the binary file without
                  the extension
            path: Path to the folder containing all the files
            tif_files: List of
            csv_files: Dictionary of csv files associated to the binary file. Keys are identifier provided for
                       convenience, values are the full file name
            extra_attributes: Other optional attributes (from or for flexilims)
            created: Date of creation. Default to the creation date of the binary file
            project: name of hexadecimal id of the project to which the dataset belongs
            is_raw: default to True. Is it processed data or raw data?
        """
        super().__init__(name=name, path=path, is_raw=is_raw, dataset_type=ScanimageData.DATASET_TYPE,
                         extra_attributes=extra_attributes, created=created, project=project)
        self.binary_file = binary_file
        self.csv_files = csv_files

    def is_valid(self):
        """Check that video, metadata and timestamps files exist"""
        if not (pathlib.Path(self.path) / self.binary_file).exists():
            return False
        for _, file_path in self.csv_files.items():
            if not (pathlib.Path(self.path) / file_path).exists():
                return False
        return True