"""Core FEC validation and pre-closing accounting audit engine (PCG / DGFiP)."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

# 18 mandatory columns defined by Article A.47 A-1 of the French LPF (Livre des Procédures Fiscales)
FEC_COLUMNS: tuple[str, ...] = (
    "JournalCode",
    "JournalLib",
    "EcritureNum",
    "EcritureDate",
    "CompteNum",
    "CompteLib",
    "CompAuxNum",
    "CompAuxLib",
    "PieceRef",
    "PieceDate",
    "EcritureLib",
    "Debit",
    "Credit",
    "EcritureLet",
    "DateLet",
    "ValidDate",
    "Montantdevise",
    "Idevise",
)


@dataclass(frozen=True)
class FecRow:
    line_no: int
    journal_code: str
    journal_lib: str
    ecriture_num: str
    ecriture_date: str
    compte_num: str
    compte_lib: str
    comp_aux_num: str
    comp_aux_lib: str
    piece_ref: str
    piece_date: str
    ecriture_lib: str
    debit: Decimal
    credit: Decimal
    ecriture_let: str
    date_let: str
    valid_date: str
    montant_devise: str
    idevise: str


@dataclass(frozen=True)
class AuditFinding:
    code: str
    severity: str  # "PASS" | "WARN" | "ERROR"
    title: str
    details: str


@dataclass
class AuditReport:
    source_name: str
    row_count: int
    total_debit: Decimal
    total_credit: Decimal
    bilan_result: Decimal
    gestion_result: Decimal
    turnover_ht: Decimal
    vat_collected: Decimal
    findings: list[AuditFinding] = field(default_factory=list)
    class_balances: dict[str, tuple[Decimal, Decimal]] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "WARN")


def parse_french_decimal(raw: str) -> Decimal:
    cleaned = raw.strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")
    if not cleaned:
        return Decimal("0.00")
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Montant invalide : {raw!r}") from exc


def _detect_delimiter(header_line: str) -> str:
    if "\t" in header_line:
        return "\t"
    if "|" in header_line:
        return "|"
    return ";"


def parse_fec_lines(lines: Iterable[str]) -> tuple[list[str], list[FecRow]]:
    iterator = iter(lines)
    try:
        first_line = next(iterator).lstrip("\ufeff").rstrip("\r\n")
    except StopIteration:
        return [], []

    delimiter = _detect_delimiter(first_line)
    header = [col.strip() for col in next(csv.reader([first_line], delimiter=delimiter))]
    rows: list[FecRow] = []

    if tuple(header) != FEC_COLUMNS:
        return header, rows

    for idx, row_values in enumerate(csv.reader(iterator, delimiter=delimiter), start=2):
        if not row_values or all(not cell.strip() for cell in row_values):
            continue
        if len(row_values) != 18:
            raise ValueError(f"Ligne {idx} : {len(row_values)} colonnes trouvées au lieu de 18.")
        rows.append(
            FecRow(
                line_no=idx,
                journal_code=row_values[0].strip(),
                journal_lib=row_values[1].strip(),
                ecriture_num=row_values[2].strip(),
                ecriture_date=row_values[3].strip(),
                compte_num=row_values[4].strip(),
                compte_lib=row_values[5].strip(),
                comp_aux_num=row_values[6].strip(),
                comp_aux_lib=row_values[7].strip(),
                piece_ref=row_values[8].strip(),
                piece_date=row_values[9].strip(),
                ecriture_lib=row_values[10].strip(),
                debit=parse_french_decimal(row_values[11]),
                credit=parse_french_decimal(row_values[12]),
                ecriture_let=row_values[13].strip(),
                date_let=row_values[14].strip(),
                valid_date=row_values[15].strip(),
                montant_devise=row_values[16].strip(),
                idevise=row_values[17].strip(),
            )
        )
    return header, rows


def _valid_yyyymmdd(date_str: str) -> bool:
    if len(date_str) != 8 or not date_str.isdigit():
        return False
    try:
        datetime.strptime(date_str, "%Y%m%d")
        return True
    except ValueError:
        return False


def audit_fec_lines(lines: Iterable[str], source_name: str = "memory") -> AuditReport:
    header, rows = parse_fec_lines(lines)
    findings: list[AuditFinding] = []

    # C01: 18 mandatory DGFiP columns
    if tuple(header) == FEC_COLUMNS:
        findings.append(
            AuditFinding(
                code="C01",
                severity="PASS",
                title="Conformité des 18 colonnes DGFiP",
                details="En-tête strictement conforme à l'article A.47 A-1 du LPF.",
            )
        )
    else:
        findings.append(
            AuditFinding(
                code="C01",
                severity="ERROR",
                title="Conformité des 18 colonnes DGFiP",
                details=f"En-tête non conforme ({len(header)} colonnes détectées).",
            )
        )
        return AuditReport(
            source_name=source_name,
            row_count=0,
            total_debit=Decimal("0.00"),
            total_credit=Decimal("0.00"),
            bilan_result=Decimal("0.00"),
            gestion_result=Decimal("0.00"),
            turnover_ht=Decimal("0.00"),
            vat_collected=Decimal("0.00"),
            findings=findings,
        )

    total_debit = sum((r.debit for r in rows), Decimal("0.00"))
    total_credit = sum((r.credit for r in rows), Decimal("0.00"))

    # C02: Global debit/credit balance
    diff_global = total_debit - total_credit
    if diff_global == Decimal("0.00"):
        findings.append(
            AuditFinding(
                code="C02",
                severity="PASS",
                title="Équilibre général Débit / Crédit",
                details=f"Total Débit = Total Crédit = {total_debit:,.2f} €.",
            )
        )
    else:
        findings.append(
            AuditFinding(
                code="C02",
                severity="ERROR",
                title="Équilibre général Débit / Crédit",
                details=f"Déséquilibre global de {diff_global:+,.2f} € (D={total_debit:,.2f}, C={total_credit:,.2f}).",
            )
        )

    # C03: Balance per accounting entry (JournalCode + EcritureNum)
    entry_totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
    for r in rows:
        entry_totals[(r.journal_code, r.ecriture_num)] += r.debit - r.credit
    unbalanced = [f"{j}/{n} ({d:+.2f}€)" for (j, n), d in entry_totals.items() if d != Decimal("0.00")]
    if not unbalanced:
        findings.append(
            AuditFinding(
                code="C03",
                severity="PASS",
                title="Équilibre par pièce comptable",
                details=f"{len(entry_totals)} pièces contrôlées et équilibrées.",
            )
        )
    else:
        findings.append(
            AuditFinding(
                code="C03",
                severity="ERROR",
                title="Équilibre par pièce comptable",
                details="Pièces déséquilibrées : " + ", ".join(unbalanced[:5]),
            )
        )

    # C04: Chronological & date format validation
    date_errors: list[str] = []
    for r in rows:
        if not _valid_yyyymmdd(r.ecriture_date) or not _valid_yyyymmdd(r.valid_date):
            date_errors.append(f"L{r.line_no} ({r.ecriture_num})")
        elif r.valid_date < r.ecriture_date:
            date_errors.append(f"L{r.line_no} ValidDate < EcritureDate ({r.valid_date} < {r.ecriture_date})")
    if not date_errors:
        findings.append(
            AuditFinding(
                code="C04",
                severity="PASS",
                title="Chronologie et format des dates",
                details="Toutes les dates respectent le format YYYYMMDD et ValidDate >= EcritureDate.",
            )
        )
    else:
        findings.append(
            AuditFinding(
                code="C04",
                severity="ERROR",
                title="Chronologie et format des dates",
                details="; ".join(date_errors[:5]),
            )
        )

    # C05: Cash account (530x) must never have a credit balance
    cash_balance = sum(
        (r.debit - r.credit for r in rows if r.compte_num.startswith("53")),
        Decimal("0.00"),
    )
    if cash_balance >= Decimal("0.00"):
        findings.append(
            AuditFinding(
                code="C05",
                severity="PASS",
                title="Contrôle du solde de caisse (53x)",
                details=f"Solde caisse débiteur ou nul ({cash_balance:,.2f} €).",
            )
        )
    else:
        findings.append(
            AuditFinding(
                code="C05",
                severity="ERROR",
                title="Contrôle du solde de caisse (53x)",
                details=f"Anomalie bloquante : caisse créditrice ({cash_balance:,.2f} €).",
            )
        )

    # C06: VAT collected (44571x) vs Turnover (70x) plausibility check
    turnover_ht = sum(
        (r.credit - r.debit for r in rows if r.compte_num.startswith("70")),
        Decimal("0.00"),
    )
    vat_collected = sum(
        (r.credit - r.debit for r in rows if r.compte_num.startswith("44571")),
        Decimal("0.00"),
    )
    if turnover_ht > Decimal("0.00"):
        eff_rate = (vat_collected / turnover_ht * Decimal("100")).quantize(Decimal("0.01"))
        if Decimal("5.00") <= eff_rate <= Decimal("21.00"):
            findings.append(
                AuditFinding(
                    code="C06",
                    severity="PASS",
                    title="Cadrage TVA collectée / Chiffre d'affaires",
                    details=f"CA HT = {turnover_ht:,.2f} €, TVA collectée = {vat_collected:,.2f} € (taux apparent : {eff_rate}%).",
                )
            )
        else:
            findings.append(
                AuditFinding(
                    code="C06",
                    severity="WARN",
                    title="Cadrage TVA collectée / Chiffre d'affaires",
                    details=f"Taux apparent inhabituel ({eff_rate}%) : CA HT = {turnover_ht:,.2f} €, TVA = {vat_collected:,.2f} €.",
                )
            )

    # C07: Balance Sheet (Classes 1-5) vs Income Statement (Classes 6-7) net result
    class_balances: dict[str, tuple[Decimal, Decimal]] = {}
    for cls in ("1", "2", "3", "4", "5", "6", "7"):
        d_sum = sum((r.debit for r in rows if r.compte_num.startswith(cls)), Decimal("0.00"))
        c_sum = sum((r.credit for r in rows if r.compte_num.startswith(cls)), Decimal("0.00"))
        class_balances[cls] = (d_sum, c_sum)

    bilan_result = sum(
        (class_balances[c][0] - class_balances[c][1] for c in ("1", "2", "3", "4", "5")),
        Decimal("0.00"),
    )
    gestion_result = sum(
        (class_balances[c][1] - class_balances[c][0] for c in ("6", "7")),
        Decimal("0.00"),
    )
    if bilan_result == gestion_result:
        findings.append(
            AuditFinding(
                code="C07",
                severity="PASS",
                title="Concordance Bilan (cl. 1–5) / Résultat (cl. 6–7)",
                details=f"Résultat net concordant : {gestion_result:+,.2f} €.",
            )
        )
    else:
        findings.append(
            AuditFinding(
                code="C07",
                severity="ERROR",
                title="Concordance Bilan (cl. 1–5) / Résultat (cl. 6–7)",
                details=f"Écart entre Bilan ({bilan_result:+,.2f} €) et Gestion ({gestion_result:+,.2f} €).",
            )
        )

    # C08: Potential duplicate invoices on Auxiliary Accounts (401x / 411x)
    seen_aux: dict[tuple[str, str, Decimal, Decimal], list[str]] = defaultdict(list)
    for r in rows:
        if r.comp_aux_num and r.journal_code in ("HA", "VT", "AC", "VE"):
            seen_aux[(r.journal_code, r.comp_aux_num, r.debit, r.credit)].append(
                f"{r.ecriture_num} ({r.piece_ref} du {r.ecriture_date})"
            )
    duplicates = [
        f"{aux} ({max(deb, cred):,.2f} €) : {' vs '.join(refs)}"
        for (_, aux, deb, cred), refs in seen_aux.items()
        if len(refs) > 1
    ]
    if not duplicates:
        findings.append(
            AuditFinding(
                code="C08",
                severity="PASS",
                title="Détection de doublons de factures tiers",
                details="Aucun doublon potentiel (même tiers + même montant TTC) détecté sur les journaux HA/VT.",
            )
        )
    else:
        findings.append(
            AuditFinding(
                code="C08",
                severity="WARN",
                title="Détection de doublons de factures tiers",
                details="Doublons potentiels à vérifier : " + " ; ".join(duplicates[:5]),
            )
        )

    return AuditReport(
        source_name=source_name,
        row_count=len(rows),
        total_debit=total_debit,
        total_credit=total_credit,
        bilan_result=bilan_result,
        gestion_result=gestion_result,
        turnover_ht=turnover_ht,
        vat_collected=vat_collected,
        findings=findings,
        class_balances=class_balances,
    )


def audit_fec_file(path: str | Path) -> AuditReport:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as fh:
        return audit_fec_lines(fh, source_name=file_path.name)


def render_markdown_report(report: AuditReport) -> str:
    badge = {"PASS": "PASS", "WARN": "WARN", "ERROR": "ERROR"}
    lines = [
        f"# Rapport de Contrôle FEC & Révision — `{report.source_name}`",
        "",
        "## 1. Synthèse Générale",
        "",
        f"- **Lignes d'écritures analysées** : {report.row_count}",
        f"- **Total Débit** : `{report.total_debit:,.2f} €`",
        f"- **Total Crédit** : `{report.total_credit:,.2f} €`",
        f"- **Chiffre d'affaires HT (cl. 70)** : `{report.turnover_ht:,.2f} €`",
        f"- **TVA collectée (44571)** : `{report.vat_collected:,.2f} €`",
        f"- **Résultat net (Produits − Charges)** : `{report.gestion_result:+,.2f} €`",
        f"- **Statut de l'audit** : **{report.error_count} erreur(s)**, **{report.warning_count} alerte(s)**",
        "",
        "## 2. Résultats des 8 Contrôles",
        "",
        "| Code | Statut | Contrôle | Détail |",
        "|---|---|---|---|",
    ]
    for f in report.findings:
        lines.append(f"| **{f.code}** | `{badge.get(f.severity, f.severity)}` | {f.title} | {f.details} |")

    if report.class_balances:
        lines.extend(
            [
                "",
                "## 3. Synthèse par Classe du Plan Comptable Général (PCG)",
                "",
                "| Classe PCG | Total Débit (€) | Total Crédit (€) | Solde (D − C) (€) |",
                "|---|---:|---:|---:|",
            ]
        )
        labels = {
            "1": "Classe 1 — Capitaux",
            "2": "Classe 2 — Immobilisations",
            "3": "Classe 3 — Stocks",
            "4": "Classe 4 — Tiers",
            "5": "Classe 5 — Financiers",
            "6": "Classe 6 — Charges",
            "7": "Classe 7 — Produits",
        }
        for cls, (deb, cred) in sorted(report.class_balances.items()):
            solde = deb - cred
            lines.append(f"| {labels.get(cls, cls)} | {deb:,.2f} | {cred:,.2f} | {solde:+,.2f} |")

    lines.append("")
    return "\n".join(lines)

