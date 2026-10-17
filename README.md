# FEC Closing Auditor (`fec-closing-auditor`)

**Contrôle qualité automatisé du Fichier des Écritures Comptables (FEC — norme DGFiP, art. L.47 A-I du LPF) et dossier de révision de clôture en Python.**  
*Automated French statutory general ledger (FEC) compliance checker and pre-closing audit engine.*

---

## Pourquoi cet outil ? / Why this project?

En cabinet d'expertise comptable comme en direction financière, la révision d'un dossier commence systématiquement par deux exigences :
1. **La conformité formelle du FEC** aux 18 champs réglementaires de l'article A.47 A-1 du Livre des Procédures Fiscales (LPF).
2. **La fiabilité des cycles comptables avant clôture** : équilibre des écritures, cadrage Bilan / Résultat, vraisemblance de la TVA collectée par rapport au chiffre d'affaires, absence de caisse créditrice et détection des saisies en doublon.

`fec-closing-auditor` automatise ces contrôles en quelques millisecondes sans dépendance externe lourde (bibliothèque standard Python 3.10+, calculs monétaires exacts en `Decimal`), et génère un **rapport de révision en Markdown** prêt à être joint au dossier de travail.

---

## Contrôles exécutés (8 contrôles de conformité & révision)

| Code | Catégorie | Contrôle | Référence / Objectif |
|---|---|---|---|
| **C01** | Conformité DGFiP | Présence et ordre exact des **18 colonnes obligatoires** du FEC | Art. A.47 A-1 LPF |
| **C02** | Intégrité | **Équilibre global** du fichier ($\sum \text{Débit} = \sum \text{Crédit}$ au centime près) | Principe de la partie double |
| **C03** | Intégrité | **Équilibre par pièce** (`JournalCode` + `EcritureNum`) | Détection d'écritures déséquilibrées |
| **C04** | Chronologie | Format des dates (`YYYYMMDD`) et cohérence `ValidDate >= EcritureDate` | Intangibilité des écritures |
| **C05** | Trésorerie | Contrôle du **sens du solde de caisse** (`530x` ne peut jamais être créditeur) | Anomalie fiscale bloquante |
| **C06** | Fiscalité / TVA | **Cadrage TVA collectée (`44571x`) vs Chiffre d'affaires (`70x`)** | Cohérence du taux moyen effectif |
| **C07** | Révision | **Cadrage Bilan (Classes 1 à 5) vs Compte de Résultat (Classes 6 et 7)** | Concordance du résultat net |
| **C08** | Tiers / Fraude | **Détection de doublons potentiels** sur factures fournisseurs/clients (même `CompAuxNum`, même montant, dates proches) | Prévention des doubles règlements |

---

## Utilisation rapide / Quickstart

```bash
# 1. Lancer l'audit sur le FEC de démonstration et afficher le rapport Markdown
python3 -m fec_auditor data/sample_fec_2026.tsv --output reports/example_audit_report.md

# 2. Exécuter la suite de tests unitaires
python3 -m unittest discover -s tests -v
```

---

## Structure du dépôt

```text
fec-closing-auditor/
├── fec_auditor/
│   ├── __init__.py
│   ├── __main__.py          # Interface CLI (python3 -m fec_auditor)
│   └── auditor.py           # Moteur de validation DGFiP, contrôles & synthèse PCG
├── data/
│   └── sample_fec_2026.tsv  # Jeu d'essai FEC réaliste (AN, HA, VT, BQ, OD)
├── reports/
│   └── example_audit_report.md
└── tests/
    └── test_auditor.py      # Tests unitaires (conformité, anomalies, doublons, TVA)
```

---

## Auteur / Author

**Cyril ANTOINE** — Comptable financier & Spécialiste Automatisation / IA  
- [LinkedIn](https://www.linkedin.com/in/cyrilantoine/) · [GitHub (@cyrilportfolio)](https://github.com/cyrilportfolio)
