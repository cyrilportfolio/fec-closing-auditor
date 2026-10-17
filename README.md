# FEC Closing Auditor (`fec-closing-auditor`)

**Contrôle qualité automatisé du Fichier des Écritures Comptables (FEC — norme DGFiP, art. L.47 A-I du LPF) et dossier de révision de clôture en Python.**  
*Automated French statutory general ledger (FEC) compliance checker and pre-closing audit engine.*

---

## Pourquoi cet outil ? / Why this project?

En cabinet d'expertise comptable comme en direction financière, la révision d'un dossier commence systématiquement par deux exigences :
1. **La conformité formelle et substantielle du FEC** aux 18 champs réglementaires de l'article A.47 A-1 du Livre des Procédures Fiscales (LPF).
2. **La fiabilité des cycles comptables avant clôture** : équilibre des écritures, cadrage Bilan / Résultat, cadrage de TVA (collectée vs chiffre d'affaires HT et déductible), intégrité du lettrage, absence de caisse créditrice, justification des soldes tiers inversés et détection des factures saisies en doublon.

`fec-closing-auditor` automatise ces **10 contrôles** sans dépendance externe (bibliothèque standard Python 3.10+, calculs monétaires exacts en `Decimal`), et génère un **rapport de révision en Markdown** ainsi qu'un **export JSON structuré** (avec synthèse par classe PCG et balance auxiliaire des tiers).

---

## Les 10 contrôles exécutés (Conformité DGFiP & Révision comptable)

| Code | Catégorie | Contrôle | Référence / Objectif |
|---|---|---|---|
| **C01** | Conformité DGFiP | Présence des **18 colonnes obligatoires**, champs obligatoires non vides par ligne et montants positifs | Art. A.47 A-1 LPF |
| **C02** | Intégrité | **Équilibre global** du grand livre ($\sum \text{Débit} = \sum \text{Crédit}$ au centime près) | Principe de la partie double |
| **C03** | Intégrité | **Équilibre par pièce comptable** (`JournalCode` + `EcritureNum`) | Détection d'écritures déséquilibrées |
| **C04** | Chronologie | Validité calendaire `YYYYMMDD` (`EcritureDate`, `PieceDate`, `ValidDate`, `DateLet`) et `ValidDate >= EcritureDate` | Intangibilité des écritures |
| **C05** | Trésorerie | Contrôle du **sens du solde de caisse** (`53x` ne peut jamais être créditeur) | Anomalie fiscale bloquante |
| **C06** | Fiscalité / TVA | **Cadrage TVA collectée (`44571x`) vs CA HT (`70x`)** et synthèse TVA déductible (`44562x` / `44566x`) | Cohérence du taux effectif & liquidation |
| **C07** | Révision | **Concordance Bilan (Classes 1 à 5) vs Compte de Résultat (Classes 6 et 7)** | Exactitude du résultat net |
| **C08** | Tiers / Fraude | **Détection de doublons potentiels** sur factures tiers (`401x`/`411x`, même `CompAuxNum`, même montant TTC > 0) | Prévention des doubles règlements |
| **C09** | Révision Tiers | **Intégrité et équilibre du lettrage** ($\sum D_{\text{let}} = \sum C_{\text{let}}$ par code `EcritureLet` et présence de `DateLet`) | Justification des comptes courants |
| **C10** | Révision Tiers | **Détection des soldes auxiliaires inversés** (fournisseurs `401x` débiteurs / clients `411x` créditeurs) | Reclassements de clôture (`4091`/`4191`) |

---

## Utilisation rapide / Quickstart

```bash
# 1. Lancer l'audit sur le FEC de démonstration et générer le rapport Markdown
python3 -m fec_auditor data/sample_fec_2026.tsv --output reports/example_audit_report.md

# 2. Générer simultanément le rapport Markdown et l'export JSON
python3 -m fec_auditor data/sample_fec_2026.tsv -o reports/example_audit_report.md --json reports/audit.json

# 3. Exécuter la suite de 10 tests unitaires
python3 -m unittest discover -s tests -v
```

---

## Structure du dépôt

```text
fec-closing-auditor/
├── pyproject.toml           # Métadonnées PEP 621 & point d'entrée CLI fec-auditor
├── fec_auditor/
│   ├── __init__.py
│   ├── __main__.py          # Interface CLI (--output Markdown, --json JSON)
│   └── auditor.py           # Moteur de validation DGFiP, 10 contrôles & restitutions PCG/Tiers
├── data/
│   └── sample_fec_2026.tsv  # Jeu d'essai FEC réaliste (AN, HA, VT, BQ, OD)
├── reports/
│   └── example_audit_report.md
└── tests/
    └── test_auditor.py      # 10 tests unitaires couvrant chaque contrôle et cas d'erreur
```

---

## Auteur / Author

**Cyril ANTOINE** — Comptable financier & Spécialiste Automatisation / IA  
- [LinkedIn](https://www.linkedin.com/in/cyrilantoine/) · [GitHub (@cyrilportfolio)](https://github.com/cyrilportfolio)
