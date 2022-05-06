from web3 import Web3

# Add configuration for different test nets

web3_local_rinkeby = Web3(Web3.HTTPProvider('127.0.0.1:8545'))
web3_local_mainnet = Web3(Web3.HTTPProvider('http://127.0.0.1:8888'))
web3_arbitrum_rinkeby = Web3(Web3.HTTPProvider('https://rinkeby.arbitrum.io/rpc'))

from web3.middleware import geth_poa_middleware
web3_local_rinkeby.middleware_onion.inject(geth_poa_middleware, layer=0)
