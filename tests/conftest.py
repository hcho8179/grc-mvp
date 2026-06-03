"""Shared pytest configuration.

Enables testing mode before any test module imports the FastAPI app so CSRF
middleware is skipped (see app.config.Settings.testing).
"""

import os

# Must run before test modules import app.main (pytest loads conftest first).
os.environ["TESTING"] = "true"

from app.config import get_settings

get_settings.cache_clear()
