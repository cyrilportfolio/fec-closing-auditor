"""Unit tests for FEC Closing Auditor (10 DGFiP compliance & closing controls)."""

from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
import unittest

from fec_auditor import (
    FEC_COLUMNS,
    audit_fec_file,
    audit_fec_lines,
    render_json_report,
    render_markdown_report,
)

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_fec_2026.tsv"
HEADER = "\t".join(FEC_COLUMNS)


def _make_row(
    journal_code: str = "OD",
    journal_lib: str = "Opérations diverses",
    ecriture_num: str = "OD01",
    ecriture_date: str = "20260115",
    compte_num: str = "606100",
    compte_lib: str = "Fournitures",
    comp_aux_num: str = "",
    comp_aux_lib: str = "",
    piece_ref: str = "PC-01",
    piece_date: str = "20260115",
    ecriture_lib: str = "Test écriture",
    debit: str = "100,00",
    credit: str = "0,00",
    ecriture_let: str = "",
    date_let: str = "",
    valid_date: str = "20260131",
    montant_devise: str = "0,00",
    idevise: str = "EUR",
) -> str:
    return "\t".join(
        [
            journal_code,
            journal_lib,
            ecriture_num,
            ecriture_date,
            compte_num,
            compte_lib,
            comp_aux_num,
            comp_aux_lib,
            piece_ref,
            piece_date,
            ecriture_lib,
            debit,
            credit,
            ecriture_let,
            date_let,
            valid_date,
            montant_devise,
            idevise,
        ]
    )


