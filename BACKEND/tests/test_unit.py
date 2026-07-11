"""
tests/test_unit.py — Unit tests for the service layer.

Uses an in-memory SQLite database so bank.db is never touched.
Each test class gets a fresh in-memory connection; the patching strategy
replaces get_db in *every* module that imported it (not just models.db).
"""

import sqlite3
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.conftest import ORIGINAL_GET_DB  # noqa: E402

import models.db as _db_module
import services.auth_service as _auth_svc
import services.account_service as _acct_svc
import services.transaction_service as _tx_svc

from flask import Flask
from werkzeug.security import generate_password_hash


# ── Minimal Flask app for tests (no blueprints needed for unit tests) ────────

def _make_test_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    app.config["DATABASE_PATH"] = ":memory:"
    return app


# ── Per-test in-memory DB factory ─────────────────────────────────────────────

def _make_in_memory_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_schema(db: sqlite3.Connection) -> None:
    db.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            full_name     TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS accounts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER UNIQUE NOT NULL REFERENCES customers(id),
            balance     REAL    NOT NULL DEFAULT 0.0
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            type        TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            timestamp   TEXT    NOT NULL
        );
    """)
    db.commit()


def _seed_one_customer(
    db: sqlite3.Connection,
    username: str = "testuser",
    password: str = "testpass",
    balance: float = 500.0,
) -> int:
    cursor = db.execute(
        "INSERT INTO customers (username, password_hash, full_name) VALUES (?, ?, ?)",
        (username, generate_password_hash(password), "Test User"),
    )
    customer_id = cursor.lastrowid
    db.execute(
        "INSERT INTO accounts (customer_id, balance) VALUES (?, ?)",
        (customer_id, balance),
    )
    db.commit()
    return customer_id


# ── Base class with per-test DB and patch/unpatch logic ───────────────────────

class ServiceTestBase(unittest.TestCase):
    """
    For each test:
      1. Create a fresh :memory: SQLite connection.
      2. Patch get_db in models.db AND in all service modules that
         imported it (bypassing the 'from X import Y' aliasing issue).
      3. Tear down cleanly by restoring originals and closing the connection.
    """

    def setUp(self):
        self._test_db = _make_in_memory_db()
        _init_schema(self._test_db)
        self.customer_id = self._seed()

        def _patched_get_db():
            return self._test_db

        # Patch everywhere that imported get_db
        _db_module.get_db = _patched_get_db
        _auth_svc.get_db = _patched_get_db
        _acct_svc.get_db = _patched_get_db
        _tx_svc.get_db = _patched_get_db

    def _seed(self) -> int:
        """Override in subclass to customise seed data."""
        return _seed_one_customer(self._test_db)

    def tearDown(self):
        _db_module.get_db = ORIGINAL_GET_DB
        _auth_svc.get_db = ORIGINAL_GET_DB
        _acct_svc.get_db = ORIGINAL_GET_DB
        _tx_svc.get_db = ORIGINAL_GET_DB
        self._test_db.close()


# ── AuthService unit tests ────────────────────────────────────────────────────

class TestAuthService(ServiceTestBase):

    def test_correct_credentials_returns_customer(self):
        from services.auth_service import verify_credentials
        result = verify_credentials("testuser", "testpass")
        self.assertIsNotNone(result)
        self.assertEqual(result["username"], "testuser")

    def test_wrong_password_returns_none(self):
        from services.auth_service import verify_credentials
        result = verify_credentials("testuser", "wrongpassword")
        self.assertIsNone(result)

    def test_unknown_username_returns_none(self):
        from services.auth_service import verify_credentials
        result = verify_credentials("nobody", "testpass")
        self.assertIsNone(result)

    def test_empty_username_returns_none(self):
        from services.auth_service import verify_credentials
        result = verify_credentials("", "testpass")
        self.assertIsNone(result)


# ── TransactionService — deposit unit tests ───────────────────────────────────

class TestDepositService(ServiceTestBase):

    def _seed(self):
        return _seed_one_customer(self._test_db, balance=500.0)

    def _get_balance(self) -> float:
        row = self._test_db.execute(
            "SELECT balance FROM accounts WHERE customer_id = ?",
            (self.customer_id,),
        ).fetchone()
        return row["balance"]

    def test_positive_deposit_increases_balance(self):
        from services.transaction_service import deposit
        success, _, new_balance = deposit(self.customer_id, "200")
        self.assertTrue(success)
        self.assertAlmostEqual(new_balance, 700.0)
        self.assertAlmostEqual(self._get_balance(), 700.0)

    def test_deposit_zero_returns_error(self):
        from services.transaction_service import deposit
        success, message, _ = deposit(self.customer_id, "0")
        self.assertFalse(success)
        self.assertIn("greater than zero", message)

    def test_deposit_negative_returns_error(self):
        from services.transaction_service import deposit
        success, message, _ = deposit(self.customer_id, "-50")
        self.assertFalse(success)
        self.assertIn("greater than zero", message)

    def test_deposit_non_numeric_returns_error(self):
        from services.transaction_service import deposit
        success, message, _ = deposit(self.customer_id, "abc")
        self.assertFalse(success)
        self.assertIn("valid", message.lower())

    def test_deposit_records_transaction(self):
        from services.transaction_service import deposit
        deposit(self.customer_id, "100")
        rows = self._test_db.execute(
            "SELECT * FROM transactions WHERE customer_id = ?",
            (self.customer_id,),
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["type"], "deposit")
        self.assertAlmostEqual(rows[0]["amount"], 100.0)


# ── TransactionService — withdrawal unit tests ────────────────────────────────

class TestWithdrawService(ServiceTestBase):

    def _seed(self):
        return _seed_one_customer(self._test_db, balance=500.0)

    def _get_balance(self) -> float:
        row = self._test_db.execute(
            "SELECT balance FROM accounts WHERE customer_id = ?",
            (self.customer_id,),
        ).fetchone()
        return row["balance"]

    def test_valid_withdrawal_decreases_balance(self):
        from services.transaction_service import withdraw
        success, _, new_balance = withdraw(self.customer_id, "150")
        self.assertTrue(success)
        self.assertAlmostEqual(new_balance, 350.0)
        self.assertAlmostEqual(self._get_balance(), 350.0)

    def test_withdraw_exact_balance_leaves_zero(self):
        from services.transaction_service import withdraw
        success, _, new_balance = withdraw(self.customer_id, "500")
        self.assertTrue(success)
        self.assertAlmostEqual(new_balance, 0.0)

    def test_withdraw_more_than_balance_returns_error(self):
        from services.transaction_service import withdraw
        success, message, _ = withdraw(self.customer_id, "600")
        self.assertFalse(success)
        self.assertIn("Insufficient", message)

    def test_withdraw_zero_returns_error(self):
        from services.transaction_service import withdraw
        success, message, _ = withdraw(self.customer_id, "0")
        self.assertFalse(success)
        self.assertIn("greater than zero", message)

    def test_withdraw_negative_returns_error(self):
        from services.transaction_service import withdraw
        success, message, _ = withdraw(self.customer_id, "-10")
        self.assertFalse(success)
        self.assertIn("greater than zero", message)

    def test_withdraw_non_numeric_returns_error(self):
        from services.transaction_service import withdraw
        success, message, _ = withdraw(self.customer_id, "xyz")
        self.assertFalse(success)
        self.assertIn("valid", message.lower())

    def test_withdrawal_records_transaction(self):
        from services.transaction_service import withdraw
        withdraw(self.customer_id, "50")
        rows = self._test_db.execute(
            "SELECT * FROM transactions WHERE customer_id = ?",
            (self.customer_id,),
        ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["type"], "withdrawal")
        self.assertAlmostEqual(rows[0]["amount"], 50.0)


if __name__ == "__main__":
    unittest.main()
