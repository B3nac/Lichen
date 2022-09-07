import json
import os
from datetime import datetime

import eth_utils
from cryptography.fernet import Fernet, InvalidToken
from cryptography.exceptions import InvalidSignature
from flask import Blueprint, render_template, request, flash

from app.forms import (
    CreateAccountForm,
    UnlockAccountForm,
    ReplayTransactionForm,
    SendEtherForm,
    CreateLootBundleForm,
    CreateMultipleAccountsForm,
    LookupAccountForm
)
from app.networks import (
    network,
    snek_contract_arbitrum_goerli,
    lootbox_contract_arbitrum_bundle_factory
)
from eth_account import Account

index_blueprint = Blueprint('index_blueprint', __name__)
create_lootbundle_blueprint = Blueprint('create_lootbundle_blueprint', __name__)
create_account_blueprint = Blueprint('create_account_blueprint', __name__)
create_fresh_account_blueprint = Blueprint('create_fresh_account_blueprint', __name__)
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

gas_price = network.eth.gasPrice

@index_blueprint.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        if not os.path.exists("accounts.json"):
            create_account_form = CreateAccountForm()
            form_create_multiple = CreateMultipleAccountsForm()
            return render_template('create.html', account="new", create_account_form=create_account_form, form_create_multiple=form_create_multiple, year=year)
        if os.path.exists("accounts.json") and not unlocked:
            unlock_account_form = UnlockAccountForm()
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)
        if os.path.exists("accounts.json") and unlocked:
            return render_template('account.html', account="unlocked", pub_address=unlocked_account[0],
                                   private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2])


@create_account_blueprint.route('/create', methods=['GET', 'POST'])
def create_account():
    unlock_account_form = UnlockAccountForm()
    create_account_form = CreateAccountForm()
    form_create_multiple = CreateMultipleAccountsForm()

    if request.method == 'GET':
        if os.path.exists("accounts.json"):
            flash("Account already exists, please delete the old account.", 'warning')
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)
        else:
            return render_template('create.html', create_account_form=create_account_form, form_create_multiple=form_create_multiple)
    if request.method == 'POST':
        new_eth_account, mnemonic = Account.create_with_mnemonic()
        mnemonic_field_value = request.form['create_from_mnemonic']
        number_of_accounts = request.form['number_of_accounts']
        wallet_key = Fernet.generate_key().decode("utf-8")
        if ' ' in mnemonic_field_value and number_of_accounts:
            multiple_accounts_list = []
            no_plaintext = Fernet(wallet_key)
            number_of_accounts = int(number_of_accounts)
            try:
                if os.path.exists("accounts.json"):
                    with open('accounts.json', 'r') as account_check:
                        current_accounts = json.load(account_check)
                    for number in range(number_of_accounts):
                        try:
                            if current_accounts[number]:
                                continue
                        except IndexError:
                            multiple_accounts_list.append(number)
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
                    return render_template('account.html', account="new", pub_address=new_eth_account.address,
                                           private_key=new_eth_account.key.hex(),
                                           mnemonic_phrase=mnemonic_field_value, wallet_key=wallet_key, year=year)
            except Exception as e:
                flash(f"{e}, french.", 'warning')
                return render_template('create.html', account="new", create_account_form=create_account_form,
                                       form_create_multiple=form_create_multiple, year=year)
        else:
            flash("Invalid mnemonic phrase", 'warning')
            return render_template('create.html', account="new", create_account_form=create_account_form,
                                   form_create_multiple=form_create_multiple, year=year)


