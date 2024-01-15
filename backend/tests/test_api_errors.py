"""
Test API error handling paths via TestClient with mocked agents.

Feature: contractforge-auditor

Tests the following error paths:
  - 413 FILE_TOO_LARGE (POST /api/upload with oversized file)
  - 415 UNSUPPORTED_MEDIA_TYPE (POST /api/upload with invalid MIME type)
  - 400 UNKNOWN_SCENARIO (POST /api/simulate with invalid scenario_key)
  - 404 JOB_NOT_FOUND (GET /api/audit-trail/{job_id}, GET /api/report/{job_id})
  - 409 REPORT_NOT_READY (GET /api/report/{job_id} before analysis completes)

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.8, 2.9, 5.1, 5.2, 5.3,
           5.4, 5.5, 6.3, 6.5, 7.3, 8.1, 8.2, 8.3, 8.5, 8.6, 8.7, 10.4,
           10.5, 10.6
"""
import io
import uuid
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import job_store


@pytest.fixture(autouse=True)
def clear_job_store():
    """Clear the job store before each test."""
    job_store._STORE.clear()
    yield
    job_store._STORE.clear()


@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)


# ── 413 FILE_TOO_LARGE ───────────────────────────────────────────────────────

class TestUpload413FileTooLarge:
    """Test 413 FILE_TOO_LARGE error on oversized contract or policy."""

    def test_contract_exceeds_15mb(self, client):
        """POST /api/upload with contract > 15 MB returns 413 FILE_TOO_LARGE."""
        # Create a file that exceeds 15 MB
        oversized_contract = io.BytesIO(b"x" * (15 * 1024 * 1024 + 1))
        small_policy = io.BytesIO(b"policy content")

        response = client.post(
            "/api/upload",
            files={
                "contract": ("contract.txt", oversized_contract, "text/plain"),
                "policy": ("policy.txt", small_policy, "text/plain"),
            },
        )

        assert response.status_code == 413
        data = response.json()["detail"]
        assert data["error_code"] == "FILE_TOO_LARGE"
        assert data["max_size_bytes"] == 15 * 1024 * 1024
        assert data["field"] == "contract"

    def test_policy_exceeds_15mb(self, client):
        """POST /api/upload with policy > 15 MB returns 413 FILE_TOO_LARGE."""
        small_contract = io.BytesIO(b"contract content")
        oversized_policy = io.BytesIO(b"y" * (15 * 1024 * 1024 + 1))

        response = client.post(
            "/api/upload",
            files={
                "contract": ("contract.txt", small_contract, "text/plain"),
                "policy": ("policy.txt", oversized_policy, "text/plain"),
            },
        )

        assert response.status_code == 413
        data = response.json()["detail"]
        assert data["error_code"] == "FILE_TOO_LARGE"
        assert data["max_size_bytes"] == 15 * 1024 * 1024
        assert data["field"] == "policy"


# ── 415 UNSUPPORTED_MEDIA_TYPE ───────────────────────────────────────────────

