from conftest import app_test as flask_app
import requests


def test_index_route_get():
    response = requests.get("http://localhost:45380/")
    if "Unlock account" in response.text:
        assert True
    else:
        assert False


def test_account_route_get():
    response = requests.get("http://localhost:45380/account")
    if "Unlock account" in response.text:
        assert True
    else:
        assert False


def test_account_lookup_route_get():
    response = requests.get("http://localhost:45380/lookup")
    assert response.status_code == 405


def test_account_lookup_route_post():
    response = requests.post("http://localhost:45380/lookup")
    assert response.status_code == 400
