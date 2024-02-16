import json
import os
from datetime import datetime
from web3.exceptions import TransactionNotFound
from requests.exceptions import MissingSchema

import eth_utils
from cryptography.fernet import Fernet, InvalidToken
from cryptography.exceptions import InvalidSignature
from flask import Blueprint, render_template, request, flash, abort

from TheLootBoxWallet.code.forms import (
    CreateAccountForm,
    UnlockAccountForm,
    ReplayTransactionForm,
    SendEtherForm,
    CreateMultipleAccountsForm,
    LookupAccountForm,
    SendVerifyForm,
    SettingsForm
)
from TheLootBoxWallet.code.networks import (
    __location__,
    config_file,
    address,
    network,
    ens_mainnet_address,
    ens_resolver,
    logs,
    configparser
)
from eth_account import Account
from TheLootBoxWallet.code.custom_logs import logger

index_blueprint = Blueprint('index_blueprint', __name__)
create_account_blueprint = Blueprint('create_account_blueprint', __name__)
create_fresh_account_blueprint = Blueprint('create_fresh_account_blueprint', __name__)
account_blueprint = Blueprint('account_blueprint', __name__)
account_lookup_blueprint = Blueprint('account_lookup_blueprint', __name__)
send_ether_blueprint = Blueprint('send_ether_blueprint', __name__)
send_verify_blueprint = Blueprint('send_verify_blueprint', __name__)
send_transaction_blueprint = Blueprint('send_transaction_blueprint', __name__)
replay_transaction_blueprint = Blueprint('replay_transaction_blueprint', __name__)
delete_accounts_blueprint = Blueprint('delete_accounts_blueprint', __name__)
settings_blueprint = Blueprint('settings_blueprint', __name__)

year: str = str(datetime.now().year)

accounts_list = []

unlocked_account = []

Account.enable_unaudited_hdwallet_features()

unlocked: bool = False

accounts_file = "/accounts.json"

tx_list = []


async def get_pub_address_from_config():
    if os.path.exists(__location__ + config_file):
        default_address = address
        if default_address == unlocked_account[0]:
            return default_address
        else:
            return unlocked_account[0]
    else:
        default_address = unlocked_account[0]
        return default_address


@index_blueprint.route('/', methods=['GET'])
async def index():
    if request.method == 'GET':
        if not os.path.exists(__location__ + accounts_file):
            create_account_form = CreateAccountForm()
            form_create_multiple = CreateMultipleAccountsForm()
            return render_template('create.html', account="new", create_account_form=create_account_form,
                                   form_create_multiple=form_create_multiple, year=year)
        if os.path.exists(__location__ + accounts_file) and not unlocked:
            unlock_account_form = UnlockAccountForm()
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)
        if os.path.exists(__location__ + accounts_file) and unlocked:
            lookup_account_form = LookupAccountForm()
            replay_transaction_form = ReplayTransactionForm()
            default_address: str = await get_pub_address_from_config()
            wei_balance = network.eth.get_balance(default_address)
            account_list = await populate_public_address_list()
            return render_template('account.html', account="unlocked", lookup_account_form=lookup_account_form,
                                   replay_transaction_form=replay_transaction_form, pub_address=default_address,
                                   private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2],
                                   account_list=account_list,
                                   account_balance=round(network.from_wei(wei_balance, 'ether'), 2), year=year)


@create_account_blueprint.route('/create', methods=['GET', 'POST'])
async def create_account():
    unlock_account_form = UnlockAccountForm()
    create_account_form = CreateAccountForm()
    form_create_multiple = CreateMultipleAccountsForm()

    if request.method == 'GET':
        if os.path.exists(__location__ + accounts_file) and account != "unlocked":
            flash("Account already exists, please delete the old account.", 'warning')
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)
        else:
            return render_template('create.html', create_account_form=create_account_form,
                                   form_create_multiple=form_create_multiple, year=year)
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
                if os.path.exists(__location__ + accounts_file):
                    with open(__location__ + accounts_file, 'r') as account_check:
                        current_accounts = json.load(account_check)
                    for number in range(number_of_accounts):
                        try:
                            if current_accounts[number]:
                                continue
                        except IndexError:
                            multiple_accounts_list.append(number)
                if not os.path.exists(__location__ + accounts_file):
                    if number_of_accounts == '':
                        number_of_accounts = 0
                    for number in range(number_of_accounts):
                        new_eth_account = Account.from_mnemonic(mnemonic_field_value,
                                                                account_path=f"m/44'/60'/0'/0/{number}")
                        pub_address = new_eth_account.address
                        private_key = no_plaintext.encrypt(bytes(new_eth_account.key.hex(), encoding='utf8'))
                        mnemonic_phrase = no_plaintext.encrypt(bytes(mnemonic_field_value, encoding='utf8'))
                        await save_account_info(pub_address, mnemonic_phrase, private_key, number)
                    multiple_accounts_list.clear()
                    return render_template('account.html', account="new", pub_address=new_eth_account.address,
                                           private_key=new_eth_account.key.hex(),
                                           mnemonic_phrase=mnemonic_field_value, wallet_key=wallet_key, year=year)
            except Exception as e:
                flash(f"{e}", 'warning')
                return render_template('create.html', account="new", create_account_form=create_account_form,
                                       form_create_multiple=form_create_multiple, year=year)
        else:
            flash("Invalid mnemonic phrase", 'warning')
            return render_template('create.html', account="new", create_account_form=create_account_form,
                                   form_create_multiple=form_create_multiple, year=year)


