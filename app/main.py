"""FastAPI app: load clean CSV at startup, serve API + static UI on one origin."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.projects import build_router
from app.store import Store

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLEAN_CSV = ROOT / "clean_transactions.csv"
DEFAULT_STATIC_DIR = ROOT / "frontend" / "out"


def create_app(
    clean_csv: str | Path = os.environ.get("CLEAN_CSV", str(DEFAULT_CLEAN_CSV)),
    static_dir: str | Path | None = os.environ.get("STATIC_DIR", str(DEFAULT_STATIC_DIR)),
) -> FastAPI:
    store = Store.from_csv(str(clean_csv))

    app = FastAPI(title="Property Transactions Pipeline")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(build_router(store))

    if static_dir is not None and Path(static_dir).is_dir():
        app.mount(
            "/",
            StaticFiles(directory=str(static_dir), html=True),
            name="static",
        )

    return app


app = create_app()