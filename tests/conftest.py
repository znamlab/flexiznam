from copy import deepcopy

import pytest

import flexiznam
from flexiznam.config import DEFAULT_CONFIG
from tests.tests_resources import flexilims_session
from tests.tests_resources.data_for_testing import PROJECT_ID, TEST_PROJECT

flexiznam.PARAMETERS.clear()
flexiznam.PARAMETERS.update(deepcopy(DEFAULT_CONFIG))
flexiznam.PARAMETERS["project_ids"][TEST_PROJECT] = PROJECT_ID


@pytest.fixture
def flm_sess():
    flexilims_session.project_id = flexiznam.PARAMETERS["project_ids"][TEST_PROJECT]
    return flexilims_session


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run tests that require external services or lab data",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line(
        "markers", "integration: mark test as requiring external services or data"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
        if "integration" in item.keywords and not config.getoption("--run-integration"):
            item.add_marker(skip_integration)
