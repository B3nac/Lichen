import os.path
from web3 import Web3
import configparser

__location__ = os.path.expanduser('~')

config_file = "/config.ini"

if os.path.exists(__location__ + config_file):
    config = configparser.ConfigParser()
    config.read(__location__ + config_file)
    network = Web3(Web3.HTTPProvider(config['DEFAULT']['network']))
    address = config['DEFAULT']['default_address']
else:
    network = Web3(Web3.HTTPProvider('https://goerli-rollup.arbitrum.io/rpc'))

from web3.middleware import geth_poa_middleware

network.middleware_onion.inject(geth_poa_middleware, layer=0)
