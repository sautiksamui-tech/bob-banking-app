"""
services/transaction_service.py — Deposit and withdrawal business logic.

Contains no Flask imports.  Every public function returns a 3-tuple:
    (success: bool, message: str, new_balance: float | None)

The route layer inspects the bool to decide which flash category to use;
it never needs to catch exceptions from this module.
"""

from datetime import datetime, timezone

from models.db import get_db


# ── Private helpers ──────────────────────────────────────────────────────────

def _parse_amount(amount_str: str) -> float:
    """Convert a string to a positive float.

    Raises:
        ValueError: if the string cannot be converted or represents a
                    non-positive value (handled by the calling function).
    """
    value = float(amount_str)
    return value


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _get_balance(db, customer_id: int) -> float:
    """Fetch the current balance for a customer (always reads fresh from DB)."""
    row = db.execute(
        "SELECT balance FROM accounts WHERE customer_id = ?",
        (customer_id,),
    ).fetchone()
    if row is None:
        raise LookupError(f"No account found for customer_id={customer_id}")
    return row["balance"]


def _record_transaction(db, customer_id: int, tx_type: str, amount: float) -> None:
    """Insert a row into the transactions table."""
    db.execute(
        "INSERT INTO transactions (customer_id, type, amount, timestamp) VALUES (?, ?, ?, ?)",
        (customer_id, tx_type, amount, _now_iso()),
    )


# ── Public API ───────────────────────────────────────────────────────────────

def deposit(customer_id: int, amount_str: str):
    """Add funds to the customer's account.

    Args:
        customer_id: Identifies the account to credit.
        amount_str:  Raw string from the form field (e.g. "150.00").

    Returns:
        (True,  "Deposit of $X.XX was successful. New balance: $Y.YY", new_balance)
        (False, error_message, None)
    """
    # ── Parse ────────────────────────────────────────────────────────────────
    try:
        amount = _parse_amount(amount_str)
    except (ValueError, TypeError):
        return False, "Please enter a valid numeric amount.", None

    # ── Validate ─────────────────────────────────────────────────────────────
    if amount <= 0:
        return False, "Deposit amount must be greater than zero.", None

    # ── Persist ──────────────────────────────────────────────────────────────
    db = get_db()
    db.execute(
        "UPDATE accounts SET balance = balance + ? WHERE customer_id = ?",
        (amount, customer_id),
    )
    _record_transaction(db, customer_id, "deposit", amount)
    db.commit()

    new_balance = _get_balance(db, customer_id)
    return (
        True,
        f"Deposit of ${amount:,.2f} was successful. New balance: ${new_balance:,.2f}",
        new_balance,
    )


def withdraw(customer_id: int, amount_str: str):
    """Deduct funds from the customer's account.

    Args:
        customer_id: Identifies the account to debit.
        amount_str:  Raw string from the form field.

    Returns:
        (True,  "Withdrawal of $X.XX was successful. New balance: $Y.YY", new_balance)
        (False, error_message, None)
    """
    # ── Parse ────────────────────────────────────────────────────────────────
    try:
        amount = _parse_amount(amount_str)
    except (ValueError, TypeError):
        return False, "Please enter a valid numeric amount.", None

    # ── Validate amount ──────────────────────────────────────────────────────
    if amount <= 0:
        return False, "Withdrawal amount must be greater than zero.", None

    # ── Check balance (always read fresh to avoid stale data) ────────────────
    db = get_db()
    current_balance = _get_balance(db, customer_id)

    if amount > current_balance:
        return (
            False,
            f"Insufficient funds. Your current balance is ${current_balance:,.2f}.",
            None,
        )

    # ── Persist ──────────────────────────────────────────────────────────────
    db.execute(
        "UPDATE accounts SET balance = balance - ? WHERE customer_id = ?",
        (amount, customer_id),
    )
    _record_transaction(db, customer_id, "withdrawal", amount)
    db.commit()

    new_balance = _get_balance(db, customer_id)
    return (
        True,
        f"Withdrawal of ${amount:,.2f} was successful. New balance: ${new_balance:,.2f}",
        new_balance,
    )
