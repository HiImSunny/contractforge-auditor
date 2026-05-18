"""
Deterministic risk scoring for ContractForge Auditor.

Implements the cap-then-weighted-mean-then-round algorithm described in
design §Risk Scoring Algorithm (Req 4.1, 4.2, 4.4, 4.5).

Worked example (ten violations):
  Violations:
    legal:        high(30) + medium(15)          = 45
    financial:    critical(50)+critical(50)+high(30) = 130 → capped 100
    operational:  medium(15)                     = 15
    compliance:   low(5)                         = 5
    data_privacy: critical(50)+high(30)+high(30) = 110 → capped 100

  Weighted overall:
    0.25*45 + 0.20*100 + 0.15*15 + 0.25*5 + 0.15*100
    = 11.25 + 20.00 + 2.25 + 1.25 + 15.00
    = 49.75  →  round(49.75) = 50

  Result: per_category = {legal:45, financial:100, operational:15,
                          compliance:5, data_privacy:100}, overall = 50
"""

# ---------------------------------------------------------------------------
# Constants (Req 4.1, 4.2)
# ---------------------------------------------------------------------------

SEVERITY_WEIGHTS: dict[str, int] = {
    "low": 5,
    "medium": 15,
    "high": 30,
    "critical": 50,
}

CATEGORY_WEIGHTS: dict[str, float] = {
    "legal": 0.25,
    "financial": 0.20,
    "operational": 0.15,
    "compliance": 0.25,
    "data_privacy": 0.15,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score(violations: list[dict]) -> tuple[dict[str, int], int]:
    """Compute per-category and overall risk scores from a list of violations.

    Each violation dict must contain at least:
      - ``risk_category``: one of the keys in ``CATEGORY_WEIGHTS``
      - ``severity``:      one of the keys in ``SEVERITY_WEIGHTS``

    Algorithm (Req 4.1, 4.2):
      1. For each risk category, sum the severity weights of all violations
         in that category.
      2. Cap each category sum at 100.
      3. Compute the weighted mean:
         ``sum(per_category[c] * CATEGORY_WEIGHTS[c] for c in CATEGORY_WEIGHTS)``
      4. Return ``(per_category_dict, round(weighted_mean))``.

    The returned ``per_category_dict`` always contains all five keys:
    ``legal``, ``financial``, ``operational``, ``compliance``,
    ``data_privacy`` (Req 4.5).

    Running this function twice on the same violation list always produces
    identical results (Req 4.4).

    Args:
        violations: List of violation dicts, each with ``risk_category``
                    and ``severity`` keys.

    Returns:
        A tuple ``(per_category, overall)`` where ``per_category`` is a
        dict mapping each risk-category name to an integer score in
        ``[0, 100]``, and ``overall`` is the rounded weighted mean in
        ``[0, 100]``.
    """
    # Initialise all categories to zero so the dict always has all five keys.
    per_category: dict[str, int] = {c: 0 for c in CATEGORY_WEIGHTS}

    for v in violations:
        category = v["risk_category"]
        severity = v["severity"]
        if category in per_category and severity in SEVERITY_WEIGHTS:
            per_category[category] += SEVERITY_WEIGHTS[severity]

    # Cap each category at 100.
    for c in per_category:
        per_category[c] = min(100, per_category[c])

    # Weighted mean, then round (Python's built-in round uses banker's
    # rounding for .5 ties, which matches the spec's "use Python round()").
    weighted_mean: float = sum(
        per_category[c] * CATEGORY_WEIGHTS[c] for c in CATEGORY_WEIGHTS
    )
    overall: int = round(weighted_mean)

    return per_category, overall


def band(score: int) -> str:
    """Map an integer score in ``[0, 100]`` to a colour band string.

    Used by the PDF report generator and the frontend heatmap (Req 3.2).

    Bands:
      - ``"green"``  for 0–33
      - ``"amber"``  for 34–66
      - ``"red"``    for 67–100

    Args:
        score: An integer in ``[0, 100]``.

    Returns:
        One of ``"green"``, ``"amber"``, or ``"red"``.
    """
    if score <= 33:
        return "green"
    if score <= 66:
        return "amber"
    return "red"
