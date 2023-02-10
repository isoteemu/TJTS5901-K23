"""
Smoketests
==========

Thease are tests that run in gitlab runner, but they target review or staging
environment.
"""
import requests
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

    deployment_address = deployment_address.rstrip("/")
    resp = requests.get(deployment_address + path, timeout=5)

    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'application/json'

    data = resp.json()

    assert data['sentry_available'] is True, "App reporting that the sentry is not available"
    assert data['database_connectable'] is True, "App reporting that the database is not available"


def test_404(deployment_address, path="/_404"):
    """
    Anti-thesis: Check that the correct error code - 404 - is returned for missing page (:param:`path`)
    """

    deployment_address = deployment_address.rstrip("/")
    resp = requests.get(deployment_address + path, timeout=5)
    assert resp.status_code == 404, f"Expected to receive 404 for path {path}"
    # QED


def test_fronpage_loading(deployment_address):
    """
    Fetch fronpage of our application, and check for known string.
    """
    from test_app import IN_TITLE  # pylint: disable=import-outside-toplevel

    resp = requests.get(deployment_address, timeout=5)

    assert resp.status_code == 200, f"Failed to fetch page {deployment_address}"
    assert IN_TITLE.encode() in resp.content
