"""Central configuration. Values can be overridden with environment variables."""
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def normalize_database_url(url: str) -> str:
    """Hosting providers (e.g. Render) hand out `postgres://` / `postgresql://` URLs.
    Point them at the psycopg 3 driver that SQLAlchemy should use."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


# SQLite keeps local development zero-setup; the hosted demo sets DATABASE_URL to PostgreSQL.
DATABASE_URL = normalize_database_url(
    os.getenv("DATABASE_URL", f"sqlite:///{(BACKEND_DIR / 'churnsense.db').as_posix()}")
)

# Browsers may call the API only from these websites (CORS).
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
# Any Vercel deployment of the frontend (production and preview URLs).
CORS_ORIGIN_REGEX = os.getenv("CORS_ORIGIN_REGEX", r"https://[a-z0-9-]+\.vercel\.app")

# Hosted demo: fill an empty database with the sample customers on start-up.
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "false").lower() == "true"
DEMO_DATA_PATH = BACKEND_DIR / "data" / "sample_customers.csv"

# Upload validation: stop listing errors after this many, so messages stay readable.
MAX_REPORTED_ERRORS = 20

# Trained model artefacts (created by `python -m ml.train`).
MODEL_DIR = Path(os.getenv("MODEL_DIR", BACKEND_DIR / "models"))
MODEL_PATH = MODEL_DIR / "churn_model.json"
METRICS_PATH = MODEL_DIR / "metrics.json"
