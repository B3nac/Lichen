import json
import os
from datetime import datetime

import eth_utils
from cryptography.fernet import Fernet, InvalidToken
from cryptography.exceptions import InvalidSignature
from flask import Blueprint, render_template, request, flash

from app.forms import CreateAccountForm, UnlockAccountForm, AccountForm, SendEtherForm, CreateLootBundleForm
from app.networks import (
    web3_arbitrum_goerli,
    dai_contract,
    snek_contract_arbitrum_goerli,
    lootbox_contract_arbitrum_bundle_factory
)
from eth_account import Account

index_blueprint = Blueprint('index_blueprint', __name__)
create_lootbundle_blueprint = Blueprint('create_lootbundle_blueprint', __name__)
create_account_blueprint = Blueprint('create_account_blueprint', __name__)
account_blueprint = Blueprint('account_blueprint', __name__)
account_lookup_blueprint = Blueprint('account_lookup_blueprint', __name__)
send_ether_blueprint = Blueprint('send_ether_blueprint', __name__)
send_transaction_blueprint = Blueprint('send_transaction_blueprint', __name__)
replay_transaction_blueprint = Blueprint('replay_transaction_blueprint', __name__)
send_lootbundle_blueprint = Blueprint('send_lootbundle_blueprint', __name__)
delete_accounts_blueprint = Blueprint('delete_accounts_blueprint', __name__)

year: str = str(datetime.now().year)

accounts_list = []

unlocked_account = []

Account.enable_unaudited_hdwallet_features()

unlocked: bool = False

gas_price = web3_arbitrum_goerli.eth.gasPrice


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
            return render_template('account.html', account="unlocked", pub_address=unlocked_account[0],
                                   private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2], form=form)


@create_account_blueprint.route('/create', methods=['GET', 'POST'])
def create_account():
    if request.method == 'GET':
        if os.path.exists("accounts.json"):
            form = UnlockAccountForm()
            return render_template('unlock.html', account="current", form=form, year=year)
        else:
            form = CreateAccountForm()
            return render_template('create.html', form=form)
    if request.method == 'POST':
        new_eth_account, mnemonic = Account.create_with_mnemonic()
        mnemonic_field_value = request.form['create_from_mnemonic']
        number_of_accounts = request.form['number_of_accounts']
        wallet_key = Fernet.generate_key().decode("utf-8")
        if mnemonic_field_value and number_of_accounts:
            multiple_accounts_list = []
            no_plaintext = Fernet(wallet_key)
            number_of_accounts = int(number_of_accounts)
            try:
                if os.path.exists("accounts.json"):
                    with open('accounts.json', 'r') as account_check:
                        current_accounts = json.load(account_check)

                    for account in range(number_of_accounts):
                        try:
                            if current_accounts[account]:
                                print("Account exists!!!!!")
                        except IndexError:
                            multiple_accounts_list.append(account)
                if not os.path.exists("accounts.json"):
                    if number_of_accounts == '':
                        number_of_accounts = 0
                    for number in range(number_of_accounts):
                        new_eth_account = Account.from_mnemonic(mnemonic_field_value,
                                                                account_path=f"m/44'/60'/0'/0/{number}")
                        pub_address = new_eth_account.address
                        private_key = no_plaintext.encrypt(bytes(new_eth_account.key.hex(), encoding='utf8'))
                        mnemonic_phrase = no_plaintext.encrypt(bytes(mnemonic_field_value, encoding='utf8'))
                        save_account_info(pub_address, mnemonic_phrase, private_key, number)
                    multiple_accounts_list.clear()
                    form = AccountForm()
                    return render_template('account.html', account="new", pub_address=new_eth_account.address,
                                           private_key=new_eth_account.key.hex(),
                                           mnemonic_phrase=mnemonic_field_value, wallet_key=wallet_key, form=form, year=year)
            except Exception as e:
                flash(f"{e}, french.", 'warning')
                form = CreateAccountForm()
                return render_template('create.html', account="new", form=form, year=year)
        else:
            try:
                form = AccountForm()
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


def populate_public_address_list():
    public_address_list = []
    with open('accounts.json', 'r') as accounts_from_file:
        account_data_json = json.load(accounts_from_file)
        for account_id in account_data_json:
            try:
                public_address_list.append(account_data_json[account_id['id']])
            except IndexError as e:
                flash(f"{e}, No account exists with id {account_id}.", 'warning')
    return public_address_list


