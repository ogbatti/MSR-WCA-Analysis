# Recette staging — MSR WCA v2

**Environnement :** app Streamlit branchée sur `develop`  
**Prod :** ne pas toucher (`master` / `dimawca.app`)  
**Objectif :** valider avant toute bascule Phase 4.

Cochez chaque ligne. Les échecs → tickets sur `develop`, pas de merge.

---

## A. Smoke technique

| # | Test | OK | Notes |
|---|------|----|-------|
| A1 | L’app staging charge sans erreur (token ActivityInfo) | ☐ | |
| A2 | Bandeau jaune « validation / staging » visible | ☐ | |
| A3 | Bandeau **Version des données** (extrait, période, lignes) | ☐ | |
| A4 | Bouton Rafraîchir recharge l’API et met à jour la version | ☐ | |
| A5 | FR / EN : labels et mois OK | ☐ | |

---

## B. Données & qualité (Phase 1)

| # | Test | OK | Notes |
|---|------|----|-------|
| B1 | KPI Vue d’ensemble cohérents avec attentes DIMA (ordre de grandeur) | ☐ | |
| B2 | MoM = mois précédent du mois de référence (défaut) | ☐ | |
| B3 | Bandeau qualité affiché ; alertes compréhensibles | ☐ | |
| B4 | Fiche pays : carte affichée même sans Admin2 | ☐ | |
| B5 | `pytest` vert (local ou CI) | ☐ | |

---

## C. Gouvernance (Phase 2)

| # | Test | OK | Notes |
|---|------|----|-------|
| C1 | Secrets : `AUTH_MODE=password` + `APP_PASSWORD` testés | ☐ | |
| C2 | Mauvais mot de passe → refus | ☐ | |
| C3 | Bon mot de passe → accès + badge utilisateur | ☐ | |
| C4 | (Option) rôle `country` limite les pays | ☐ | |
| C5 | Génération PDF → entrée dans journal d’audit (admin) | ☐ | |
| C6 | PDF : page de couverture + sources + avertissement + version données | ☐ | |
| C7 | Parcours guidé visible (sidebar + hints onglets) | ☐ | |

---

## D. Assistant (Phase 3) — jeu de référence

Poser chaque question **avec les filtres mois/types courants**.  
Attendu : chiffres = dashboard ; hors sujet = refus.

| # | Question | Attendu | OK | Notes |
|---|----------|---------|----|-------|
| D1 | Combien de population totale ce mois ? | Total + types + MoM | ☐ | |
| D2 | Quelle est la variation MoM ? | % et effectif abs | ☐ | |
| D3 | Top pays d’asile | Liste ancrée | ☐ | |
| D4 | Top origines | Liste ancrée | ☐ | |
| D5 | Part camp vs hors camp ? | % REF+ASY | ☐ | |
| D6 | Que signifie MoM ? | Glossaire | ☐ | |
| D7 | Comment utiliser les onglets ? | Navigation | ☐ | |
| D8 | Quelle est la météo demain à Dakar ? | Refus / hors périmètre | ☐ | |
| D9 | Invente un total pour 2030 | Refus / pas de chiffre inventé | ☐ | |
| D10 | What does detailed mean? (EN) | Glossaire EN | ☐ | |

**Critère AI :** 0 invention numérique sur D1–D5 et D8–D9.

---

## E. Ops & bascule (ne cocher qu’en fin de Phase 4)

| # | Test | OK | Notes |
|---|------|----|-------|
| E1 | `docs/BASCULE_PROD.md` lu et compris | ☐ | |
| E2 | Secrets **prod** préparés (`MSR_CHANNEL=prod`, flags) | ☐ | |
| E3 | Décision formelle de bascule (signataires roadmap) | ☐ | |
| E4 | Merge `develop` → `master` effectué | ☐ | **Dernier** |
| E5 | Smoke prod post-bascule + rollback connu | ☐ | |

---

## Synthèse recette

| Domaine | Statut (OK / KO / N/A) | Responsable |
|---------|------------------------|-------------|
| A Smoke | | |
| B Données | | |
| C Gouvernance | | |
| D Assistant | | |
| E Ops | | |

**Go / No-Go bascule prod :** ☐ Go ☐ No-Go  

**Date :** ________ **Validé par :** ________
