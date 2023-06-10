# TheLootBoxWallet

Built on Linux for Linux and ported to other operating systems in the future. No ads, no user tracking, and security is a priority. Protect your loot with TheLootBoxWallet! 

TheLootBoxWallet is an Ethereum wallet that runs locally on your desktop with a focus on privacy and security. A lockbox for your ethereum assets.

---

### Features

- Account wallet credentials are stored encrypted and decrypted only when the client is in use and unlocked by the account key.

- Runs locally as a self-contained stand-alone application.

- Makes it easier to create "loot bundles" more explanation on what those are later.

---

### Install from .deb file release

#### Dependencies

You might need the following dependencies for GTK.

`sudo apt install libgirepository1.0-dev gcc libcairo2-dev pkg-config python3-dev gir1.2-gtk-3.0`

`pip3 install pycairo PyGObject`

#### Steps to install

- Download the deb file from the latest release.

https://github.com/TheLootBox-xyz/TheLootBoxWallet/releases

- Run the install command.

`sudo dpkg -i thelootboxwallet-release`

- Start thelootboxwallet from `/usr/bin/thelootboxwallet/start`.

---

### Start from binary (In progress)

#### Linux dependencies

Sometimes you have to install `libxcb-xinerama0` on debian based distros.

`sudo apt install libxcb-xinerama0`

#### Steps to run

- Download thelootboxwallet binary from releases.

https://github.com/TheLootBox-xyz/TheLootBoxWallet/releases

- Make the binary executable.

`chmod +x thelootboxwallet-release`

- Start the binary with a bash alias.

`alias thelootboxwallet='~/path/to/thelootboxwallet-release'`

- Or like this.

`./thelootboxwallet-release`

- To background the process.

`./thelootboxwallet-release &`

---

### Setup from source

I highly recommended creating a virtual environment to avoid dependency conflicts.

`python3 -m venv envname`

Once the venv is created source it in order to install the dependencies to that environment.

`source path/to/envname/bin/activate`

Clone TheLootBox repository from Github.

`git clone git@github.com:TheLootBox-xyz/TheLootBoxClient.git`

The required dependencies can be installed with pip.

`pip install -r requirements.txt`
 
Then start TheLootBoxClient.

`python3 start.py`

---

### Customize default settings

You can customize the default network and ethereum account with a `config.ini` file. If you don't have a `config.ini` file TheLootBoxWallet will use the first public address created as the default address.

Example `config.ini` file:

```bash
[DEFAULT]

network = https://goerli-rollup.arbitrum.io/rpc
default_address = your_public_ethereum_address
```

### Preview screenshot

![TheLootBoxClient](./app/static/images/TheLootBoxClient.png)

### In progress

~~- Setting up TheLootBox contract functions.~~

~~- Add setup instructions.~~

~~- Add multiple account support.~~

~~- Add unit tests.~~

---

### Supporting development

If you would like to send anything to my ens name `b3nac.eth` it will be appreciated, but is obviously not required.
