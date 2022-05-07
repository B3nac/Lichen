# TheLootBoxClient

Protect your loot with TheLootBoxClient! 

TheLootBox local Ethereum account creation and contract interaction client that focuses on security. A lockbox for your ethereum assets.

---

### Features

- Account wallet credentials are stored encrypted and decrypted only when the client is in use and unlocked by the account key.

- Runs locally and interacts with TheLootBox contracts on the Ethereum blockchain inherently more secure.

- Makes it easier to create "loot bundles" more explanation on what those are later. :)

---

#### Setup

I highly recommended creating a virtual environment to avoid dependency conflicts.

`python3 -m venv envname`

Once the venv is created source it in order to install the dependencies to that environment.

`source path/to/envname/bin/activate`

The required dependencies can be installed with pip.

`pip install flask flask_wtf wtforms web3 eth-account cryptography.fernet webview`
 
Then start TheLootBoxClient.

`python3 start.py`

---

### Preview screenshot

![TheLootBoxClient](./app/static/images/TheLootBoxClient.png)

### In progress

~~- Setting up TheLootBox contract functions.~~

- Add setup instructions

### Supporting development

If you would like to send anything to my ens name `b3nac.eth` it will be appreciated, but is obviously not required.
