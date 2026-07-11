import os

# Base directory is the BACKEND/ folder (where this file lives)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Flask secret key — used to sign session cookies.
# In production this MUST come from an environment variable.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# Absolute path to the SQLite database file so the app works regardless of
# which directory it is launched from.
DATABASE_PATH = os.path.join(_BASE_DIR, "bank.db")

# Set to False in production to suppress stack traces in error responses.
DEBUG = True
