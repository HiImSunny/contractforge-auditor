"""In-memory job store (Req 5.5). Thread-safe dict keyed by job_id."""
from queue import Queue
from threading import Lock
from typing import Any

_STORE: dict[str, dict[str, Any]] = {}
_LOCK = Lock()

# Per-job event queues for SSE streaming.
# Each queue holds dicts: {"event": str, "data": str}
# Sentinel None signals the stream to close.
_QUEUES: dict[str, list[Queue]] = {}
_QLOCK = Lock()


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


# ── SSE helpers ──────────────────────────────────────────────────────────────

def subscribe(job_id: str) -> Queue:
    """Register a new SSE subscriber for *job_id*. Returns a Queue."""
    q: Queue = Queue()
    with _QLOCK:
        _QUEUES.setdefault(job_id, []).append(q)
    return q


def unsubscribe(job_id: str, q: Queue) -> None:
    """Remove a subscriber queue."""
    with _QLOCK:
        listeners = _QUEUES.get(job_id, [])
        if q in listeners:
            listeners.remove(q)


def push_event(job_id: str, event: str, data: str) -> None:
    """Broadcast an SSE event to all subscribers of *job_id*."""
    with _QLOCK:
        for q in _QUEUES.get(job_id, []):
            q.put({"event": event, "data": data})


def close_stream(job_id: str) -> None:
    """Send sentinel None to all subscribers so they close the connection."""
    with _QLOCK:
        for q in _QUEUES.get(job_id, []):
            q.put(None)
