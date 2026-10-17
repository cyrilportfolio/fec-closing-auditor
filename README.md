# 🕵️‍♂️📊 FEC Closing Auditor (`fec-closing-auditor`)

> **Le radar anti-boulettes pour votre Fichier des Écritures Comptables (FEC) avant la clôture.**  
> *Zero-dependency Python demonstrator that audits a French statutory general ledger (FEC — DGFiP) and generates a clean pre-closing review report in milliseconds.*

---

## 🎯 Le pitch en 30 secondes

En cabinet d'expertise comptable ou en direction financière, ouvrir un FEC de 50 000 lignes à la veille d'une clôture (ou d'un contrôle fiscal), c'est souvent chercher une aiguille dans une botte de foin :
- *« Est-ce que les 18 colonnes DGFiP sont vraiment toutes là et remplies ? »*
- *« Pourquoi la caisse est créditrice de 250 € au mois de janvier ?! »*
- *« Tiens, on n'aurait pas saisi deux fois la facture de Cloud Compute Europe ? »*
- *« La TVA collectée colle-t-elle vraiment au chiffre d'affaires HT ? »*

**`fec-closing-auditor`** est un démonstrateur léger en Python pur (zéro dépendance externe, calculs au centime près avec `Decimal`) qui passe votre grand livre au scanner à travers **10 contrôles de conformité DGFiP et de révision comptable** et crache un dossier de travail propre en **Markdown** ou en **JSON**.

---

## 🚀 Tester le démonstrateur en 1 commande

Aucune installation de librairie requise (Python 3.10+ suffit) :

```bash
# 1. Scanner le FEC de démo et afficher le rapport de révision dans le terminal
python3 -m fec_auditor data/sample_fec_2026.tsv

# 2. Sauvegarder le rapport Markdown + l'export JSON structuré
python3 -m fec_auditor data/sample_fec_2026.tsv \
  --output reports/example_audit_report.md \
  --json reports/audit.json

# 3. Lancer les 10 tests unitaires (conformité, caisse créditrice, doublons, lettrage...)
python3 -m unittest discover -s tests -v
```

👉 **Envie de voir le résultat tout de suite ?** Consultez directement l'exemple généré : [`reports/example_audit_report.md`](reports/example_audit_report.md).

---

## 🔍 Les 10 contrôles sous le capot

Chaque fichier FEC passe par 10 points de contrôle classés en 3 niveaux (`PASS`, `WARN`, `ERROR`) :

| Code | Niveau | Ce que le radar vérifie | Pourquoi ça sauve votre clôture |
|---|---|---|---|
| **C01** | `ERROR` | **Structure DGFiP (18 colonnes)**, champs obligatoires non vides & montants $\ge 0$ | Évite le rejet immédiat du FEC (art. A.47 A-1 du LPF). |
| **C02** | `ERROR` | **Équilibre global** ($\sum \text{Débit} = \sum \text{Crédit}$) | La base de la partie double : pas un centime d'écart toléré. |
| **C03** | `ERROR` | **Équilibre par pièce** (`JournalCode` + `EcritureNum`) | Repère immédiatement une écriture boiteuse. |
| **C04** | `ERROR` | **Chronologie & Dates** (`YYYYMMDD` valides et `ValidDate >= EcritureDate`) | Garantit l'intangibilité chronologique des écritures. |
| **C05** | `ERROR` | **Sens de la Caisse (`53x`)** | Une caisse espèces ne peut pas être négative (anomalie fiscale classique). |
| **C06** | `WARN` | **Cadrage TVA collectée (`44571`) / CA HT (`70x`)** + synthèse TVA déductible | Vérifie d'un coup d'œil la cohérence du taux effectif de TVA. |
| **C07** | `ERROR` | **Concordance Bilan (cl. 1–5) vs Résultat (cl. 6–7)** | Confirme que le résultat net au bilan égale Produits − Charges. |
| **C08** | `WARN` | **Chasse aux doublons de factures tiers (`401`/`411`)** | Détecte deux factures pour le même tiers avec le même montant TTC. |
| **C09** | `WARN` | **Intégrité du lettrage** ($\sum D_{\text{let}} = \sum C_{\text{let}}$ & `DateLet`) | Repère les lettrages partiels ou non équilibrés. |
| **C10** | `WARN` | **Soldes tiers inversés** (fournisseurs débiteurs / clients créditeurs) | Prépare la liste des reclassements de clôture (`4091` / `4191`). |

---

## 📦 Ce que contient le dépôt

```text
fec-closing-auditor/
├── fec_auditor/
│   ├── auditor.py           # 🧠 Le moteur des 10 contrôles + calcul des balances PCG & Tiers
│   └── __main__.py          # 💻 L'interface en ligne de commande (--output, --json)
├── data/
│   └── sample_fec_2026.tsv  # 📄 Un mini-FEC réaliste (ouverture AN, achats HA, ventes VT, banque BQ, OD)
├── reports/
│   └── example_audit_report.md # 📋 Exemple de feuille de révision générée automatiquement
└── tests/
    └── test_auditor.py      # 🧪 10 tests unitaires qui simulent les vraies erreurs de saisie
```

---

## 👋 À propos de l'auteur

Créé par **Cyril ANTOINE** — Comptable financier (18+ ans d'expérience) qui embarque sur la vague de l'automatisation Python et des agents IA 🌊🤖.

- 🔗 [LinkedIn](https://www.linkedin.com/in/cyrilantoine/)
- 💻 [Autres projets Finance & Python sur GitHub (`@cyrilportfolio`)](https://github.com/cyrilportfolio)
