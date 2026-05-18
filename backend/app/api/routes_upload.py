"""POST /api/upload — file upload endpoint (Req 1.1–1.5, 8.1).

Accepts a multipart form with two files:
  - ``contract``: PDF or plain-text contract document (Req 1.2)
  - ``policy``:   PDF, CSV, or plain-text policy document (Req 1.3)

Validates MIME types and file sizes (Req 1.4, 1.5), creates a new job in
the in-memory job store, and returns the assigned ``job_id`` together with
the uploaded filenames and detected language (Req 8.1).
"""
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException

from app.services import job_store

router = APIRouter()

MAX_SIZE = 15 * 1024 * 1024  # 15 MB (Req 1.4)
CONTRACT_MIME = {"application/pdf", "text/plain"}
POLICY_MIME = {"application/pdf", "text/csv", "text/plain"}


@router.post("/upload")
async def upload(contract: UploadFile = File(...), policy: UploadFile = File(...)):
    """Upload a contract and policy file to create a new analysis job.

    Validates MIME types (Req 1.2, 1.3, 1.5) and file sizes (Req 1.4),
    then stores the raw bytes and decoded text in the job store.

    Returns:
        A JSON object with ``job_id``, ``contract_filename``,
        ``policy_filename``, and ``detected_language``.

    Raises:
        HTTPException 415: If either file has an unsupported MIME type.
        HTTPException 413: If either file exceeds the 15 MB size limit.
    """
    # Check MIME types (Req 1.2, 1.3, 1.5)
    if contract.content_type not in CONTRACT_MIME:
        raise HTTPException(
            415,
            {
                "error_code": "UNSUPPORTED_MEDIA_TYPE",
                "field": "contract",
                "message": f"Unsupported contract type: {contract.content_type}",
            },
        )
    if policy.content_type not in POLICY_MIME:
        raise HTTPException(
            415,
            {
                "error_code": "UNSUPPORTED_MEDIA_TYPE",
                "field": "policy",
                "message": f"Unsupported policy type: {policy.content_type}",
            },
        )

    contract_bytes = await contract.read()
    policy_bytes = await policy.read()

    # Check file sizes (Req 1.4)
    if len(contract_bytes) > MAX_SIZE:
        raise HTTPException(
            413,
            {
                "error_code": "FILE_TOO_LARGE",
                "max_size_bytes": MAX_SIZE,
                "field": "contract",
            },
        )
    if len(policy_bytes) > MAX_SIZE:
        raise HTTPException(
            413,
            {
                "error_code": "FILE_TOO_LARGE",
                "max_size_bytes": MAX_SIZE,
                "field": "policy",
            },
        )

    job_id = str(uuid.uuid4())

    # Decode text content; PDF bytes are kept raw for the ingestion agent
    contract_text = (
        contract_bytes.decode("utf-8", errors="replace")
        if contract.content_type == "text/plain"
        else ""
    )
    policy_text = policy_bytes.decode("utf-8", errors="replace")

    job_store.put(
        job_id,
        contract_filename=contract.filename,
        policy_filename=policy.filename,
        contract_text=contract_text,
        contract_bytes=contract_bytes if contract.content_type == "application/pdf" else b"",
        policy_text=policy_text,
        detected_language="en",  # updated after ingestion agent runs
    )

    return {
        "job_id": job_id,
        "contract_filename": contract.filename,
        "policy_filename": policy.filename,
        "detected_language": "en",
    }
