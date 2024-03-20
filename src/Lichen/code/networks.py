import os.path
from web3 import AsyncWeb3, AsyncHTTPProvider
import configparser
from ens import AsyncENS
from Lichen.code.utils import __location__

config_file = "/lichen.ini"

if os.path.exists(__location__ + config_file):
    config = configparser.ConfigParser()
    config.read(__location__ + config_file)
    try:
        network = AsyncWeb3(AsyncHTTPProvider(config['DEFAULT']['network']))
        address = config['DEFAULT']['default_address']
        ens_mainnet_address = config['DEFAULT']['ens_mainnet_node']
        ens_mainnet_node = AsyncWeb3(AsyncHTTPProvider(config['DEFAULT']['ens_mainnet_node']))
        ens_resolver = AsyncENS.from_web3(ens_mainnet_node)
        if config['DEFAULT']['logs']:
            logs = config['DEFAULT']['logs']
    except:
        network = AsyncWeb3(AsyncHTTPProvider('https://goerli-rollup.arbitrum.io/rpc'))
        address = ""
        ens_mainnet_address = "https://mainnet.infura.io/v3/c027bbda707e4d6d83124ca432d42e6f"
        ens_mainnet_node = AsyncWeb3(AsyncHTTPProvider(ens_mainnet_address))
        logs = False
        ens_resolver = AsyncENS.from_web3(ens_mainnet_node)
else:
    network = AsyncWeb3(AsyncHTTPProvider('https://goerli-rollup.arbitrum.io/rpc'))
    address = ""
    ens_mainnet_address = "https://mainnet.infura.io/v3/c027bbda707e4d6d83124ca432d42e6f"
    ens_mainnet_node = AsyncWeb3(AsyncHTTPProvider(ens_mainnet_address))
    logs = False
    ens_resolver = AsyncENS.from_web3(ens_mainnet_node)

