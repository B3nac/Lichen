from app.tests.conftest import app_test as flask_app
from ..forms import UnlockAccountForm


class TestAccountForm:
    def test_account_form(client):
        context = flask_app.test_request_context('http://127.0.0.1:5000/account', method='POST')
        context.push()
        UnlockAccountForm.Meta.csrf = False
        form = UnlockAccountForm(account_key='0', submit=True)
        assert form.validate_on_submit() == False