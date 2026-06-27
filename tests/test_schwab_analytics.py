"""Tests for Schwab monthly P&L analytics."""

import pytest
from src.schwab.database import SchwabDatabase
from src.schwab.analytics import SchwabAnalytics


def _make_db(tmp_path) -> SchwabDatabase:
    db = SchwabDatabase(str(tmp_path / "schwab.db"))
    db.init_tables()
    return db


def _insert_trade(db, activity_id, time, account_hash, account_number, transfer_items):
    """Helper to insert a transaction with transfer items."""
    transaction = {
        "activityId": activity_id,
        "time": time,
        "type": "TRADE",
        "status": "VALID",
        "netAmount": sum(i.get("cost", 0) for i in transfer_items),
        "transferItems": transfer_items,
    }
    db.upsert_transaction(transaction, account_hash, account_number)


def test_analyze_monthly_pnl_empty_db(tmp_path):
    """Returns 0 when there are no transactions."""
    db = _make_db(tmp_path)
    analytics = SchwabAnalytics(db=db)
    assert analytics.analyze_monthly_pnl() == 0


def test_analyze_monthly_pnl_creates_table(tmp_path):
    """monthly_pnl table is created even if no transactions exist."""
    db = _make_db(tmp_path)
    analytics = SchwabAnalytics(db=db)
    analytics.analyze_monthly_pnl()

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_pnl'")
        assert cursor.fetchone() is not None


def test_analyze_monthly_pnl_opening_trade(tmp_path):
    """A single OPENING (buy) trade is recorded with correct buy cost."""
    db = _make_db(tmp_path)
    _insert_trade(
        db,
        activity_id=1001,
        time="2026-01-15T10:00:00+0000",
        account_hash="HASH1",
        account_number="ACC1",
        transfer_items=[
            # fee leg
            {
                "instrument": {"assetType": "CURRENCY", "symbol": "CURRENCY_USD"},
                "amount": 0.0,
                "cost": -0.65,
                "feeType": "COMMISSION",
            },
            # trade leg
            {
                "instrument": {
                    "assetType": "EQUITY",
                    "symbol": "VTI",
                    "description": "Vanguard Total Stock Market ETF",
                    "instrumentId": 5215623,
                    "closingPrice": 369.99,
                    "type": "EXCHANGE_TRADED_FUND",
                },
                "amount": 10.0,
                "cost": -3692.50,
                "price": 369.25,
                "positionEffect": "OPENING",
            },
        ],
    )

    analytics = SchwabAnalytics(db=db)
    count = analytics.analyze_monthly_pnl()
    assert count == 1

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM monthly_pnl WHERE year_month = '2026-01'")
        row = cursor.fetchone()

    assert row is not None
    assert row["account_hash"] == "HASH1"
    assert row["total_buy_cost"] == pytest.approx(-3692.50)
    assert row["total_sell_proceeds"] == 0.0
    assert row["net_cash_flow"] == pytest.approx(-3692.50)
    assert row["total_fees"] == pytest.approx(0.65)
    assert row["trade_count"] == 1
    assert row["opening_count"] == 1
    assert row["closing_count"] == 0
    assert row["unique_symbols"] == 1


