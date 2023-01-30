import pytest
from tjts5901 import create_app

@pytest.fixture
def app():
    flask_app = create_app({
        'TESTING': True,
    })

    yield flask_app

    ...


@pytest.fixture
def client(app):
    return app.test_client()

