from flask import Flask
from flask import render_template
import string
import secrets

alphabet = string.ascii_letters + string.digits
app = Flask(__name__)
app.config['SECRET_KEY'] = ''.join(secrets.choice(alphabet) for i in range(15))

from app.blueprints import (
    index_blueprint,
    create_lootbundle_blueprint,
    create_account_blueprint,
    account_blueprint,
    send_ether_blueprint,
    send_transaction_blueprint
)

app.register_blueprint(index_blueprint)
app.register_blueprint(create_lootbundle_blueprint)
app.register_blueprint(create_account_blueprint)
app.register_blueprint(account_blueprint)
app.register_blueprint(send_ether_blueprint)
app.register_blueprint(send_transaction_blueprint)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('405.html'), 405
