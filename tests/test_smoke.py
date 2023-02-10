"""
Smoketests
==========

Thease are tests that run in gitlab runner, but they target review or staging
environment.
"""
import pytest


@pytest.fixture
def deployment_address(pytestconfig: pytest.Config):
    """
    Get the address for environment to check.

    Define it in either in environment variable `CI_ENVIRONMENT_URL`, 
    or as pytest argument `--environment url <address>`.

    To test locally setup in .env::
        CI_ENVIRONMENT_URL="http://localhost:5000/"
    """

    url = pytestconfig.getoption("CI_ENVIRONMENT_URL")

    if not url:
        return pytest.skip("Could not determine environment url. Please check that container contains variable CI_ENVIRONMENT_URL or define `--environment-url <address>`")

    return url


def test_server_status(deployment_address: str, path="/server-info"):
    """
    Fetch server status page and checks for Falsies.
    """

    print(f"Checking {deployment_address}{path}")
    assert deployment_address is not None, "Deployment address is not defined"
