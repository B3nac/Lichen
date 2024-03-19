CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pubaddress TEXT NOT NULL,
    privatekey TEXT NOT NULL,
    mnemonicphrase TEXT NOT NULL
);
CREATE TABLE apps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appname TEXT NOT NULL,
    apikey TEXT NOT NULL
);