@create_fresh_account_blueprint.route('/create_fresh', methods=['POST'])
def create_fresh():
    if request.method == 'POST':
        create_account_form = CreateAccountForm()
        form_create_multiple = CreateMultipleAccountsForm()
        new_eth_account, mnemonic = Account.create_with_mnemonic()
        wallet_key = Fernet.generate_key().decode("utf-8")
        try:
            create_account_callback(new_eth_account, mnemonic, wallet_key)
            return render_template('account.html', account="new", pub_address=new_eth_account.address,
                               private_key=new_eth_account.key.hex(),
                               mnemonic_phrase=mnemonic, wallet_key=wallet_key,
                               create_account_form=create_account_form,
                               form_create_multiple=form_create_multiple)
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
    replay_transaction_form = ReplayTransactionForm()
    create_account_form = CreateAccountForm()
    lookup_account_form = LookupAccountForm()
    unlock_account_form = UnlockAccountForm()
    form_create_multiple = CreateMultipleAccountsForm()
    if request.method == 'POST':
        try:
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
                wei_balance = network.eth.get_balance(pub_address)
        except (InvalidSignature, InvalidToken, ValueError):
            flash("Invalid account key", 'warning')
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)
        else:
            return render_template('account.html', account="unlocked", pub_address=pub_address,
                               private_key=decrypt_private_key, mnemonic_phrase=decrypt_mnemonic_phrase,
                               account_list=populate_public_address_list(), replay_transaction_form=replay_transaction_form,
                               lookup_account_form=lookup_account_form, year=year,
                               account_balance=round(network.fromWei(wei_balance, 'ether'), 2))
    if request.method == 'GET':
        if not unlocked:
            if not os.path.exists("accounts.json"):
                flash("No accounts exist, please create an account.", 'warning')
                return render_template('create.html', account="new", create_account_form=create_account_form, form_create_multiple=form_create_multiple)
        if unlocked:
            pub_address = unlocked_account[0]
            private_key = unlocked_account[1]
            mnemonic_phrase = unlocked_account[2]
            wei_balance = network.eth.get_balance(pub_address)
            return render_template('account.html', account="unlocked", pub_address=pub_address,
                                   private_key=private_key, mnemonic_phrase=mnemonic_phrase,
                                   account_list=populate_public_address_list(), replay_transaction_form=replay_transaction_form,
                                   lookup_account_form=lookup_account_form,
                                   year=year,
                                   account_balance=round(network.fromWei(wei_balance, 'ether'), 2),
                                   lootbundles=lootbox_contract_arbitrum_bundle_factory.functions.allBundles().call())
        else:
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)


@account_lookup_blueprint.route('/lookup', methods=['POST'])
def account_lookup():
    lookup_account_form = LookupAccountForm()
    if request.method == 'POST':
        try:
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
            wei_balance = network.eth.get_balance(unlocked_account[0])
        except (InvalidSignature, InvalidToken, ValueError):
            flash("Invalid account key", 'warning')
            wei_balance = network.eth.get_balance(unlocked_account[0])
            return render_template('account.html', account="unlocked", pub_address=unlocked_account[0],
                                   private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2],
                                   account_list=populate_public_address_list(),
                                   account_balance=round(network.fromWei(wei_balance, 'ether'), 2),
                                   year=year)
        return render_template('account.html', account="unlocked", pub_address=pub_address,
                               private_key=decrypt_private_key, mnemonic_phrase=decrypt_mnemonic_phrase,
                               account_list=populate_public_address_list(),
                               account_balance=round(network.fromWei(wei_balance, 'ether'), 2),
                               lookup_account_form=lookup_account_form, year=year,
                               lootbundles=lootbox_contract_arbitrum_bundle_factory.functions.allBundles().call())


@send_ether_blueprint.route('/send', methods=['GET'])
def send():
    unlock_account_form = UnlockAccountForm()
    create_account_form = CreateAccountForm()
    send_ether_form = SendEtherForm()
    form_create_multiple = CreateMultipleAccountsForm()
    if request.method == 'GET':
        if not unlocked:
            if not os.path.exists("accounts.json"):
                flash("No accounts exist, please create an account.", 'warning')
                return render_template('create.html', account="new", create_account_form=create_account_form, form_create_multiple=form_create_multiple)
            else:
                return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)
        if os.path.exists("accounts.json"):
            if unlocked:
                return render_template('send.html', account="unlocked", send_ether_form=send_ether_form)
            if not unlocked:
                return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form)


@send_transaction_blueprint.route('/send_transaction', methods=['POST'])
def send_transaction():
    if request.method == 'POST' and unlocked:
        to_account = request.form['to_public_address']
        amount = request.form['amount_of_ether']
        try:
            tx = {
                'nonce': network.eth.get_transaction_count(unlocked_account[0], 'pending'),
                'to': to_account,
                'value': network.toWei(amount, 'ether'),
                'gas': network.toWei('0.03', 'gwei'),
                'gasPrice': gas_price,
                'from': unlocked_account[0]
            }
            sign = network.eth.account.sign_transaction(tx, unlocked_account[1])
            network.eth.send_raw_transaction(sign.rawTransaction)

            flash('Transaction sent successfully!', 'success')
        except Exception as e:
            flash(e, 'warning')
        lookup_account_form = LookupAccountForm()
        replay_transaction_form = ReplayTransactionForm()
        wei_balance = network.eth.get_balance(unlocked_account[0])
        return render_template('account.html', account="unlocked", pub_address=unlocked_account[0],
                               private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2],
                               account_list=populate_public_address_list(), lookup_account_form=lookup_account_form, replay_transaction_form=replay_transaction_form,
                               account_balance=round(network.fromWei(wei_balance, 'ether'), 2), year=year)
    else:
        unlock_account_form = UnlockAccountForm()
        return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)


