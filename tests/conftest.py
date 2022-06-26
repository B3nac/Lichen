import pytest
from flask import Flask, request

app_test = Flask(__name__)
app_test.config['TESTING'] = True
app_test.config['SECRET_KEY'] = 'SOFLIPPINRANDOM'
app_test.config['WTF_CSRF_ENABLED'] = False

@pytest.fixture()
def client():
    with app_test.test_client() as client:
        yield client
