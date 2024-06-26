from flask import session
from flask_wtf import FlaskForm
from wtforms.csrf.session import SessionCSRF
from wtforms import StringField, SubmitField, validators, BooleanField, IntegerField
from wtforms.widgets import PasswordInput
from wtforms.validators import InputRequired, Length
from datetime import timedelta
import string
import secrets

alphabet = string.ascii_letters + string.digits
random = ''.join(secrets.choice(alphabet) for i in range(15))


class CreateAccountForm(FlaskForm):
    create = SubmitField('Create new account')

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session


class CreateAppTokenForm(FlaskForm):
    create = SubmitField('Create app token')
    app_name = StringField('App name', validators=[InputRequired(), Length(max=50)])
    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session

class CreateMultipleAccountsForm(FlaskForm):
    create_from_mnemonic = StringField('Create account from mnemonic', validators=[InputRequired()])
    number_of_accounts = StringField('Create multiple accounts from mnemonic', validators=[InputRequired()])
    create_multiple = SubmitField('Create multiple accounts')

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session


class LookupAccountForm(FlaskForm):
    account_search = SubmitField('Lookup account')
    account_key = StringField('Account unlock key', validators=[InputRequired(), Length(min=44, max=44)],
                              widget=PasswordInput(hide_value=True))
    account_id = IntegerField('Account id', validators=[InputRequired(), Length(min=1, max=50)])

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session


class UnlockAccountForm(FlaskForm):
    account_key = StringField('Account unlock key', validators=[InputRequired(), Length(min=44, max=44)])
    submit = SubmitField('Unlock account')

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session


class SendEtherForm(FlaskForm):
    to_public_address = StringField('To public address', validators=[InputRequired(), Length(min=0, max=42)])
    amount_of_ether = StringField('Amount of Ether to send', validators=[InputRequired(), Length(min=0, max=42)])
    submit = SubmitField('Verify')

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session


class SendVerifyForm(FlaskForm):
    gas_amount = StringField('Amount of gas', validators=[InputRequired(), Length(min=0, max=42)])
    submit = SubmitField('Send')

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session


class SettingsForm(FlaskForm):
    network = StringField('Network endpoint', validators=[InputRequired()])
    default_address = StringField('Default Ethereum address', validators=[InputRequired(), Length(min=42, max=42)])
    ens_mainnet_node = StringField('ENS mainnet endpoint', validators=[InputRequired()])
    submit = SubmitField('Save')

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session
