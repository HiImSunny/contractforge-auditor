"""In-memory job store (Req 5.5). Thread-safe dict keyed by job_id."""
from threading import Lock
from typing import Any

_STORE: dict[str, dict[str, Any]] = {}
_LOCK = Lock()


def get(job_id: str) -> dict | None:
    with _LOCK:
        return _STORE.get(job_id)


def put(job_id: str, **fields) -> None:
    with _LOCK:
        if job_id not in _STORE:
            _STORE[job_id] = {"audit_entries": []}
        _STORE[job_id].update(fields)


def append_audit(job_id: str, entry: dict) -> None:
    with _LOCK:
        if job_id not in _STORE:
            _STORE[job_id] = {"audit_entries": []}
        _STORE[job_id]["audit_entries"].append(entry)


def exists(job_id: str) -> bool:
    with _LOCK:
        return job_id in _STORE
