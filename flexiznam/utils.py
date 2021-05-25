import pandas as pd


def compare_series(first_series, second_series, series_name=('offline', 'flexilims')):
    """Compare two series and return a dataframe of differences

    Args:
        first_series: first pandas series
        second_series: second pandas series
        series_name: tuple of name for the two series.

    Returns:
        Dataframe of differences
    """
    offline_index = set(second_series.index)
    online_index = set(first_series.index)
    intersection = offline_index.intersection(online_index)
    differences = second_series[intersection].compare(first_series[intersection])
    differences.columns = series_name
    only_offline = offline_index - online_index
    off = pd.DataFrame([second_series[only_offline].rename(series_name[0], axis=0),
                        pd.Series({k: 'N/A' for k in only_offline}, name=series_name[1])])
    differences = pd.concat((differences, off.T))
    only_online = online_index - offline_index
    online = pd.DataFrame([pd.Series({k: 'N/A' for k in only_online}, name=series_name[0]),
                           first_series[only_online].rename(series_name[1], axis=0)])
    differences = pd.concat((differences, online.T))
    return differences
