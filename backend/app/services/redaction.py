"""PII redaction for logs (Req 5.4).

Applies a set of regex patterns to strip email addresses, phone numbers,
and government identifier patterns (SSN, passport-style, numeric) from
any free-text string before it is written to server logs.

The RedactionFilter class integrates with Python's standard logging
framework so that every log record's message is automatically redacted
when the filter is installed on a handler or logger.
"""
import logging
import re

PII_PATTERNS = [
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
    (re.compile(r"\+?\d[\d\s().\-]{7,}\d"), "[REDACTED_PHONE]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_GOVID]"),
    (re.compile(r"\b\d{9}(?:\d{3})?\b"), "[REDACTED_GOVID]"),
    (re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"), "[REDACTED_GOVID]"),
]


def redact(text: str) -> str:
    """Apply all PII patterns to text and return the redacted string."""
    for pattern, repl in PII_PATTERNS:
        text = pattern.sub(repl, text)
    return text


class RedactionFilter(logging.Filter):
    """logging.Filter that redacts PII from every log record message."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(str(record.msg))
        if record.args:
            record.args = (
                tuple(redact(str(a)) for a in record.args)
                if isinstance(record.args, tuple)
                else redact(str(record.args))
            )
        return True