@account_blueprint.route('/account', methods=['GET', 'POST'])
def account():
    if request.method == 'POST':
        try:
            form = AccountForm()
            account_unlock_key = request.form['account_key']
            no_plaintext = Fernet(account_unlock_key)
            with open('accounts.json', 'r') as accounts_from_file:
                account_data_json = json.load(accounts_from_file)
                pub_address = account_data_json[int(0)]['public_address']
                decrypt_private_key = no_plaintext.decrypt(
                    bytes(account_data_json[int(0)]['private_key'], encoding='utf8')).decode('utf-8')
                decrypt_mnemonic_phrase = no_plaintext.decrypt(
                    bytes(account_data_json[int(0)]['mnemonic_phrase'], encoding='utf8')).decode('utf-8')
                unlocked_account.append(pub_address)
                unlocked_account.append(decrypt_private_key)
                unlocked_account.append(decrypt_mnemonic_phrase)
                global unlocked
                unlocked = True
                wei_balance = web3_arbitrum_goerli.eth.get_balance(pub_address)
        except (InvalidSignature, InvalidToken):
            flash("Invalid account key", 'warning')
            form = UnlockAccountForm()
            return render_template('unlock.html', account="current", form=form, year=year)
        else:
            return render_template('account.html', account="unlocked", pub_address=pub_address,
                               private_key=decrypt_private_key, mnemonic_phrase=decrypt_mnemonic_phrase,
                               account_list=populate_public_address_list(), form=form, year=year,
                               account_balance=round(web3_arbitrum_goerli.fromWei(wei_balance, 'ether'), 2))
    if request.method == 'GET':
        if not unlocked:
            if not os.path.exists("accounts.json"):
                flash("No accounts exist, please create an account.", 'warning')
                form = CreateAccountForm()
                return render_template('create.html', account="new", form=form)
        if unlocked:
            form = AccountForm()
            pub_address = unlocked_account[0]
            private_key = unlocked_account[1]
            mnemonic_phrase = unlocked_account[2]
            wei_balance = web3_arbitrum_goerli.eth.get_balance(pub_address)
            return render_template('account.html', account="unlocked", pub_address=pub_address,
                                   private_key=private_key, mnemonic_phrase=mnemonic_phrase,
                                   account_list=populate_public_address_list(), form=form, year=year,
                                   account_balance=round(web3_arbitrum_goerli.fromWei(wei_balance, 'ether'), 2))
        else:
            form = UnlockAccountForm()
            return render_template('unlock.html', account="current", form=form, year=year)


@account_lookup_blueprint.route('/lookup', methods=['POST'])
def account_lookup():
    if request.method == 'POST':
        form = AccountForm()
        account_unlock_key = request.form['account_key']
        no_plaintext = Fernet(account_unlock_key)
        lookup_account = request.form['account_id']
        with open('accounts.json', 'r') as accounts_from_file:
            account_data_json = json.load(accounts_from_file)
            pub_address = account_data_json[int(lookup_account)]['public_address']
            decrypt_private_key = no_plaintext.decrypt(
                bytes(account_data_json[int(lookup_account)]['private_key'], encoding='utf8')).decode('utf-8')
            decrypt_mnemonic_phrase = no_plaintext.decrypt(
                bytes(account_data_json[int(lookup_account)]['mnemonic_phrase'], encoding='utf8')).decode('utf-8')
        wei_balance = web3_arbitrum_goerli.eth.get_balance(unlocked_account[0])
        return render_template('account.html', account="unlocked", pub_address=pub_address,
                               private_key=decrypt_private_key, mnemonic_phrase=decrypt_mnemonic_phrase,
                               account_list=populate_public_address_list(),
                               account_balance=round(web3_arbitrum_goerli.fromWei(wei_balance, 'ether'), 2),
                               form=form, year=year)


@send_ether_blueprint.route('/send', methods=['GET'])
def send():
    if request.method == 'GET':
        if not unlocked:
            if not os.path.exists("accounts.json"):
                flash("No accounts exist, please create an account.", 'warning')
                form = CreateAccountForm()
                return render_template('create.html', account="new", form=form)
            else:
                form = UnlockAccountForm()
                return render_template('unlock.html', account="current", form=form, year=year)
        if os.path.exists("accounts.json"):
            if unlocked:
                form = SendEtherForm()
                return render_template('send.html', account="unlocked", form=form)
            if not unlocked:
                form = UnlockAccountForm()
                return render_template('unlock.html', account="current", form=form)


@send_transaction_blueprint.route('/send_transaction', methods=['POST'])
def send_transaction():
    if request.method == 'POST' and unlocked:
        form = AccountForm()
        to_account = request.form['to_public_address']
        amount = request.form['amount_of_ether']
        try:
            tx = {
                'nonce': web3_arbitrum_goerli.eth.get_transaction_count(unlocked_account[0], 'pending'),
                'to': to_account,
                'value': web3_arbitrum_goerli.toWei(amount, 'ether'),
                'gas': web3_arbitrum_goerli.toWei('0.03', 'gwei'),
                'gasPrice': gas_price,
                'from': unlocked_account[0]
            }
            sign = web3_arbitrum_goerli.eth.account.sign_transaction(tx, unlocked_account[1])
            web3_arbitrum_goerli.eth.send_raw_transaction(sign.rawTransaction)

            flash('Transaction sent successfully!', 'success')
        except Exception as e:
            flash(e, 'warning')
        wei_balance = web3_arbitrum_goerli.eth.get_balance(unlocked_account[0])
        return render_template('account.html', account="unlocked", pub_address=unlocked_account[0],
                               private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2],
                               account_list=populate_public_address_list(),
                               account_balance=round(web3_arbitrum_goerli.fromWei(wei_balance, 'ether'), 2),
                               form=form, year=year)
    else:
        form = UnlockAccountForm()
        return render_template('unlock.html', account="current", form=form, year=year)


