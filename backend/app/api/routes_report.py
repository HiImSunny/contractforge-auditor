"""GET /api/report/{job_id} — return PDF governance report (Req 7.1, 7.3, 8.4)."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.services import job_store
from app.services.pdf_report import render_pdf

router = APIRouter()


@router.get("/report/{job_id}")
async def get_report(job_id: str):
    """Generate and return the PDF governance report for the given job.

    Retrieves the completed GovernanceReport from the job store, generates
    a PDF using WeasyPrint, and returns it as an attachment.

    Returns:
        application/pdf response with Content-Disposition: attachment.

    Raises:
        HTTPException 404: If job_id is not found.
        HTTPException 409: If analysis has not yet completed (no report stored).
    """
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(
            404,
            {"error_code": "JOB_NOT_FOUND", "message": f"Job {job_id} not found"},
        )

    report = job.get("report")
    if not report:
        raise HTTPException(
            409,
            {"error_code": "REPORT_NOT_READY", "message": "Analysis not yet complete for this job"},
        )

    # Generate PDF (Req 7.1, 7.2)
    pdf_bytes = render_pdf(report)

    filename = f"contractforge-report-{job_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
