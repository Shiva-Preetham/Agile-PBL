"""ChurnSense API entry point.

Run locally:  uvicorn app.main:app --reload   (from the backend/ folder)
Interactive API docs are then at http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import CORS_ORIGIN_REGEX, CORS_ORIGINS, SEED_DEMO_DATA
from app.database import SessionLocal, init_db
from app.routers import customers, dashboard, model
from app.seed import seed_demo_data

logger = logging.getLogger("churnsense")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    if SEED_DEMO_DATA:
        with SessionLocal() as db:
            added = seed_demo_data(db)
        logger.info("Demo seeding: %s customers added", added)
    yield


app = FastAPI(
    title="ChurnSense API",
    description="Explainable customer churn prediction: validate, predict, explain, act.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(model.router)
app.include_router(dashboard.router)


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok", "version": __version__}