@replay_transaction_blueprint.route('/replay', methods=['POST'])
def replay_transaction():
    if request.method == 'POST' and unlocked:
        tx = request.form['tx_hash']
        try:
            tx_hash = network.eth.get_transaction(tx)

            replay_tx = {
                'to': tx_hash['to'],
                'from': tx_hash['from'],
                'value': tx_hash['value'],
                'data': tx_hash['input'],
            }

            status = network.eth.call(replay_tx, tx_hash.blockNumber - 1)
            newlines = "\n\n"
            newline = "\n"
            return render_template('transaction_data.html', account="unlocked", to=tx_hash['to'],
                                   from_data=tx_hash['from'], value=tx_hash['value'],
                                   data=tx_hash['input'], status=status, newlines=newlines, newline=newline, year=year)
        except ValueError as e:
            flash(f"{e}", 'warning')
            return render_template('transaction_data.html', account="unlocked", year=year)


@create_lootbundle_blueprint.route('/createlootbundle', methods=['GET'])
def createlootbundle():
    unlock_account_form = UnlockAccountForm()
    create_lootbundle_form = CreateLootBundleForm()
    global unlocked
    if request.method == 'GET':
        if not unlocked:
            try:
                with open('accounts.json', 'r') as accounts_from_file:
                    account_data_json = json.load(accounts_from_file)
                    pub_address = account_data_json[int(0)]['public_address']
                    private_key = account_data_json[int(0)]['private_key']
                    mnemonic_phrase = account_data_json[int(0)]['mnemonic_phrase']
            except Exception:
                create_account_form=CreateAccountForm()
                form_create_multiple=CreateMultipleAccountsForm()
                flash("No accounts exists, please create a account", 'warning')
                return render_template('create.html', account="new", create_account_form=create_account_form,
                                       form_create_multiple=form_create_multiple)
            return render_template('unlock.html', account="current", pub_address=pub_address,
                                   private_key=private_key, mnemonic_phrase=mnemonic_phrase, unlock_account_form=unlock_account_form, year=year)
        if unlocked:
            return render_template('createlootbundle.html', account="unlocked", create_lootbundle_form=create_lootbundle_form, year=year)


@send_lootbundle_blueprint.route('/send_lootbundle_transaction', methods=['POST'])
def send_lootbundle_transaction():
    if request.method == 'POST':
        if unlocked:
            try:
                # Approve transaction
                approve = snek_contract_arbitrum_goerli.functions.approve('0x587B0a60a97a60e9B00dbAE03Bd50DffF2cAbB78',
                                                                 10000000000000000000).buildTransaction(
                    {'chainId': 421613, 'gas': network.toWei('0.03', 'gwei'),
                     'gasPrice': gas_price,
                     'nonce': network.eth.get_transaction_count(unlocked_account[0], 'pending'),
                     'from': unlocked_account[0]})

                sign_approve = network.eth.account.sign_transaction(approve, unlocked_account[1])
                network.eth.send_raw_transaction(sign_approve.rawTransaction)

                # Create bundle
                create_bundle = lootbox_contract_arbitrum_bundle_factory.functions.createBundle(10000000000000000000)\
                    .buildTransaction(
                    {'chainId': 421613, 'gas': network.toWei('0.03', 'gwei'),
                     'gasPrice': gas_price,
                     'nonce': network.eth.get_transaction_count(unlocked_account[0], 'pending'),
                     'from': unlocked_account[0]})

                sign_create_bundle = network.eth.account.sign_transaction(create_bundle, unlocked_account[1])
                network.eth.send_raw_transaction(sign_create_bundle.rawTransaction)
                flash('LootBundle created successfully!', 'success')
            except Exception as e:
                flash(e, 'warning')
        lookup_account_form = LookupAccountForm()
        replay_transaction_form = ReplayTransactionForm()
        wei_balance = network.eth.get_balance(unlocked_account[0])
        return render_template('account.html', account="unlocked", pub_address=unlocked_account[0],
                               private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2],
                               account_list=populate_public_address_list(), lookup_account_form=lookup_account_form, replay_transaction_form=replay_transaction_form,
                               account_balance=round(network.fromWei(wei_balance, 'ether'), 2), year=year,
                               lootbundles=lootbox_contract_arbitrum_bundle_factory.functions.allBundles().call())


@delete_accounts_blueprint.route('/delete', methods=['POST'])
def delete_accounts():
    create_account_form = CreateAccountForm()
    if os.path.exists("accounts.json"):
        os.remove("accounts.json")
        return render_template('create.html', account="new", create_account_form=create_account_form, year=year)
    else:
        flash("No accounts exist", 'warning')
        return render_template('create.html', account="new", create_account_form=create_account_form, year=year)
