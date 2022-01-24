import flexiznam
import pytest
import yaml
from flexiznam.camp import sync_data
from tests.tests_resources import data_for_testing


def test_clean_yaml(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    miniaml, faml = acq_yaml_and_files.get_example_yaml_files()
    path_to_full_yaml = tmp_path / 'full_yaml.yml'
    path_to_mini_yaml = tmp_path / 'mini_yaml.yml'
    with open(path_to_mini_yaml, 'w') as minifile:
        yaml.dump(miniaml, minifile)
    with open(path_to_full_yaml, 'w') as fullfile:
        yaml.dump(faml, fullfile)

    sync_data.clean_yaml(path_to_mini_yaml)
    sync_data.clean_yaml(path_to_full_yaml)


def test_parse_yaml(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    miniaml, faml = acq_yaml_and_files.get_example_yaml_files()
    path_to_full_yaml = tmp_path / 'full_yaml.yml'
    path_to_mini_yaml = tmp_path / 'mini_yaml.yml'
    with open(path_to_mini_yaml, 'w') as minifile:
        yaml.dump(miniaml, minifile)
    with open(path_to_full_yaml, 'w') as fullfile:
        yaml.dump(faml, fullfile)

    m = sync_data.parse_yaml(path_to_mini_yaml, raw_data_folder=tmp_path, verbose=False)
    assert len(m) == 9
    # there should not be any error
    errs = sync_data.find_xxerrorxx(yml_data=m)
    assert not errs

    # I should be able to re-parse the output
    target = tmp_path / 'parsed.yml'
    sync_data.write_session_data_as_yaml(session_data=m, target_file=target)
    sync_data.parse_yaml(target, raw_data_folder=tmp_path, verbose=False)
    # test error
    sess_data = sync_data.parse_yaml(path_to_full_yaml, raw_data_folder=tmp_path,
                                     verbose=False)
    errs = sync_data.find_xxerrorxx(yml_data=sess_data)
    assert len(errs) == 4


def test_write_yaml(tmp_path):
    acq_yaml_and_files.create_acq_files(tmp_path)
    miniaml, faml = acq_yaml_and_files.get_example_yaml_files()
    path_to_full_yaml = tmp_path / 'full_yaml.yml'
    with open(path_to_full_yaml, 'w') as fullfile:
        yaml.dump(faml, fullfile)
    sess_data = sync_data.parse_yaml(path_to_full_yaml, raw_data_folder=tmp_path,
                                     verbose=False)
    target = tmp_path / 'target_out.yml'
    pure_yaml = sync_data.write_session_data_as_yaml(session_data=sess_data,
                                                     target_file=target)

    def rec_test(d, name='root'):
        for k, v in d.items():
            bad = False
            if isinstance(v, dict):
                rec_test(v, name=name + '/' + k)
            elif isinstance(v, list):
                if any([not (isinstance(el, str) or (el is None)) for el in v]):
                    bad = True
            elif not isinstance(v, str):
                if v is None:
                    continue
                bad = True
            if bad:
                raise IOError('Potentially invalid yaml. It contains: %s in %s of %s' %
                              (v, k, name))
    rec_test(pure_yaml)
    with open(target, 'r') as reader:
        reload = yaml.safe_load(reader)
    assert reload == pure_yaml


@pytest.mark.integtest
def test_upload(tmp_path, flm_sess):
    session_name = acq_yaml_and_files.create_acq_files(tmp_path, session_name='unique')
    miniaml, faml = acq_yaml_and_files.get_example_yaml_files(session_name=session_name)
    path_to_mini_yaml = tmp_path / 'mini_yaml.yml'
    with open(path_to_mini_yaml, 'w') as fullfile:
        yaml.dump(miniaml, fullfile)

    sync_data.upload_yaml(source_yaml=path_to_mini_yaml, raw_data_folder=tmp_path,
                          flexilims_session=flm_sess)

    # check that a session has been properly created
    sess_name = miniaml['mouse'] + '_' + miniaml['session']
    s = flexiznam.get_entity(datatype='session', name=sess_name,
                             flexilims_session=flm_sess)
    assert s is not None
    r = flexiznam.get_children(s['id'], 'recording', flexilims_session=flm_sess)
    for _, rec in r.iterrows():
        rec_name = rec['name']
        assert rec_name.startswith(sess_name)
        d = flexiznam.get_children(rec['id'], 'dataset', flexilims_session=flm_sess)
        for _, ds in d.iterrows():
            assert ds['name'].startswith(rec_name)

    # doing it again will crash
    with pytest.raises(flexiznam.FlexilimsError):
        sync_data.upload_yaml(source_yaml=path_to_mini_yaml, raw_data_folder=tmp_path,
                              flexilims_session=flm_sess)
    # but is fine with `skip`
    sync_data.upload_yaml(source_yaml=path_to_mini_yaml, raw_data_folder=tmp_path,
                          flexilims_session=flm_sess, conflicts='skip')

    parsed = sync_data.parse_yaml(path_to_yaml=path_to_mini_yaml,
                                  raw_data_folder=tmp_path)
    path_to_parsed = tmp_path / 'parsed_mini_yaml.yml'
    sync_data.write_session_data_as_yaml(parsed, target_file=path_to_parsed,
                                         overwrite=True)
    sync_data.upload_yaml(source_yaml=path_to_parsed, raw_data_folder=tmp_path,
                          flexilims_session=flm_sess, conflicts='skip')