@create_fresh_account_blueprint.route('/create_fresh', methods=['POST'])
async def create_fresh():
    if request.method == 'POST':
        create_account_form = CreateAccountForm()
        form_create_multiple = CreateMultipleAccountsForm()
        new_eth_account, mnemonic = Account.create_with_mnemonic()
        wallet_key = Fernet.generate_key().decode("utf-8")
        try:
            await create_account_callback(new_eth_account, mnemonic, wallet_key)
            return render_template('account.html', account="new", pub_address=new_eth_account.address,
                                   private_key=new_eth_account.key.hex(),
                                   mnemonic_phrase=mnemonic, wallet_key=wallet_key,
                                   create_account_form=create_account_form,
                                   form_create_multiple=form_create_multiple, year=year)
        except eth_utils.exceptions.ValidationError as e:
            flash(f"{e}, probably incorrect format.", 'warning')


async def create_account_callback(new_eth_account, mnemonic, wallet_key):
    if not os.path.exists(__location__ + accounts_file):
        account_id = 0
        no_plaintext = Fernet(wallet_key)
        pub_address = new_eth_account.address
        private_key = no_plaintext.encrypt(bytes(new_eth_account.key.hex(), encoding='utf8'))
        mnemonic_phrase = no_plaintext.encrypt(bytes(mnemonic, encoding='utf8'))
        await save_account_info(pub_address, mnemonic_phrase, private_key, account_id)


async def save_account_info(pub_address, mnemonic_phrase, private_key, account_id):
    account_info = {'id': int(account_id), 'public_address': str(pub_address),
                    'private_key': str(private_key.decode("utf-8")),
                    'mnemonic_phrase': str(mnemonic_phrase.decode("utf-8"))}
    accounts_list.append(account_info)
    with open(__location__ + accounts_file, 'w', encoding='utf-8') as accounts:
        json.dump(accounts_list, accounts, ensure_ascii=False, indent=4)


async def populate_public_address_list():
    public_address_list = []
    with open(__location__ + accounts_file, 'r') as accounts_from_file:
        account_data_json = json.load(accounts_from_file)
        for account_id in account_data_json:
            try:
                public_address_list.append(account_data_json[account_id['id']])
            except IndexError as e:
                flash(f"{e}, No account exists with id {account_id}.", 'warning')
    return public_address_list


async def get_ens_name(default_address):
    try:
        if ens_mainnet_address:
            domain = await ens_resolver.name(default_address)
            if domain is None:
                domain = "No ENS name associated with this address."
        else:
            domain = None
    except Exception:
        flash(f"No ENS name associated with this address.", 'warning')


