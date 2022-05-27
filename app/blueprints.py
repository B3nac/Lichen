import json
import os
from eth_account import Account
import eth_utils
from datetime import datetime

from cryptography.fernet import Fernet
from flask import Blueprint, render_template, request, flash

from app.networks import (
    web3_arbitrum_rinkeby,
    dai_contract_rinkeby,
    web3_local_rinkeby,
    lootbox_contract_arbitrum_bundle
)
from app.forms import CreateAccountForm, UnlockAccountForm, AccountForm, SendEtherForm, CreateLootBundleForm

index_blueprint = Blueprint('index_blueprint', __name__)
create_lootbundle_blueprint = Blueprint('create_lootbundle_blueprint', __name__)
create_account_blueprint = Blueprint('create_account_blueprint', __name__)
account_blueprint = Blueprint('account_blueprint', __name__)
send_ether_blueprint = Blueprint('send_ether_blueprint', __name__)
send_transaction_blueprint = Blueprint('send_transaction_blueprint', __name__)
send_lootbundle_blueprint = Blueprint('send_lootbundle_blueprint', __name__)

year = str(datetime.now().year)

accounts_list = []

Account.enable_unaudited_hdwallet_features()

unlocked: bool = False

gas_price = web3_arbitrum_rinkeby.eth.gasPrice


@index_blueprint.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        if not os.path.exists("accounts.json"):
            form = CreateAccountForm()
            return render_template('create.html', account="new", form=form, year=year)
        if os.path.exists("accounts.json") and not unlocked:
            form = UnlockAccountForm()
            return render_template('unlock.html', account="current", form=form, year=year)
        if os.path.exists("accounts.json") and unlocked:
            form = AccountForm()
            return render_template('account.html', account="unlocked", pub_address=accounts_list[0],
                                   private_key=accounts_list[1], mnemonic_phrase=accounts_list[2], form=form)


@create_account_blueprint.route('/create', methods=['GET', 'POST'])
def create_account():
    form = CreateAccountForm()
    if request.method == 'GET':
        return render_template('create.html', form=form)
    if request.method == 'POST':
        new_eth_account, mnemonic = Account.create_with_mnemonic()
        wallet_key = Fernet.generate_key().decode("utf-8")
        no_plaintext = Fernet(wallet_key)
        mnemonic_field_value = request.form.get('create_from_mnemonic')
        number_of_accounts = request.form.get('number_of_accounts')
        if mnemonic_field_value and number_of_accounts:
            multiple_accounts_list = []
            try:
                if os.path.exists("accounts.json"):
                    with open('accounts.json', 'r') as account_check:
                        current_accounts = json.load(account_check)

                for account in range(int(number_of_accounts)):
                    try:
                        if current_accounts[account]:
                            print("Account exists!!!!!")
                    except IndexError:
                        multiple_accounts_list.append(account)
                for number in multiple_accounts_list:
                    new_eth_account = Account.from_mnemonic(mnemonic_field_value,
                                                            account_path=f"m/44'/60'/0'/0/{number}")
                    pub_address = new_eth_account.address
                    private_key = no_plaintext.encrypt(bytes(new_eth_account.key.hex(), encoding='utf8'))
                    mnemonic_phrase = no_plaintext.encrypt(bytes(mnemonic_field_value, encoding='utf8'))
                    save_account_info(pub_address, mnemonic_phrase, private_key, number)
                multiple_accounts_list.clear()
                return render_template('unlock.html', account="current", form=form, year=year)
            except Exception as e:
                flash(f"{e}, french.", 'warning')
                return render_template('create.html', account="new", form=form, year=year)
            except eth_utils.exceptions.ValidationError as e:
                flash(f"{e}, toast.", 'warning')
                return render_template('create.html', account="new", form=form, year=year)
        else:
            try:
                form = AccountForm()
                wallet_key = Fernet.generate_key().decode("utf-8")
                create_account_callback(new_eth_account, mnemonic, wallet_key)
                return render_template('account.html', account="new", pub_address=new_eth_account.address,
                                       private_key=new_eth_account.key.hex(),
                                       mnemonic_phrase=mnemonic, wallet_key=wallet_key, form=form)
            except eth_utils.exceptions.ValidationError as e:
                flash(f"{e}, probably incorrect format.", 'warning')


