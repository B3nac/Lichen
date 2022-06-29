import requests


def test_index_route_get():
    response = requests.get("http://localhost:40682/")
    if "Unlock account" in response.text:
        assert True
    else:
        assert False


def test_index_route_post():
    response = requests.post("http://localhost:40682/")
    assert response.status_code == 405


def test_account_route_get():
    response = requests.get("http://localhost:40682/account")
    if "Unlock account" in response.text:
        assert True
    else:
        assert False


def test_account_route_post():
    response = requests.get("http://localhost:40682/account")
    assert response.status_code == 200


def test_account_lookup_route_get():
    response = requests.get("http://localhost:40682/lookup")
    assert response.status_code == 405


def test_account_lookup_route_post():
    response = requests.post("http://localhost:40682/lookup")
    assert response.status_code == 400


def test_account_create_route_get():
    response = requests.get("http://localhost:40682/create")
    assert response.status_code == 200


def test_account_create_route_post():
    response = requests.get("http://localhost:40682/create")
    assert response.status_code == 200


def test_send_route_get():
    response = requests.get("http://localhost:40682/send")
    assert response.status_code == 200


def test_send_transaction_route_get():
    response = requests.get("http://localhost:40682/send_transaction")
    assert response.status_code == 405


def test_send_transaction_route_post():
    response = requests.post("http://localhost:40682/send_transaction")
    assert response.status_code == 500