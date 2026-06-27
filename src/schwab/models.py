"""SQL schema definitions for Charles Schwab sync tables."""

CREATE_ACCOUNT_SNAPSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS account_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_hash TEXT NOT NULL,
    account_number TEXT,
    snapshot_at TEXT NOT NULL,
    account_type TEXT,
    liquidation_value REAL,
    equity REAL,
    cash_balance REAL,
    buying_power REAL,
    current_balances_json TEXT,
    initial_balances_json TEXT,
    projected_balances_json TEXT,
    raw_json TEXT NOT NULL,
    synced_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);
"""

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    account_hash TEXT NOT NULL,
    transaction_id TEXT NOT NULL,
    account_number TEXT,
    time TEXT,
    trade_date TEXT,
    type TEXT,
    status TEXT,
    sub_account TEXT,
    position_id TEXT,
    order_id TEXT,
    net_amount REAL,
    raw_json TEXT NOT NULL,
    synced_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    PRIMARY KEY (account_hash, transaction_id)
);
"""

CREATE_TRANSACTION_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS transaction_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_hash TEXT NOT NULL,
    transaction_id TEXT NOT NULL,
    item_index INTEGER NOT NULL,
    asset_type TEXT,
    instrument_id INTEGER,
    symbol TEXT,
    description TEXT,
    instrument_type TEXT,
    closing_price REAL,
    amount REAL,
    cost REAL,
    price REAL,
    fee_type TEXT,
    position_effect TEXT,
    raw_json TEXT NOT NULL,
    UNIQUE (account_hash, transaction_id, item_index),
    FOREIGN KEY (account_hash, transaction_id)
        REFERENCES transactions(account_hash, transaction_id)
);
"""

CREATE_SYNC_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS sync_state (
    entity_type TEXT PRIMARY KEY NOT NULL,
    last_sync_at TEXT,
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);
"""

RAW_TABLES = [
    CREATE_ACCOUNT_SNAPSHOTS_TABLE,
    CREATE_TRANSACTIONS_TABLE,
    CREATE_TRANSACTION_ITEMS_TABLE,
    CREATE_SYNC_STATE_TABLE,
]

RAW_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_schwab_snapshots_account ON account_snapshots(account_hash);",
    "CREATE INDEX IF NOT EXISTS idx_schwab_snapshots_at ON account_snapshots(snapshot_at);",
    "CREATE INDEX IF NOT EXISTS idx_schwab_transactions_account ON transactions(account_hash);",
    "CREATE INDEX IF NOT EXISTS idx_schwab_transactions_time ON transactions(time);",
    "CREATE INDEX IF NOT EXISTS idx_schwab_transactions_type ON transactions(type);",
    "CREATE INDEX IF NOT EXISTS idx_schwab_txn_items_parent ON transaction_items(account_hash, transaction_id);",
    "CREATE INDEX IF NOT EXISTS idx_schwab_txn_items_symbol ON transaction_items(symbol);",
    "CREATE INDEX IF NOT EXISTS idx_schwab_txn_items_asset_type ON transaction_items(asset_type);",
]

