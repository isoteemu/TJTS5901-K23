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
    flask_app = create_app({
        'TESTING': True,
        'DEBUG': False,

        # We need to set SERVER_NAME and PREFERRED_URL_SCHEME for testing.
        'SERVER_NAME': 'localhost.localdomain',
        'PREFERRED_URL_SCHEME': 'http',
    })

    # If you have done ties4080 course and have used Flask-WTF, you might
    # have noticed that CSRF protection is enabled by default. This is
    # problematic for testing, because we don't have a browser to generate
    # CSRF tokens. We can disable CSRF protection for testing, but we need
    # to make sure that we don't have CSRF protection enabled in production.

    # flask_app.config['WTF_CSRF_ENABLED'] = False
    # flask_app.config['WTF_CSRF_METHODS'] = []
    # flask_app.config['WTF_CSRF_CHECK_DEFAULT'] = False

    flask_app.testing = True
    yield flask_app

    # Do some cleanup here if needed.
    ...


@pytest.fixture
def client(app):
    return app.test_client()

