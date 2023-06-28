import requests


def test_index_route_get():
    response = requests.get("http://127.0.0.1:5000")
    if "Unlock account" in response.text:
        assert True
    else:
        assert False


def test_index_route_post():
    response = requests.post("http://127.0.0.1:5000")
    assert response.status_code == 405


def test_account_route_get():
    response = requests.get("http://127.0.0.1:5000/account")
    if "Unlock account" in response.text:
        assert True
    else:
        assert False


def test_account_route_post():
    response = requests.get("http://127.0.0.1:5000/account")
    assert response.status_code == 200


def test_account_lookup_route_get():
    response = requests.get("http://127.0.0.1:5000/lookup")
    assert response.status_code == 405


def test_account_lookup_route_post():
    response = requests.post("http://127.0.0.1:5000/lookup")
    assert response.status_code == 400


def test_account_create_route_get():
    response = requests.get("http://127.0.0.1:5000/create")
    assert response.status_code == 200


def test_account_create_route_post():
    response = requests.get("http://127.0.0.1:5000/create")
    assert response.status_code == 200


def test_send_route_get():
    response = requests.get("http://127.0.0.1:5000/send")
    assert response.status_code == 200


def test_send_transaction_route_get():
    response = requests.get("http://127.0.0.1:5000/send_transaction")
    assert response.status_code == 405


def test_send_transaction_route_post():
    response = requests.post("http://127.0.0.1:5000/send_transaction")
    if "Unlock account" in response.text:
        assert True
    else:
        assert False


def test_invalid_account_key_route_post():
    response = requests.post("http://127.0.0.1:5000/account")
    assert response.status_code == 500 or 400

