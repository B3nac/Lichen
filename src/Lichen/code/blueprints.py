import os
from datetime import datetime
from web3.exceptions import TransactionNotFound
from requests.exceptions import MissingSchema
import eth_utils
from cryptography.fernet import Fernet, InvalidToken
from cryptography.exceptions import InvalidSignature
from flask import Blueprint, render_template, request, flash, abort

from Lichen.code.forms import (
    CreateAccountForm,
    UnlockAccountForm,
    SendEtherForm,
    CreateMultipleAccountsForm,
    LookupAccountForm,
    SendVerifyForm,
    SettingsForm
)
from Lichen.code.networks import (
    address,
    network,
    ens_mainnet_address,
    ens_resolver,
    logs,
    configparser
)

from eth_account import Account
from Lichen.code.custom_logs import logger
from Lichen.code import utils

index_blueprint = Blueprint('index_blueprint', __name__)
create_account_blueprint = Blueprint('create_account_blueprint', __name__)
create_fresh_account_blueprint = Blueprint('create_fresh_account_blueprint', __name__)
account_blueprint = Blueprint('account_blueprint', __name__)
account_lookup_blueprint = Blueprint('account_lookup_blueprint', __name__)
send_ether_blueprint = Blueprint('send_ether_blueprint', __name__)
send_verify_blueprint = Blueprint('send_verify_blueprint', __name__)
send_transaction_blueprint = Blueprint('send_transaction_blueprint', __name__)
delete_accounts_blueprint = Blueprint('delete_accounts_blueprint', __name__)
settings_blueprint = Blueprint('settings_blueprint', __name__)
sign_and_send_blueprint = Blueprint('sign_and_send_blueprint', __name__)

year: str = str(datetime.now().year)

accounts_list = []

unlocked_account = []

Account.enable_unaudited_hdwallet_features()

unlocked: bool = False

tx_list = []


@index_blueprint.route('/', methods=['GET'])
async def index():
    if request.method == 'GET':
        if not os.path.exists(utils.__location__ + utils.accounts_file):
            create_account_form = CreateAccountForm()
            form_create_multiple = CreateMultipleAccountsForm()
            return render_template('create.html', account="new", create_account_form=create_account_form,
                                   form_create_multiple=form_create_multiple, year=year)
        if os.path.exists(utils.__location__ + utils.accounts_file) and not unlocked:
            unlock_account_form = UnlockAccountForm()
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)
        if os.path.exists(utils.__location__ + utils.accounts_file) and unlocked:
            lookup_account_form = LookupAccountForm()
            default_address: str = await utils.get_pub_address_from_config()
            wei_balance = network.eth.get_balance(default_address)
            account_list = await utils.populate_public_address_list()
            return render_template('account.html', account="unlocked", lookup_account_form=lookup_account_form,
                                   pub_address=default_address, private_key=unlocked_account[1],
                                   mnemonic_phrase=unlocked_account[2],
                                   account_list=account_list,
                                   account_balance=round(network.from_wei(wei_balance, 'ether'), 2), year=year)


@create_account_blueprint.route('/create', methods=['GET', 'POST'])
async def create_account():
    unlock_account_form = UnlockAccountForm()
    create_account_form = CreateAccountForm()
    form_create_multiple = CreateMultipleAccountsForm()

    if request.method == 'GET':
        if os.path.exists(utils.__location__ + utils.accounts_file) and account != "unlocked":
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
                if not os.path.exists(utils.__location__ + utils.accounts_file):
                    if number_of_accounts == '':
                        number_of_accounts = 0
                    for number in range(number_of_accounts):
                        new_eth_account = Account.from_mnemonic(mnemonic_field_value,
                                                                account_path=f"m/44'/60'/0'/0/{number}")
                        pub_address = new_eth_account.address
                        private_key = no_plaintext.encrypt(bytes(new_eth_account.key.hex(), encoding='utf8'))
                        mnemonic_phrase = no_plaintext.encrypt(bytes(mnemonic_field_value, encoding='utf8'))
                        await utils.save_account_info(pub_address, private_key, mnemonic_phrase)
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
        wallet_key = Fernet.generate_key().decode('utf-8')
        try:
            await utils.create_account_callback(new_eth_account, wallet_key, mnemonic)
            return render_template('account.html', account="new", pub_address=new_eth_account.address,
                                   private_key=new_eth_account.key.hex(),
                                   wallet_key=wallet_key, mnemonic_phrase=mnemonic,
                                   create_account_form=create_account_form,
                                   form_create_multiple=form_create_multiple, year=year)
        except eth_utils.exceptions.ValidationError as e:
            flash(f"{e}, probably incorrect format.", 'warning')

