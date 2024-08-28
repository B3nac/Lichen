from tests.conftest import app_test as flask_app
from src.Lichen.code.forms import UnlockAccountForm, CreateAccountForm, CreateMultipleAccountsForm, LookupAccountForm, SendEtherForm

class TestCreateMultipleAccountsForm:
    def test_create_multiple_accounts_form(self):
        context = flask_app.test_request_context('http://127.0.0.1:5000/create', method='POST')
        context.push()
        CreateMultipleAccountsForm.Meta.csrf = False
        form = CreateMultipleAccountsForm(create_from_mnemonic='0', number_of_accounts=5, submit=True)
        assert form.validate_on_submit() == False

class TestUnlockAccountForm:
    def test_unlock_account_form(self):
        context = flask_app.test_request_context('http://127.0.0.1:5000/account', method='POST')
        context.push()
        UnlockAccountForm.Meta.csrf = False
        form = UnlockAccountForm(account_key='0', submit=True)
        assert form.validate_on_submit() == False

class TestLookupAccountForm:
    def test_lookup_account_form(self):
        context = flask_app.test_request_context('http://127.0.0.1:5000/lookup', method='POST')
        context.push()
        LookupAccountForm.Meta.csrf = False
        form = LookupAccountForm(account_id='0', account_key='meep', submit=True)
        assert form.validate_on_submit() == False

class TestSendEtherForm:
    def test_lookup_account_form(self):
        context = flask_app.test_request_context('http://127.0.0.1:5000/send', method='POST')
        context.push()
        SendEtherForm.Meta.csrf = False
        form = SendEtherForm(to_public_address='0', amount_of_ether='.001', submit=True)
        assert form.validate_on_submit() == False

