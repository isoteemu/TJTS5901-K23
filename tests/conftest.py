from os import environ
import pytest
from flask import Flask
from faker import Faker
from werkzeug.security import generate_password_hash


from tjts5901.app import create_app


def pytest_addoption(parser: pytest.Parser):
    """
    Callback to add command-line options for pytest.

    Add option to define environment url to test.

    Usage example from agruments::
        $ pytest --environment-url "https://example.com"

    Note: GitLab CI automatically sets environment variable `CI_ENVIRONMENT_URL`
    to the address of environment to test.

    Usage example from environment variable::
        $ CI_ENVIRONMENT_URL="https://example.com" pytest

    Note: If you want to test locally, you can define environment variable in
    .env file.
    """

    parser.addoption("--environment-url",
                     dest="CI_ENVIRONMENT_URL",
                     help="Deployment webaddress",
                     default=environ.get("CI_ENVIRONMENT_URL"))


@pytest.fixture(scope="session")
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


@pytest.fixture(scope='session', autouse=True)
def faker_session_locale(app: Flask):
    """
    Fixture to set faker locale.

    This fixture is autouse, so it will be applied to all tests.
    """
    languages = []
    with app.app_context():
        for locale in app.extensions['babel'].instance.list_translations():
            languages.append(str(locale))

    return languages


@pytest.fixture()
def user(app: Flask, faker: Faker):
    """
    User fixture.

    Creates a user into database and returns it.
    """

    from tjts5901.models import User

    print(faker.locales[0])

    with app.app_context():
        password = faker.password()
        user = User(
            email=faker.email(),
            password=generate_password_hash(password),
            locale=f"{faker.locales[0]}.UTF-8",
        )
        user.save()
        setattr(user, '_plaintext_password', password)

        yield user

        user.delete()