def test_analyze_monthly_pnl_opening_and_closing(tmp_path):
    """Buy then sell in the same month: net_cash_flow captures both legs."""
    db = _make_db(tmp_path)
    # Buy 10 shares at $369.25
    _insert_trade(
        db,
        activity_id=2001,
        time="2026-02-10T10:00:00+0000",
        account_hash="HASH1",
        account_number="ACC1",
        transfer_items=[
            {
                "instrument": {"assetType": "EQUITY", "symbol": "VTI"},
                "amount": 10.0,
                "cost": -3692.50,
                "price": 369.25,
                "positionEffect": "OPENING",
            },
        ],
    )
    # Sell 10 shares at $380.00
    _insert_trade(
        db,
        activity_id=2002,
        time="2026-02-20T10:00:00+0000",
        account_hash="HASH1",
        account_number="ACC1",
        transfer_items=[
            {
                "instrument": {"assetType": "EQUITY", "symbol": "VTI"},
                "amount": 10.0,
                "cost": 3800.00,
                "price": 380.00,
                "positionEffect": "CLOSING",
            },
        ],
    )

    analytics = SchwabAnalytics(db=db)
    count = analytics.analyze_monthly_pnl()
    assert count == 1

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM monthly_pnl WHERE year_month = '2026-02'")
        row = cursor.fetchone()

    assert row["total_buy_cost"] == pytest.approx(-3692.50)
    assert row["total_sell_proceeds"] == pytest.approx(3800.00)
    assert row["net_cash_flow"] == pytest.approx(107.50)
    assert row["trade_count"] == 2
    assert row["opening_count"] == 1
    assert row["closing_count"] == 1
    assert row["unique_symbols"] == 1


def test_analyze_monthly_pnl_multiple_months(tmp_path):
    """Trades in different months produce separate rows."""
    db = _make_db(tmp_path)
    _insert_trade(
        db, 3001, "2026-03-05T10:00:00+0000", "HASH1", "ACC1",
        [{"instrument": {"assetType": "EQUITY", "symbol": "AAPL"},
          "amount": 5.0, "cost": -900.0, "price": 180.0, "positionEffect": "OPENING"}],
    )
    _insert_trade(
        db, 3002, "2026-04-10T10:00:00+0000", "HASH1", "ACC1",
        [{"instrument": {"assetType": "EQUITY", "symbol": "AAPL"},
          "amount": 5.0, "cost": 950.0, "price": 190.0, "positionEffect": "CLOSING"}],
    )

    analytics = SchwabAnalytics(db=db)
    count = analytics.analyze_monthly_pnl()
    assert count == 2

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT year_month, net_cash_flow FROM monthly_pnl ORDER BY year_month")
        rows = cursor.fetchall()

    assert rows[0]["year_month"] == "2026-03"
    assert rows[0]["net_cash_flow"] == pytest.approx(-900.0)
    assert rows[1]["year_month"] == "2026-04"
    assert rows[1]["net_cash_flow"] == pytest.approx(950.0)


def test_analyze_monthly_pnl_upsert_is_idempotent(tmp_path):
    """Re-running analyze produces the same row count, not duplicates."""
    db = _make_db(tmp_path)
    _insert_trade(
        db, 4001, "2026-05-01T10:00:00+0000", "HASH1", "ACC1",
        [{"instrument": {"assetType": "EQUITY", "symbol": "MSFT"},
          "amount": 3.0, "cost": -1200.0, "price": 400.0, "positionEffect": "OPENING"}],
    )

    analytics = SchwabAnalytics(db=db)
    assert analytics.analyze_monthly_pnl() == 1
    assert analytics.analyze_monthly_pnl() == 1  # idempotent

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM monthly_pnl")
        assert cursor.fetchone()[0] == 1


def test_analyze_monthly_pnl_multiple_accounts(tmp_path):
    """Different account hashes produce separate rows for the same month."""
    db = _make_db(tmp_path)
    _insert_trade(
        db, 5001, "2026-06-01T10:00:00+0000", "HASH_A", "ACC_A",
        [{"instrument": {"assetType": "EQUITY", "symbol": "SPY"},
          "amount": 2.0, "cost": -1000.0, "price": 500.0, "positionEffect": "OPENING"}],
    )
    _insert_trade(
        db, 5002, "2026-06-15T10:00:00+0000", "HASH_B", "ACC_B",
        [{"instrument": {"assetType": "EQUITY", "symbol": "QQQ"},
          "amount": 4.0, "cost": -2000.0, "price": 500.0, "positionEffect": "OPENING"}],
    )

    analytics = SchwabAnalytics(db=db)
    count = analytics.analyze_monthly_pnl()
    assert count == 2

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT account_hash, net_cash_flow FROM monthly_pnl ORDER BY account_hash"
        )
        rows = cursor.fetchall()

    assert {r["account_hash"] for r in rows} == {"HASH_A", "HASH_B"}


