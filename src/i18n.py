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
        "fr": "Carte des zones de résidence (Admin2 → Admin1 → pays)",
        "en": "Residence areas map (Admin2 → Admin1 → country)",
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
    "kpi_female": {"fr": "% Femmes*", "en": "% Female*"},
    "kpi_children": {"fr": "% Enfants*", "en": "% Children*"},
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
    "composition_map": {
        "fr": "Composition par type (camemberts — pays d'asile WCA)",
        "en": "Composition by type (pie markers — WCA host countries)",
    },
    "registration_ref_asy": {
        "fr": "Enregistrement REF + ASY",
        "en": "REF + ASY registration",
    },
    "registration_registered": {
        "fr": "Enregistrés individuellement",
        "en": "Individually registered",
    },
    "registration_not_registered": {
        "fr": "Non enregistrés individuellement",
        "en": "Not individually registered",
    },
    "registration_note": {
        "fr": "Basé sur le champ ActivityInfo « basis » : registration = enregistré individuellement ; autres bases (estimate, census, pre-registration, survey…) = non enregistré individuellement.",
        "en": "Based on the ActivityInfo “basis” field: registration = individually registered; other bases (estimate, census, pre-registration, survey…) = not individually registered.",
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
}


def t(key: str, lang: str) -> str:
    return STRINGS.get(key, {}).get(lang, key)