@create_app_token_blueprint.route('/create_app_token', methods=['POST'])
async def create_app_token():
    pass

@account_blueprint.route('/account', methods=['GET', 'POST'])
async def account():
    create_account_form = CreateAccountForm()
    lookup_account_form = LookupAccountForm()
    unlock_account_form = UnlockAccountForm()
    form_create_multiple = CreateMultipleAccountsForm()
    if request.method == 'POST':
        try:
            account_unlock_key = request.form['account_key']
            no_plaintext = Fernet(account_unlock_key)
            connection = await utils.get_db_connection()
            accounts = connection.execute('SELECT * FROM accounts').fetchall()
            for row in accounts:
                try:
                    pub_address = row[1]
                    decrypt_private_key = no_plaintext.decrypt(
                    bytes(row[2], encoding='utf8')).decode('utf-8')
                    decrypt_mnemonic_phrase = no_plaintext.decrypt(
                    bytes(row[3], encoding='utf8')).decode('utf-8')
                    unlocked_account.append(pub_address)
                    unlocked_account.append(decrypt_private_key)
                    unlocked_account.append(decrypt_mnemonic_phrase)
                except Exception as e:
                    logger.debug(e)
            connection.close()
            global unlocked
            unlocked = True
            account_list = await utils.populate_public_address_list()
        except (Exception) as e:
            flash(f"Invalid account key. {e}", 'warning')
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)
        else:
            try:
                connected = await network.is_connected()
                if connected:
                    default_address: str = unlocked_account[0]
                    ens_name: str = await utils.get_ens_name(default_address)
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
                                   account_list=account_list,
                                   lookup_account_form=lookup_account_form, year=year,
                                   account_balance=account_balance)
    if request.method == 'GET':
        if not unlocked:
            if not os.path.exists(utils.__location__ + utils.accounts_file):
                flash("No accounts exist, please create an account.", 'warning')
                return render_template('create.html', account="new", create_account_form=create_account_form,
                                       form_create_multiple=form_create_multiple)
        if unlocked:
            default_address: str = unlocked_account[0]
            account_list = await utils.populate_public_address_list()
            private_key = unlocked_account[1]
            mnemonic_phrase = unlocked_account[2]
            try:
                connected = await network.is_connected()
                if connected:
                    ens_name: str = await utils.get_ens_name(default_address)
                    wei_balance = await network.eth.get_balance(default_address)
            except Exception as e:
                ens_name: str = "None"
                wei_balance = 0
                flash(f"No internet connection or invalid rpc urls. Please connect and try again {e}", 'warning')
            return render_template('account.html', account="unlocked", pub_address=default_address, ens_name=ens_name,
                                   private_key=private_key, mnemonic_phrase=mnemonic_phrase,
                                   account_list=account_list,
                                   lookup_account_form=lookup_account_form,
                                   year=year,
                                   account_balance=round(network.from_wei(wei_balance, 'ether'), 2))
        else:
            return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)


@account_lookup_blueprint.route('/lookup', methods=['POST'])
async def account_lookup():
    lookup_account_form = LookupAccountForm()
    if request.method == 'POST':
        try:
            account_unlock_key = request.form['account_key']
            no_plaintext = Fernet(account_unlock_key)
            lookup_account = request.form['account_id']
            pub_address = ""
            decrypt_private_key = None
            decrypt_mnemonic_phrase = None
            account_list = []
            wei_balance = 0
            connection = await utils.get_db_connection()
            account = connection.execute(f'SELECT * FROM accounts WHERE id={lookup_account}').fetchone()
            if account:
                try:
                    pub_address = account[1]
                    decrypt_private_key = no_plaintext.decrypt(
                        bytes(account[2], encoding='utf8')).decode('utf-8')
                    decrypt_mnemonic_phrase = no_plaintext.decrypt(
                        bytes(account[3], encoding='utf8')).decode('utf-8')
                    wei_balance = await network.eth.get_balance(pub_address)
                    account_list = await utils.populate_public_address_list()
                    connection.close()
                except IndexError as e:
                    flash(f"{e}, No account exists with id {account_id}.", 'warning')
                    connection.close()
            else:
                flash(f"No account exists with id {lookup_account}.", 'warning')
            return render_template('account.html', account="unlocked", pub_address=pub_address,
                                   private_key=decrypt_private_key, mnemonic_phrase=decrypt_mnemonic_phrase,
                                   account_list=account_list,
                                   account_balance=round(network.from_wei(wei_balance, 'ether'), 2),
                                   lookup_account_form=lookup_account_form, year=year)
        except (InvalidSignature, InvalidToken, ValueError, IndexError):
            flash("Invalid account key or account id", 'warning')
            default_address = ""
            wei_balance = 0
            account_list = await utils.populate_public_address_list()
            return render_template('account.html', account="unlocked", pub_address=default_address,
                                   private_key=unlocked_account[1], mnemonic_phrase=unlocked_account[2],
                                   account_list=account_list,
                                   account_balance=round(network.from_wei(wei_balance, 'ether'), 2),
                                   lookup_account_form=lookup_account_form, year=year)