class TestFecAuditor(unittest.TestCase):
    def test_sample_fec_passes_all_10_controls(self) -> None:
        report = audit_fec_file(SAMPLE_PATH)
        self.assertEqual(len(report.findings), 10)
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.warning_count, 0)
        self.assertEqual(report.total_debit, Decimal("107150.00"))
        self.assertEqual(report.total_credit, Decimal("107150.00"))
        self.assertEqual(report.turnover_ht, Decimal("20000.00"))
        self.assertEqual(report.vat_collected, Decimal("4000.00"))
        self.assertEqual(report.vat_deductible, Decimal("700.00"))
        self.assertEqual(report.gestion_result, Decimal("15750.00"))
        self.assertEqual(report.bilan_result, Decimal("15750.00"))
        self.assertEqual(len(report.aux_balances), 4)

    def test_invalid_header_triggers_c01_error(self) -> None:
        report = audit_fec_lines(["JournalCode\tCompteNum\tDebit\tCredit\n"])
        self.assertEqual(report.error_count, 1)
        self.assertEqual(report.findings[0].code, "C01")
        self.assertEqual(report.findings[0].severity, "ERROR")

    def test_empty_fec_with_valid_header_triggers_c01_error(self) -> None:
        report = audit_fec_lines([HEADER])
        c01 = next(f for f in report.findings if f.code == "C01")
        self.assertEqual(c01.severity, "ERROR")

    def test_missing_mandatory_field_triggers_c01_error(self) -> None:
        rows = [
            HEADER,
            _make_row(piece_ref="", debit="100,00", credit="0,00"),
            _make_row(compte_num="512100", debit="0,00", credit="100,00"),
        ]
        report = audit_fec_lines(rows)
        c01 = next(f for f in report.findings if f.code == "C01")
        self.assertEqual(c01.severity, "ERROR")
        self.assertIn("PieceRef", c01.details)

    def test_unbalanced_entry_triggers_c02_and_c03_error(self) -> None:
        rows = [
            HEADER,
            _make_row(ecriture_num="OD01", debit="100,00", credit="0,00"),
            _make_row(ecriture_num="OD01", compte_num="512100", debit="0,00", credit="90,00"),
        ]
        report = audit_fec_lines(rows)
        c02 = next(f for f in report.findings if f.code == "C02")
        c03 = next(f for f in report.findings if f.code == "C03")
        self.assertEqual(c02.severity, "ERROR")
        self.assertEqual(c03.severity, "ERROR")

    def test_invalid_piece_date_or_valid_date_triggers_c04_error(self) -> None:
        rows = [
            HEADER,
            _make_row(ecriture_date="20260120", valid_date="20260110", debit="100,00", credit="0,00"),
            _make_row(ecriture_date="20260120", valid_date="20260125", compte_num="512100", debit="0,00", credit="100,00"),
        ]
        report = audit_fec_lines(rows)
        c04 = next(f for f in report.findings if f.code == "C04")
        self.assertEqual(c04.severity, "ERROR")

    def test_credit_cash_account_triggers_c05_error(self) -> None:
        rows = [
            HEADER,
            _make_row(journal_code="CA", compte_num="530000", debit="0,00", credit="250,00"),
            _make_row(journal_code="CA", compte_num="606400", debit="250,00", credit="0,00"),
        ]
        report = audit_fec_lines(rows)
        c05 = next(f for f in report.findings if f.code == "C05")
        self.assertEqual(c05.severity, "ERROR")

    def test_duplicate_supplier_invoice_triggers_c08_warning(self) -> None:
        rows = [
            HEADER,
            _make_row(journal_code="HA", ecriture_num="HA01", compte_num="606100", debit="1000,00", credit="0,00"),
            _make_row(
                journal_code="HA",
                ecriture_num="HA01",
                compte_num="401000",
                comp_aux_num="FRN01",
                comp_aux_lib="ACME SARL",
                debit="0,00",
                credit="1000,00",
            ),
            _make_row(journal_code="HA", ecriture_num="HA02", compte_num="606100", debit="1000,00", credit="0,00"),
            _make_row(
                journal_code="HA",
                ecriture_num="HA02",
                compte_num="401000",
                comp_aux_num="FRN01",
                comp_aux_lib="ACME SARL",
                debit="0,00",
                credit="1000,00",
            ),
        ]
        report = audit_fec_lines(rows)
        c08 = next(f for f in report.findings if f.code == "C08")
        self.assertEqual(c08.severity, "WARN")

    def test_unbalanced_lettrage_triggers_c09_warning(self) -> None:
        rows = [
            HEADER,
            _make_row(
                journal_code="VT",
                ecriture_num="VT01",
                compte_num="411000",
                comp_aux_num="CLI01",
                comp_aux_lib="CLIENT A",
                debit="1200,00",
                credit="0,00",
                ecriture_let="AA",
                date_let="20260201",
            ),
            _make_row(
                journal_code="VT",
                ecriture_num="VT01",
                compte_num="706000",
                debit="0,00",
                credit="1200,00",
            ),
            _make_row(
                journal_code="BQ",
                ecriture_num="BQ01",
                compte_num="512100",
                debit="1000,00",
                credit="0,00",
            ),
            _make_row(
                journal_code="BQ",
                ecriture_num="BQ01",
                compte_num="411000",
                comp_aux_num="CLI01",
                comp_aux_lib="CLIENT A",
                debit="0,00",
                credit="1000,00",
                ecriture_let="AA",
                date_let="20260201",
            ),
        ]
        report = audit_fec_lines(rows)
        c09 = next(f for f in report.findings if f.code == "C09")
        self.assertEqual(c09.severity, "WARN")

    def test_inverted_supplier_balance_triggers_c10_warning_and_exports_work(self) -> None:
        rows = [
            HEADER,
            _make_row(
                journal_code="BQ",
                ecriture_num="BQ01",
                compte_num="401000",
                comp_aux_num="FRN09",
                comp_aux_lib="FOURNISSEUR DEBITEUR",
                debit="500,00",
                credit="0,00",
            ),
            _make_row(
                journal_code="BQ",
                ecriture_num="BQ01",
                compte_num="512100",
                debit="0,00",
                credit="500,00",
            ),
        ]
        report = audit_fec_lines(rows)
        c10 = next(f for f in report.findings if f.code == "C10")
        self.assertEqual(c10.severity, "WARN")
        md = render_markdown_report(report)
        self.assertIn("Balance Auxiliaire des Tiers", md)
        payload = json.loads(render_json_report(report))
        self.assertEqual(payload["warning_count"], 1)


if __name__ == "__main__":
    unittest.main()
