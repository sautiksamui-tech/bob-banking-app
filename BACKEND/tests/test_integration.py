"""
tests/test_integration.py — Integration tests using Flask's test client.

Verifies that routes, services, and the in-memory database work together
correctly end-to-end.  No real bank.db file is touched.
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


# ── Build a fully-wired test app ─────────────────────────────────────────────

def _create_integration_app():
    """Return a Flask test app with blueprints registered and in-memory DB."""
    import config as _config  # noqa: PLC0415

    # We need to override DATABASE_PATH before importing blueprints/services
    # that call get_db(), so we patch at the config level.
    _config.DATABASE_PATH = ":memory:"

    from app import create_app
    test_app = create_app()
    test_app.config["TESTING"] = True
    test_app.config["DATABASE_PATH"] = ":memory:"
    return test_app


# We maintain a single module-level in-memory DB connection across the test
# suite so all tables/data created in setUp are visible to the route handlers.
_SHARED_DB: sqlite3.Connection | None = None


def _get_shared_db():
    global _SHARED_DB
    if _SHARED_DB is None:
        _SHARED_DB = sqlite3.connect(":memory:", check_same_thread=False)
        _SHARED_DB.row_factory = sqlite3.Row
    return _SHARED_DB


def _reset_shared_db():
    global _SHARED_DB
    if _SHARED_DB is not None:
        _SHARED_DB.close()
        _SHARED_DB = None


# ── Base class ───────────────────────────────────────────────────────────────

class IntegrationTestBase(unittest.TestCase):
    """
    Sets up a fresh in-memory database and a Flask test client for each test.

    Strategy: patch models.db.get_db to return an in-memory connection so
    that all services operate on isolated test data.
    """

    def setUp(self):
        _reset_shared_db()

        # Patch get_db everywhere it was imported
        def patched_get_db():
            return _get_shared_db()

        _db_module.get_db = patched_get_db
        _auth_svc.get_db = patched_get_db
        _acct_svc.get_db = patched_get_db
        _tx_svc.get_db = patched_get_db

        # Import and build the app *after* patching.
        from flask import Flask
        from routes.auth_routes import auth_bp
        from routes.dashboard_routes import dashboard_bp
        from routes.transaction_routes import transaction_bp

        app = Flask(
            __name__,
            template_folder=os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "FRONTEND", "templates",
            ),
        )
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        app.config["DATABASE_PATH"] = ":memory:"
        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(transaction_bp)

        # Initialise schema on the shared in-memory DB.
        db = _get_shared_db()
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

        # Seed one customer.
        cursor = db.execute(
            "INSERT INTO customers (username, password_hash, full_name) VALUES (?, ?, ?)",
            ("testuser", generate_password_hash("testpass"), "Test User"),
        )
        self.customer_id = cursor.lastrowid
        db.execute(
            "INSERT INTO accounts (customer_id, balance) VALUES (?, ?)",
            (self.customer_id, 500.0),
        )
        db.commit()

        self.app = app
        self.client = app.test_client()

    def tearDown(self):
        _db_module.get_db = ORIGINAL_GET_DB
        _auth_svc.get_db = ORIGINAL_GET_DB
        _acct_svc.get_db = ORIGINAL_GET_DB
        _tx_svc.get_db = ORIGINAL_GET_DB
        _reset_shared_db()

    def _login(self):
        """Helper: perform a successful login and return the response."""
        return self.client.post(
            "/login",
            data={"username": "testuser", "password": "testpass"},
            follow_redirects=True,
        )

    def _get_balance(self):
        db = _get_shared_db()
        row = db.execute(
            "SELECT balance FROM accounts WHERE customer_id = ?",
            (self.customer_id,),
        ).fetchone()
        return row["balance"]


# ── Authentication route tests ───────────────────────────────────────────────

class TestLoginRoute(IntegrationTestBase):

    def test_get_login_page_returns_200(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Sign In", resp.data)

    def test_post_valid_credentials_redirects_to_dashboard(self):
        resp = self.client.post(
            "/login",
            data={"username": "testuser", "password": "testpass"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/dashboard", resp.headers["Location"])

    def test_post_invalid_password_shows_error(self):
        resp = self.client.post(
            "/login",
            data={"username": "testuser", "password": "wrongpass"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid username or password", resp.data)

    def test_post_unknown_username_shows_error(self):
        resp = self.client.post(
            "/login",
            data={"username": "nobody", "password": "testpass"},
            follow_redirects=True,
        )
        self.assertIn(b"Invalid username or password", resp.data)

    def test_get_dashboard_without_login_redirects_to_login(self):
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_logout_clears_session_and_redirects(self):
        self._login()
        resp = self.client.get("/logout")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])
        # After logout, /dashboard must redirect again.
        resp2 = self.client.get("/dashboard")
        self.assertEqual(resp2.status_code, 302)


# ── Dashboard route tests ────────────────────────────────────────────────────

class TestDashboardRoute(IntegrationTestBase):

    def test_dashboard_shows_customer_name_and_balance(self):
        self._login()
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Test User", resp.data)
        self.assertIn(b"500.00", resp.data)

    def test_dashboard_unauthenticated_redirects(self):
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 302)


# ── Deposit route tests ──────────────────────────────────────────────────────

class TestDepositRoute(IntegrationTestBase):

    def test_valid_deposit_updates_balance(self):
        self._login()
        resp = self.client.post("/deposit", data={"amount": "200"})
        self.assertEqual(resp.status_code, 302)  # PRG redirect
        self.assertAlmostEqual(self._get_balance(), 700.0)

    def test_deposit_zero_shows_error_flash(self):
        self._login()
        resp = self.client.post("/deposit", data={"amount": "0"}, follow_redirects=True)
        self.assertIn(b"greater than zero", resp.data)

    def test_deposit_negative_shows_error_flash(self):
        self._login()
        resp = self.client.post("/deposit", data={"amount": "-10"}, follow_redirects=True)
        self.assertIn(b"greater than zero", resp.data)

    def test_deposit_non_numeric_shows_error_flash(self):
        self._login()
        resp = self.client.post("/deposit", data={"amount": "abc"}, follow_redirects=True)
        self.assertIn(b"valid", resp.data.lower())

    def test_deposit_without_login_redirects(self):
        resp = self.client.post("/deposit", data={"amount": "100"})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])


# ── Withdrawal route tests ───────────────────────────────────────────────────

class TestWithdrawRoute(IntegrationTestBase):

    def test_valid_withdrawal_updates_balance(self):
        self._login()
        resp = self.client.post("/withdraw", data={"amount": "150"})
        self.assertEqual(resp.status_code, 302)
        self.assertAlmostEqual(self._get_balance(), 350.0)

    def test_withdraw_exact_balance_succeeds(self):
        self._login()
        resp = self.client.post("/withdraw", data={"amount": "500"})
        self.assertEqual(resp.status_code, 302)
        self.assertAlmostEqual(self._get_balance(), 0.0)

    def test_withdraw_over_balance_shows_insufficient_funds(self):
        self._login()
        resp = self.client.post("/withdraw", data={"amount": "999"}, follow_redirects=True)
        self.assertIn(b"Insufficient", resp.data)

    def test_withdraw_zero_shows_error_flash(self):
        self._login()
        resp = self.client.post("/withdraw", data={"amount": "0"}, follow_redirects=True)
        self.assertIn(b"greater than zero", resp.data)

    def test_withdraw_without_login_redirects(self):
        resp = self.client.post("/withdraw", data={"amount": "100"})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])


if __name__ == "__main__":
    unittest.main()