def create_account_callback(new_eth_account, mnemonic, wallet_key):
    if not os.path.exists("accounts.json"):
        account_id = 0
        no_plaintext = Fernet(wallet_key)
        pub_address = new_eth_account.address
        private_key = no_plaintext.encrypt(bytes(new_eth_account.key.hex(), encoding='utf8'))
        mnemonic_phrase = no_plaintext.encrypt(bytes(mnemonic, encoding='utf8'))
        save_account_info(pub_address, mnemonic_phrase, private_key, account_id)


def save_account_info(pub_address, mnemonic_phrase, private_key, account_id):
    account_info = {'id': int(account_id), 'public_address': str(pub_address),
                    'private_key': str(private_key.decode("utf-8")),
                    'mnemonic_phrase': str(mnemonic_phrase.decode("utf-8"))}
    accounts_list.append(account_info)
    json.dump(accounts_list, open('accounts.json', 'w'))


@account_blueprint.route('/account', methods=['GET', 'POST'])
def account():
    if request.method == 'POST':
        public_address_list = []
        form = AccountForm()
        account_unlock_key = request.form['account_unlock_key']
        no_plaintext = Fernet(account_unlock_key)
        with open('accounts.json', 'r') as accounts_from_file:
            account_data_json = json.load(accounts_from_file)
            for account_id in range(10):
                try:
                    if account_data_json[account_id]:
                        public_address_list.append(account_data_json[account_id])
                except IndexError as e:
                    flash(f"{e}, No account exists with id {account_id}.", 'warning')
            pub_address = account_data_json[int(0)]['public_address']
            decrypt_private_key = no_plaintext.decrypt(
                bytes(account_data_json[int(0)]['private_key'], encoding='utf8')).decode('utf-8')
            decrypt_mnemonic_phrase = no_plaintext.decrypt(
                bytes(account_data_json[int(0)]['mnemonic_phrase'], encoding='utf8')).decode('utf-8')
            global unlocked
            unlocked = True
        return render_template('account.html', account="unlocked", pub_address=pub_address,
                               private_key=decrypt_private_key, mnemonic_phrase=decrypt_mnemonic_phrase,
                               account_list=public_address_list, form=form)
    if request.method == 'GET':
        if not unlocked:
            if not os.path.exists("accounts.json"):
                flash("No accounts exist, please create an account.", 'warning')
                form = CreateAccountForm()
                return render_template('create.html', account="new", form=form)
        if unlocked:
            account_unlock_key = request.form['account_unlock_key']
            no_plaintext = Fernet(account_unlock_key)
            with open('accounts.json', 'r') as accounts_from_file:
                account_data_json = json.load(accounts_from_file)
                form = AccountForm()
                pub_address = account_data_json[int(0)]['public_address']
                private_key = no_plaintext.decrypt(bytes(account_data_json[int(0)]['private_key'], encoding='utf8'))
                mnemonic_phrase = no_plaintext.decrypt(bytes(account_data_json[int(0)]['mnemonic_phrase'],
                                                             encoding='utf8'))
            return render_template('account.html', account="unlocked", pub_address=pub_address,
                                   private_key=private_key, mnemonic_phrase=mnemonic_phrase, form=form)
        else:
            form = UnlockAccountForm()
            return render_template('unlock.html', account="current", form=form)


@send_ether_blueprint.route('/send', methods=['GET'])
def send():
    global unlocked
    if request.method == 'GET':
        if not unlocked:
            if not os.path.exists("accounts.json"):
                flash("No accounts exist, please create an account.", 'warning')
                form = CreateAccountForm()
                return render_template('create.html', account="new", form=form)
            if os.path.exists("accounts.json"):
                if unlocked:
                    form = SendEtherForm()
                    return render_template('send.html', account="unlocked", form=form)
                if not unlocked:
                    form = UnlockAccountForm()
                    return render_template('unlock.html', account="current", form=form)


