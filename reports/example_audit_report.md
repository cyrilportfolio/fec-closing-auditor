# Rapport de Contrôle FEC & Révision — `sample_fec_2026.tsv`

## 1. Synthèse Générale

- **Lignes d'écritures analysées** : 23
- **Total Débit / Crédit** : `107,150.00 €` / `107,150.00 €`
- **Chiffre d'affaires HT (cl. 70)** : `20,000.00 €`
- **Cadrage TVA** : Collectée `4,000.00 €` − Déductible `700.00 €` = **TVA nette `+3,300.00 €`**
- **Résultat net comptable (Produits − Charges)** : `+15,750.00 €`
- **Statut de l'audit** : **0 erreur(s)**, **0 alerte(s)**

## 2. Résultats des 10 Contrôles de Conformité & Révision

| Code | Statut | Contrôle | Détail |
|---|---|---|---|
| **C01** | `PASS` | Conformité structurelle DGFiP (18 champs) | En-tête conforme et 23 lignes validées sans champ obligatoire manquant. |
| **C02** | `PASS` | Équilibre général Débit / Crédit | Total Débit = Total Crédit = 107,150.00 €. |
| **C03** | `PASS` | Équilibre par pièce comptable | 8 pièces contrôlées et équilibrées. |
| **C04** | `PASS` | Chronologie et format des dates | Dates (EcritureDate, PieceDate, ValidDate, DateLet) au format YYYYMMDD et ValidDate >= EcritureDate. |
| **C05** | `PASS` | Contrôle du solde de caisse (53x) | Solde caisse débiteur ou nul (500.00 €). |
| **C06** | `PASS` | Cadrage TVA collectée / Chiffre d'affaires | CA HT = 20,000.00 €, TVA collectée = 4,000.00 € (taux effectif : 20.00%), TVA déductible = 700.00 €. |
| **C07** | `PASS` | Concordance Bilan (cl. 1–5) / Résultat (cl. 6–7) | Résultat net concordant : +15,750.00 €. |
| **C08** | `PASS` | Détection de doublons de factures tiers | Aucun doublon potentiel (même tiers + même montant TTC) sur les journaux d'achats/ventes. |
| **C09** | `PASS` | Intégrité et équilibre du lettrage | 2 groupe(s) de lettrage équilibré(s) avec DateLet renseignée. |
| **C10** | `PASS` | Sens des soldes auxiliaires (Clients / Fournisseurs) | 4 compte(s) tiers analysé(s), aucun solde inversé en clôture. |

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

## 4. Balance Auxiliaire des Tiers (Clients 411 & Fournisseurs 401)

| Code Tiers | Raison Sociale | Compte Général | Total Débit (€) | Total Crédit (€) | Solde (D − C) (€) |
|---|---|---|---:|---:|---:|
| `CLI001` | SAS CHAMPAGNE CONSEIL | `411000` | 14,400.00 | 14,400.00 | +0.00 |
| `CLI002` | FINTECH GRAND EST | `411000` | 9,600.00 | 0.00 | +9,600.00 |
| `FRN001` | CLOUD COMPUTE EUROPE | `401000` | 1,800.00 | 1,800.00 | +0.00 |
| `FRN002` | CABINET ALRICK AUDIT | `401000` | 0.00 | 2,400.00 | -2,400.00 |
