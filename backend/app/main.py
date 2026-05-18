"""FastAPI application entry point for ContractForge Auditor (Req 10.4, 10.5, 5.4).

Req 10.4 — CORS is configured from FRONTEND_ORIGIN (comma-separated) plus a
            regex that allows all *.vercel.app preview deployments.
Req 10.5 — Importing ``app.config`` at module level triggers the fail-fast
            GOOGLE_API_KEY check before any request can be served.
Req 5.4  — A RedactionFilter is installed on the root logger so that PII is
            stripped from every log record before it is written.
"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import config first — triggers fail-fast GOOGLE_API_KEY check (Req 10.5, 10.6)
from app import config  # noqa: F401
from app.services.redaction import RedactionFilter
from app.api import (
    routes_upload,
    routes_analyze,
    routes_simulate,
    routes_audit,
    routes_report,
    routes_health,
    routes_load_sample,
)

# Install PII redaction filter on the root logger (Req 5.4)
logging.getLogger().addFilter(RedactionFilter())

app = FastAPI(
    title="ContractForge Auditor",
    version="0.1.0",
    description="Multi-agent AI platform for enterprise contract governance.",
)

# CORS (Req 10.4) — parse comma-separated FRONTEND_ORIGIN + allow *.vercel.app
_raw_origins = config.FRONTEND_ORIGIN.split(",")
_origins = [o.strip() for o in _raw_origins if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers under /api
app.include_router(routes_upload.router, prefix="/api")
app.include_router(routes_analyze.router, prefix="/api")
app.include_router(routes_simulate.router, prefix="/api")
app.include_router(routes_audit.router, prefix="/api")
app.include_router(routes_report.router, prefix="/api")
app.include_router(routes_health.router, prefix="/api")
app.include_router(routes_load_sample.router, prefix="/api")
