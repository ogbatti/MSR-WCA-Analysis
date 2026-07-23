# Bascule production — MSR WCA v2

> **Ne pas exécuter** tant que `docs/RECETTE_STAGING.md` n’est pas en **Go** avec signataires.

## Prérequis

- [ ] Recette staging complète (A–D OK)
- [ ] Checklist `docs/ROADMAP_V2.md` signée
- [ ] CI verte sur `develop`
- [ ] Secrets prod préparés (ci-dessous)
- [ ] Communication interne (DIMA / RBWCA) : fenêtre de bascule

## Secrets production (Streamlit Cloud — app `master`)

```toml
ACTIVITYINFO_TOKEN = "..."
MSR_CHANNEL = "prod"

# Auth : ouvrir progressivement
AUTH_MODE = "password"   # puis oidc quand Azure AD prêt
APP_PASSWORD = "..."     # ou [app_users] / [auth] OIDC

# Feature flags — bascule prudente
FEATURE_ASSISTANT = "on"   # mettre "off" pour cacher l’onglet au 1er jour
ASSISTANT_LLM = "off"      # reformulation LLM désactivée par défaut en prod
```

`MSR_CHANNEL=prod` retire le bandeau staging.

## Procédure de bascule

1. Sur GitHub : PR ou merge **`develop` → `master`** (fast-forward de préférence).
2. Vérifier que l’app Cloud **production** suit bien la branche `master`.
3. Coller / mettre à jour les secrets prod.
4. Reboot de l’app Cloud si besoin.
5. Smoke prod (15 min) :
   - charge données + version
   - KPI / un pays / un PDF
   - Assistant (si `FEATURE_ASSISTANT=on`) : 2 questions + 1 hors sujet
6. Annoncer la bascule ; garder le staging `develop` actif pour la suite.

## Rollback (si incident)

1. Sur la prod Streamlit Cloud : **redeploy** / pin sur le commit `master` **précédent** (avant merge),  
   **ou** `git revert` du merge sur `master` + push.
2. Remettre les secrets d’avant si modifiés.
3. Communiquer le rollback ; corriger sur `develop` ; nouvelle recette.

Commit prod actuel avant bascule (à noter le jour J) : `________________`

## Après bascule

- Ne plus pousser de features directement sur `master`.
- Continuer sur `develop` → staging → recette → merge.
- Planifier SSO Azure AD et eval AI DIMA s’ils étaient en No-Go partiel.
