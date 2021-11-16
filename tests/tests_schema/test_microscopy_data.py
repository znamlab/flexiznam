def test_microscopy_data(tmp_path):
    acq_yaml_and_files.create_sample_file(tmp_path)
    ds = MicroscopyData.from_folder(tmp_path / 'PZAH4.1c' / 'left_retina', verbose=False,
                                    mouse=None, flm_session=None)
    assert len(ds) == 5
    d = ds['Stitch_A01_S4_IPL_layer.png']
    assert d.name == 'Stitch_A01_S4_IPL_layer.png'
    assert d.is_valid()
