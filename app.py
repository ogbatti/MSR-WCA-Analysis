"""
MSR WCA — Interactive Streamlit dashboard
Monthly Statistical Report — Forced displacement & statelessness (ActivityInfo)
UNHCR-branded UI
"""
from __future__ import annotations

import base64
import html
import importlib
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Force-reload local modules so Streamlit picks up helpers after edits
for _mod_name in (
    "src.theme",
    "src.config",
    "src.reference_data",
    "src.i18n",
    "src.charts",
    "src.indicators",
    "src.narratives",
    "src.forecasting",
    "src.reports",
    "src.data_loader",
):
    if _mod_name in sys.modules:
        importlib.reload(sys.modules[_mod_name])
    else:
        importlib.import_module(_mod_name)

import src.charts as _charts_mod
import src.indicators as _indicators_mod

age_sex_pyramid_chart = _charts_mod.age_sex_pyramid_chart
accommodation_bar = _charts_mod.accommodation_bar
accommodation_share_pie = _charts_mod.accommodation_share_pie
admin2_residence_map = _charts_mod.admin2_residence_map
adult_age_detail_bar = _charts_mod.adult_age_detail_bar
choropleth_hosts = _charts_mod.choropleth_hosts
corridor_map = _charts_mod.corridor_map
forecast_lines = _charts_mod.forecast_lines
mom_yoy_bars = _charts_mod.mom_yoy_bars
monthly_trend_line = _charts_mod.monthly_trend_line
psn_needs_bar = _charts_mod.psn_needs_bar
returns_trend_line = _charts_mod.returns_trend_line
stock_by_type_bar = _charts_mod.stock_by_type_bar
top_bar = _charts_mod.top_bar

admin1_stock = _indicators_mod.admin1_stock
admin2_map_points = _indicators_mod.admin2_map_points
admin2_stock = _indicators_mod.admin2_stock
accommodation_share_ref_asy = _indicators_mod.accommodation_share_ref_asy
accommodation_stock = _indicators_mod.accommodation_stock
age_adult_detail = _indicators_mod.age_adult_detail
age_sex_pyramid = _indicators_mod.age_sex_pyramid
annual_stock = _indicators_mod.annual_stock
corridor_flows = _indicators_mod.corridor_flows
country_pop_breakdown = _indicators_mod.country_pop_breakdown
country_stock = _indicators_mod.country_stock
data_quality_summary = _indicators_mod.data_quality_summary
kpi_snapshot = _indicators_mod.kpi_snapshot
mom_yoy = _indicators_mod.mom_yoy
monthly_stock = _indicators_mod.monthly_stock
origin_stock = _indicators_mod.origin_stock
psn_by_country = _indicators_mod.psn_by_country
psn_by_need = _indicators_mod.psn_by_need
returns_monthly = _indicators_mod.returns_monthly

from src.data_loader import (
    analytical_subset,
    filter_population,
    load_countries,
    load_geoloc,
    load_population,
    load_psn,
    load_total_psn,
)
from src.forecasting import project_multi, scenario_table
from src.i18n import t
from src.narratives import (
    build_forecast_narrative,
    build_overview_narrative,
    build_trend_narrative,
    pop_label,
)
from src.reference_data import format_month_label
from src.theme import APP_CSS

