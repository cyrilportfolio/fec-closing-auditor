# Rapport de Contrôle FEC & Révision — `sample_fec_2026.tsv`

## 1. Synthèse Générale

- **Lignes d'écritures analysées** : 23
- **Total Débit** : `107,150.00 €`
- **Total Crédit** : `107,150.00 €`
- **Chiffre d'affaires HT (cl. 70)** : `20,000.00 €`
- **TVA collectée (44571)** : `4,000.00 €`
- **Résultat net (Produits − Charges)** : `+15,750.00 €`
- **Statut de l'audit** : **0 erreur(s)**, **0 alerte(s)**

## 2. Résultats des 8 Contrôles

| Code | Statut | Contrôle | Détail |
|---|---|---|---|
| **C01** | `PASS` | Conformité des 18 colonnes DGFiP | En-tête strictement conforme à l'article A.47 A-1 du LPF. |
| **C02** | `PASS` | Équilibre général Débit / Crédit | Total Débit = Total Crédit = 107,150.00 €. |
| **C03** | `PASS` | Équilibre par pièce comptable | 8 pièces contrôlées et équilibrées. |
| **C04** | `PASS` | Chronologie et format des dates | Toutes les dates respectent le format YYYYMMDD et ValidDate >= EcritureDate. |
| **C05** | `PASS` | Contrôle du solde de caisse (53x) | Solde caisse débiteur ou nul (500.00 €). |
| **C06** | `PASS` | Cadrage TVA collectée / Chiffre d'affaires | CA HT = 20,000.00 €, TVA collectée = 4,000.00 € (taux apparent : 20.00%). |
| **C07** | `PASS` | Concordance Bilan (cl. 1–5) / Résultat (cl. 6–7) | Résultat net concordant : +15,750.00 €. |
| **C08** | `PASS` | Détection de doublons de factures tiers | Aucun doublon potentiel (même tiers + même montant TTC) détecté sur les journaux HA/VT. |

## 3. Synthèse par Classe du Plan Comptable Général (PCG)

| Classe PCG | Total Débit (€) | Total Crédit (€) | Solde (D − C) (€) |
|---|---:|---:|---:|
| Classe 1 — Capitaux | 0.00 | 62,000.00 | -62,000.00 |
| Classe 2 — Immobilisations | 15,000.00 | 750.00 | +14,250.00 |
| Classe 3 — Stocks | 0.00 | 0.00 | +0.00 |
| Classe 4 — Tiers | 26,500.00 | 22,600.00 | +3,900.00 |
| Classe 5 — Financiers | 61,400.00 | 1,800.00 | +59,600.00 |
| Classe 6 — Charges | 4,250.00 | 0.00 | +4,250.00 |
| Classe 7 — Produits | 0.00 | 20,000.00 | -20,000.00 |
