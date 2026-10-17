"""Unit tests for FEC Closing Auditor (DGFiP compliance & closing controls)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import unittest

from fec_auditor import FEC_COLUMNS, audit_fec_file, audit_fec_lines

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_fec_2026.tsv"


class TestFecAuditor(unittest.TestCase):
    def test_sample_fec_passes_all_controls(self) -> None:
        report = audit_fec_file(SAMPLE_PATH)
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.warning_count, 0)
        self.assertEqual(report.total_debit, Decimal("107150.00"))
        self.assertEqual(report.total_credit, Decimal("107150.00"))
        self.assertEqual(report.turnover_ht, Decimal("20000.00"))
        self.assertEqual(report.vat_collected, Decimal("4000.00"))
        self.assertEqual(report.gestion_result, Decimal("15750.00"))
        self.assertEqual(report.bilan_result, Decimal("15750.00"))

    def test_invalid_header_triggers_c01_error(self) -> None:
        bad_lines = ["JournalCode\tCompteNum\tDebit\tCredit\n"]
        report = audit_fec_lines(bad_lines, source_name="bad_header.tsv")
        self.assertEqual(report.error_count, 1)
        self.assertEqual(report.findings[0].code, "C01")
        self.assertEqual(report.findings[0].severity, "ERROR")

    def test_credit_cash_account_triggers_c05_error(self) -> None:
        header = "\t".join(FEC_COLUMNS)
        r1 = "\t".join(
            [
                "CA", "Caisse", "CA01", "20260110", "530000", "Caisse",
                "", "", "PC-01", "20260110", "Retrait espèces excessif",
                "0,00", "250,00", "", "", "20260115", "0,00", "EUR",
            ]
        )
        r2 = "\t".join(
            [
                "CA", "Caisse", "CA01", "20260110", "606400", "Fournitures administratives",
                "", "", "PC-01", "20260110", "Retrait espèces excessif",
                "250,00", "0,00", "", "", "20260115", "0,00", "EUR",
            ]
        )
        report = audit_fec_lines([header, r1, r2], source_name="cash_error.tsv")
        c05 = next(f for f in report.findings if f.code == "C05")
        self.assertEqual(c05.severity, "ERROR")

    def test_duplicate_supplier_invoice_triggers_c08_warning(self) -> None:
        header = "\t".join(FEC_COLUMNS)
        rows = [
            header,
            "\t".join([
                "HA", "Achats", "HA01", "20260201", "606100", "Achats",
                "", "", "F-99", "20260201", "Facture fournisseur",
                "1000,00", "0,00", "", "", "20260210", "0,00", "EUR",
            ]),
            "\t".join([
                "HA", "Achats", "HA01", "20260201", "401000", "Fournisseurs",
                "FRN01", "ACME SARL", "F-99", "20260201", "Facture fournisseur",
                "0,00", "1000,00", "", "", "20260210", "0,00", "EUR",
            ]),
            "\t".join([
                "HA", "Achats", "HA02", "20260203", "606100", "Achats",
                "", "", "F-99-BIS", "20260203", "Facture fournisseur doublon",
                "1000,00", "0,00", "", "", "20260210", "0,00", "EUR",
            ]),
            "\t".join([
                "HA", "Achats", "HA02", "20260203", "401000", "Fournisseurs",
                "FRN01", "ACME SARL", "F-99-BIS", "20260203", "Facture fournisseur doublon",
                "0,00", "1000,00", "", "", "20260210", "0,00", "EUR",
            ]),
        ]
        report = audit_fec_lines(rows, source_name="dup.tsv")
        c08 = next(f for f in report.findings if f.code == "C08")
        self.assertEqual(c08.severity, "WARN")


if __name__ == "__main__":
    unittest.main()
