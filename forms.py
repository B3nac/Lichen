from flask import session
from flask_wtf import FlaskForm
from wtforms.csrf.session import SessionCSRF
from wtforms import StringField, SubmitField, validators, BooleanField
import os
from datetime import timedelta
import string
import secrets

alphabet = string.ascii_letters + string.digits
random = ''.join(secrets.choice(alphabet) for i in range(15))


class CreateAccountForm(FlaskForm):
    create_from_mnemonic = StringField('Create account from mnemonic', [validators.Length(min=0, max=42)])
    submit = SubmitField('Create new account')

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session


class AccountForm(FlaskForm):
    create_from_mnemonic = StringField('Create account from mnemonic', [validators.Length(min=0, max=42)], id='password')
    show_password = BooleanField('Show account private key', id='check')

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session


class UnlockAccountForm(FlaskForm):
    account_unlock_key = StringField('Account unlock key', [validators.Length(min=0, max=42)])
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
    to_public_address = StringField('To public address', [validators.Length(min=0, max=42)])
    amount_of_ether = StringField('Amount of Ether to send', [validators.Length(min=0, max=42)])
    submit = SubmitField('Send Ether')

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session


class CreateLootBundleForm(FlaskForm):
    submit = SubmitField('Create LootBundle')

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = random.encode()
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session
