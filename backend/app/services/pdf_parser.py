"""pdfplumber-based PDF text extractor (Req 1.7 fallback).

This module provides a single public function, ``extract_text``, that converts
raw PDF bytes into a plain-text string using ``pdfplumber``.  It is called by
the Ingestion Agent when Gemini native PDF understanding returns empty text
(Req 1.7).  On any failure the function returns an empty string so the caller
can detect the fallback and record it in the audit trail.
"""
import io
import logging

logger = logging.getLogger(__name__)


def extract_text(data: bytes) -> str:
    """Extract plain text from PDF bytes using pdfplumber.

    Iterates over every page, joins non-empty page texts with a blank line,
    and returns the result.  Returns an empty string on any failure so the
    caller can detect the fallback and record it in the audit trail (Req 1.7).

    Parameters
    ----------
    data:
        Raw PDF file contents.

    Returns
    -------
    str
        Extracted plain text, or ``""`` if ``data`` is empty or extraction
        fails for any reason.
    """
    if not data:
        return ""
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n\n".join(p for p in pages if p.strip())
    except Exception as exc:
        logger.warning("pdfplumber extraction failed: %s", exc)
        return ""
