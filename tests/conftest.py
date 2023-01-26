import pytest
from flask import Flask

from tjts5901.app import create_app


@pytest.fixture
def app():
    """
    Application fixture.

    Every test that requires `app` as parameter can use this fixture.

    Example:
    >>> def test_mytest(app: Flask):
    >>>     ...
    """
    _app = create_app({
        'TESTING': True,
        'DEBUG': False,

        # We need to set SERVER_NAME and PREFERRED_URL_SCHEME for testing.
        'SERVER_NAME': 'localhost',
        'PREFERRED_URL_SCHEME': 'http',
    })

    # If you have done ties4080 course and have used Flask-WTF, you might
    # have noticed that CSRF protection is enabled by default. This is
    # problematic for testing, because we don't have a browser to generate
    # CSRF tokens. We can disable CSRF protection for testing, but we need
    # to make sure that we don't have CSRF protection enabled in production.

    # _app.config['WTF_CSRF_ENABLED'] = False
    # _app.config['WTF_CSRF_METHODS'] = []
    # _app.config['WTF_CSRF_CHECK_DEFAULT'] = False

    _app.testing = True
    yield _app

    # Do some cleanup here if needed.
    ...


@pytest.fixture
def client(app: Flask):
    """
    Setup testing client.

    See:
    https://flask.palletsprojects.com/en/2.2.x/testing/#the-testing-skeleton
    https://werkzeug.palletsprojects.com/en/2.2.x/test/#werkzeug.test.Client
    """

    # Setup all the context needed for client to work.
    with app.test_client() as test_client:
        with app.app_context():
            yield test_client


