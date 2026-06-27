"""Analytics module for Charles Schwab trading data.

Provides two monthly aggregation methods:

1. analyze_monthly_pnl() — cash-flow P&L from transactions + transaction_items.
   - OPENING legs (buys) have a negative cost  → cash out
   - CLOSING legs (sells) have a positive cost → cash in
   - net_cash_flow = total_sell_proceeds + total_buy_cost
   This is a cash-flow approximation; true P&L requires a separate cost-basis ledger.

2. analyze_monthly_snapshots() — month-end portfolio balance from account_snapshots.
   Uses the last snapshot of each calendar month per account, extracting balance
   fields from both the pre-extracted scalar columns and the current_balances_json
   blob (long/short market value, margin balance, maintenance requirement, etc.).
"""

import json
from typing import Optional

from .database import SchwabDatabase
from .models import CREATE_ANALYSIS_TABLE, CREATE_MONTHLY_SNAPSHOTS_TABLE, ANALYSIS_INDEXES
from ..time_utils import utc_now_iso


class SchwabAnalytics:
    """Generates monthly P&L summaries from Schwab transaction data."""

    def __init__(self, db: Optional[SchwabDatabase] = None):
        """Initialize analytics.

        Args:
            db: Database manager instance.
        """
        self.db = db or SchwabDatabase()

    def _ensure_analysis_table(self) -> None:
        """Create the monthly_pnl table and indexes if they don't exist."""
        with self.db.get_connection() as conn:
            conn.execute(CREATE_ANALYSIS_TABLE)
            conn.execute(CREATE_MONTHLY_SNAPSHOTS_TABLE)
            for index_sql in ANALYSIS_INDEXES:
                conn.execute(index_sql)

    def analyze_monthly_pnl(self) -> int:
        """Compute monthly P&L summaries and write to monthly_pnl.

        Aggregates transaction_items by (year_month, account_hash):
        - total_buy_cost: sum of cost for OPENING trade legs (negative values)
        - total_sell_proceeds: sum of cost for CLOSING trade legs (positive values)
        - net_cash_flow: total_sell_proceeds + total_buy_cost
        - total_fees: sum of ABS(cost) for fee legs (COMMISSION, SEC_FEE, etc.)
        - trade_count / opening_count / closing_count: leg counts
        - unique_symbols: distinct non-fee tickers traded

        Returns:
            Number of monthly records written.
        """
        self._ensure_analysis_table()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Use substr instead of strftime because the Schwab API returns
            # timestamps with timezone offset as "+0000" (no colon), which
            # SQLite's strftime cannot parse — substr(time, 1, 7) is always
            # "YYYY-MM" regardless of timezone format.
            cursor.execute("""
                SELECT
                    substr(t.time, 1, 7) AS year_month,
                    t.account_hash,
                    -- Trade legs (fee_type IS NULL means it's an actual trade leg)
                    SUM(CASE
                        WHEN ti.fee_type IS NULL AND ti.position_effect = 'OPENING'
                        THEN ti.cost ELSE 0
                    END) AS total_buy_cost,
                    SUM(CASE
                        WHEN ti.fee_type IS NULL AND ti.position_effect = 'CLOSING'
                        THEN ti.cost ELSE 0
                    END) AS total_sell_proceeds,
                    SUM(CASE
                        WHEN ti.fee_type IS NULL
                        THEN COALESCE(ti.cost, 0) ELSE 0
                    END) AS net_cash_flow,
                    -- Fee legs
                    SUM(CASE
                        WHEN ti.fee_type IS NOT NULL
                        THEN ABS(COALESCE(ti.cost, 0)) ELSE 0
                    END) AS total_fees,
                    -- Counts
                    COUNT(CASE WHEN ti.fee_type IS NULL THEN 1 END) AS trade_count,
                    COUNT(CASE WHEN ti.fee_type IS NULL
                               AND ti.position_effect = 'OPENING' THEN 1 END) AS opening_count,
                    COUNT(CASE WHEN ti.fee_type IS NULL
                               AND ti.position_effect = 'CLOSING' THEN 1 END) AS closing_count,
                    COUNT(DISTINCT CASE
                        WHEN ti.fee_type IS NULL AND ti.symbol IS NOT NULL
                        THEN ti.symbol
                    END) AS unique_symbols
                FROM transactions t
                JOIN transaction_items ti
                    ON ti.account_hash   = t.account_hash
                   AND ti.transaction_id = t.transaction_id
                WHERE t.time IS NOT NULL
                  AND t.type = 'TRADE'
                GROUP BY year_month, t.account_hash
                ORDER BY year_month
            """)
            rows = cursor.fetchall()

        if not rows:
            return 0

        now = utc_now_iso()
        count = 0

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            for row in rows:
                year_month = row["year_month"]
                if not year_month:
                    continue

                cursor.execute(
                    """
                    INSERT INTO monthly_pnl (
                        year_month, account_hash,
                        total_buy_cost, total_sell_proceeds, net_cash_flow,
                        total_fees,
                        trade_count, opening_count, closing_count,
                        unique_symbols,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(year_month, account_hash) DO UPDATE SET
                        total_buy_cost      = excluded.total_buy_cost,
                        total_sell_proceeds = excluded.total_sell_proceeds,
                        net_cash_flow       = excluded.net_cash_flow,
                        total_fees          = excluded.total_fees,
                        trade_count         = excluded.trade_count,
                        opening_count       = excluded.opening_count,
                        closing_count       = excluded.closing_count,
                        unique_symbols      = excluded.unique_symbols,
                        updated_at          = excluded.updated_at
                    """,
                    (
                        year_month,
                        row["account_hash"],
                        row["total_buy_cost"],
                        row["total_sell_proceeds"],
                        row["net_cash_flow"],
                        row["total_fees"],
                        row["trade_count"],
                        row["opening_count"],
                        row["closing_count"],
                        row["unique_symbols"],
                        now,
                    ),
                )
                count += 1

        return count

    def analyze_monthly_snapshots(self) -> int:
        """Compute month-end portfolio balance snapshots and write to monthly_account_snapshots.

        For each (year_month, account_hash) pair in account_snapshots, picks the row
        with the latest snapshot_at and extracts both the pre-stored scalar columns and
        additional fields from current_balances_json using SQLite's json_extract().

        Fields populated from current_balances_json (NULL when absent for the
        account type — e.g. margin fields on a cash account):
          long_market_value, short_market_value, margin_balance, short_balance,
          long_margin_value, short_margin_value, maintenance_requirement,
          money_market_fund, total_cash, cash_available_for_trading,
          cash_available_for_withdrawal.

        Returns:
            Number of monthly records written.
        """
        self._ensure_analysis_table()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Pick the last snapshot row of each calendar month per account.
            # substr(snapshot_at, 1, 7) gives 'YYYY-MM' regardless of timezone format.
            cursor.execute("""
                SELECT
                    substr(s.snapshot_at, 1, 7)              AS year_month,
                    s.account_hash,
                    s.account_number,
                    s.account_type,
                    s.snapshot_at,
                    s.liquidation_value,
                    s.equity,
                    s.cash_balance,
                    s.buying_power,
                    -- Extended fields from current_balances_json
                    json_extract(s.current_balances_json, '$.longMarketValue')
                        AS long_market_value,
                    json_extract(s.current_balances_json, '$.shortMarketValue')
                        AS short_market_value,
                    json_extract(s.current_balances_json, '$.marginBalance')
                        AS margin_balance,
                    json_extract(s.current_balances_json, '$.shortBalance')
                        AS short_balance,
                    json_extract(s.current_balances_json, '$.longMarginValue')
                        AS long_margin_value,
                    json_extract(s.current_balances_json, '$.shortMarginValue')
                        AS short_margin_value,
                    json_extract(s.current_balances_json, '$.maintenanceRequirement')
                        AS maintenance_requirement,
                    json_extract(s.current_balances_json, '$.moneyMarketFund')
                        AS money_market_fund,
                    json_extract(s.current_balances_json, '$.totalCash')
                        AS total_cash,
                    json_extract(s.current_balances_json, '$.cashAvailableForTrading')
                        AS cash_available_for_trading,
                    json_extract(s.current_balances_json, '$.cashAvailableForWithdrawal')
                        AS cash_available_for_withdrawal
                FROM account_snapshots s
                INNER JOIN (
                    SELECT account_hash, substr(snapshot_at, 1, 7) AS ym,
                           MAX(snapshot_at) AS last_at
                    FROM account_snapshots
                    GROUP BY account_hash, ym
                ) latest
                    ON  s.account_hash  = latest.account_hash
                    AND s.snapshot_at   = latest.last_at
                ORDER BY year_month
            """)
            rows = cursor.fetchall()

        if not rows:
            return 0

        now = utc_now_iso()
        count = 0

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            for row in rows:
                year_month = row["year_month"]
                if not year_month:
                    continue

                cursor.execute(
                    """
                    INSERT INTO monthly_account_snapshots (
                        year_month, account_hash, account_number, account_type,
                        snapshot_at,
                        liquidation_value, equity, cash_balance, buying_power,
                        long_market_value, short_market_value,
                        margin_balance, short_balance,
                        long_margin_value, short_margin_value,
                        maintenance_requirement, money_market_fund,
                        total_cash, cash_available_for_trading,
                        cash_available_for_withdrawal,
                        updated_at
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?
                    )
                    ON CONFLICT(year_month, account_hash) DO UPDATE SET
                        account_number              = excluded.account_number,
                        account_type                = excluded.account_type,
                        snapshot_at                 = excluded.snapshot_at,
                        liquidation_value           = excluded.liquidation_value,
                        equity                      = excluded.equity,
                        cash_balance                = excluded.cash_balance,
                        buying_power                = excluded.buying_power,
                        long_market_value           = excluded.long_market_value,
                        short_market_value          = excluded.short_market_value,
                        margin_balance              = excluded.margin_balance,
                        short_balance               = excluded.short_balance,
                        long_margin_value           = excluded.long_margin_value,
                        short_margin_value          = excluded.short_margin_value,
                        maintenance_requirement     = excluded.maintenance_requirement,
                        money_market_fund           = excluded.money_market_fund,
                        total_cash                  = excluded.total_cash,
                        cash_available_for_trading  = excluded.cash_available_for_trading,
                        cash_available_for_withdrawal = excluded.cash_available_for_withdrawal,
                        updated_at                  = excluded.updated_at
                    """,
                    (
                        year_month,
                        row["account_hash"],
                        row["account_number"],
                        row["account_type"],
                        row["snapshot_at"],
                        row["liquidation_value"],
                        row["equity"],
                        row["cash_balance"],
                        row["buying_power"],
                        row["long_market_value"],
                        row["short_market_value"],
                        row["margin_balance"],
                        row["short_balance"],
                        row["long_margin_value"],
                        row["short_margin_value"],
                        row["maintenance_requirement"],
                        row["money_market_fund"],
                        row["total_cash"],
                        row["cash_available_for_trading"],
                        row["cash_available_for_withdrawal"],
                        now,
                    ),
                )
                count += 1

        return count
