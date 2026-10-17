"""FEC Closing Auditor — Contrôle automatisé du FEC (DGFiP) et révision comptable."""

from .auditor import (
    FEC_COLUMNS,
    AuditFinding,
    AuditReport,
    audit_fec_file,
    audit_fec_lines,
    parse_fec_lines,
    render_markdown_report,
)

__all__ = [
    "FEC_COLUMNS",
    "AuditFinding",
    "AuditReport",
    "audit_fec_file",
    "audit_fec_lines",
    "parse_fec_lines",
    "render_markdown_report",
]
