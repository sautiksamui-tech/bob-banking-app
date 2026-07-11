"""
routes/dashboard_routes.py — Customer dashboard.

Routes:
  GET /dashboard — show account summary (name + balance)
"""

from flask import Blueprint, render_template, session

from routes.utils import login_required
from services.account_service import get_account

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    """Render the dashboard for the logged-in customer."""
    customer_id = session["customer_id"]
    customer_name = session.get("customer_name", "Customer")

    account = get_account(customer_id)
    balance = account["balance"] if account else 0.0

    return render_template(
        "dashboard.html",
        customer_name=customer_name,
        balance=balance,
    )
