"""CLI entry point: python3 -m fec_auditor <path_to_fec.tsv> [--output report.md]."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .auditor import audit_fec_file, render_markdown_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fec_auditor",
        description="Contrôle automatisé du FEC (norme DGFiP) et rapport de révision comptable.",
    )
    parser.add_argument("fec_file", type=Path, help="Chemin du fichier FEC (.tsv, .txt, .csv)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Chemin du rapport Markdown généré (optionnel)",
    )
    args = parser.parse_args(argv)

    report = audit_fec_file(args.fec_file)
    md = render_markdown_report(report)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(md, encoding="utf-8")
        print(f"Rapport enregistré dans : {args.output}")
    else:
        print(md)

    return 1 if report.error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
