import os
from flask import Flask

from models.db import init_db, seed_db, close_db
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.transaction_routes import transaction_bp


def create_app():
    """Application factory — creates and configures the Flask app."""

    # Resolve paths relative to this file so the app can be launched from
    # any working directory.
    _backend_dir = os.path.dirname(os.path.abspath(__file__))
    _frontend_dir = os.path.join(_backend_dir, "..", "FRONTEND")

    app = Flask(
        __name__,
        template_folder=os.path.join(_frontend_dir, "templates"),
        static_folder=os.path.join(_frontend_dir, "static"),
    )

    # ── Configuration ────────────────────────────────────────────────────────
    import config  # noqa: PLC0415
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["DATABASE_PATH"] = config.DATABASE_PATH
    app.config["DEBUG"] = config.DEBUG

    # ── Teardown: close DB connection at the end of every request ────────────
    app.teardown_appcontext(close_db)

    # ── Register Blueprints ──────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transaction_bp)

    # ── Database initialisation (idempotent) ─────────────────────────────────
    with app.app_context():
        init_db()
        seed_db()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
