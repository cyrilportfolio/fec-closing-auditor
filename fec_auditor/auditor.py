"""Core FEC validation and pre-closing accounting audit engine (PCG / DGFiP)."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any, Iterable

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

MANDATORY_ROW_FIELDS: tuple[tuple[str, str], ...] = (
    ("journal_code", "JournalCode"),
    ("journal_lib", "JournalLib"),
    ("ecriture_num", "EcritureNum"),
    ("ecriture_date", "EcritureDate"),
    ("compte_num", "CompteNum"),
    ("compte_lib", "CompteLib"),
    ("piece_ref", "PieceRef"),
    ("piece_date", "PieceDate"),
    ("ecriture_lib", "EcritureLib"),
    ("valid_date", "ValidDate"),
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


@dataclass(frozen=True)
class AuxAccountSummary:
    comp_aux_num: str
    comp_aux_lib: str
    compte_num: str
    debit: Decimal
    credit: Decimal
    solde: Decimal


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
    vat_deductible: Decimal
    findings: list[AuditFinding] = field(default_factory=list)
    class_balances: dict[str, tuple[Decimal, Decimal]] = field(default_factory=dict)
    aux_balances: list[AuxAccountSummary] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "WARN")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "row_count": self.row_count,
            "total_debit": str(self.total_debit),
            "total_credit": str(self.total_credit),
            "bilan_result": str(self.bilan_result),
            "gestion_result": str(self.gestion_result),
            "turnover_ht": str(self.turnover_ht),
            "vat_collected": str(self.vat_collected),
            "vat_deductible": str(self.vat_deductible),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "findings": [asdict(f) for f in self.findings],
            "class_balances": {
                k: {"debit": str(v[0]), "credit": str(v[1]), "solde": str(v[0] - v[1])}
                for k, v in self.class_balances.items()
            },
            "aux_balances": [
                {
                    "comp_aux_num": a.comp_aux_num,
                    "comp_aux_lib": a.comp_aux_lib,
                    "compte_num": a.compte_num,
                    "debit": str(a.debit),
                    "credit": str(a.credit),
                    "solde": str(a.solde),
                }
                for a in self.aux_balances
            ],
        }


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


def parse_fec_lines(lines: Iterable[str]) -> tuple[list[str], list[FecRow], list[str]]:
    iterator = iter(lines)
    try:
        first_line = next(iterator).lstrip("\ufeff").rstrip("\r\n")
    except StopIteration:
        return [], [], ["Fichier vide (aucune ligne d'en-tête)."]

    delimiter = _detect_delimiter(header_line=first_line)
    header = [col.strip() for col in next(csv.reader([first_line], delimiter=delimiter))]
    rows: list[FecRow] = []
    parse_errors: list[str] = []

    if tuple(header) != FEC_COLUMNS:
        return header, rows, parse_errors

    for idx, row_values in enumerate(csv.reader(iterator, delimiter=delimiter), start=2):
        if not row_values or all(not cell.strip() for cell in row_values):
            continue
        if len(row_values) != 18:
            parse_errors.append(f"L{idx}: {len(row_values)} colonnes au lieu de 18")
            continue
        try:
            debit = parse_french_decimal(row_values[11])
            credit = parse_french_decimal(row_values[12])
        except ValueError as err:
            parse_errors.append(f"L{idx}: {err}")
            continue

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
                debit=debit,
                credit=credit,
                ecriture_let=row_values[13].strip(),
                date_let=row_values[14].strip(),
                valid_date=row_values[15].strip(),
                montant_devise=row_values[16].strip(),
                idevise=row_values[17].strip(),
            )
        )
    return header, rows, parse_errors


def _valid_yyyymmdd(date_str: str) -> bool:
    if len(date_str) != 8 or not date_str.isdigit():
        return False
    try:
        datetime.strptime(date_str, "%Y%m%d")
        return True
    except ValueError:
        return False


def audit_fec_lines(lines: Iterable[str], source_name: str = "memory") -> AuditReport:
    header, rows, parse_errors = parse_fec_lines(lines)
    findings: list[AuditFinding] = []

    # C01: 18 mandatory DGFiP columns, non-empty file, mandatory row fields, non-negative amounts
    if tuple(header) != FEC_COLUMNS:
        findings.append(
            AuditFinding(
                code="C01",
                severity="ERROR",
                title="Conformité structurelle DGFiP (18 champs)",
                details=f"En-tête non conforme à l'art. A.47 A-1 du LPF ({len(header)} colonnes détectées).",
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
            vat_deductible=Decimal("0.00"),
            findings=findings,
        )

    structural_issues = list(parse_errors)
    if not rows:
        structural_issues.append("Aucune écriture comptable présente dans le fichier.")

    for r in rows:
        missing = [label for attr, label in MANDATORY_ROW_FIELDS if not getattr(r, attr)]
        if missing:
            structural_issues.append(f"L{r.line_no} ({r.ecriture_num}): champ(s) obligatoire(s) vide(s) ({', '.join(missing)})")
        if r.debit < Decimal("0.00") or r.credit < Decimal("0.00"):
            structural_issues.append(f"L{r.line_no} ({r.ecriture_num}): montant négatif interdit en norme FEC")

    if not structural_issues:
        findings.append(
            AuditFinding(
                code="C01",
                severity="PASS",
                title="Conformité structurelle DGFiP (18 champs)",
                details=f"En-tête conforme et {len(rows)} lignes validées sans champ obligatoire manquant.",
            )
        )
    else:
        findings.append(
            AuditFinding(
                code="C01",
                severity="ERROR",
                title="Conformité structurelle DGFiP (18 champs)",
                details="; ".join(structural_issues[:5]),
            )
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

    # C04: Chronological & date format validation (EcritureDate, PieceDate, ValidDate, DateLet)
    date_errors: list[str] = []
    for r in rows:
        if not (_valid_yyyymmdd(r.ecriture_date) and _valid_yyyymmdd(r.piece_date) and _valid_yyyymmdd(r.valid_date)):
            date_errors.append(f"L{r.line_no} ({r.ecriture_num}): date invalide (attendu YYYYMMDD)")
        elif r.valid_date < r.ecriture_date:
            date_errors.append(f"L{r.line_no} ValidDate < EcritureDate ({r.valid_date} < {r.ecriture_date})")
        if r.ecriture_let and r.date_let and not _valid_yyyymmdd(r.date_let):
            date_errors.append(f"L{r.line_no} DateLet invalide ({r.date_let})")

    if not date_errors:
        findings.append(
            AuditFinding(
                code="C04",
                severity="PASS",
                title="Chronologie et format des dates",
                details="Dates (EcritureDate, PieceDate, ValidDate, DateLet) au format YYYYMMDD et ValidDate >= EcritureDate.",
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

    # C06: VAT collected (44571x) vs Turnover (70x) plausibility check + deductible VAT summary
    turnover_ht = sum(
        (r.credit - r.debit for r in rows if r.compte_num.startswith("70")),
        Decimal("0.00"),
    )
    vat_collected = sum(
        (r.credit - r.debit for r in rows if r.compte_num.startswith("44571")),
        Decimal("0.00"),
    )
    vat_deductible = sum(
        (r.debit - r.credit for r in rows if r.compte_num.startswith(("44562", "44566"))),
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
                    details=(
                        f"CA HT = {turnover_ht:,.2f} €, TVA collectée = {vat_collected:,.2f} € "
                        f"(taux effectif : {eff_rate}%), TVA déductible = {vat_deductible:,.2f} €."
                    ),
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
    else:
        findings.append(
            AuditFinding(
                code="C06",
                severity="PASS",
                title="Cadrage TVA collectée / Chiffre d'affaires",
                details="Aucun chiffre d'affaires (70x) enregistré sur la période.",
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
        if (
            r.comp_aux_num
            and r.compte_num.startswith(("401", "411"))
            and r.journal_code in ("HA", "VT", "AC", "VE")
            and (r.debit + r.credit) > Decimal("0.00")
        ):
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
                details="Aucun doublon potentiel (même tiers + même montant TTC) sur les journaux d'achats/ventes.",
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

    # C09: Lettrage equilibrium & DateLet completeness on auxiliary accounts
    lettrage_groups: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0.00"))
    missing_date_let: list[str] = []
    for r in rows:
        if r.ecriture_let:
            key = (r.comp_aux_num or r.compte_num, r.ecriture_let)
            lettrage_groups[key] += r.debit - r.credit
            if not r.date_let:
                missing_date_let.append(f"L{r.line_no} ({r.ecriture_num}, lettrage {r.ecriture_let})")
    unbalanced_let = [
        f"{acct}/{code} ({diff:+.2f}€)"
        for (acct, code), diff in lettrage_groups.items()
        if diff != Decimal("0.00")
    ]
    if not unbalanced_let and not missing_date_let:
        findings.append(
            AuditFinding(
                code="C09",
                severity="PASS",
                title="Intégrité et équilibre du lettrage",
                details=f"{len(lettrage_groups)} groupe(s) de lettrage équilibré(s) avec DateLet renseignée.",
            )
        )
    else:
        issues_c09 = unbalanced_let + missing_date_let
        findings.append(
            AuditFinding(
                code="C09",
                severity="WARN",
                title="Intégrité et équilibre du lettrage",
                details="Anomalies de lettrage : " + ", ".join(issues_c09[:5]),
            )
        )

    # C10: Auxiliary accounts balance & inverted balances detection (401 debit / 411 credit)
    aux_totals: dict[tuple[str, str, str], list[Decimal]] = defaultdict(
        lambda: [Decimal("0.00"), Decimal("0.00")]
    )
    for r in rows:
        if r.comp_aux_num:
            bucket = aux_totals[(r.comp_aux_num, r.comp_aux_lib, r.compte_num)]
            bucket[0] += r.debit
            bucket[1] += r.credit

    aux_balances: list[AuxAccountSummary] = []
    inverted_aux: list[str] = []
    for (aux_num, aux_lib, cpt_num), (deb, cred) in sorted(aux_totals.items()):
        solde = deb - cred
        aux_balances.append(
            AuxAccountSummary(
                comp_aux_num=aux_num,
                comp_aux_lib=aux_lib,
                compte_num=cpt_num,
                debit=deb,
                credit=cred,
                solde=solde,
            )
        )
        if cpt_num.startswith("401") and solde > Decimal("0.00"):
            inverted_aux.append(f"Fournisseur {aux_num} ({aux_lib}) débiteur de {solde:+,.2f} €")
        elif cpt_num.startswith("411") and solde < Decimal("0.00"):
            inverted_aux.append(f"Client {aux_num} ({aux_lib}) créditeur de {solde:+,.2f} €")

    if not inverted_aux:
        findings.append(
            AuditFinding(
                code="C10",
                severity="PASS",
                title="Sens des soldes auxiliaires (Clients / Fournisseurs)",
                details=f"{len(aux_balances)} compte(s) tiers analysé(s), aucun solde inversé en clôture.",
            )
        )
    else:
        findings.append(
            AuditFinding(
                code="C10",
                severity="WARN",
                title="Sens des soldes auxiliaires (Clients / Fournisseurs)",
                details="Soldes tiers inversés à justifier : " + " ; ".join(inverted_aux[:5]),
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
        vat_deductible=vat_deductible,
        findings=findings,
        class_balances=class_balances,
        aux_balances=aux_balances,
    )


def audit_fec_file(path: str | Path) -> AuditReport:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as fh:
        return audit_fec_lines(fh, source_name=file_path.name)


def render_markdown_report(report: AuditReport) -> str:
    vat_net = report.vat_collected - report.vat_deductible
    lines = [
        f"# Rapport de Contrôle FEC & Révision — `{report.source_name}`",
        "",
        "## 1. Synthèse Générale",
        "",
        f"- **Lignes d'écritures analysées** : {report.row_count}",
        f"- **Total Débit / Crédit** : `{report.total_debit:,.2f} €` / `{report.total_credit:,.2f} €`",
        f"- **Chiffre d'affaires HT (cl. 70)** : `{report.turnover_ht:,.2f} €`",
        f"- **Cadrage TVA** : Collectée `{report.vat_collected:,.2f} €` − Déductible `{report.vat_deductible:,.2f} €` = **TVA nette `{vat_net:+,.2f} €`**",
        f"- **Résultat net comptable (Produits − Charges)** : `{report.gestion_result:+,.2f} €`",
        f"- **Statut de l'audit** : **{report.error_count} erreur(s)**, **{report.warning_count} alerte(s)**",
        "",
        "## 2. Résultats des 10 Contrôles de Conformité & Révision",
        "",
        "| Code | Statut | Contrôle | Détail |",
        "|---|---|---|---|",
    ]
    for f in report.findings:
        lines.append(f"| **{f.code}** | `{f.severity}` | {f.title} | {f.details} |")

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

    if report.aux_balances:
        lines.extend(
            [
                "",
                "## 4. Balance Auxiliaire des Tiers (Clients 411 & Fournisseurs 401)",
                "",
                "| Code Tiers | Raison Sociale | Compte Général | Total Débit (€) | Total Crédit (€) | Solde (D − C) (€) |",
                "|---|---|---|---:|---:|---:|",
            ]
        )
        for a in report.aux_balances:
            lines.append(
                f"| `{a.comp_aux_num}` | {a.comp_aux_lib} | `{a.compte_num}` | {a.debit:,.2f} | {a.credit:,.2f} | {a.solde:+,.2f} |"
            )

    lines.append("")
    return "\n".join(lines)


def render_json_report(report: AuditReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n"
