"""POST /api/load-sample — load bundled sample data for demo (Req 12.4)."""
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException

from app.services import job_store

router = APIRouter()

# Resolve sample file paths relative to this file's location
_SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"
_EN_CONTRACT = _SAMPLES_DIR / "contracts" / "saas_msa_en.txt"
_VI_CONTRACT = _SAMPLES_DIR / "contracts" / "hop_dong_dich_vu_vi.txt"
_POLICY = _SAMPLES_DIR / "policies" / "policy_bilingual.csv"

@router.post("/load-sample")
async def load_sample():
    """Load the bundled English SaaS MSA sample and bilingual policy.
    
    Creates a new job with the sample contract and policy pre-loaded,
    ready for POST /api/analyze. Returns the job_id so the frontend
    can immediately call analyze.
    
    Returns:
        {"job_id": str, "detected_language": "en"}
    
    Raises:
        HTTPException 500: If sample files are not found.
    """
    try:
        contract_text = _EN_CONTRACT.read_text(encoding="utf-8")
        policy_text = _POLICY.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise HTTPException(500, {"error_code": "SAMPLE_NOT_FOUND", "message": str(e)})
    
    job_id = str(uuid.uuid4())
    job_store.put(
        job_id,
        contract_filename="saas_msa_en.txt",
        policy_filename="policy_bilingual.csv",
        contract_text=contract_text,
        contract_bytes=b"",
        policy_text=policy_text,
        detected_language="en",
    )
    
    return {"job_id": job_id, "detected_language": "en"}
