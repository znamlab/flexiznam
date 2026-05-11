from tests.tests_resources.mock_flexilims import MockFlexilims
from .data_for_testing import populate_test_data, PROJECT_ID

flexilims_session = MockFlexilims(project_id=PROJECT_ID)
populate_test_data(flexilims_session)
