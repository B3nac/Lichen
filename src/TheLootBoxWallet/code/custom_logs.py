import logging

logging.basicConfig(filename='TheLootBoxWallet.log', encoding='utf-8', level=logging.INFO)

logging.getLogger("web3.RequestManager").setLevel(logging.WARNING)
logging.getLogger("web3.providers.HTTPProvider").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
