"""
services/account_service.py — Account balance retrieval.

Contains no Flask imports; relies solely on models.db.get_db().
"""

from models.db import get_db


def get_account(customer_id: int):
    """Return the account row for the given customer.

    Args:
        customer_id: The integer primary key from the customers table,
                     typically taken from session["customer_id"].

    Returns:
        sqlite3.Row with keys (id, customer_id, balance) or None if the
        account does not exist.
    """
    db = get_db()
    return db.execute(
        "SELECT id, customer_id, balance FROM accounts WHERE customer_id = ?",
        (customer_id,),
    ).fetchone()
