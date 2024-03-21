import os   
import sqlite3
from cryptography.fernet import Fernet
from Lichen.code.custom_logs import logger

__location__ = os.path.expanduser('~')
accounts_file = "/lichen.db"
config_file = "/lichen.ini"

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


async def create_account_callback(new_eth_account, wallet_key, mnemonic):
    if not os.path.exists(__location__ + accounts_file):
        no_plaintext = Fernet(wallet_key)
        pub_address = new_eth_account.address
        private_key = no_plaintext.encrypt(bytes(new_eth_account.key.hex(), encoding='utf8'))
        mnemonic_phrase = no_plaintext.encrypt(bytes(mnemonic, encoding='utf8'))
        await save_account_info(pub_address, private_key, mnemonic_phrase)


async def save_account_info(pub_address, private_key, mnemonic_phrase):
    connection = sqlite3.connect('lichen.db')
    decode_private_key = private_key.decode('utf-8')
    decode_mnemonic = mnemonic_phrase.decode('utf-8')
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts';")
        accounts_list = cursor.fetchall()
        if accounts_list == []:
            with open('/usr/lib/Lichen/app/Lichen/schema.sql') as f:
                connection.executescript(f.read())
            cursor.execute("INSERT INTO accounts (pubaddress, privatekey, mnemonicphrase) VALUES (?, ?, ?)",
                    (f"{pub_address}", f"{decode_private_key}", f"{decode_mnemonic}")
                    )
            connection.commit()

        elif accounts_list:
            cursor.execute("INSERT INTO accounts (pubaddress, privatekey, mnemonicphrase) VALUES (?, ?, ?)",
                    (f"{pub_address}", f"{decode_private_key}", f"{decode_mnemonic}")
                    )
            connection.commit()
    except Exception as e:
        logger.debug(e)
    finally:
        connection.close()

async def populate_public_address_list():
    public_address_list = []
    connection = get_db_connection()
    accounts = connection.execute('SELECT * FROM accounts').fetchall()
    for account_id in accounts:
        try:
            public_address_list.append(account_id[1])
        except IndexError as e:
            connection.close()
            flash(f"{e}, No account exists with id {account_id}.", 'warning')
    connection.close()
    return public_address_list


async def get_ens_name(default_address):
    try:
        if ens_mainnet_address is not None:
            domain = await ens_resolver.name(default_address)
            if domain is None:
                domain = "No ENS name associated with this address."
                return domain
            if domain:
                return domain
        else:
            domain = "No ENS name associated with this address."
            return domain
    except Exception:
        domain = "No ENS name associated with this address."
        return domain


def get_db_connection():
    connection = sqlite3.connect('lichen.db')
    connection.row_factory = sqlite3.Row
    return connection

