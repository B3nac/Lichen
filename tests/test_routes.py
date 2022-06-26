from conftest import app_test as flask_app
import requests

def test_index_route():
    response = requests.get("http://localhost:27081/")
    assert response.status_code == 200