# ===========================================================================
# analyze_monthly_snapshots tests
# ===========================================================================

import json as _json


def _insert_snapshot(db, account_hash, account_number, snapshot_at, account_type,
                     liquidation_value, equity, cash_balance, buying_power,
                     current_balances=None):
    """Helper to insert a raw account snapshot."""
    current = current_balances or {}
    current.setdefault("liquidationValue", liquidation_value)
    current.setdefault("equity", equity)
    current.setdefault("cashBalance", cash_balance)
    current.setdefault("buyingPower", buying_power)

    account = {
        "securitiesAccount": {
            "accountNumber": account_number,
            "type": account_type,
            "currentBalances": current,
            "initialBalances": {},
            "projectedBalances": {},
        }
    }
    db.insert_account_snapshot(account, account_hash, snapshot_at)


def test_analyze_monthly_snapshots_empty_db(tmp_path):
    """Returns 0 when there are no snapshots."""
    db = _make_db(tmp_path)
    analytics = SchwabAnalytics(db=db)
    assert analytics.analyze_monthly_snapshots() == 0


def test_analyze_monthly_snapshots_creates_table(tmp_path):
    """monthly_account_snapshots table is created even with no data."""
    db = _make_db(tmp_path)
    analytics = SchwabAnalytics(db=db)
    analytics.analyze_monthly_snapshots()

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_account_snapshots'"
        )
        assert cursor.fetchone() is not None


def test_analyze_monthly_snapshots_picks_last_of_month(tmp_path):
    """When multiple snapshots exist in a month, the latest one is used."""
    db = _make_db(tmp_path)
    # Earlier snapshot in March
    _insert_snapshot(db, "HASH1", "ACC1", "2026-03-10T12:00:00Z", "MARGIN",
                     liquidation_value=10000.0, equity=9000.0,
                     cash_balance=500.0, buying_power=1000.0)
    # Later snapshot in March — this should win
    _insert_snapshot(db, "HASH1", "ACC1", "2026-03-31T12:00:00Z", "MARGIN",
                     liquidation_value=11000.0, equity=9500.0,
                     cash_balance=600.0, buying_power=1200.0)

    analytics = SchwabAnalytics(db=db)
    count = analytics.analyze_monthly_snapshots()
    assert count == 1

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM monthly_account_snapshots WHERE year_month = '2026-03'")
        row = cursor.fetchone()

    assert row is not None
    assert row["liquidation_value"] == pytest.approx(11000.0)
    assert row["equity"] == pytest.approx(9500.0)
    assert row["snapshot_at"] == "2026-03-31T12:00:00Z"


def test_analyze_monthly_snapshots_extracts_json_fields(tmp_path):
    """Extended fields are extracted from current_balances_json via json_extract."""
    db = _make_db(tmp_path)
    balances = {
        "longMarketValue": 8500.0,
        "shortMarketValue": -200.0,
        "marginBalance": 1500.0,
        "maintenanceRequirement": 750.0,
        "cashAvailableForTrading": 450.0,
        "cashAvailableForWithdrawal": 300.0,
        "moneyMarketFund": 100.0,
        "totalCash": 600.0,
    }
    _insert_snapshot(db, "HASH1", "ACC1", "2026-04-30T18:00:00Z", "MARGIN",
                     liquidation_value=10000.0, equity=8500.0,
                     cash_balance=600.0, buying_power=1000.0,
                     current_balances=balances)

    analytics = SchwabAnalytics(db=db)
    analytics.analyze_monthly_snapshots()

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM monthly_account_snapshots WHERE year_month = '2026-04'")
        row = cursor.fetchone()

    assert row["long_market_value"] == pytest.approx(8500.0)
    assert row["short_market_value"] == pytest.approx(-200.0)
    assert row["margin_balance"] == pytest.approx(1500.0)
    assert row["maintenance_requirement"] == pytest.approx(750.0)
    assert row["cash_available_for_trading"] == pytest.approx(450.0)
    assert row["money_market_fund"] == pytest.approx(100.0)
    assert row["total_cash"] == pytest.approx(600.0)


