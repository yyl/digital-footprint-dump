from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from src.schwab.database import SchwabDatabase
from src.schwab.sync import SchwabSyncManager, _parse_sync_datetime


def test_schwab_database_stores_snapshots_append_only_and_transactions_upsert(tmp_path):
    db = SchwabDatabase(str(tmp_path / "schwab.db"))
    db.init_tables()

    account = {
        "securitiesAccount": {
            "accountNumber": "20001000",
            "type": "MARGIN",
            "initialBalances": {
                "cashBalance": 125.0,
                "liquidationValue": 1000.0,
            },
            "currentBalances": {
                "buyingPower": 500.0,
                "equity": 995.0,
            },
            "projectedBalances": {},
        }
    }
    transaction = {
        "activityId": 132498126081,
        "time": "2026-06-15T14:36:16+0000",
        "accountNumber": "20001000",
        "type": "TRADE",
        "status": "VALID",
        "subAccount": "MARGIN",
        "netAmount": -3420.0,
        "transferItems": [{"instrument": {"symbol": "SPCX"}}],
    }

    db.insert_account_snapshot(account, "HASH123", "2026-06-19T12:00:00Z")
    db.insert_account_snapshot(account, "HASH123", "2026-06-19T13:00:00Z")
    assert db.upsert_transaction(transaction, "HASH123", "20001000") is True

    updated_transaction = dict(transaction)
    updated_transaction["status"] = "CANCELED"
    assert db.upsert_transaction(updated_transaction, "HASH123", "20001000") is False

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM account_snapshots")
        assert cursor.fetchone()[0] == 2

        cursor.execute("SELECT status, raw_json FROM transactions")
        row = cursor.fetchone()
        assert row["status"] == "CANCELED"
        assert "transferItems" in row["raw_json"]


def test_schwab_sync_fetches_accounts_and_transactions(tmp_path):
    db = SchwabDatabase(str(tmp_path / "schwab.db"))
    api = MagicMock()
    api.ensure_auth.return_value = True
    api.needs_auth.return_value = False
    api.get_account_numbers.return_value = [
        {"accountNumber": "20001000", "hashValue": "HASH123"}
    ]
    api.get_accounts.return_value = [
        {
            "securitiesAccount": {
                "accountNumber": "20001000",
                "currentBalances": {"equity": 1000.0},
            }
        }
    ]
    api.get_transactions.return_value = [
        {
            "activityId": 1,
            "time": "2026-06-15T14:36:16+0000",
            "type": "TRADE",
            "status": "VALID",
            "netAmount": -10.0,
        }
    ]

    manager = SchwabSyncManager(db=db, api=api)
    stats = manager.sync()

    assert stats == {
        "account_snapshots": 1,
        "transactions": 1,
        "accounts": 1,
    }
    api.get_transactions.assert_called_once()
    assert api.get_transactions.call_args.args[0] == "HASH123"

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT account_hash FROM account_snapshots")
        assert cursor.fetchone()["account_hash"] == "HASH123"
        cursor.execute("SELECT account_hash, transaction_id FROM transactions")
        row = cursor.fetchone()
        assert row["account_hash"] == "HASH123"
        assert row["transaction_id"] == "1"


def test_schwab_sync_defaults_to_client_and_database():
    with patch("src.schwab.sync.SchwabDatabase") as mock_db_cls, patch(
        "src.schwab.sync.SchwabAPIClient"
    ) as mock_api_cls:
        manager = SchwabSyncManager()

    assert manager.db == mock_db_cls.return_value
    assert manager.api == mock_api_cls.return_value


def test_schwab_transaction_window_uses_one_year_for_initial_sync(tmp_path):
    db = SchwabDatabase(str(tmp_path / "schwab.db"))
    db.init_tables()
    manager = SchwabSyncManager(db=db, api=MagicMock())

    sync_start = datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc)

    assert manager._transaction_window("HASH123", sync_start) == (
        "2025-06-20T12:00:00.000Z",
        "2026-06-20T12:00:00.000Z",
    )


def test_schwab_transaction_window_uses_latest_transaction(tmp_path):
    db = SchwabDatabase(str(tmp_path / "schwab.db"))
    db.init_tables()
    db.upsert_transaction(
        {
            "activityId": 1,
            "time": "2026-06-15T14:36:16+0000",
            "type": "TRADE",
            "status": "VALID",
        },
        "HASH123",
        "20001000",
    )
    manager = SchwabSyncManager(db=db, api=MagicMock())

    sync_start = datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc)

    assert manager._transaction_window("HASH123", sync_start) == (
        "2026-06-15T14:36:16.000Z",
        "2026-06-20T12:00:00.000Z",
    )


def test_parse_schwab_datetime_offset_without_colon():
    parsed = _parse_sync_datetime("2026-06-15T14:36:16+0000")

    assert parsed == datetime(2026, 6, 15, 14, 36, 16, tzinfo=timezone.utc)