@replay_transaction_blueprint.route('/replay', methods=['POST'])
def replay_transaction():
    if request.method == 'POST' and unlocked:
        tx = request.form['tx_hash']
        tx_hash = web3_arbitrum_goerli.eth.get_transaction(tx)

        replay_tx = {
            'to': tx_hash['to'],
            'from': tx_hash['from'],
            'value': tx_hash['value'],
            'data': tx_hash['input'],
        }

        try:
            status = web3_arbitrum_goerli.eth.call(replay_tx, tx_hash.blockNumber - 1)
            newlines = "\n\n"
            return render_template('transaction_data.html', account="unlocked", to=tx_hash['to'],
                                   from_data=tx_hash['from'], value=tx_hash['value'],
                                   data=tx_hash['input'], status=status, newlines=newlines, year=year)
        except Exception as e:
            flash(f"{e}", 'warning')
            status = web3_arbitrum_goerli.eth.call(replay_tx, tx_hash.blockNumber - 1)
            return render_template('transaction_data.html', account="unlocked", to=tx_hash['to'],
                                   from_data=tx_hash['from'], value=tx_hash['value'], data=tx_hash['input'],
                                   status=status, year=year)


@create_lootbundle_blueprint.route('/createlootbundle', methods=['GET'])
def createlootbundle():
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
                                   private_key=private_key, mnemonic_phrase=mnemonic_phrase, form=form, year=year)
        if unlocked:
            form = CreateLootBundleForm()
            return render_template('createlootbundle.html', account="unlocked", form=form, year=year)


@send_lootbundle_blueprint.route('/send_lootbundle_transaction', methods=['POST'])
def send_lootbundle_transaction():
    if request.method == 'POST':
        if unlocked:
            try:
                # Approve transaction
                approve = snek_contract_arbitrum_goerli.functions.approve('0x587B0a60a97a60e9B00dbAE03Bd50DffF2cAbB78',
                                                                 10000000000000000000).buildTransaction(
                    {'chainId': 421613, 'gas': web3_arbitrum_goerli.toWei('0.03', 'gwei'),
                     'gasPrice': gas_price,
                     'nonce': web3_arbitrum_goerli.eth.get_transaction_count(unlocked_account[0], 'pending'),
                     'from': unlocked_account[0]})

                sign_approve = web3_arbitrum_goerli.eth.account.sign_transaction(approve, unlocked_account[1])
                web3_arbitrum_goerli.eth.send_raw_transaction(sign_approve.rawTransaction)

                # Create bundle
                create_bundle = lootbox_contract_arbitrum_bundle_factory.functions.createBundle(10000000000000000000)\
                    .buildTransaction(
                    {'chainId': 421613, 'gas': web3_arbitrum_goerli.toWei('0.03', 'gwei'),
                     'gasPrice': gas_price,
                     'nonce': web3_arbitrum_goerli.eth.get_transaction_count(unlocked_account[0], 'pending'),
                     'from': unlocked_account[0]})

                sign_create_bundle = web3_arbitrum_goerli.eth.account.sign_transaction(create_bundle, unlocked_account[1])
                web3_arbitrum_goerli.eth.send_raw_transaction(sign_create_bundle.rawTransaction)
                flash('LootBundle created successfully!', 'success')
            except Exception as e:
                flash(e, 'warning')
        form = AccountForm()
        wei_balance = web3_arbitrum_goerli.eth.get_balance(unlocked_account[0])
        return render_template('account.html', account="unlocked", pub_address=unlocked_account[0],
                               private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2],
                               account_list=populate_public_address_list(),
                               account_balance=round(web3_arbitrum_goerli.fromWei(wei_balance, 'ether'), 2),
                               form=form, year=year,
                               lootbundles=lootbox_contract_arbitrum_bundle_factory.functions.allBundles().call())


@delete_accounts_blueprint.route('/delete', methods=['POST'])
def delete_accounts():
    form = CreateAccountForm()
    if os.path.exists("accounts.json"):
        os.remove("accounts.json")
        return render_template('create.html', account="new", form=form, year=year)
    else:
        flash("No accounts exist", 'warning')
        return render_template('create.html', account="new", form=form, year=year)