@account_blueprint.route('/account', methods=['GET', 'POST'])
async def account():
    replay_transaction_form = ReplayTransactionForm()
    create_account_form = CreateAccountForm()
    lookup_account_form = LookupAccountForm()
    unlock_account_form = UnlockAccountForm()
    form_create_multiple = CreateMultipleAccountsForm()
    if request.method == 'POST':
        try:
            account_unlock_key = request.form['account_key']
            no_plaintext = Fernet(account_unlock_key)
            with open(__location__ + accounts_file, 'r') as accounts_from_file:
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
                account_list = await populate_public_address_list()
                default_address: str = await get_pub_address_from_config()
        except (InvalidSignature, InvalidToken, ValueError):
            flash("Invalid account key.", 'warning')
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)
        else:
            try:
                connected = await network.is_connected()
                if connected:
                    default_address: str = await get_pub_address_from_config()
                    ens_name: str = await get_ens_name(default_address)
                    wei_balance = await network.eth.get_balance(default_address)
                    account_balance = await round(network.from_wei(wei_balance, 'ether'), 2)
                else:
                    default_address = pub_address
                    ens_name = ""
                    account_balance = 0
            except Exception:
                default_address = pub_address
                ens_name = "None"
                account_balance = 0
            return render_template('account.html', account="unlocked", pub_address=default_address, ens_name=ens_name,
                                   private_key=decrypt_private_key, mnemonic_phrase=decrypt_mnemonic_phrase,
                                   account_list=account_list, replay_transaction_form=replay_transaction_form,
                                   lookup_account_form=lookup_account_form, year=year,
                                   account_balance=account_balance)
    if request.method == 'GET':
        if not unlocked:
            if not os.path.exists(__location__ + accounts_file):
                flash("No accounts exist, please create an account.", 'warning')
                return render_template('create.html', account="new", create_account_form=create_account_form,
                                       form_create_multiple=form_create_multiple)
        if unlocked:
            default_address: str = await get_pub_address_from_config()
            account_list = await populate_public_address_list()
            private_key = unlocked_account[1]
            mnemonic_phrase = unlocked_account[2]
            try:
                connected = await network.is_connected()
                if connected:
                    ens_name: str = await get_ens_name(default_address)
                    wei_balance = await network.eth.get_balance(default_address)
            except Exception:
                ens_name: str = "None"
                wei_balance = 0
                flash("No internet connection or invalid rpc urls. Please connect and try again", 'warning')
            return render_template('account.html', account="unlocked", pub_address=default_address, ens_name=ens_name,
                                   private_key=private_key, mnemonic_phrase=mnemonic_phrase,
                                   account_list=account_list, replay_transaction_form=replay_transaction_form,
                                   lookup_account_form=lookup_account_form,
                                   year=year,
                                   account_balance=round(network.from_wei(wei_balance, 'ether'), 2))
        else:
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)


@account_lookup_blueprint.route('/lookup', methods=['POST'])
async def account_lookup():
    lookup_account_form = LookupAccountForm()
    replay_transaction_form = ReplayTransactionForm()
    default_address: str = await get_pub_address_from_config()

    if request.method == 'POST':
        try:
            account_unlock_key = request.form['account_key']
            no_plaintext = Fernet(account_unlock_key)
            lookup_account = request.form['account_id']
            with open(__location__ + accounts_file, 'r') as accounts_from_file:
                account_data_json = json.load(accounts_from_file)
                pub_address = account_data_json[int(lookup_account)]['public_address']
                decrypt_private_key = no_plaintext.decrypt(
                    bytes(account_data_json[int(lookup_account)]['private_key'], encoding='utf8')).decode('utf-8')
                decrypt_mnemonic_phrase = no_plaintext.decrypt(
                    bytes(account_data_json[int(lookup_account)]['mnemonic_phrase'], encoding='utf8')).decode('utf-8')
                wei_balance = network.eth.get_balance(pub_address)
                account_list = await populate_public_address_list()
            return render_template('account.html', account="unlocked", pub_address=pub_address,
                                   private_key=decrypt_private_key, mnemonic_phrase=decrypt_mnemonic_phrase,
                                   account_list=account_list,
                                   account_balance=round(network.from_wei(wei_balance, 'ether'), 2),
                                   lookup_account_form=lookup_account_form,
                                   replay_transaction_form=replay_transaction_form, year=year)
        except (InvalidSignature, InvalidToken, ValueError, IndexError):
            flash("Invalid account key or account id", 'warning')
            wei_balance = network.eth.get_balance(default_address)
            account_list = await populate_public_address_list()
            return render_template('account.html', account="unlocked", pub_address=default_address,
                                   private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2],
                                   account_list=account_list,
                                   account_balance=round(network.from_wei(wei_balance, 'ether'), 2),
                                   lookup_account_form=lookup_account_form,
                                   replay_transaction_form=replay_transaction_form, year=year)

        return render_template('account.html', account="unlocked", pub_address=default_address,
                               private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2],
                               account_list=account_list,
                               account_balance=round(network.from_wei(wei_balance, 'ether'), 2),
                               lookup_account_form=lookup_account_form, replay_transaction_form=replay_transaction_form,
                               year=year)


@send_ether_blueprint.route('/send', methods=['GET'])
def send():
    unlock_account_form = UnlockAccountForm()
    create_account_form = CreateAccountForm()
    send_ether_form = SendEtherForm()
    form_create_multiple = CreateMultipleAccountsForm()
    if request.method == 'GET':
        if not unlocked:
            if not os.path.exists(__location__ + accounts_file):
                flash("No accounts exist, please create an account.", 'warning')
                return render_template('create.html', account="new", create_account_form=create_account_form,
                                       form_create_multiple=form_create_multiple, year=year)
            else:
                return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form,
                                       year=year)
        if os.path.exists(__location__ + accounts_file):
            if unlocked:
                return render_template('send.html', account="unlocked", send_ether_form=send_ether_form, year=year)
            if not unlocked:
                return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form,
                                       year=year)


