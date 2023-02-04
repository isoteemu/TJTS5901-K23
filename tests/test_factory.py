from tjts5901 import create_app

def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_hello(client):
    response = client.get('/hello', headers={'Accept-Language': 'en_US'})
    assert response.data == b'Hello, World!'
