"""
services/auth_service.py — Customer authentication.

Contains no Flask imports; relies solely on models.db.get_db() and werkzeug.
"""

from werkzeug.security import check_password_hash

from models.db import get_db


def verify_credentials(username: str, password: str):
    """Verify a username/password pair against the stored hash.

    Returns the customer row (sqlite3.Row) on success, or ``None`` on
    failure.  The same ``None`` return is used for both "username not found"
    and "wrong password" to avoid revealing which field was incorrect
    (username enumeration prevention).

    Args:
        username: The username submitted by the login form.
        password: The plain-text password submitted by the login form.

    Returns:
        sqlite3.Row with keys (id, username, full_name, …) or None.
    """
    db = get_db()
    customer = db.execute(
        "SELECT id, username, password_hash, full_name FROM customers WHERE username = ?",
        (username,),
    ).fetchone()

    if customer is None:
        return None

    if not check_password_hash(customer["password_hash"], password):
        return None

    return customer
