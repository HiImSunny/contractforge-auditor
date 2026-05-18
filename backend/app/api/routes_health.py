"""GET /api/health — health check endpoint (Req 8.6).

Returns a lightweight JSON response indicating that the API process is
running and whether the Gemini API key is configured.  Intended for use
by load balancers, container orchestrators, and monitoring systems.

No authentication is required for this endpoint.
"""
import os

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """Return the current health status of the API.

    Checks for the presence of the ``GOOGLE_API_KEY`` environment variable
    to report whether Gemini is configured (Req 8.6).

    Returns:
        A JSON object with:
          - ``status``: always ``"ok"`` when the process is reachable.
          - ``version``: the current application version string.
          - ``gemini_configured``: ``true`` if ``GOOGLE_API_KEY`` is set.
    """
    return {
        "status": "ok",
        "version": "0.1.0",
        "gemini_configured": bool(os.environ.get("GOOGLE_API_KEY", "")),
    }
