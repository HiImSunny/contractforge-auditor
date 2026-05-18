"""
backend/app/services/dpi_inspector.py
──────────────────────────────────────
Lite DPI (Deep Prompt Inspection) fallback for ContractForge Auditor.

When Lobster Trap (https://github.com/veeainc/lobstertrap) is not available
(e.g. production on Render where running a Go binary sidecar is not feasible),
this module provides the same inspection logic using Python regex patterns.

Output format mirrors the ``_lobstertrap`` metadata field returned by the
Lobster Trap binary so the rest of the pipeline (gemini_client.py) can treat
both paths identically.

Security layers in ContractForge Auditor:
  Layer 1 — Lobster Trap binary (local/Docker, Go, sub-ms regex DPI)
  Layer 2 — This module (production fallback, Python regex DPI, same patterns)
  Layer 3 — GUARDRAIL prefix on every agent prompt (application-level)
  Layer 4 — Pydantic v2 schema validation + repair retry on every response
  Layer 5 — PII redaction filter on all log output (redaction.py)
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Literal

# ── Verdict type ──────────────────────────────────────────────────────────────

Verdict = Literal["ALLOW", "DENY", "QUARANTINE", "LOG"]

# ── Compiled regex patterns (mirrors Lobster Trap DPI metadata fields) ────────

_INJECTION_PATTERNS = re.compile(
    r"(?i)("
    r"ignore\s+(previous|prior|above|all)\s+instructions"
    r"|you\s+are\s+now\s+"
    r"|new\s+(role|persona|system|instruction)"
    r"|disregard\s+(your|the)\s+(rules|guidelines|instructions)"
    r"|forget\s+(everything|all)"
    r"|act\s+as\s+(if|a|an)\s+"
    r"|\[SYSTEM\]|<system>|</system>"
    r"|===\s*(END\s+)?GUARDRAIL"
    r"|override\s+(system|prompt|instruction)"
    r")"
)

_ROLE_IMPERSONATION = re.compile(
    r"(?i)("
    r"you\s+are\s+(now\s+)?(a|an|the)\s+(admin|root|superuser|god|unrestricted)"
    r"|pretend\s+(you\s+are|to\s+be)"
    r"|roleplay\s+as"
    r"|from\s+now\s+on\s+you\s+(are|will\s+be)"
    r")"
)

_EXFILTRATION_PATTERNS = re.compile(
    r"(?i)("
    r"send\s+(this|the|all|data|content|output)\s+to"
    r"|post\s+(to|this\s+to|data\s+to)"
    r"|curl\s+https?://"
    r"|wget\s+https?://"
    r"|upload\s+(to|this\s+to)"
    r"|exfiltrate"
    r"|http[s]?://(?!generativelanguage\.googleapis\.com)[^\s]+"
    r")"
)

_CREDENTIAL_PATTERNS = re.compile(
    r"("
    r"AIza[A-Za-z0-9\-_]{35}"           # Google API key
    r"|sk-[A-Za-z0-9]{32,}"             # OpenAI key
    r"|Bearer\s+[A-Za-z0-9\-._~+/]+=*"  # Bearer token
    r"|GOOGLE_API_KEY\s*=\s*\S+"         # env var with value
    r"|password\s*[:=]\s*\S{8,}"        # password assignment
    r"|secret\s*[:=]\s*\S{8,}"          # secret assignment
    r")"
)

_SYSTEM_COMMANDS = re.compile(
    r"(?i)("
    r"rm\s+-[rf]"
    r"|del\s+/[fqs]"
    r"|format\s+[a-z]:"
    r"|subprocess\.(run|call|Popen)"
    r"|os\.system\s*\("
    r"|exec\s*\("
    r"|eval\s*\("
    r"|__import__\s*\("
    r"|import\s+os\b"
    r"|import\s+subprocess\b"
    r")"
)

_SENSITIVE_PATHS = re.compile(
    r"("
    r"/etc/(?:passwd|shadow|sudoers|hosts)"
    r"|/root/\."
    r"|\.ssh/"
    r"|\.env\b"
    r"|/proc/self"
    r"|C:\\Windows\\System32"
    r")"
)

_OBFUSCATION_PATTERNS = re.compile(
    r"("
    r"base64\.(b64decode|decode)"
    r"|\\x[0-9a-fA-F]{2}"              # hex escape sequences
    r"|\\u[0-9a-fA-F]{4}"              # unicode escapes
    r"|chr\(\d+\)"                      # chr() calls
    r"|rot13"
    r"|atob\s*\("
    r")"
)

_PII_PATTERNS = re.compile(
    r"("
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"  # email
    r"|\b\d{3}[\s\-.]?\d{3}[\s\-.]?\d{4}\b"               # phone
    r"|\b[A-Z]{1,2}\d{6,9}\b"                              # gov ID
    r"|\b\d{3}-\d{2}-\d{4}\b"                              # SSN
    r")"
)

# ── Risk signal weights (mirrors Lobster Trap composite risk_score) ───────────

_SIGNAL_WEIGHTS: dict[str, float] = {
    "contains_injection_patterns": 0.40,
    "contains_role_impersonation": 0.30,
    "contains_exfiltration": 0.35,
    "contains_credentials": 0.35,
    "contains_system_commands": 0.25,
    "contains_sensitive_paths": 0.20,
    "contains_obfuscation": 0.20,
    "contains_pii": 0.10,
}


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class DPIResult:
    """Mirrors the ``_lobstertrap`` metadata field from the Lobster Trap binary."""

    verdict: Verdict
    risk_score: float                          # 0.0–1.0
    deny_message: str = ""
    matched_rule: str = ""
    latency_ms: int = 0

    # Detected signals
    contains_injection_patterns: bool = False
    contains_role_impersonation: bool = False
    contains_exfiltration: bool = False
    contains_credentials: bool = False
    contains_system_commands: bool = False
    contains_sensitive_paths: bool = False
    contains_obfuscation: bool = False
    contains_pii: bool = False

    # Source
    inspector: str = "lite-dpi-python"        # "lobstertrap-binary" when using real LT

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "risk_score": self.risk_score,
            "deny_message": self.deny_message,
            "matched_rule": self.matched_rule,
            "latency_ms": self.latency_ms,
            "inspector": self.inspector,
            "ingress": {
                "detected": {
                    "contains_injection_patterns": self.contains_injection_patterns,
                    "contains_role_impersonation": self.contains_role_impersonation,
                    "contains_exfiltration": self.contains_exfiltration,
                    "contains_credentials": self.contains_credentials,
                    "contains_system_commands": self.contains_system_commands,
                    "contains_sensitive_paths": self.contains_sensitive_paths,
                    "contains_obfuscation": self.contains_obfuscation,
                    "contains_pii": self.contains_pii,
                    "risk_score": self.risk_score,
                },
                "action": self.verdict,
                "deny_message": self.deny_message,
                "matched_rule": self.matched_rule,
            },
        }


# ── Policy rules (mirrors configs/lobstertrap_policy.yaml) ───────────────────

@dataclass
class _Rule:
    name: str
    signal: str
    action: Verdict
    deny_message: str
    risk_threshold: float = 0.0  # additional risk_score threshold (AND logic)


_INGRESS_RULES: list[_Rule] = [
    _Rule(
        name="block_prompt_injection",
        signal="contains_injection_patterns",
        action="DENY",
        deny_message="[CONTRACTFORGE] Blocked: prompt injection detected in contract content.",
    ),
    _Rule(
        name="block_role_impersonation",
        signal="contains_role_impersonation",
        action="DENY",
        deny_message="[CONTRACTFORGE] Blocked: role impersonation attempt detected.",
    ),
    _Rule(
        name="block_data_exfiltration",
        signal="contains_exfiltration",
        action="DENY",
        deny_message="[CONTRACTFORGE] Blocked: data exfiltration pattern detected.",
    ),
    _Rule(
        name="block_credentials_in_prompt",
        signal="contains_credentials",
        action="DENY",
        deny_message="[CONTRACTFORGE] Blocked: credentials detected in prompt.",
    ),
    _Rule(
        name="block_system_commands",
        signal="contains_system_commands",
        action="DENY",
        deny_message="[CONTRACTFORGE] Blocked: dangerous system command detected.",
        risk_threshold=0.3,
    ),
    _Rule(
        name="block_sensitive_paths",
        signal="contains_sensitive_paths",
        action="DENY",
        deny_message="[CONTRACTFORGE] Blocked: sensitive path access denied.",
    ),
    _Rule(
        name="block_obfuscation",
        signal="contains_obfuscation",
        action="DENY",
        deny_message="[CONTRACTFORGE] Blocked: obfuscation/evasion technique detected.",
    ),
]


# ── Public API ────────────────────────────────────────────────────────────────

def inspect(prompt: str) -> DPIResult:
    """Run DPI on *prompt* and return a :class:`DPIResult`.

    This is the Python fallback used when Lobster Trap binary is not available.
    Uses the same regex patterns and policy rules as ``configs/lobstertrap_policy.yaml``.

    Parameters
    ----------
    prompt:
        The full prompt string to inspect (including GUARDRAIL prefix).

    Returns
    -------
    DPIResult
        Verdict is ALLOW, DENY, or QUARANTINE.
        ``risk_score`` is a float in [0.0, 1.0].
    """
    t0 = time.monotonic()

    # ── Detect signals ────────────────────────────────────────────────────
    signals: dict[str, bool] = {
        "contains_injection_patterns": bool(_INJECTION_PATTERNS.search(prompt)),
        "contains_role_impersonation": bool(_ROLE_IMPERSONATION.search(prompt)),
        "contains_exfiltration": bool(_EXFILTRATION_PATTERNS.search(prompt)),
        "contains_credentials": bool(_CREDENTIAL_PATTERNS.search(prompt)),
        "contains_system_commands": bool(_SYSTEM_COMMANDS.search(prompt)),
        "contains_sensitive_paths": bool(_SENSITIVE_PATHS.search(prompt)),
        "contains_obfuscation": bool(_OBFUSCATION_PATTERNS.search(prompt)),
        "contains_pii": bool(_PII_PATTERNS.search(prompt)),
    }

    # ── Compute composite risk score ──────────────────────────────────────
    risk_score = min(
        1.0,
        sum(_SIGNAL_WEIGHTS[k] for k, v in signals.items() if v),
    )

    # ── Evaluate rules (first-match-wins) ─────────────────────────────────
    verdict: Verdict = "ALLOW"
    deny_message = ""
    matched_rule = ""

    for rule in _INGRESS_RULES:
        if not signals.get(rule.signal, False):
            continue
        if rule.risk_threshold > 0 and risk_score < rule.risk_threshold:
            continue
        verdict = rule.action
        deny_message = rule.deny_message
        matched_rule = rule.name
        break

    # High composite risk → QUARANTINE even if no single rule matched
    if verdict == "ALLOW" and risk_score >= 0.75:
        verdict = "QUARANTINE"
        deny_message = "[CONTRACTFORGE] Quarantined: composite risk score too high."
        matched_rule = "quarantine_high_risk"

    latency_ms = int((time.monotonic() - t0) * 1000)

    return DPIResult(
        verdict=verdict,
        risk_score=risk_score,
        deny_message=deny_message,
        matched_rule=matched_rule,
        latency_ms=latency_ms,
        **signals,  # type: ignore[arg-type]
    )
