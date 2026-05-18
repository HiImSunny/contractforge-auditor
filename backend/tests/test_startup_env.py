"""
Startup integration test: asserts the app exits non-zero when GOOGLE_API_KEY is unset.

Validates: Requirements 10.6
"""
import os
import subprocess
import sys


def test_startup_fails_without_google_api_key():
    """The app must exit with a non-zero status and print 'GOOGLE_API_KEY is required' to stderr
    when GOOGLE_API_KEY is not set in the environment.
    
    Validates: Requirement 10.6
    """
    # Run a subprocess that imports app.config with GOOGLE_API_KEY unset
    env = {k: v for k, v in os.environ.items() if k != "GOOGLE_API_KEY"}
    env.pop("GOOGLE_API_KEY", None)
    
    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, 'backend'); from app import config"],
        capture_output=True,
        text=True,
        env=env,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    
    assert result.returncode != 0, (
        f"Expected non-zero exit when GOOGLE_API_KEY is unset, got {result.returncode}"
    )
    assert "GOOGLE_API_KEY is required" in result.stderr, (
        f"Expected 'GOOGLE_API_KEY is required' in stderr, got: {result.stderr!r}"
    )