st.set_page_config(
    page_title="MSR WCA · UNHCR",
    page_icon="assets/unhcr_logo.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

LOGO_PATH = ROOT / "assets" / "unhcr_logo.svg"
FLAG_FR_PATH = ROOT / "assets" / "flag_fr.svg"
FLAG_UK_PATH = ROOT / "assets" / "flag_uk.svg"


def _logo_data_uri() -> str | None:
    if not LOGO_PATH.exists():
        return None
    raw = LOGO_PATH.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    mime = "image/svg+xml" if LOGO_PATH.suffix.lower() == ".svg" else "image/png"
    return f"data:{mime};base64,{b64}"


def _flag_data_uri(path: Path) -> str | None:
    if not path.exists():
        return None
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def _language_selector() -> str:
    """Sidebar language picker with SVG flags (reliable on Windows)."""
    if "lang" not in st.session_state:
        st.session_state.lang = "fr"

    fr_uri = _flag_data_uri(FLAG_FR_PATH)
    uk_uri = _flag_data_uri(FLAG_UK_PATH)
    current = st.session_state.lang

    st.sidebar.markdown(
        f"**{t('language', current)}**",
    )
    c_fr, c_en = st.sidebar.columns(2)
    with c_fr:
        if fr_uri:
            st.markdown(
                f'<div class="lang-flag"><img src="{fr_uri}" alt="France" /></div>',
                unsafe_allow_html=True,
            )
        if st.button(
            "FR",
            key="lang_fr",
            use_container_width=True,
            type="primary" if current == "fr" else "secondary",
        ):
            st.session_state.lang = "fr"
            st.rerun()
    with c_en:
        if uk_uri:
            st.markdown(
                f'<div class="lang-flag"><img src="{uk_uri}" alt="United Kingdom" /></div>',
                unsafe_allow_html=True,
            )
        if st.button(
            "EN",
            key="lang_en",
            use_container_width=True,
            type="primary" if current == "en" else "secondary",
        ):
            st.session_state.lang = "en"
            st.rerun()
    return st.session_state.lang


def _inject_brand() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def _render_header(lang: str) -> None:
    logo = _logo_data_uri()
    kicker = "UNHCR · RBWCA · DIMA" if lang == "en" else "HCR · RBWCA · DIMA"
    img = f'<img src="{logo}" alt="UNHCR logo" />' if logo else ""
    st.markdown(
        f"""
        <div class="brand-header">
          {img}
          <div class="brand-text">
            <p class="brand-kicker">{kicker}</p>
            <h1>{t("app_title", lang)}</h1>
            <p class="brand-sub">{t("app_subtitle", lang)}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _kpi_cards(lang: str, kpi: dict) -> None:
    items = [
        (t("kpi_total", lang), _fmt_int(kpi["total"]), None),
        (t("kpi_ref_asy", lang), _fmt_int(kpi.get("ref_asy")), None),
        (t("kpi_idp", lang), _fmt_int(kpi.get("idp")), None),
        (t("kpi_sta", lang), _fmt_int(kpi.get("sta")), None),
        (t("kpi_female", lang), _fmt_pct(kpi["female_share"]), None),
        (t("kpi_children", lang), _fmt_pct(kpi["children_share"]), None),
        (
            t("kpi_mom", lang),
            _fmt_pct(kpi["mom"]),
            _fmt_int(kpi["mom_abs"]) if kpi.get("mom_abs") is not None else None,
        ),
        (t("kpi_hosts", lang), str(kpi["countries"]), None),
    ]
    cards = []
    for label, value, delta in items:
        delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
        cards.append(
            f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>{delta_html}</div>'
        )
    st.markdown(f'<div class="kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)
    st.caption(t("kpi_note_demog", lang))
    cov_f = _fmt_pct(kpi.get("sex_coverage"))
    cov_c = _fmt_pct(kpi.get("age_coverage"))
    if lang == "fr":
        st.caption(f"Couverture ventilation — sexe : {cov_f} · âge (enfants) : {cov_c}")
    else:
        st.caption(f"Disaggregation coverage — sex: {cov_f} · age (children): {cov_c}")


def _md_to_html(text: str) -> str:
    """Lightweight markdown → HTML for narrative boxes."""
    escaped = html.escape(text)
    escaped = re.sub(r"^### (.+)$", r"<h4>\1</h4>", escaped, flags=re.MULTILINE)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?m)^- (.+)$", r"• \1", escaped)
    escaped = escaped.replace("\n\n", "<br/><br/>").replace("\n", "<br/>")
    return escaped


def _narrative_box(text: str) -> None:
    st.markdown(
        f'<div class="narrative-box">{_md_to_html(text)}</div>',
        unsafe_allow_html=True,
    )


def _fmt_int(n: float | None) -> str:
    if n is None or pd.isna(n):
        return "—"
    return f"{n:,.0f}".replace(",", " ")


def _fmt_pct(n: float | None) -> str:
    if n is None or pd.isna(n):
        return "—"
    return f"{n * 100:.1f}%"


@st.cache_data(show_spinner=False)
def _months(df: pd.DataFrame) -> list[str]:
    return sorted(df["year_month"].dropna().unique().tolist())


def _about_content(lang: str) -> None:
    if lang == "fr":
        st.markdown(
            """
### À propos de l'application

Ce tableau de bord présente le **MSR** (*Monthly Statistical Report* /
**Rapport statistique mensuel**) du HCR pour la région **Afrique de l'Ouest
et du Centre (WCA / RBWCA)**. Il permet d'explorer la **population totale**
de personnes relevant du mandat du HCR (réfugiés, demandeurs d'asile, PDI,
apatrides, etc.), ses tendances, sa géographie et des scénarios de projection.

**Fonctionnalités principales**
- Indicateurs clés séparés (total, REF+ASY, PDI, apatrides) et parts démographiques sur populations ventilées
- Qualité des données, export CSV, tendances MoM/YoY et flux de retours (RET/RDP)
- Cartes WCA, corridors REF/ASY, hotspots Admin1 et fiche pays
- Hébergement (camp / hors camp) et Personnes ayant des besoins spécifiques (PSN)
- Projection illustrative jusqu'en 2036 (hypothèses métier, historique court)

### Sources de données

| Source | Contenu |
|--------|---------|
| **ActivityInfo** — base *WCA DIMA Statistics & Analysis* | Formulaire `population` : effectifs mensuels par type, sexe/âge, origine × asile, Admin1/2 |
| Référentiels ActivityInfo | Pays WCA, types de population, géolocalisation |
| Enrichissement local | Centroïdes des origines hors WCA les plus importantes (Soudan, Rwanda, etc.) pour les corridors |

**Méthode d'agrégation :** priorité aux lignes `detailed` (admin / localité) ;
bascule automatique sur `total` pour les types uniquement reportés à ce niveau
(ex. PDI, apatrides), sans mélanger les niveaux d'agrégation au sein d'un même type.

### Glossaire

| Acronyme | Signification |
|----------|----------------|
| **MSR** | *Monthly Statistical Report* — Rapport statistique mensuel |
| **UNHCR / HCR** | Haut-Commissariat des Nations Unies pour les réfugiés |
| **WCA / RBWCA** | *West and Central Africa* / Bureau régional Afrique de l'Ouest et du Centre |
| **DIMA** | *Data, Identity Management and Analysis* (données, gestion d'identité et analyse) |
| **REF** | Réfugiés |
| **ASY** | Demandeurs d'asile |
| **IDP / PDI** | Personnes déplacées internes |
| **STA** | Apatrides |
| **RET** | Réfugiés rapatriés |
| **RDP** | PDI de retour |
| **OOC** | Autres personnes relevant du mandat (*Others of concern*) |
| **NOC** | Hors mandat (*Not of concern*) |
| **MoM** | Variation d'un mois sur l'autre (*Month-over-Month*) |
| **YoY** | Variation d'une année sur l'autre (*Year-over-Year*) |
| **Admin1 / Admin2** | Subdivisions administratives (région / département, selon le pays) |
| **ISO3** | Code pays à 3 lettres (norme ISO 3166-1 alpha-3) |
| **HCR3** | Code pays interne HCR (ex. CHD, NIG, BKF) |
| **PSN** | *Persons with Specific Needs* — Personnes ayant des besoins spécifiques |
            """
        )
    else:
        st.markdown(
            """
### About this application

This dashboard presents the **MSR** (**Monthly Statistical Report**) of UNHCR
for the **West and Central Africa (WCA / RBWCA)** region. It explores the
**total population** of people of concern (refugees, asylum-seekers, IDPs,
stateless persons, etc.), trends, geography and scenario projections.

**Main features**
- Split KPIs (total, REF+ASY, IDPs, stateless) and demographic shares on disaggregated populations only
- Data quality, CSV export, MoM/YoY trends and returnee flows (RET/RDP)
- WCA maps, REF/ASY corridors, Admin1 hotspots and country profile
- Accommodation (camp / out-of-camp) and Persons with Specific Needs (PSN)
- Illustrative projection to 2036 (business assumptions, short history)

### Data sources

| Source | Content |
|--------|---------|
| **ActivityInfo** — *WCA DIMA Statistics & Analysis* | `population` form: monthly figures by type, sex/age, origin × asylum, Admin1/2 |
| ActivityInfo references | WCA countries, population types, geolocation |
| Local enrichment | Centroids for major non-WCA origins (Sudan, Rwanda, etc.) for corridor maps |

**Aggregation method:** prefer `detailed` rows (admin / locality);
automatically fall back to `total` for types only reported at that level
(e.g. IDPs, stateless), without mixing aggregation levels within a type.

### Glossary

| Acronym | Meaning |
|---------|---------|
| **MSR** | Monthly Statistical Report |
| **UNHCR** | United Nations High Commissioner for Refugees |
| **WCA / RBWCA** | West and Central Africa / Regional Bureau |
| **DIMA** | Data, Identity Management and Analysis |
| **REF** | Refugees |
| **ASY** | Asylum-seekers |
| **IDP** | Internally Displaced Persons |
| **STA** | Stateless persons |
| **RET** | Refugee returnees |
| **RDP** | IDP returnees |
| **OOC** | Others of concern |
| **NOC** | Not of concern |
| **MoM** | Month-over-Month change |
| **YoY** | Year-over-Year change |
| **Admin1 / Admin2** | Administrative subdivisions |
| **ISO3** | ISO 3166-1 alpha-3 country code |
| **HCR3** | UNHCR internal country code (e.g. CHD, NIG, BKF) |
| **PSN** | Persons with Specific Needs |
            """
        )


def main() -> None:
    _inject_brand()

    lang = _language_selector()

    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), width=160)
    st.sidebar.markdown(f"**{t('filters', lang)}**")

    _render_header(lang)

    force = st.sidebar.button(t("refresh", lang))
    try:
        pop = load_population(force_refresh=force)
        countries = load_countries()
        try:
            geoloc = load_geoloc()
        except Exception:  # noqa: BLE001
            geoloc = pd.DataFrame()
        try:
            psn_raw = load_psn()
            total_psn_raw = load_total_psn()
        except Exception:  # noqa: BLE001
            psn_raw = pd.DataFrame()
            total_psn_raw = pd.DataFrame()
    except Exception as exc:  # noqa: BLE001
        st.error(f"{t('loading_error', lang)}\n\n`{exc}`")
        st.stop()

    wca_iso3 = (
        countries["iso3"].dropna().astype(str).str.upper().unique().tolist()
        if "iso3" in countries.columns
        else []
    )

    base = analytical_subset(pop)
    if base.empty:
        st.warning("No analytical rows found.")
        st.stop()

    months = _months(base)
    month_labels = [format_month_label(m, lang) for m in months]
    label_to_ym = dict(zip(month_labels, months))

    month_label = st.sidebar.selectbox(
        t("month", lang),
        options=month_labels,
        index=len(month_labels) - 1,
        key="ref_month_label",
    )
    month = label_to_ym[month_label]
    ref_idx = months.index(month)
    # Default comparison = previous month (MoM), relative to the selected reference month
    mom_default = months[ref_idx - 1] if ref_idx > 0 else months[ref_idx]
    mom_label = format_month_label(mom_default, lang)

    if st.session_state.get("_ref_for_compare") != month:
        st.session_state["_ref_for_compare"] = month
        st.session_state["compare_month_label"] = mom_label
    elif st.session_state.get("compare_month_label") not in month_labels:
        # Language switch: rematch to MoM default for current reference
        st.session_state["compare_month_label"] = mom_label

    compare_label = st.sidebar.selectbox(
        t("compare_month", lang),
        options=month_labels,
        key="compare_month_label",
    )
    st.sidebar.caption(
        "Par défaut : mois précédent (MoM)"
        if lang == "fr"
        else "Default: previous month (MoM)"
    )
    compare_month = label_to_ym[compare_label]

    pop_options = sorted(base["pop_code"].dropna().unique().tolist())
    default_pops = [c for c in ["REF", "ASY", "IDP", "STA"] if c in pop_options] or pop_options
    pop_codes = st.sidebar.multiselect(
        t("pop_types", lang),
        options=pop_options,
        default=default_pops,
        format_func=lambda c: f"{c} — {pop_label(c, lang)}",
    )

    host_options = (
        base[["asylum_iso3", "asylum_name_en", "asylum_name_fr"]]
        .dropna(subset=["asylum_iso3"])
        .drop_duplicates()
        .sort_values("asylum_name_en")
    )
    if wca_iso3:
        host_options = host_options[host_options["asylum_iso3"].isin(wca_iso3)]
    host_label = "asylum_name_fr" if lang == "fr" else "asylum_name_en"
    host_map = dict(zip(host_options["asylum_iso3"], host_options[host_label]))
    selected_hosts = st.sidebar.multiselect(
        t("host_countries", lang),
        options=host_options["asylum_iso3"].tolist(),
        default=[],
        format_func=lambda c: host_map.get(c, c),
    )

    origin_options = (
        base[["origin_hcr3", "origin_name_en", "origin_name_fr"]]
        .drop_duplicates()
        .sort_values("origin_hcr3")
    )
    origin_label_col = "origin_name_fr" if lang == "fr" else "origin_name_en"
    origin_map = {
        r["origin_hcr3"]: (r[origin_label_col] or r["origin_hcr3"])
        for _, r in origin_options.iterrows()
    }
    selected_origins = st.sidebar.multiselect(
        t("origins", lang),
        options=origin_options["origin_hcr3"].tolist(),
        default=[],
        format_func=lambda c: f"{c} — {origin_map.get(c, c)}",
    )

    if not pop_codes:
        st.info(
            "Select at least one population type."
            if lang == "en"
            else "Sélectionnez au moins un type de population."
        )
        st.stop()

    filtered_all = filter_population(
        base,
        pop_codes=pop_codes,
        asylum_iso3=selected_hosts or None,
        origin_hcr3=selected_origins or None,
        aggregation=None,
    )
    current = filtered_all[filtered_all["year_month"] == month]
    previous = filtered_all[filtered_all["year_month"] == compare_month]
    kpi = kpi_snapshot(current, previous)

    (
        tab_overview,
        tab_trends,
        tab_maps,
        tab_territory,
        tab_shelter,
        tab_reports,
        tab_forecast,
        tab_about,
    ) = st.tabs(
        [
            t("overview", lang),
            t("trends", lang),
            t("maps", lang),
            t("territory", lang),
            t("shelter_psn", lang),
            t("reports", lang),
            t("forecast", lang),
            t("about", lang),
        ]
    )

    with tab_overview:
        _kpi_cards(lang, kpi)

        by_type = (
            current.groupby("pop_code", as_index=False)[["total", "female", "male", "children"]]
            .sum()
            .sort_values("total", ascending=False)
        )
        hosts = country_stock(current, name_col=host_label)
        origins = origin_stock(current)
        o_name = "origin_name_fr" if lang == "fr" else "origin_name_en"
        hosts_agg = (
            hosts.groupby(["asylum_iso3", host_label], as_index=False)["total"]
            .sum()
            .sort_values("total", ascending=False)
        )
        origins_agg = (
            origins.groupby(["origin_hcr3", o_name], as_index=False)["total"]
            .sum()
            .sort_values("total", ascending=False)
        )

        left, right = st.columns(2)
        with left:
            st.plotly_chart(stock_by_type_bar(by_type, lang), width="stretch")
        with right:
            table = by_type.assign(
                pop=lambda d: d["pop_code"].map(lambda c: pop_label(c, lang))
            )[["pop", "total", "female", "male", "children"]].rename(
                columns={
                    "pop": t("pop_types", lang),
                    "total": t("total_population", lang),
                    "female": "Female" if lang == "en" else "Femmes",
                    "male": "Male" if lang == "en" else "Hommes",
                    "children": "Children" if lang == "en" else "Enfants",
                }
            )
            st.dataframe(table, width="stretch", hide_index=True)

        host_col, origin_col = st.columns(2)
        with host_col:
            st.plotly_chart(
                top_bar(hosts_agg, host_label, t("top_hosts", lang), lang=lang),
                width="stretch",
            )
        with origin_col:
            st.plotly_chart(
                top_bar(origins_agg, o_name, t("top_origins", lang), lang=lang),
                width="stretch",
            )

        pyramid = age_sex_pyramid(current)
        if not pyramid.empty and (pyramid["female"].sum() + pyramid["male"].sum()) > 0:
            st.plotly_chart(age_sex_pyramid_chart(pyramid, lang), width="stretch")
        adult = age_adult_detail(current)
        if not adult.empty and adult["total"].sum() > 0:
            with st.expander(t("adult_age_detail", lang)):
                st.plotly_chart(adult_age_detail_bar(adult, lang), width="stretch")
                st.dataframe(
                    adult.rename(
                        columns={
                            "age_band": "Tranche" if lang == "fr" else "Age band",
                            "female": "Femmes" if lang == "fr" else "Female",
                            "male": "Hommes" if lang == "fr" else "Male",
                            "total": t("total_population", lang),
                        }
                    ),
                    width="stretch",
                    hide_index=True,
                )

        with st.expander(t("data_quality", lang)):
            q = data_quality_summary(current)
            if q.empty:
                st.info("—")
            else:
                q_show = q.assign(
                    pop=lambda d: d["pop_code"].map(lambda c: pop_label(c, lang)),
                    sex_coverage=lambda d: (d["sex_coverage"] * 100).round(1),
                    age_coverage=lambda d: (d["age_coverage"] * 100).round(1),
                )[["pop", "total", "sex_coverage", "age_coverage", "aggregation"]].rename(
                    columns={
                        "pop": t("pop_types", lang),
                        "total": t("total_population", lang),
                        "sex_coverage": "% sexe" if lang == "fr" else "% sex",
                        "age_coverage": "% âge" if lang == "fr" else "% age",
                        "aggregation": "Aggregation",
                    }
                )
                st.dataframe(q_show, width="stretch", hide_index=True)

        export_cols = [
            c
            for c in [
                "year_month",
                "pop_code",
                "asylum_iso3",
                "asylum_name_en",
                "asylum_name_fr",
                "origin_hcr3",
                "origin_name_en",
                "origin_name_fr",
                "coa_admin1",
                "coa_admin2",
                "accommodation_type",
                "aggregation_type",
                "total",
                "female",
                "male",
                "children",
            ]
            if c in current.columns
        ]
        csv_bytes = current[export_cols].to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            t("export_csv", lang),
            data=csv_bytes,
            file_name=f"msr_wca_{month}.csv",
            mime="text/csv",
        )

        narrative = build_overview_narrative(
            lang=lang,
            month=month_label,
            kpi=kpi,
            top_hosts=list(zip(hosts_agg[host_label], hosts_agg["total"])),
            top_origins=list(zip(origins_agg[o_name].fillna("—"), origins_agg["total"])),
            pop_codes=pop_codes,
        )
        _narrative_box(narrative)

    with tab_trends:
        monthly = monthly_stock(filtered_all)
        trend = mom_yoy(monthly, pop_codes=pop_codes)
        st.plotly_chart(monthly_trend_line(monthly, lang), width="stretch")
        st.caption(t("monthly_change_help", lang))
        st.plotly_chart(mom_yoy_bars(trend, lang), width="stretch")

        # Returns on full analytical base (not limited to selected stock types)
        returns_src = filter_population(
            base,
            pop_codes=["RET", "RDP"],
            asylum_iso3=selected_hosts or None,
            aggregation=None,
        )
        ret = returns_monthly(returns_src)
        if not ret.empty:
            st.plotly_chart(returns_trend_line(ret, lang), width="stretch")

        focus = ", ".join(pop_label(c, lang) for c in pop_codes)
        _narrative_box(build_trend_narrative(lang, trend, focus))

        with st.expander("MoM / YoY table"):
            show = trend.copy()
            if "date" in show.columns:
                show["date"] = pd.to_datetime(show["date"]).dt.strftime("%Y-%m-%d")
            for col in ["mom", "yoy", "female_share", "children_share"]:
                if col in show.columns:
                    show[col] = show[col].map(
                        lambda x: None if pd.isna(x) else round(x * 100, 2)
                    )
            st.dataframe(show, width="stretch", hide_index=True)

    with tab_maps:
        breakdown = country_pop_breakdown(current, lang=lang)
        if wca_iso3:
            breakdown = breakdown[breakdown["asylum_iso3"].isin(wca_iso3)]
        # Corridors: REF/ASY only (avoid IDP same-country noise)
        corridor_src = current[current["pop_code"].isin(["REF", "ASY"])]
        if corridor_src.empty:
            corridor_src = current
        flows = corridor_flows(
            corridor_src, top_n=30, wca_iso3=wca_iso3 or None, extra_external=15
        )

        st.plotly_chart(
            choropleth_hosts(breakdown, lang, wca_iso3=wca_iso3 or None),
            width="stretch",
        )
        st.plotly_chart(corridor_map(flows, lang), width="stretch")

    with tab_territory:
        profile_options = host_options["asylum_iso3"].tolist()
        profile_iso = st.selectbox(
            t("select_country", lang),
            options=[""] + profile_options,
            format_func=lambda c: (
                ("— " + ("choisir un pays" if lang == "fr" else "select a country") + " —")
                if c == ""
                else host_map.get(c, c)
            ),
            key="profile_iso",
        )

        a1 = admin1_stock(current)

        if profile_iso:
            country_df = current[current["asylum_iso3"] == profile_iso]
            country_name = host_map.get(profile_iso, profile_iso)
            st.subheader(f"{t('country_profile', lang)} — {country_name}")
            c_kpi = kpi_snapshot(country_df, previous[previous["asylum_iso3"] == profile_iso])
            k1, k2, k3, k4 = st.columns(4)
            k1.metric(t("kpi_total", lang), _fmt_int(c_kpi["total"]))
            k2.metric(t("kpi_ref_asy", lang), _fmt_int(c_kpi.get("ref_asy")))
            k3.metric(t("kpi_idp", lang), _fmt_int(c_kpi.get("idp")))
            k4.metric(t("kpi_mom", lang), _fmt_pct(c_kpi.get("mom")))

            points = admin2_map_points(
                country_df, geoloc, profile_iso, countries_df=countries
            )
            st.plotly_chart(
                admin2_residence_map(points, lang, country_name),
                width="stretch",
            )
            if points.empty:
                st.caption(
                    "Aucune coordonnée disponible pour ce pays (centroïde introuvable)."
                    if lang == "fr"
                    else "No coordinates available for this country (centroid not found)."
                )
            elif "geo_level" in points.columns and (points["geo_level"] == "country").all():
                st.caption(
                    "Localisation approximative au centroïde du pays (Admin1/2 indisponibles)."
                    if lang == "fr"
                    else "Approximate location at country centroid (Admin1/2 unavailable)."
                )

            c_by_type = (
                country_df.groupby("pop_code", as_index=False)["total"]
                .sum()
                .sort_values("total", ascending=False)
            )
            c_orig = origin_stock(country_df)
            c_o = "origin_name_fr" if lang == "fr" else "origin_name_en"
            c_orig_agg = (
                c_orig.groupby(["origin_hcr3", c_o], as_index=False)["total"]
                .sum()
                .sort_values("total", ascending=False)
            )
            pc1, pc2 = st.columns(2)
            with pc1:
                st.plotly_chart(stock_by_type_bar(c_by_type, lang), width="stretch")
                pyr = age_sex_pyramid(country_df)
                if not pyr.empty and (pyr["female"].sum() + pyr["male"].sum()) > 0:
                    st.plotly_chart(age_sex_pyramid_chart(pyr, lang), width="stretch")
            with pc2:
                st.plotly_chart(
                    top_bar(c_orig_agg, c_o, t("top_origins", lang), lang=lang),
                    width="stretch",
                )

            a1_c = a1[a1["asylum_iso3"] == profile_iso] if not a1.empty else a1
            a2_c = admin2_stock(country_df)
            col_a, col_b = st.columns(2)
            with col_a:
                if a1_c.empty:
                    st.markdown(f"**{t('admin1', lang)}**")
                    st.info("—")
                else:
                    top_a1 = a1_c.groupby("coa_admin1", as_index=False)["total"].sum()
                    st.plotly_chart(
                        top_bar(
                            top_a1.sort_values("total", ascending=False),
                            "coa_admin1",
                            t("admin1", lang),
                            n=15,
                            lang=lang,
                        ),
                        width="stretch",
                    )
            with col_b:
                if a2_c.empty:
                    st.markdown(f"**{t('admin2', lang)}**")
                    st.info("—")
                else:
                    top_a2 = a2_c.groupby(["coa_admin2", "coa_admin1"], as_index=False)[
                        "total"
                    ].sum()
                    top_a2["label"] = (
                        top_a2["coa_admin2"].astype(str)
                        + " / "
                        + top_a2["coa_admin1"].astype(str)
                    )
                    st.plotly_chart(
                        top_bar(
                            top_a2.sort_values("total", ascending=False),
                            "label",
                            t("admin2", lang),
                            n=15,
                            lang=lang,
                        ),
                        width="stretch",
                    )
        else:
            st.info(
                "Sélectionnez un pays pour afficher la fiche détaillée."
                if lang == "fr"
                else "Select a country to display the detailed profile."
            )

    with tab_shelter:
        acc_share = accommodation_share_ref_asy(current)
        if not acc_share.empty:
            st.plotly_chart(accommodation_share_pie(acc_share, lang), width="stretch")
            order = ["out-of-camp", "camp", "unknown"]
            share_sorted = acc_share.copy()
            share_sorted["_ord"] = share_sorted["accommodation_type"].map(
                {k: i for i, k in enumerate(order)}
            ).fillna(99)
            share_sorted = share_sorted.sort_values("_ord")
            cols = st.columns(len(share_sorted))
            for col, (_, row) in zip(cols, share_sorted.iterrows()):
                label = {
                    "camp": "Camp / sites aménagés" if lang == "fr" else "Camp / planned sites",
                    "out-of-camp": "Hors camp / zones urbaines" if lang == "fr" else "Out of camp / urban areas",
                    "unknown": "Inconnu / non renseigné" if lang == "fr" else "Unknown / not reported",
                }.get(row["accommodation_type"], row["accommodation_type"])
                col.metric(label, f"{row['share']*100:.1f}%", _fmt_int(row["total"]))

        acc = accommodation_stock(current)
        with st.expander(
            (t("accommodation", lang) + " — détail")
            if lang == "fr"
            else (t("accommodation", lang) + " — detail")
        ):
            st.plotly_chart(accommodation_bar(acc, lang), width="stretch")
            if not acc.empty:
                acc_show = acc.copy()
                acc_show["pop"] = acc_show["pop_code"].map(lambda c: pop_label(c, lang))
                st.dataframe(
                    acc_show[["accommodation_type", "pop", "total"]].rename(
                        columns={
                            "accommodation_type": t("accommodation", lang),
                            "pop": t("pop_types", lang),
                            "total": t("total_population", lang),
                        }
                    ),
                    width="stretch",
                    hide_index=True,
                )

        st.caption(t("psn_note", lang))
        psn_m = (
            psn_raw[psn_raw["year_month"] == month]
            if not psn_raw.empty and "year_month" in psn_raw.columns
            else pd.DataFrame()
        )
        tpsn_m = (
            total_psn_raw[total_psn_raw["year_month"] == month]
            if not total_psn_raw.empty and "year_month" in total_psn_raw.columns
            else pd.DataFrame()
        )
        if selected_hosts:
            if not psn_m.empty:
                psn_m = psn_m[psn_m["asylum_iso3"].isin(selected_hosts)]
            if not tpsn_m.empty:
                tpsn_m = tpsn_m[tpsn_m["asylum_iso3"].isin(selected_hosts)]

        psn_total_val = float(tpsn_m["total"].sum()) if not tpsn_m.empty else (
            float(psn_m["total"].sum()) if not psn_m.empty else 0.0
        )
        st.metric(t("psn_total", lang), _fmt_int(psn_total_val))

        s1, s2 = st.columns(2)
        with s1:
            needs = psn_by_need(psn_m)
            st.plotly_chart(psn_needs_bar(needs, lang), width="stretch")
        with s2:
            by_c = psn_by_country(tpsn_m if not tpsn_m.empty else psn_m, lang=lang)
            if by_c.empty:
                st.info("—")
            else:
                name_c = "asylum_name_fr" if lang == "fr" else "asylum_name_en"
                if name_c not in by_c.columns:
                    name_c = [c for c in by_c.columns if c.startswith("asylum_name")][0]
                agg_c = (
                    by_c.groupby(name_c, as_index=False)["total"]
                    .sum()
                    .sort_values("total", ascending=False)
                )
                st.plotly_chart(
                    top_bar(agg_c, name_c, t("psn_by_country", lang), lang=lang),
                    width="stretch",
                )

    with tab_reports:
        from src.reports import BUILDERS, REPORT_CATALOG

        st.caption(t("reports_intro", lang))
        report_country = st.selectbox(
            t("report_country", lang),
            options=[""] + host_options["asylum_iso3"].tolist(),
            format_func=lambda c: (
                ("— " + ("choisir un pays" if lang == "fr" else "select a country") + " —")
                if c == ""
                else host_map.get(c, c)
            ),
            key="report_country_iso",
        )

        def _build_report(rid: str) -> bytes:
            if rid == "flash":
                return BUILDERS[rid](
                    lang=lang,
                    month=month,
                    month_label=month_label,
                    current=current,
                    previous=previous,
                    pop_codes=pop_codes,
                )
            if rid == "country":
                return BUILDERS[rid](
                    lang=lang,
                    month_label=month_label,
                    country_iso3=report_country,
                    country_name=host_map.get(report_country, report_country),
                    current=current,
                    previous=previous,
                )
            if rid == "trend":
                return BUILDERS[rid](
                    lang=lang,
                    filtered_all=filtered_all,
                    pop_codes=pop_codes,
                    base=base,
                    selected_hosts=selected_hosts or None,
                )
            if rid == "corridors":
                return BUILDERS[rid](
                    lang=lang,
                    month_label=month_label,
                    current=current,
                    wca_iso3=wca_iso3 or None,
                )
            if rid == "methodology":
                return BUILDERS[rid](lang=lang, current=current)
            if rid == "shelter":
                return BUILDERS[rid](
                    lang=lang, month_label=month_label, current=current
                )
            if rid == "psn":
                return BUILDERS[rid](
                    lang=lang,
                    month=month,
                    month_label=month_label,
                    psn_raw=psn_raw,
                    total_psn_raw=total_psn_raw,
                    selected_hosts=selected_hosts or None,
                )
            return b""

        for meta in REPORT_CATALOG:
            rid = meta["id"]
            st.markdown(f"**{meta['title'][lang]}**")
            st.caption(meta["desc"][lang])
            needs_country = meta.get("needs_country", False)
            if needs_country and not report_country:
                st.info(
                    "Sélectionnez un pays ci-dessus pour activer ce rapport."
                    if lang == "fr"
                    else "Select a country above to enable this report."
                )
            else:
                gen_key = f"gen_{rid}"
                pdf_key = f"pdf_bytes_{rid}"
                c1, c2 = st.columns([1, 2])
                with c1:
                    if st.button(
                        "Générer" if lang == "fr" else "Generate",
                        key=gen_key,
                    ):
                        try:
                            st.session_state[pdf_key] = _build_report(rid)
                        except Exception as exc:  # noqa: BLE001
                            st.session_state.pop(pdf_key, None)
                            st.error(f"{meta['title'][lang]}: {exc}")
                with c2:
                    if pdf_key in st.session_state and st.session_state[pdf_key]:
                        st.download_button(
                            t("download_pdf", lang),
                            data=st.session_state[pdf_key],
                            file_name=f"msr_wca_{rid}_{month}.pdf",
                            mime="application/pdf",
                            key=f"dl_{rid}",
                        )
            st.markdown("---")

    with tab_forecast:
        st.info(t("forecast_disclaimer", lang))
        st.subheader(t("assumptions", lang))
        st.dataframe(scenario_table(lang), width="stretch", hide_index=True)

        fc_pops = st.multiselect(
            t("forecast_pop", lang),
            options=pop_codes,
            default=[c for c in ["REF", "IDP", "STA"] if c in pop_codes] or pop_codes[:1],
            format_func=lambda c: f"{c} — {pop_label(c, lang)}",
            key="fc_pops",
        )
        g1, g2, g3, g4 = st.columns(4)
        growth = g1.slider(t("growth", lang), -0.05, 0.10, 0.015, 0.005)
        conflict = g2.slider(t("conflict", lang), 0.0, 0.15, 0.02, 0.005)
        returns = g3.slider(t("returns", lang), 0.0, 0.15, 0.025, 0.005)
        horizon = g4.slider(t("horizon", lang), 2027, 2036, 2036, 1)

        annual = annual_stock(filtered_all, pop_codes=fc_pops)
        if annual.empty:
            st.warning(
                "Historique annuel insuffisant."
                if lang == "fr"
                else "Insufficient annual history."
            )
        else:
            forecast = project_multi(
                annual,
                pop_codes=fc_pops,
                horizon_year=horizon,
                growth=growth,
                conflict=conflict,
                returns=returns,
            )
            st.plotly_chart(forecast_lines(forecast, lang), width="stretch")

            focus_code = fc_pops[0] if fc_pops else "REF"
            narrative = build_forecast_narrative(
                lang,
                forecast[forecast["pop_code"] == focus_code],
                focus_code,
                horizon,
            )
            _narrative_box(narrative)
            with st.expander(t("scenario_compare", lang)):
                st.dataframe(
                    forecast.sort_values(["pop_code", "scenario", "year"]),
                    width="stretch",
                    hide_index=True,
                )

    with tab_about:
        _about_content(lang)

    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"WCA: {len(countries)} pays · {len(base):,} lignes · "
        f"{base['date'].min().date()} → {base['date'].max().date()}"
    )
    credit = "© UNHCR · Source: ActivityInfo — WCA DIMA Statistics & Analysis"
    st.markdown(f'<div class="footer-credit">{credit}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
