"""PDF report generation using matplotlib + Jinja2 + WeasyPrint (Req 7.1, 7.2).

Req 7.1 — The system shall generate a downloadable PDF governance report
          containing all eight sections defined in design §PDF Report Layout.
Req 7.2 — The PDF shall embed a server-side matplotlib semicircular gauge
          image keyed off the integer ``risk_score`` field of the
          ``GovernanceReport``.

Public API
----------
render_pdf(report: dict) -> bytes
    Accepts a ``GovernanceReport`` serialised as a plain Python dict (e.g.
    the output of ``GovernanceReport.model_dump()``) and returns the
    rendered PDF as raw bytes suitable for streaming in an HTTP response.
"""

import base64
import io
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Gauge generation (Req 7.2)
# ---------------------------------------------------------------------------


def _generate_gauge_png(score: int) -> str:
    """Generate a semicircular gauge PNG and return as a base64 string.

    The gauge arc runs from π (left) to 0 (right) on a polar axis.
    Colour bands mirror the ``band()`` function in ``risk_scoring.py``:

    * 0–33  → green  (#22c55e)
    * 34–66 → amber  (#f59e0b)
    * 67–100 → red   (#ef4444)

    Args:
        score: Integer risk score in [0, 100].

    Returns:
        Base64-encoded PNG string (no ``data:`` prefix — the template adds
        that).
    """
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend; must be set before pyplot import
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(4, 2.5), subplot_kw={"projection": "polar"})

    # Background arc (full semicircle, light grey)
    theta_bg = np.linspace(np.pi, 0, 100)
    ax.plot(theta_bg, [1] * 100, color="#e5e7eb", linewidth=20, solid_capstyle="round")

    # Foreground arc (score fraction of semicircle)
    theta_score = np.linspace(np.pi, np.pi - (score / 100) * np.pi, 100)
    if score <= 33:
        arc_color = "#22c55e"   # green
    elif score <= 66:
        arc_color = "#f59e0b"   # amber
    else:
        arc_color = "#ef4444"   # red

    ax.plot(theta_score, [1] * 100, color=arc_color, linewidth=20, solid_capstyle="round")

    # Score text in the centre of the semicircle
    ax.text(0, 0, str(score), ha="center", va="center",
            fontsize=32, fontweight="bold", color="#111827")
    ax.text(0, -0.35, "/ 100", ha="center", va="center",
            fontsize=12, color="#6b7280")

    # Tidy up the polar axes
    ax.set_ylim(0, 1.3)
    ax.set_xlim(0, np.pi)
    ax.axis("off")
    fig.patch.set_alpha(0)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", transparent=True, dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ---------------------------------------------------------------------------
# PDF rendering (Req 7.1)
# ---------------------------------------------------------------------------


def render_pdf(report: dict) -> bytes:
    """Render a ``GovernanceReport`` dict to PDF bytes using WeasyPrint.

    Steps:
    1. Generate a semicircular gauge PNG from ``report["risk_score"]``
       (Req 7.2).
    2. Load ``backend/app/templates/report.html`` via Jinja2's
       ``FileSystemLoader``.
    3. Render the template with the report dict, the base64 gauge PNG, and
       the current UTC timestamp.
    4. Convert the rendered HTML to PDF bytes with WeasyPrint (Req 7.1).

    Args:
        report: ``GovernanceReport`` serialised as a plain Python dict.
                Typically produced by ``GovernanceReport.model_dump()``.

    Returns:
        Raw PDF bytes.

    Raises:
        jinja2.TemplateNotFound: If ``report.html`` is missing from the
            templates directory.
        weasyprint.html.HTMLParseError: If the rendered HTML is malformed.
    """
    from jinja2 import Environment, FileSystemLoader
    from weasyprint import HTML

    # Gauge PNG (base64, no data-URI prefix — the template adds it)
    gauge_png_b64 = _generate_gauge_png(report.get("risk_score", 0))

    # Locate the templates directory relative to this file:
    #   backend/app/services/pdf_report.py  →  backend/app/templates/
    templates_dir = Path(__file__).parent.parent / "templates"

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=True,  # XSS-safe rendering of user-supplied contract text
    )
    template = env.get_template("report.html")

    html_content = template.render(
        report=report,
        gauge_png_b64=gauge_png_b64,
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    )

    # WeasyPrint converts the HTML+CSS string to PDF bytes.
    # base_url is set to the templates directory so that any relative
    # resource references (fonts, etc.) resolve correctly, even though the
    # template is designed to be fully self-contained.
    pdf_bytes: bytes = HTML(
        string=html_content,
        base_url=str(templates_dir),
    ).write_pdf()

    return pdf_bytes