@send_transaction_blueprint.route('/send_verify_transaction', methods=['POST'])
async def send_verify_transaction():
    if request.method == 'POST' and unlocked:
        send_ether_form = SendEtherForm()
        try:
            to_account = request.form['to_public_address']
            amount = request.form['amount_of_ether']
            default_address: str = await get_pub_address_from_config()
            gas_price = await network.eth.gas_price
            send_verify_form = SendVerifyForm()
            if ".eth" in to_account:
                ens_name = ens_resolver.address(to_account)
                if ens_name is None:
                    abort(404, 'ENS address not found or invalid, transaction cancelled.')
                    to_account = ens_name
            tx = {
                'nonce': network.eth.get_transaction_count(default_address, 'pending'),
                'to': to_account,
                'value': network.to_wei(amount, 'ether'),
                'gas': network.to_wei('0.03', 'gwei'),
                'gasPrice': gas_price,
                'from': default_address
            }
            tx_list.append(tx)
            gas_amount = network.eth.estimate_gas(tx)
            return render_template('send_verify_transaction.html', account="unlocked",
                                   send_verify_form=send_verify_form,
                                   gas_amount=gas_amount, year=year)
        except Exception as e:
            flash(f"{e}", 'warning')
            return render_template('send.html', account="unlocked", send_ether_form=send_ether_form, year=year)
        else:
            unlock_account_form = UnlockAccountForm()
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)


@send_transaction_blueprint.route('/send_transaction', methods=['POST'])
async def send_transaction():
    if request.method == 'POST' and unlocked:
        lookup_account_form = LookupAccountForm()
        replay_transaction_form = ReplayTransactionForm()
        default_address: str = await get_pub_address_from_config()
        wei_balance = network.eth.get_balance(default_address)
        account_list = await populate_public_address_list()
        try:
            sign = network.eth.account.sign_transaction(tx_list[0], unlocked_account[1])
            sent_transaction = network.eth.send_raw_transaction(sign.rawTransaction)
            tx_list.clear()
            if logs:
                logger.info(bytes(sent_transaction.hex(), encoding='utf8'))
            flash(
                f'Transaction sent successfully! Transaction hash'
                f'{bytes(sent_transaction.hex(), encoding="utf8").decode("utf-8")}',
                'success')
        except Exception as e:
            if logs:
                logger.debug(e)
            flash(f"{e}", 'warning')
        return render_template('account.html', account="unlocked", pub_address=default_address,
                               private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2],
                               account_list=account_list, lookup_account_form=lookup_account_form,
                               replay_transaction_form=replay_transaction_form,
                               account_balance=round(network.from_wei(wei_balance, 'ether'), 2), year=year)
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
            return render_template('transaction_data.html', account="unlocked", transaction_data=replay_tx,
                                   status=status, year=year)
        except (ValueError, TransactionNotFound) as e:
            flash(f"{e}", 'warning')
            return render_template('transaction_data.html', account="unlocked", year=year)


@delete_accounts_blueprint.route('/delete', methods=['POST'])
def delete_accounts():
    create_account_form = CreateAccountForm()
    form_create_multiple = CreateMultipleAccountsForm()
    if os.path.exists(__location__ + accounts_file):
        os.remove(__location__ + accounts_file)
        return render_template('create.html', account="new", create_account_form=create_account_form,
                               form_create_multiple=form_create_multiple, year=year)
    else:
        flash("No accounts exist.", 'warning')
        return render_template('create.html', account="new", create_account_form=create_account_form,
                               form_create_multiple=form_create_multiple, year=year)


@settings_blueprint.route('/settings', methods=['GET', 'POST'])
def settings():
    settings_form = SettingsForm()
    if request.method == 'GET':
        if os.path.exists(__location__ + accounts_file):
            if unlocked:
                return render_template('settings.html', account="unlocked", settings_form=settings_form, year=year)
            if not unlocked:
                return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form,
                                       year=year)
    if request.method == 'POST' and unlocked:
        try:
            config = configparser.ConfigParser()
            config.read(__location__ + config_file)
            config['DEFAULT']['network'] = request.form['network']
            config['DEFAULT']['default_address'] = request.form['default_address']
            config['DEFAULT']['ens_mainnet_node'] = request.form['ens_mainnet_node']
            with open(__location__ + config_file, 'w') as thelootboxwalletconfig:
                config.write(thelootboxwalletconfig)
                flash("Settings changed successfully!", 'success')
            return render_template('settings.html', account="unlocked", settings_form=settings_form, year=year)
        except Exception as e:
            flash(f"{e}", 'warning')
            return render_template('settings.html', account="unlocked", settings_form=settings_form, year=year)

