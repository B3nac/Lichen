CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pubaddress TEXT NOT NULL,
    privatekey TEXT NOT NULL,
    mnemonicphrase TEXT NOT NULL
);
