import pathlib
from pathlib import PurePosixPath

import pandas as pd

from flexiznam.schema import Dataset


def compare_series(first_series, second_series, series_name=('first', 'second')):
    """Compare two series and return a dataframe of differences

    Args:
        first_series: first :py:class:`pandas.Series`
        second_series: second :py:class:`pandas.Series`
        series_name: tuple of name for the two series.

    Returns:
        :py:class:`pandas.DataFrame`: DataFrame of differences
    """
    second_index = set(second_series.index)
    first_index = set(first_series.index)
    intersection = second_index.intersection(first_index)
    differences = first_series[intersection].compare(second_series[intersection])
    differences.columns = series_name
    only_in_first = first_index - second_index
    first_s = pd.DataFrame([pd.Series({k: 'NA' for k in only_in_first},
                                      name=series_name[1]),
                           first_series[only_in_first].rename(series_name[0], axis=0)])
    differences = pd.concat((differences, first_s.T))
    only_in_second = second_index - first_index
    second_s = pd.DataFrame([second_series[only_in_second].rename(series_name[1], axis=0),
                             pd.Series({k: 'NA' for k in only_in_second},
                                       name=series_name[0])])
    differences = pd.concat((differences, second_s.T))
    return differences


def clean_dictionary_recursively(dictionary, keys=(), path2string=True,
                                 format_dataset=False):
    """Recursively clean a dictionary inplace

    Args:
        dictionary: dict (of dict)
        keys (list): list of keys to pop from the dictionary
        path2string (bool): replace :py:class:`pathlib.Path` object by their
            string representation (default True)
        format_dataset (bool): replace :py:class:`flexiznam.schema.Dataset`
            instances by their yaml representation (default False)
    """

    if isinstance(keys, str):
        keys = [keys]
    for k in keys:
        dictionary.pop(k, None)
    if format_dataset:
        ds_classes = set(Dataset.SUBCLASSES.values())
        ds_classes.add(Dataset)
    for k, v in dictionary.items():
        if isinstance(v, dict):
            clean_dictionary_recursively(v, keys, path2string, format_dataset)
        if path2string and isinstance(v, pathlib.Path):
            dictionary[k] = str(PurePosixPath(v))
            print('THIS IS NEW VER.', flush=True)
        if format_dataset:
            if any([isinstance(v, cls) for cls in ds_classes]):
                ds_dict = v.format(mode='yaml')
                # we have now a dictionary with a flat structure. Reshape it to match
                # what acquisition yaml are supposed to look like
                for field in ['name', 'project', 'type']:
                    ds_dict.pop(field, None)

                # rename extra_attributes to match acquisition yaml.
                # Making a copy with dict is required to write yaml later on. If I keep
                # the reference the output file has `*id001` instead of `{}`
                ds_dict['attributes'] = dict(ds_dict.pop('extra_attributes', {}))
                dictionary[k] = ds_dict
