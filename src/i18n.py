"""Bilingual UI strings."""
from __future__ import annotations

STRINGS = {
    "app_title": {
        "fr": "MSR — Rapport statistique mensuel WCA",
        "en": "MSR — Monthly Statistical Report WCA",
    },
    "app_subtitle": {
        "fr": "Déplacement forcé & apatridie · Afrique de l'Ouest et du Centre",
        "en": "Forced displacement & statelessness · West & Central Africa",
    },
    "language": {"fr": "Langue", "en": "Language"},
    "filters": {"fr": "Filtres", "en": "Filters"},
    "month": {"fr": "Mois de référence", "en": "Reference month"},
    "compare_month": {"fr": "Mois de comparaison (MoM)", "en": "Comparison month (MoM)"},
    "pop_types": {"fr": "Types de population", "en": "Population types"},
    "host_countries": {"fr": "Pays d'asile", "en": "Countries of asylum"},
    "origins": {"fr": "Pays d'origine", "en": "Countries of origin"},
    "refresh": {"fr": "Rafraîchir les données API", "en": "Refresh API data"},
    "overview": {"fr": "Vue d'ensemble", "en": "Overview"},
    "trends": {"fr": "Tendances", "en": "Trends"},
    "maps": {"fr": "Cartes & corridors", "en": "Maps & corridors"},
    "territory": {"fr": "Fiche pays", "en": "Country profile"},
    "adult_age_detail": {
        "fr": "Détail des âges adultes (18–24 / 25–49 / 50–59)",
        "en": "Adult age detail (18–24 / 25–49 / 50–59)",
    },
    "monthly_change": {
        "fr": "Variation mensuelle (personnes)",
        "en": "Monthly change (people)",
    },
    "monthly_change_help": {
        "fr": "Chaque barre montre combien de personnes ont été ajoutées ou retirées par rapport au mois précédent (vert = hausse, rouge = baisse). Survolez pour voir le % MoM et YoY.",
        "en": "Each bar shows how many people were added or removed versus the previous month (green = increase, red = decrease). Hover for MoM and YoY %.",
    },
    "acc_ref_asy": {
        "fr": "REF + ASY — camp vs hors camp",
        "en": "REF + ASY — camp vs out of camp",
    },
    "residence_map": {
        "fr": "Carte des zones de résidence (Admin2)",
        "en": "Residence areas map (Admin2)",
    },
    "shelter_psn": {"fr": "Hébergement & PSN", "en": "Shelter & PSN"},
    "admin": {"fr": "Admin1 / Admin2", "en": "Admin1 / Admin2"},
    "reports": {"fr": "Rapports", "en": "Reports"},
    "reports_intro": {
        "fr": "Téléchargez des rapports PDF prêts à partager. Utilisez les filtres de la barre latérale (mois, types, pays) — la fiche pays exige un pays sélectionné ci-dessous.",
        "en": "Download ready-to-share PDF reports. Sidebar filters (month, types, countries) apply — the country profile requires a country selected below.",
    },
    "download_pdf": {"fr": "Télécharger PDF", "en": "Download PDF"},
    "report_country": {
        "fr": "Pays pour le rapport « Profil pays »",
        "en": "Country for the “Country profile” report",
    },
    "forecast": {"fr": "Projection illustrative", "en": "Illustrative projection"},
    "about": {"fr": "À propos & glossaire", "en": "About & glossary"},
    "narrative": {"fr": "Interprétation", "en": "Narrative"},
    "kpi_total": {"fr": "Population totale", "en": "Total population"},
    "kpi_ref_asy": {"fr": "REF + ASY", "en": "REF + ASY"},
    "kpi_idp": {"fr": "PDI", "en": "IDPs"},
    "kpi_sta": {"fr": "Apatrides", "en": "Stateless"},
    "kpi_female": {"fr": "Part femmes*", "en": "Female share*"},
    "kpi_children": {"fr": "Part enfants*", "en": "Children share*"},
    "kpi_mom": {"fr": "Variation MoM", "en": "MoM change"},
    "kpi_hosts": {"fr": "Pays d'asile", "en": "Host countries"},
    "kpi_note_demog": {
        "fr": "* Parts calculées uniquement sur les populations ventilées par sexe / âge (souvent REF/ASY).",
        "en": "* Shares computed only on populations with sex / age breakdown (often REF/ASY).",
    },
    "data_quality": {"fr": "Qualité des données", "en": "Data quality"},
    "export_csv": {"fr": "Exporter CSV (mois filtré)", "en": "Export CSV (filtered month)"},
    "top_hosts": {"fr": "Top pays d'accueil", "en": "Top host countries"},
    "top_origins": {"fr": "Top pays d'origine", "en": "Top countries of origin"},
    "stock_by_type": {
        "fr": "Population totale par type",
        "en": "Total population by type",
    },
    "monthly_trend": {
        "fr": "Évolution mensuelle de la population totale",
        "en": "Monthly total population trend",
    },
    "mom_yoy": {"fr": "Variations MoM / YoY", "en": "MoM / YoY changes"},
    "returns_trend": {
        "fr": "Flux de retours (RET / RDP)",
        "en": "Returnee flows (RET / RDP)",
    },
    "choropleth": {
        "fr": "Population totale par pays d'asile (WCA)",
        "en": "Total population by country of asylum (WCA)",
    },
    "corridors": {
        "fr": "Corridors REF / ASY (origine → asile)",
        "en": "REF / ASY corridors (origin → asylum)",
    },
    "age_sex": {"fr": "Pyramide des âges par sexe", "en": "Age–sex pyramid"},
    "admin1": {"fr": "Répartition Admin1", "en": "Admin1 distribution"},
    "admin2": {"fr": "Répartition Admin2 (pays sélectionné)", "en": "Admin2 (selected country)"},
    "hotspots": {"fr": "Hotspots Admin1 (MoM)", "en": "Admin1 hotspots (MoM)"},
    "country_profile": {"fr": "Fiche pays", "en": "Country profile"},
    "select_country": {"fr": "Pays pour fiche / Admin2", "en": "Country for profile / Admin2"},
    "accommodation": {"fr": "Hébergement", "en": "Accommodation"},
    "psn_total": {"fr": "Total PSN (mois)", "en": "Total PSN (month)"},
    "psn_by_need": {"fr": "PSN par catégorie de besoin", "en": "PSN by need category"},
    "psn_by_country": {"fr": "PSN par pays d'asile", "en": "PSN by country of asylum"},
    "psn_note": {
        "fr": "Les PSN (Persons with Specific Needs) ne sont pas le stock global : ce sont des sous-ensembles à besoins spécifiques.",
        "en": "PSN (Persons with Specific Needs) are not the overall stock: they are subsets with specific needs.",
    },
    "assumptions": {"fr": "Hypothèses métier", "en": "Business assumptions"},
    "forecast_disclaimer": {
        "fr": "Illustration basée sur des hypothèses métier. L'historique mensuel disponible est court (~17 mois) : ces projections ne constituent pas une prévision statistique.",
        "en": "Illustration based on business assumptions. Available monthly history is short (~17 months): these projections are not a statistical forecast.",
    },
    "growth": {"fr": "Croissance annuelle résiduelle", "en": "Residual annual growth"},
    "conflict": {"fr": "Choc conflit annuel", "en": "Annual conflict shock"},
    "returns": {"fr": "Taux de retour / solutions", "en": "Return / solutions rate"},
    "horizon": {"fr": "Horizon", "en": "Horizon"},
    "forecast_pop": {"fr": "Population à projeter", "en": "Population to project"},
    "scenario_compare": {"fr": "Comparaison des scénarios", "en": "Scenario comparison"},
    "total_population": {"fr": "Population totale", "en": "Total population"},
    "loading_error": {
        "fr": "Impossible de charger les données ActivityInfo. Vérifiez le token et le réseau.",
        "en": "Unable to load ActivityInfo data. Check the token and network.",
    },
    "data_version_title": {
        "fr": "Version des données",
        "en": "Data version",
    },
    "quality_banner_title": {
        "fr": "Qualité des données (mois filtré)",
        "en": "Data quality (filtered month)",
    },
    "quality_empty": {
        "fr": "Aucune donnée pour évaluer la qualité sur la sélection actuelle.",
        "en": "No data to assess quality for the current selection.",
    },
    "quality_low_sex": {
        "fr": "{pop_code} : couverture sexe faible ({pct} %). Les parts démographiques sont à interpréter avec prudence.",
        "en": "{pop_code}: low sex coverage ({pct}%). Treat demographic shares with caution.",
    },
    "quality_agg_total": {
        "fr": "{pop_code} : agrégation « total » utilisée (pas de detailed disponible).",
        "en": "{pop_code}: using “total” aggregation (no detailed available).",
    },
    "quality_agg_total_ok": {
        "fr": "{pop_code} : reporté au niveau « total » (attendu pour ce type).",
        "en": "{pop_code}: reported at “total” level (expected for this type).",
    },
    "quality_agg_gap": {
        "fr": "{pop_code} : écart detailed vs total de {pct} % sur le mois — vérifier la source.",
        "en": "{pop_code}: detailed vs total gap of {pct}% this month — check the source.",
    },
    "quality_ok": {
        "fr": "Aucun signal d’alerte majeur sur la sélection actuelle.",
        "en": "No major quality alerts for the current selection.",
    },
    "channel_staging": {
        "fr": "Environnement de validation (develop / staging) — la production n’est pas modifiée.",
        "en": "Validation environment (develop / staging) — production is unchanged.",
    },
    "guided_title": {
        "fr": "Parcours recommandé",
        "en": "Recommended path",
    },
    "guided_1": {
        "fr": "1. Flash — Vue d’ensemble (KPI du mois)",
        "en": "1. Flash — Overview (month KPIs)",
    },
    "guided_2": {
        "fr": "2. Fiche pays — zoom asile / Admin",
        "en": "2. Country profile — asylum / Admin zoom",
    },
    "guided_3": {
        "fr": "3. Tendances — MoM et retours",
        "en": "3. Trends — MoM and returnees",
    },
    "guided_4": {
        "fr": "4. Rapports — PDF institutionnels",
        "en": "4. Reports — institutional PDFs",
    },
    "guided_hint_overview": {
        "fr": "Étape 1/4 — Validez les KPI et la qualité, puis ouvrez la fiche pays.",
        "en": "Step 1/4 — Validate KPIs and quality, then open the country profile.",
    },
    "guided_hint_territory": {
        "fr": "Étape 2/4 — Explorez un pays, puis passez aux tendances.",
        "en": "Step 2/4 — Explore a country, then move to trends.",
    },
    "guided_hint_trends": {
        "fr": "Étape 3/4 — Analysez l’évolution, puis générez les PDF.",
        "en": "Step 3/4 — Review the evolution, then generate PDFs.",
    },
    "guided_hint_reports": {
        "fr": "Étape 4/4 — Générez et téléchargez les rapports (audit enregistré).",
        "en": "Step 4/4 — Generate and download reports (audit logged).",
    },
    "audit_title": {
        "fr": "Journal d’audit (exports)",
        "en": "Audit log (exports)",
    },
    "assistant": {
        "fr": "Assistant",
        "en": "Assistant",
    },
    "assistant_intro": {
        "fr": "Posez une question sur les effectifs du mois filtré, le MoM, les tops pays, l’hébergement REF/ASY, le glossaire ou l’utilisation de l’app. Les chiffres viennent des calculs MSR — pas d’invention.",
        "en": "Ask about filtered-month figures, MoM, top countries, REF/ASY accommodation, the glossary, or how to use the app. Figures come from MSR calculations — nothing is invented.",
    },
    "assistant_placeholder": {
        "fr": "Ex. Combien de REF+ASY ce mois ? / Que signifie MoM ?",
        "en": "E.g. How many REF+ASY this month? / What does MoM mean?",
    },
    "assistant_send": {"fr": "Envoyer", "en": "Send"},
    "assistant_clear": {"fr": "Effacer la conversation", "en": "Clear conversation"},
    "assistant_grounded": {
        "fr": "Réponse ancrée sur les données chargées",
        "en": "Answer grounded in loaded data",
    },
}


def t(key: str, lang: str) -> str:
    return STRINGS.get(key, {}).get(lang, key)