@send_transaction_blueprint.route('/send_transaction', methods=['POST'])
def send_transaction():
    if request.method == 'POST':
        if unlocked:
            to_account = request.form['to_public_address']
            amount = request.form['amount_of_ether']
            try:
                tx = {
                    'nonce': web3_arbitrum_rinkeby.eth.get_transaction_count(accounts_list[0], 'pending'),
                    'to': to_account,
                    'value': web3_arbitrum_rinkeby.toWei(amount, 'ether'),
                    'gas': web3_arbitrum_rinkeby.toWei('0.02', 'gwei'),
                    'gasPrice': gas_price,
                    'from': accounts_list[0]
                }
                sign = web3_arbitrum_rinkeby.eth.account.sign_transaction(tx, accounts_list[1])
                web3_arbitrum_rinkeby.eth.send_raw_transaction(sign.rawTransaction)
                flash('Transaction sent successfully!', 'success')
            except Exception as e:
                flash(e, 'warning')
        return render_template('account.html', account="unlocked", pub_address=accounts_list[0],
                               private_key=accounts_list[1], mnemonic_phrase=accounts_list[2])


@create_lootbundle_blueprint.route('/createlootbundle', methods=['GET'])
def create():
    global unlocked
    if request.method == 'GET':
        if not unlocked:
            form = UnlockAccountForm()
            with open('accounts.json', 'r') as accounts_from_file:
                account_data_json = json.load(accounts_from_file)
                pub_address = account_data_json[int(0)]['public_address']
                private_key = account_data_json[int(0)]['private_key']
                mnemonic_phrase = account_data_json[int(0)]['mnemonic_phrase']
            return render_template('unlock.html', account="current", pub_address=pub_address,
                                   private_key=private_key, mnemonic_phrase=mnemonic_phrase, form=form)
        if unlocked:
            form = CreateLootBundleForm()
            return render_template('createlootbundle.html', account="unlocked", form=form)


@send_lootbundle_blueprint.route('/send_lootbundle_transaction', methods=['POST'])
def send_lootbundle_transaction():
    if request.method == 'POST':
        if unlocked:
            try:
                # Approve transaction
                approve = dai_contract_rinkeby.functions.approve('0xE742e87184f840a559d26356362979AA6de56E3E',
                                                                 10000000000000000000).buildTransaction(
                    {'chainId': 4, 'gas': web3_local_rinkeby.toWei('0.02', 'gwei'),
                     'nonce': web3_local_rinkeby.eth.get_transaction_count(accounts_list[0], 'pending'),
                     'from': accounts_list[0]})

                sign_approve = web3_arbitrum_rinkeby.eth.account.sign_transaction(approve, accounts_list[1])
                web3_local_rinkeby.eth.send_raw_transaction(sign_approve.rawTransaction)

                # Create bundle
                create_bundle = lootbox_contract_arbitrum_bundle.functions.createBundle(
                    10000000000000000000).buildTransaction(
                    {'chainId': 4, 'gas': web3_local_rinkeby.toWei('0.02', 'gwei'),
                     'nonce': web3_local_rinkeby.eth.get_transaction_count(accounts_list[0], 'pending'),
                     'from': accounts_list[0]})

                sign_create_bundle = web3_arbitrum_rinkeby.eth.account.sign_transaction(create_bundle, accounts_list[1])
                web3_arbitrum_rinkeby.eth.send_raw_transaction(sign_create_bundle.rawTransaction)
                flash('LootBundle created successfully!', 'success')
            except Exception as e:
                flash(e, 'warning')
        return render_template('account.html', account="unlocked", pub_address=accounts_list[0],
                               private_key=accounts_list[1], mnemonic_phrase=accounts_list[2])
