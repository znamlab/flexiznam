import pandas as pd


def compare_series(first_series, second_series, series_name=('first', 'second')):
    """Compare two series and return a dataframe of differences

    Args:
        first_series: first pandas series
        second_series: second pandas series
        series_name: tuple of name for the two series.

    Returns:
        Dataframe of differences
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
