"""
Central configuration module for ContractForge Auditor backend.

Reads all required and optional settings from environment variables at import
time.  If a required variable is absent the process exits immediately with a
clear error message so misconfigured deployments fail fast rather than
producing cryptic runtime errors later.

Relevant requirements: 10.5 (API key validation), 10.6 (fail-fast on missing
key), 10.7 (configurable model and CORS origin).
"""

import os
import sys

# ---------------------------------------------------------------------------
# Required — fail fast if missing (Req 10.5, 10.6)
# ---------------------------------------------------------------------------
GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    print("GOOGLE_API_KEY is required", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Optional with sensible defaults (Req 10.7)
# ---------------------------------------------------------------------------
FRONTEND_ORIGIN: str = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

# ---------------------------------------------------------------------------
# Lobster Trap DPI proxy (optional — Veea Track 1 integration)
# When set, all Gemini calls are routed through the proxy for deep prompt
# inspection, policy enforcement, and governance audit trail.
# ---------------------------------------------------------------------------
LOBSTERTRAP_URL: str = os.environ.get("LOBSTERTRAP_URL", "")
