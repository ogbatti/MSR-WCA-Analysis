# MSR WCA — Roadmap v2 (institutionnel 9/10 + AI)

## Règle d’or — production gelée

| Environnement | Branche Git | Déploiement |
|---------------|-------------|-------------|
| **Production** (existante) | `master` uniquement | Streamlit Cloud actuel + `dimawca.app` |
| **Staging / v2** | `develop` | 2ᵉ app Streamlit Cloud (à créer) |

- **Aucun merge `develop` → `master`** tant que la checklist de validation n’est pas signée.
- Les évolutions “9/10” et l’assistant AI se font **uniquement sur `develop`** (et staging).
- La prod actuelle reste telle quelle pour les utilisateurs.

---

## Objectif

Outil de référence MSR WCA : chiffres opposables, gouvernance, PDF institutionnels, assistant AI branché sur les **mêmes calculs** que le dashboard.

---

## Phases

### Phase 0 — Isolation
- [x] Branche `develop`
- [x] App Streamlit Cloud **staging** pointant sur `develop`
- [x] Ce document + checklist go-live
- [ ] Secrets staging (`ACTIVITYINFO_TOKEN`, plus tard clé LLM)

### Phase 1 — Confiance dans les données
- [x] Version / horodatage extrait ActivityInfo (UI + PDF) — `population_meta.json`
- [x] Bandeau qualité (couverture sexe REF/ASY, écarts detailed vs total)
- [x] Tests automatiques agrégation (`tests/test_analytical_subset.py`)
- [x] Bandeau « staging » pour distinguer clairement de la prod
- [x] CI GitHub Actions (prochaine itération)
- [ ] Réconciliation vs totaux de référence externes (si source dispo)

### Phase 2 — Produit + gouvernance
- [x] Auth configurable (password / users / OIDC prêt Azure AD) — `src/auth.py`
- [x] Rôles lecteur / pays / admin (+ filtre pays)
- [x] Audit exports PDF (+ journal admin) — `src/audit.py`
- [x] PDF couverture institutionnelle (sources + avertissement)
- [x] Parcours guidé Flash → Pays → Tendance → Rapports
- [x] Exemple secrets : `.streamlit/secrets.toml.example`
- [ ] SSO Azure AD branché en réel sur le staging (config tenant UNHCR)

### Phase 3 — Assistant AI (MVP)
- [x] Chat FR/EN (onglet Assistant)
- [x] Outils → indicateurs / filtres session (chiffres = code)
- [x] Aide navigation + glossaire
- [x] Garde-fous : pas d’invention numérique ; refus hors périmètre ; audit questions
- [x] LLM optionnel (`ASSISTANT_LLM=on`) pour reformuler uniquement
- [ ] Évaluation qualité sur jeu de questions de référence (DIMA)

### Phase 4 — Validation puis bascule prod
- [x] Grille de recette staging — `docs/RECETTE_STAGING.md`
- [x] Procédure bascule / rollback — `docs/BASCULE_PROD.md`
- [x] Feature flags `FEATURE_ASSISTANT` / `ASSISTANT_LLM` — `src/flags.py`
- [x] CI GitHub Actions (pytest) — `.github/workflows/ci.yml`
- [ ] Recette staging exécutée et signée (Go)
- [ ] Merge `develop` → `master` **uniquement après Go**
- [ ] Smoke prod post-bascule

---

## Créer l’app staging (manuel — compte Streamlit)

1. Aller sur [share.streamlit.io](https://share.streamlit.io)
2. **New app** → repo `ogbatti/MSR-WCA-Analysis`
3. **Branch :** `develop` (pas `master`)
4. Main file : `app.py`
5. Nom suggéré : `dimawca-staging` → URL du type `dimawca-staging.streamlit.app`
6. Secrets : reprendre `ACTIVITYINFO_TOKEN` (comme la prod)
7. **Ne pas** brancher le domaine `dimawca.app` sur cette app

---

## Checklist validation go-live (avant merge vers `master`)

### Données
- [ ] Flash / fiche pays reconnus comme référence mensuelle (DIMA)
- [ ] Version des données visible et cohérente UI ↔ PDF
- [ ] Tests agrégation verts en CI
- [ ] Bandeau qualité compris et utile

### Produit
- [ ] Parcours Flash → Pays → Tendance → PDF validé
- [ ] PDF utilisable en briefing sans reprise lourde
- [ ] Auth + rôles OK sur staging
- [ ] Audit minimal des exports

### AI
- [ ] Jeu de questions de référence : **0 invention numérique**
- [ ] Aide navigation / glossaire utile
- [ ] Hors périmètre → refus clair
- [ ] Pas d’envoi de données brutes sensibles au LLM

### Ops
- [ ] Staging stable ; rollback documenté
- [ ] Décision formelle DIMA (+ métier si besoin)
- [ ] Plan de bascule `develop` → `master` communiqué

**Signataires (noms / dates) :**

| Rôle | Nom | Date | OK |
|------|-----|------|-----|
| DIMA | | | |
| Métier / RBWCA | | | |
| Technique | | | |

---

## Workflow Git au quotidien

```text
master   = prod figée
develop  = seule branche de travail v2
feature/* (optionnel) → PR vers develop
develop → master     = uniquement après checklist
```
