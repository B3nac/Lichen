from flask import Flask
from flask import render_template
import string
import secrets

alphabet = string.ascii_letters + string.digits
app = Flask(__name__)
app.config['SECRET_KEY'] = ''.join(secrets.choice(alphabet) for i in range(15))

from TheLootBoxWallet.code.blueprints import (
    index_blueprint,
    create_account_blueprint,
    create_fresh_account_blueprint,
    account_blueprint,
    account_lookup_blueprint,
    send_ether_blueprint,
    send_verify_blueprint,
    send_transaction_blueprint,
    replay_transaction_blueprint,
    delete_accounts_blueprint,
    settings_blueprint,
    sign_and_send_blueprint
)

app.register_blueprint(index_blueprint)
app.register_blueprint(create_account_blueprint)
app.register_blueprint(create_fresh_account_blueprint)
app.register_blueprint(account_blueprint)
app.register_blueprint(account_lookup_blueprint)
app.register_blueprint(send_ether_blueprint)
app.register_blueprint(send_verify_blueprint)
app.register_blueprint(send_transaction_blueprint)
app.register_blueprint(replay_transaction_blueprint)
app.register_blueprint(delete_accounts_blueprint)
app.register_blueprint(settings_blueprint)
app.register_blueprint(sign_and_send_blueprint)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('405.html'), 405
