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

# Monthly P&L from trade cash flows
CREATE_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS monthly_pnl (
    year_month TEXT NOT NULL,
    account_hash TEXT NOT NULL,
    -- Cash-flow totals across trade legs only (excludes fee legs)
    total_buy_cost REAL NOT NULL DEFAULT 0,
    total_sell_proceeds REAL NOT NULL DEFAULT 0,
    net_cash_flow REAL NOT NULL DEFAULT 0,
    -- Fee totals (fee legs only: COMMISSION, SEC_FEE, etc.)
    total_fees REAL NOT NULL DEFAULT 0,
    -- Trade leg counts
    trade_count INTEGER NOT NULL DEFAULT 0,
    opening_count INTEGER NOT NULL DEFAULT 0,
    closing_count INTEGER NOT NULL DEFAULT 0,
    -- Distinct tickers active this month
    unique_symbols INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (year_month, account_hash)
);
"""

# Month-end account balance snapshot (last snapshot of each calendar month)
CREATE_MONTHLY_SNAPSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS monthly_account_snapshots (
    year_month TEXT NOT NULL,
    account_hash TEXT NOT NULL,
    account_number TEXT,
    account_type TEXT,
    snapshot_at TEXT NOT NULL,          -- timestamp of the source snapshot used
    -- Core balance fields (from currentBalances, falling back to initialBalances)
    liquidation_value REAL,             -- total account value
    equity REAL,                        -- equity value
    cash_balance REAL,                  -- cash on hand
    buying_power REAL,                  -- available buying power
    -- Extended fields extracted from current_balances_json
    long_market_value REAL,             -- value of all long positions
    short_market_value REAL,            -- value of all short positions
    margin_balance REAL,                -- margin debit balance (positive = owe)
    short_balance REAL,                 -- proceeds from short sales held
    long_margin_value REAL,             -- long market value usable as margin collateral
    short_margin_value REAL,            -- short market value for margin purposes
    maintenance_requirement REAL,       -- total margin maintenance requirement
    money_market_fund REAL,             -- money market fund balance
    total_cash REAL,                    -- sum of all cash equivalents
    cash_available_for_trading REAL,    -- settled cash available to trade
    cash_available_for_withdrawal REAL, -- cash eligible for withdrawal
    updated_at TEXT NOT NULL,
    PRIMARY KEY (year_month, account_hash)
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

ANALYSIS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_schwab_pnl_year_month ON monthly_pnl(year_month);",
    "CREATE INDEX IF NOT EXISTS idx_schwab_pnl_account ON monthly_pnl(account_hash);",
    "CREATE INDEX IF NOT EXISTS idx_schwab_snapshots_month ON monthly_account_snapshots(year_month);",
    "CREATE INDEX IF NOT EXISTS idx_schwab_snapshots_month_acct ON monthly_account_snapshots(account_hash);",
]
