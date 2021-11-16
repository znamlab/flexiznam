
def test_scanimage(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    data_dir = tmp_path / 'PZAH4.1c/S20210513/R193432_Retinotopy'
    ds = ScanimageData.from_folder(data_dir, verbose=False)
    assert len(ds) == 1
    d = next(iter(ds.values()))
    assert d.name == 'PZAH4.1c_S20210513_R193432_Retinotopy00001'
    assert d.name == next(iter(ds.keys()))
    assert d.is_valid()
    assert len(d) == 39