class TestUpload415UnsupportedMediaType:
    """Test 415 UNSUPPORTED_MEDIA_TYPE error on invalid MIME types."""

    def test_contract_unsupported_mime(self, client):
        """POST /api/upload with unsupported contract MIME returns 415."""
        contract = io.BytesIO(b"contract content")
        policy = io.BytesIO(b"policy content")

        response = client.post(
            "/api/upload",
            files={
                "contract": ("contract.docx", contract, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                "policy": ("policy.txt", policy, "text/plain"),
            },
        )

        assert response.status_code == 415
        data = response.json()["detail"]
        assert data["error_code"] == "UNSUPPORTED_MEDIA_TYPE"
        assert data["field"] == "contract"

    def test_policy_unsupported_mime(self, client):
        """POST /api/upload with unsupported policy MIME returns 415."""
        contract = io.BytesIO(b"contract content")
        policy = io.BytesIO(b"policy content")

        response = client.post(
            "/api/upload",
            files={
                "contract": ("contract.txt", contract, "text/plain"),
                "policy": ("policy.xlsx", policy, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            },
        )

        assert response.status_code == 415
        data = response.json()["detail"]
        assert data["error_code"] == "UNSUPPORTED_MEDIA_TYPE"
        assert data["field"] == "policy"

    def test_contract_application_json_unsupported(self, client):
        """POST /api/upload with application/json contract returns 415."""
        contract = io.BytesIO(b'{"key": "value"}')
        policy = io.BytesIO(b"policy content")

        response = client.post(
            "/api/upload",
            files={
                "contract": ("contract.json", contract, "application/json"),
                "policy": ("policy.txt", policy, "text/plain"),
            },
        )

        assert response.status_code == 415
        data = response.json()["detail"]
        assert data["error_code"] == "UNSUPPORTED_MEDIA_TYPE"
        assert data["field"] == "contract"


# ── 400 UNKNOWN_SCENARIO ─────────────────────────────────────────────────────

class TestSimulate400UnknownScenario:
    """Test 400 UNKNOWN_SCENARIO error on invalid scenario_key."""

    def test_unknown_scenario_key(self, client):
        """POST /api/simulate with invalid scenario_key returns 400 UNKNOWN_SCENARIO."""
        job_id = str(uuid.uuid4())
        # Pre-populate the job store with a completed report
        job_store.put(
            job_id,
            report={
                "simulations": [
                    {
                        "scenario_key": "force_majeure",
                        "impact_score": 50,
                        "affected_clause_ids": [],
                        "narrative": "test",
                    }
                ]
            },
        )

        response = client.post(
            "/api/simulate",
            json={"job_id": job_id, "scenario_key": "invalid_scenario"},
        )

        assert response.status_code == 400
        data = response.json()["detail"]
        assert data["error_code"] == "UNKNOWN_SCENARIO"

    def test_scenario_key_typo(self, client):
        """POST /api/simulate with typo in scenario_key returns 400."""
        job_id = str(uuid.uuid4())
        job_store.put(
            job_id,
            report={
                "simulations": [
                    {
                        "scenario_key": "force_majeure",
                        "impact_score": 50,
                        "affected_clause_ids": [],
                        "narrative": "test",
                    }
                ]
            },
        )

        response = client.post(
            "/api/simulate",
            json={"job_id": job_id, "scenario_key": "force_majeur"},  # typo
        )

        assert response.status_code == 400
        data = response.json()["detail"]
        assert data["error_code"] == "UNKNOWN_SCENARIO"

    def test_scenario_key_empty_string(self, client):
        """POST /api/simulate with empty scenario_key returns 400."""
        job_id = str(uuid.uuid4())
        job_store.put(
            job_id,
            report={
                "simulations": [
                    {
                        "scenario_key": "force_majeure",
                        "impact_score": 50,
                        "affected_clause_ids": [],
                        "narrative": "test",
                    }
                ]
            },
        )

        response = client.post(
            "/api/simulate",
            json={"job_id": job_id, "scenario_key": ""},
        )

        assert response.status_code == 400
        data = response.json()["detail"]
        assert data["error_code"] == "UNKNOWN_SCENARIO"


# ── 404 JOB_NOT_FOUND ────────────────────────────────────────────────────────

class TestJobNotFound404:
    """Test 404 JOB_NOT_FOUND error on missing job_id."""

    def test_audit_trail_job_not_found(self, client):
        """GET /api/audit-trail/{job_id} with unknown job_id returns 404."""
        unknown_job_id = str(uuid.uuid4())

        response = client.get(f"/api/audit-trail/{unknown_job_id}")

        assert response.status_code == 404
        data = response.json()["detail"]
        assert data["error_code"] == "JOB_NOT_FOUND"

    def test_report_job_not_found(self, client):
        """GET /api/report/{job_id} with unknown job_id returns 404."""
        unknown_job_id = str(uuid.uuid4())

        response = client.get(f"/api/report/{unknown_job_id}")

        assert response.status_code == 404
        data = response.json()["detail"]
        assert data["error_code"] == "JOB_NOT_FOUND"

    def test_simulate_job_not_found(self, client):
        """POST /api/simulate with unknown job_id returns 404."""
        unknown_job_id = str(uuid.uuid4())

        response = client.post(
            "/api/simulate",
            json={"job_id": unknown_job_id, "scenario_key": "force_majeure"},
        )

        assert response.status_code == 404
        data = response.json()["detail"]
        assert data["error_code"] == "JOB_NOT_FOUND"


# ── 409 REPORT_NOT_READY ─────────────────────────────────────────────────────

class TestReportNotReady409:
    """Test 409 REPORT_NOT_READY error when analysis is incomplete."""

    def test_report_not_ready_no_report_field(self, client):
        """GET /api/report/{job_id} without report field returns 409."""
        job_id = str(uuid.uuid4())
        # Create a job without a report (analysis not yet complete)
        job_store.put(job_id, contract_filename="test.txt", policy_filename="policy.txt")

        response = client.get(f"/api/report/{job_id}")

        assert response.status_code == 409
        data = response.json()["detail"]
        assert data["error_code"] == "REPORT_NOT_READY"

    def test_report_not_ready_empty_report(self, client):
        """GET /api/report/{job_id} with empty report dict returns 409."""
        job_id = str(uuid.uuid4())
        # Create a job with an empty report dict (no report data)
        job_store.put(job_id, report={})

        response = client.get(f"/api/report/{job_id}")

        assert response.status_code == 409
        data = response.json()["detail"]
        assert data["error_code"] == "REPORT_NOT_READY"

    def test_report_not_ready_none_report(self, client):
        """GET /api/report/{job_id} with None report returns 409."""
        job_id = str(uuid.uuid4())
        # Create a job with report=None
        job_store.put(job_id, report=None)

        response = client.get(f"/api/report/{job_id}")

        assert response.status_code == 409
        data = response.json()["detail"]
        assert data["error_code"] == "REPORT_NOT_READY"

    def test_simulate_report_not_ready(self, client):
        """POST /api/simulate without report returns 409."""
        job_id = str(uuid.uuid4())
        # Create a job without a report
        job_store.put(job_id, contract_filename="test.txt")

        response = client.post(
            "/api/simulate",
            json={"job_id": job_id, "scenario_key": "force_majeure"},
        )

        assert response.status_code == 409
        data = response.json()["detail"]
        assert data["error_code"] == "REPORT_NOT_READY"


# ── Integration: Valid paths still work ──────────────────────────────────────

class TestValidPaths:
    """Verify that valid paths still work correctly."""

    def test_upload_valid_files(self, client):
        """POST /api/upload with valid files returns 200."""
        contract = io.BytesIO(b"contract content")
        policy = io.BytesIO(b"policy content")

        response = client.post(
            "/api/upload",
            files={
                "contract": ("contract.txt", contract, "text/plain"),
                "policy": ("policy.txt", policy, "text/plain"),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["contract_filename"] == "contract.txt"
        assert data["policy_filename"] == "policy.txt"
        assert data["detected_language"] == "en"

    def test_audit_trail_valid_job(self, client):
        """GET /api/audit-trail/{job_id} with valid job returns 200."""
        job_id = str(uuid.uuid4())
        job_store.put(job_id, contract_filename="test.txt")

        response = client.get(f"/api/audit-trail/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_simulate_valid_scenario(self, client):
        """POST /api/simulate with valid scenario returns 200."""
        job_id = str(uuid.uuid4())
        job_store.put(
            job_id,
            report={
                "simulations": [
                    {
                        "scenario_key": "force_majeure",
                        "impact_score": 50,
                        "affected_clause_ids": ["C-001"],
                        "narrative": "test narrative",
                    }
                ]
            },
        )

        response = client.post(
            "/api/simulate",
            json={"job_id": job_id, "scenario_key": "force_majeure"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["scenario_key"] == "force_majeure"
        assert data["impact_score"] == 50
