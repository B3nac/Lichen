import os
import secrets
import sqlite3
from cryptography.fernet import Fernet
from Lichen.code.custom_logs import logger

__location__ = os.path.expanduser('~')
accounts_file = "/lichen.db"
config_file = "/lichen.ini"


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
        if not accounts_list:
            with open('/usr/lib/Lichen/app/Lichen/accounts_schema.sql') as f:
                connection.executescript(f.read())
                cursor.execute("INSERT INTO accounts (pubaddress, privatekey, mnemonicphrase) VALUES (?, ?, ?)",
                               (f"{pub_address}", f"{decode_private_key}", f"{decode_mnemonic}")
                               )
                connection.commit()
                connection.close()

        elif accounts_list:
            cursor.execute("INSERT INTO accounts (pubaddress, privatekey, mnemonicphrase) VALUES (?, ?, ?)",
                           (f"{pub_address}", f"{decode_private_key}", f"{decode_mnemonic}")
                           )
            connection.commit()
            connection.close()
    except Exception as e:
        logger.debug(e)
    finally:
        connection.close()


async def populate_public_address_list():
    public_address_list = []
    connection = await get_db_connection()
    accounts = connection.execute('SELECT * FROM accounts').fetchall()
    for account_id in accounts:
        try:
            public_address_list.append(account_id[1])
        except IndexError as e:
            connection.close()
            logger.debug(f"{e}, No account exists with id {account_id}.", 'warning')
    connection.close()
    return public_address_list


async def get_db_connection():
    connection = sqlite3.connect('lichen.db')
    connection.row_factory = sqlite3.Row
    return connection


async def create_app_token(app_name):
    app_token = secrets.token_hex(18)
    try:
        connection = sqlite3.connect('lichen.db')
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='apps';")
        apps_list = cursor.fetchall()
        if not apps_list:
            with open('/usr/lib/Lichen/app/Lichen/apps_schema.sql') as f:
                connection.executescript(f.read())
                cursor.execute("INSERT INTO apps (appname, apikey) VALUES (?, ?)",
                               (f"{app_name}", f"{app_token}")
                               )
                connection.commit()
    except Exception as e:
        logger.debug(e)
        connection.close()
    finally:
        connection.close()
        return app_token
