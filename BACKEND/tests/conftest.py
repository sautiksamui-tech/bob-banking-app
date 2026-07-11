"""
tests/conftest.py — Shared pytest fixtures.

Saves the original models.db.get_db reference at import time, before any
test file can overwrite it, so every tearDown can restore the real function.
"""

import sys
import os

# Ensure BACKEND/ is importable in all test files.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import models.db as _db_module

# Save the true original once, at collection time.
ORIGINAL_GET_DB = _db_module.get_db
