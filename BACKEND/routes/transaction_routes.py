"""
routes/transaction_routes.py — Deposit and withdrawal handlers.

Routes:
  GET  /transactions — render deposit/withdrawal form page
  POST /deposit      — process a deposit; POST-Redirect-GET pattern
  POST /withdraw     — process a withdrawal; POST-Redirect-GET pattern
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from routes.utils import login_required
from services.transaction_service import deposit, withdraw

transaction_bp = Blueprint("transactions", __name__)


@transaction_bp.route("/transactions")
@login_required
def transactions():
    """Render the transactions page (deposit + withdrawal forms)."""
    customer_name = session.get("customer_name", "Customer")
    return render_template("transactions.html", customer_name=customer_name)


@transaction_bp.route("/deposit", methods=["POST"])
@login_required
def do_deposit():
    """Handle a deposit form submission.

    Uses POST-Redirect-GET: always redirects after processing so that
    a browser refresh does not re-submit the form.
    """
    customer_id = session["customer_id"]
    amount_str = request.form.get("amount", "")

    success, message, _ = deposit(customer_id, amount_str)

    flash(message, "success" if success else "danger")
    return redirect(url_for("transactions.transactions"))


@transaction_bp.route("/withdraw", methods=["POST"])
@login_required
def do_withdraw():
    """Handle a withdrawal form submission.

    Uses POST-Redirect-GET: always redirects after processing.
    """
    customer_id = session["customer_id"]
    amount_str = request.form.get("amount", "")

    success, message, _ = withdraw(customer_id, amount_str)

    flash(message, "success" if success else "danger")
    return redirect(url_for("transactions.transactions"))
