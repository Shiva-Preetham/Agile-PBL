"""ChurnSense API entry point.

Run locally:  uvicorn app.main:app --reload   (from the backend/ folder)
Interactive API docs are then at http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.database import init_db
from app.routers import customers, model


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ChurnSense API",
    description="Explainable customer churn prediction: validate, predict, explain, act.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(model.router)


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok", "version": __version__}