@send_ether_blueprint.route('/send', methods=['GET'])
def send():
    unlock_account_form = UnlockAccountForm()
    create_account_form = CreateAccountForm()
    send_ether_form = SendEtherForm()
    form_create_multiple = CreateMultipleAccountsForm()
    if request.method == 'GET':
        if not unlocked:
            if not os.path.exists(utils.__location__ + utils.accounts_file):
                flash("No accounts exist, please create an account.", 'warning')
                return render_template('create.html', account="new", create_account_form=create_account_form,
                                       form_create_multiple=form_create_multiple, year=year)
            else:
                return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form,
                                       year=year)
        if os.path.exists(utils.__location__ + utils.accounts_file):
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
            default_address: str = await utils.get_pub_address_from_config()
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
        default_address: str = await utils.get_pub_address_from_config()
        wei_balance = network.eth.get_balance(default_address)
        account_list = await utils.populate_public_address_list()
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
                               account_balance=round(network.from_wei(wei_balance, 'ether'), 2), year=year)
    else:
        unlock_account_form = UnlockAccountForm()
        return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form, year=year)


@delete_accounts_blueprint.route('/delete', methods=['POST'])
def delete_accounts():
    create_account_form = CreateAccountForm()
    form_create_multiple = CreateMultipleAccountsForm()
    if os.path.exists(utils.__location__ + utils.accounts_file):
        os.remove(utils.__location__ + utils.accounts_file)
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
        if os.path.exists(utils.__location__ + utils.accounts_file):
            if unlocked:
                return render_template('settings.html', account="unlocked", settings_form=settings_form, year=year)
            if not unlocked:
                return render_template('unlock.html', account="current", unlock_account_form=unlock_account_form,
                                       year=year)
    if request.method == 'POST' and unlocked:
        allowed_prefix = ['http://', 'https://']
        try:
            if not any(value in request.form['network'] for value in allowed_prefix):
                flash("Invalid network url.", 'warning')
                return render_template('settings.html', account="unlocked", settings_form=settings_form, year=year)
            if not any(value in request.form['ens_mainnet_node'] for value in allowed_prefix):
                flash("Invalid mainnet url for ENS lookups.", 'warning')
                return render_template('settings.html', account="unlocked", settings_form=settings_form, year=year)
            config = configparser.ConfigParser()
            config.read(utils.__location__ + utils.config_file)
            config['DEFAULT']['network'] = request.form['network']
            config['DEFAULT']['default_address'] = request.form['default_address']
            config['DEFAULT']['ens_mainnet_node'] = request.form['ens_mainnet_node']
            with open(utils.__location__ + config_file, 'w') as lichen_config:
                config.write(lichen_config)
                flash("Settings changed successfully!", 'success')
            return render_template('settings.html', account="unlocked", settings_form=settings_form, year=year)
        except Exception as e:
            flash(f"{e}", 'warning')
            return render_template('settings.html', account="unlocked", settings_form=settings_form, year=year)


@sign_and_send_blueprint.route('/sign_and_send', methods=['POST'])
async def sign_and_send():
    if request.method == 'POST' and unlocked:
        tx_variables = request.json
        nonce = await network.eth.get_transaction_count(tx_variables['from'], 'pending')
        gas_price = await network.eth.gas_price
        try:
            tx = {
                    'nonce': nonce,
                    'to': tx_variables['to'],
                    'value': network.to_wei(tx_variables['value'], 'ether'),
                    'gas': network.to_wei('0.03', 'gwei'),
                    'gasPrice': gas_price,
                    'from': tx_variables['from']
                }
            sign = network.eth.account.sign_transaction(tx, unlocked_account[1])
            await network.eth.send_raw_transaction(sign.rawTransaction)
        except Exception as e:
            logger.debug(e)