def test_analyze_monthly_snapshots_missing_json_fields_are_null(tmp_path):
    """Fields absent from current_balances_json are stored as NULL (not erroring)."""
    db = _make_db(tmp_path)
    # Cash account — no margin fields in the JSON
    _insert_snapshot(db, "HASH1", "ACC1", "2026-05-15T09:00:00Z", "CASH",
                     liquidation_value=5000.0, equity=5000.0,
                     cash_balance=5000.0, buying_power=5000.0)

    analytics = SchwabAnalytics(db=db)
    analytics.analyze_monthly_snapshots()

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM monthly_account_snapshots WHERE year_month = '2026-05'")
        row = cursor.fetchone()

    assert row is not None
    assert row["long_market_value"] is None
    assert row["margin_balance"] is None
    assert row["maintenance_requirement"] is None
    assert row["liquidation_value"] == pytest.approx(5000.0)


def test_analyze_monthly_snapshots_multiple_months(tmp_path):
    """Snapshots in different months produce separate rows."""
    db = _make_db(tmp_path)
    _insert_snapshot(db, "HASH1", "ACC1", "2026-01-31T12:00:00Z", "MARGIN",
                     liquidation_value=9000.0, equity=8000.0,
                     cash_balance=400.0, buying_power=800.0)
    _insert_snapshot(db, "HASH1", "ACC1", "2026-02-28T12:00:00Z", "MARGIN",
                     liquidation_value=9500.0, equity=8500.0,
                     cash_balance=450.0, buying_power=900.0)

    analytics = SchwabAnalytics(db=db)
    count = analytics.analyze_monthly_snapshots()
    assert count == 2

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT year_month, liquidation_value FROM monthly_account_snapshots ORDER BY year_month"
        )
        rows = cursor.fetchall()

    assert rows[0]["year_month"] == "2026-01"
    assert rows[0]["liquidation_value"] == pytest.approx(9000.0)
    assert rows[1]["year_month"] == "2026-02"
    assert rows[1]["liquidation_value"] == pytest.approx(9500.0)


def test_analyze_monthly_snapshots_upsert_idempotent(tmp_path):
    """Re-running analyze doesn't create duplicate rows."""
    db = _make_db(tmp_path)
    _insert_snapshot(db, "HASH1", "ACC1", "2026-06-30T12:00:00Z", "MARGIN",
                     liquidation_value=12000.0, equity=11000.0,
                     cash_balance=700.0, buying_power=1400.0)

    analytics = SchwabAnalytics(db=db)
    assert analytics.analyze_monthly_snapshots() == 1
    assert analytics.analyze_monthly_snapshots() == 1  # idempotent

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM monthly_account_snapshots")
        assert cursor.fetchone()[0] == 1


def test_analyze_monthly_snapshots_multiple_accounts(tmp_path):
    """Different accounts produce separate rows for the same month."""
    db = _make_db(tmp_path)
    _insert_snapshot(db, "HASH_A", "ACC_A", "2026-06-30T12:00:00Z", "MARGIN",
                     liquidation_value=50000.0, equity=45000.0,
                     cash_balance=5000.0, buying_power=10000.0)
    _insert_snapshot(db, "HASH_B", "ACC_B", "2026-06-28T12:00:00Z", "CASH",
                     liquidation_value=20000.0, equity=20000.0,
                     cash_balance=20000.0, buying_power=20000.0)

    analytics = SchwabAnalytics(db=db)
    count = analytics.analyze_monthly_snapshots()
    assert count == 2

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT account_hash, liquidation_value FROM monthly_account_snapshots ORDER BY account_hash"
        )
        rows = cursor.fetchall()

    assert {r["account_hash"] for r in rows} == {"HASH_A", "HASH_B"}
