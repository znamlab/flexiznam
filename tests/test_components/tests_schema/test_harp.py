def test_harp(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    data_dir = tmp_path / 'PZAH4.1c/S20210513/ParamLog/R193432_Retinotopy'
    ds = HarpData.from_folder(data_dir, verbose=False)
    assert len(ds) == 1
    d = next(iter(ds.values()))
    assert d.name == next(iter(ds.keys()))
    assert d.is_valid()
    assert len(d.csv_files) == 5