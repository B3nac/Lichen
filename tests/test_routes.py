from conftest import app_test as flask_app
import requests

def test_index_route():
    response = requests.get("http://localhost:27081/")
    if "Unlock account" in response.text:
        assert True
    else:
        assert False


def test_account_route():
    response = requests.get("http://localhost:27081/account")
    if "Unlock account" in response.text:
        assert True
    else:
        assert False
