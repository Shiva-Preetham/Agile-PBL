"""Central configuration. Values can be overridden with environment variables."""
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

# SQLite keeps the prototype zero-setup. Set DATABASE_URL to a PostgreSQL URL
# (e.g. postgresql+psycopg://user:pass@localhost/churnsense) for production.
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{(BACKEND_DIR / 'churnsense.db').as_posix()}"
)

# Upload validation: stop listing errors after this many, so messages stay readable.
MAX_REPORTED_ERRORS = 20
