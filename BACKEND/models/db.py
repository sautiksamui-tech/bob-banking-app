"""
models/db.py — The only module that speaks directly to SQLite.

Provides:
  get_db()   — per-request connection (stored on Flask g)
  close_db() — teardown hook registered in app.py
  init_db()  — idempotent table creation
  seed_db()  — insert two test customers if the table is empty
"""

import sqlite3
from datetime import datetime

from flask import current_app, g
from werkzeug.security import generate_password_hash


# ── Connection helper ────────────────────────────────────────────────────────

def get_db():
    """Return the open SQLite connection for this request.

    Opens a new connection if one has not yet been created for the current
    application context and stores it on Flask's ``g`` object so the same
    connection is reused within a single request.
    """
    if "_database" not in g:
        g._database = sqlite3.connect(
            current_app.config["DATABASE_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        # Row factory lets callers access columns by name: row["balance"]
        g._database.row_factory = sqlite3.Row
    return g._database


def close_db(e=None):  # noqa: ARG001
    """Close the database connection at the end of the request context."""
    db = g.pop("_database", None)
    if db is not None:
        db.close()


# ── Schema initialisation ────────────────────────────────────────────────────

def init_db():
    """Create all tables if they do not already exist.

    Safe to call on every application startup — the ``IF NOT EXISTS`` clause
    makes this operation idempotent.
    """
    db = get_db()
    db.executescript(
        """
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
        """
    )
    db.commit()


# ── Seed data ────────────────────────────────────────────────────────────────

_SEED_CUSTOMERS = [
    {
        "username": "alice",
        "password": "password123",
        "full_name": "Alice Johnson",
        "balance": 1000.00,
    },
    {
        "username": "bob",
        "password": "secret456",
        "full_name": "Bob Smith",
        "balance": 2500.00,
    },
]


def seed_db():
    """Insert test customers and their accounts if the table is empty.

    Called once at startup.  The ``COUNT(*)`` guard prevents duplicates
    if the database file already exists from a previous run.
    """
    db = get_db()
    row = db.execute("SELECT COUNT(*) AS cnt FROM customers").fetchone()
    if row["cnt"] > 0:
        return  # Data already seeded — nothing to do

    for customer in _SEED_CUSTOMERS:
        cursor = db.execute(
            "INSERT INTO customers (username, password_hash, full_name) VALUES (?, ?, ?)",
            (
                customer["username"],
                generate_password_hash(customer["password"]),
                customer["full_name"],
            ),
        )
        customer_id = cursor.lastrowid
        db.execute(
            "INSERT INTO accounts (customer_id, balance) VALUES (?, ?)",
            (customer_id, customer["balance"]),
        )

    db.commit()
