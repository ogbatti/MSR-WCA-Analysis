"""Plotly chart helpers — UNHCR brand styling."""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from folium.features import GeoJson, GeoJsonTooltip

from src.config import POP_TYPE_LABELS, ROOT
from src.theme import (
    BLUE_01,
    BLUE_02,
    BLUE_03,
    BLUE_04,
    BLUE_05,
    BLUE_06,
    BLUE_PRIMARY,
    CHOROPLETH_BLUES,
    GREEN_PRIMARY,
    GREY_02,
    GREY_03,
    RED_PRIMARY,
    SCENARIO_COLORS,
    YELLOW_PRIMARY,
    apply_unhcr_layout,
    pop_color,
)

# Dark → light blue ramp for composition pie slices (by preferred pop order)
_COMPOSITION_BLUE_RAMP = [
    BLUE_06,
    BLUE_05,
    BLUE_04,
    BLUE_03,
    BLUE_02,
    BLUE_01,
    GREY_02,
    "#E5E5E5",
]
_POP_ORDER = ["REF", "ASY", "IDP", "STA", "RET", "RDP", "OOC", "NOC"]
_WORLD_COUNTRIES_PATH = ROOT / "assets" / "world_countries.json"


@lru_cache(maxsize=1)
def _world_countries_geojson() -> dict | None:
    """Load Natural-Earth style world countries GeoJSON (feature id = ISO3)."""
    if not _WORLD_COUNTRIES_PATH.exists():
        return None
    try:
        with _WORLD_COUNTRIES_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return None


def _feature_iso3(feature: dict) -> str:
    props = feature.get("properties") or {}
    for key in ("id", "ISO_A3", "iso_a3", "ADM0_A3", "ISO3"):
        if key == "id":
            val = feature.get("id")
        else:
            val = props.get(key)
        if val and str(val).upper() not in {"", "-99", "NONE", "NULL"}:
            return str(val).upper()
    return ""


def _add_wca_region_layer(fmap: folium.Map, wca_iso3: list[str] | None) -> None:
    """Highlight WCA countries and grey out the rest of the world."""
    geo = _world_countries_geojson()
    if not geo or not wca_iso3:
        return
    wca = {str(c).upper() for c in wca_iso3 if c}

    def style_fn(feature: dict) -> dict:
        iso = _feature_iso3(feature)
        if iso in wca:
            return {
                "fillColor": BLUE_01,
                "color": BLUE_PRIMARY,
                "weight": 1.6,
                "fillOpacity": 0.42,
                "opacity": 0.95,
            }
        return {
            "fillColor": GREY_02,
            "color": GREY_03,
            "weight": 0.35,
            "fillOpacity": 0.55,
            "opacity": 0.7,
        }

    def highlight_fn(feature: dict) -> dict:
        iso = _feature_iso3(feature)
        if iso in wca:
            return {
                "fillColor": BLUE_02,
                "color": BLUE_06,
                "weight": 2.2,
                "fillOpacity": 0.55,
            }
        return {
            "fillColor": GREY_03,
            "color": GREY_03,
            "weight": 0.5,
            "fillOpacity": 0.65,
        }

    GeoJson(
        geo,
        name="WCA region",
        style_function=style_fn,
        highlight_function=highlight_fn,
        tooltip=GeoJsonTooltip(
            fields=["name"],
            aliases=[""],
            labels=False,
            sticky=False,
        ),
        smooth_factor=1.2,
        zoom_on_click=False,
    ).add_to(fmap)

    # Stronger contour only for WCA countries (outline on top)
    wca_only = {
        "type": "FeatureCollection",
        "features": [f for f in geo.get("features", []) if _feature_iso3(f) in wca],
    }
    if wca_only["features"]:
        GeoJson(
            wca_only,
            name="WCA outline",
            style_function=lambda _f: {
                "fillColor": "transparent",
                "fillOpacity": 0,
                "color": BLUE_06,
                "weight": 2.4,
                "opacity": 0.95,
            },
            interactive=False,
            zoom_on_click=False,
        ).add_to(fmap)


def _pop_name(code: str, lang: str) -> str:
    return POP_TYPE_LABELS.get(code, {}).get(lang, code)


def _total_label(lang: str) -> str:
    return "Total population" if lang == "en" else "Population totale"


def stock_by_type_bar(df: pd.DataFrame, lang: str) -> go.Figure:
    d = df.copy()
    d["pop"] = d["pop_code"].map(lambda c: _pop_name(c, lang))
    color_map = {
        _pop_name(code, lang): pop_color(code) for code in d["pop_code"].unique()
    }
    y_lbl = _total_label(lang)
    title = (
        "Total population by type"
        if lang == "en"
        else "Population totale par type"
    )
    fig = px.bar(
        d,
        x="pop",
        y="total",
        color="pop",
        color_discrete_map=color_map,
        labels={"pop": "", "total": y_lbl},
        text_auto=".2s",
        title=title,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    apply_unhcr_layout(fig)
    fig.update_layout(showlegend=False, height=380)
    return fig


def monthly_trend_line(monthly: pd.DataFrame, lang: str) -> go.Figure:
    d = monthly.copy()
    d["pop"] = d["pop_code"].map(lambda c: _pop_name(c, lang))
    color_map = {
        _pop_name(code, lang): pop_color(code) for code in d["pop_code"].unique()
    }
    y_lbl = _total_label(lang)
    title = (
        "Monthly total population trend"
        if lang == "en"
        else "Évolution mensuelle de la population totale"
    )
    fig = px.line(
        d,
        x="date",
        y="total",
        color="pop",
        markers=True,
        color_discrete_map=color_map,
        labels={"date": "Date", "total": y_lbl, "pop": ""},
        title=title,
    )
    apply_unhcr_layout(fig)
    fig.update_layout(height=420, legend_title_text="")
    return fig


def mom_yoy_bars(trend: pd.DataFrame, lang: str) -> go.Figure:
    """
    Clearer alternative to MoM/YoY % bars: absolute month-to-month change
    (people gained/lost), with hover showing MoM % and YoY % when available.
    """
    d = trend.dropna(subset=["mom_abs"]).copy()
    title = (
        "Monthly change in total population (people)"
        if lang == "en"
        else "Variation mensuelle de la population totale (personnes)"
    )
    if d.empty:
        fig = go.Figure()
        apply_unhcr_layout(fig, title=title)
        return fig

    colors = [GREEN_PRIMARY if v >= 0 else RED_PRIMARY for v in d["mom_abs"]]
    custom = []
    for _, r in d.iterrows():
        mom_p = f"{r['mom']*100:.1f}%" if pd.notna(r.get("mom")) else "—"
        yoy_p = f"{r['yoy']*100:.1f}%" if pd.notna(r.get("yoy")) else "—"
        custom.append((mom_p, yoy_p, f"{r['total']:,.0f}"))

    fig = go.Figure(
        go.Bar(
            x=d["year_month"],
            y=d["mom_abs"],
            marker_color=colors,
            customdata=custom,
            hovertemplate=(
                "<b>%{x}</b><br>"
                + ("Change: " if lang == "en" else "Variation : ")
                + "%{y:,.0f}<br>"
                + "MoM: %{customdata[0]}<br>"
                + "YoY: %{customdata[1]}<br>"
                + ("Total: " if lang == "en" else "Total : ")
                + "%{customdata[2]}<extra></extra>"
            ),
        )
    )
    fig.add_hline(y=0, line_width=1, line_color="#666666")
    apply_unhcr_layout(fig, title=title)
    fig.update_layout(
        height=400,
        yaxis_title="Personnes" if lang == "fr" else "People",
        xaxis_title="",
        showlegend=False,
    )
    return fig


def top_bar(
    df: pd.DataFrame, name_col: str, title: str, n: int = 12, lang: str = "en"
) -> go.Figure:
    d = df.head(n).iloc[::-1]
    y_lbl = _total_label(lang)
    fig = px.bar(
        d,
        x="total",
        y=name_col,
        orientation="h",
        labels={"total": y_lbl, name_col: ""},
        text_auto=".2s",
        title=title,
        color_discrete_sequence=[BLUE_PRIMARY],
    )
    fig.update_traces(marker_color=BLUE_PRIMARY, textposition="outside", cliponaxis=False)
    apply_unhcr_layout(fig)
    fig.update_layout(height=440, showlegend=False)
    return fig


def choropleth_hosts(
    breakdown_df: pd.DataFrame,
    lang: str,
    wca_iso3: list[str] | None = None,
) -> go.Figure:
    """
    WCA-only choropleth. Hover shows country name (no ISO) and totals by population type.
    `breakdown_df` from indicators.country_pop_breakdown.
    """
    if breakdown_df is None or breakdown_df.empty:
        return go.Figure()

    d = breakdown_df.copy()
    if "asylum_iso3" not in d.columns:
        return go.Figure()

    if wca_iso3:
        d = d[d["asylum_iso3"].isin(wca_iso3)]
    d = d.dropna(subset=["asylum_iso3"])
    if d.empty:
        return go.Figure()

    y_lbl = _total_label(lang)
    title = (
        "Total population by country of asylum (WCA)"
        if lang == "en"
        else "Population totale par pays d'asile (WCA)"
    )

    skip = {"asylum_iso3", "country_name", "total"}
    pop_cols = [c for c in d.columns if c not in skip]
    # Stable order preferring common MSR types
    preferred = [
        POP_TYPE_LABELS.get(c, {}).get(lang, c)
        for c in ["REF", "ASY", "IDP", "STA", "RET", "RDP", "OOC", "NOC"]
    ]
    pop_cols = [c for c in preferred if c in pop_cols] + [
        c for c in pop_cols if c not in preferred
    ]

    custom = [d["country_name"].tolist()]
    for col in pop_cols:
        custom.append(d[col].tolist())

    hover_lines = ["<b>%{customdata[0]}</b>", f"{y_lbl}: %{{z:,.0f}}"]
    for i, col in enumerate(pop_cols, start=1):
        hover_lines.append(f"{col}: %{{customdata[{i}]:,.0f}}")
    hovertemplate = "<br>".join(hover_lines) + "<extra></extra>"

    fig = go.Figure(
        data=go.Choropleth(
            locations=d["asylum_iso3"],
            z=d["total"],
            locationmode="ISO-3",
            colorscale=CHOROPLETH_BLUES,
            customdata=list(zip(*custom)) if custom else None,
            hovertemplate=hovertemplate,
            colorbar=dict(title=y_lbl),
            marker_line_color="#FFFFFF",
            marker_line_width=0.6,
        )
    )
    apply_unhcr_layout(fig, title=title)
    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=56, b=0),
        geo=dict(
            projection_type="natural earth",
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#8FC1E1",
            showland=True,
            landcolor="#F7FBFE",
            countrycolor="#D0D0D0",
            bgcolor="rgba(0,0,0,0)",
            fitbounds="locations",
            visible=True,
        ),
    )
    return fig


def age_sex_pyramid_chart(pyramid: pd.DataFrame, lang: str) -> go.Figure:
    """Horizontal age–sex pyramid (female left, male right) — UNHCR standard bands."""
    title = (
        "Age–sex pyramid (UNHCR standard bands)"
        if lang == "en"
        else "Pyramide des âges par sexe (tranches standards HCR)"
    )
    if pyramid is None or pyramid.empty:
        fig = go.Figure()
        apply_unhcr_layout(fig, title=title)
        return fig

    d = pyramid.copy()
    female_lbl = "Female" if lang == "en" else "Femmes"
    male_lbl = "Male" if lang == "en" else "Hommes"

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=d["age_band"],
            x=-d["female"],
            orientation="h",
            name=female_lbl,
            marker_color=RED_PRIMARY,
            hovertemplate=f"{female_lbl}: %{{customdata:,.0f}}<extra></extra>",
            customdata=d["female"],
        )
    )
    fig.add_trace(
        go.Bar(
            y=d["age_band"],
            x=d["male"],
            orientation="h",
            name=male_lbl,
            marker_color=BLUE_PRIMARY,
            hovertemplate=f"{male_lbl}: %{{x:,.0f}}<extra></extra>",
        )
    )
    apply_unhcr_layout(fig, title=title)
    max_abs = max(float(d["female"].max() or 0), float(d["male"].max() or 0), 1.0)
    fig.update_layout(
        barmode="overlay",
        height=460,
        xaxis=dict(
            title=_total_label(lang),
            tickvals=[-max_abs, -max_abs / 2, 0, max_abs / 2, max_abs],
            ticktext=[
                f"{max_abs:,.0f}",
                f"{max_abs / 2:,.0f}",
                "0",
                f"{max_abs / 2:,.0f}",
                f"{max_abs:,.0f}",
            ],
        ),
        yaxis=dict(title="" if lang == "en" else "Tranche d'âge", categoryorder="array", categoryarray=list(d["age_band"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return fig


def corridor_map(flows: pd.DataFrame, lang: str) -> go.Figure:
    fig = go.Figure()
    title = (
        "Displacement corridors (origin → asylum)"
        if lang == "en"
        else "Corridors de déplacement (origine → asile)"
    )
    if flows.empty:
        apply_unhcr_layout(fig, title=title)
        fig.update_layout(height=520)
        return fig

    max_t = flows["total"].max() or 1
    o_name = "origin_name_fr" if lang == "fr" else "origin_name_en"
    a_name = "asylum_name_fr" if lang == "fr" else "asylum_name_en"

    for _, r in flows.iterrows():
        if pd.isna(r.get("origin_lat")) or pd.isna(r.get("asylum_lat")):
            continue
        o_lon, o_lat = float(r["origin_lon"]), float(r["origin_lat"])
        a_lon, a_lat = float(r["asylum_lon"]), float(r["asylum_lat"])
        width = 1 + 6 * (r["total"] / max_t)
        # Arrow tip at ~75% of the path toward asylum (origin → asylum)
        ax = o_lon + 0.75 * (a_lon - o_lon)
        ay = o_lat + 0.75 * (a_lat - o_lat)
        hover = (
            f"{r.get(o_name)} → {r.get(a_name)}<br>"
            f"{r.get('pop_code')}: {r['total']:,.0f}"
        )
        fig.add_trace(
            go.Scattergeo(
                lon=[o_lon, a_lon],
                lat=[o_lat, a_lat],
                mode="lines",
                line=dict(width=width, color=RED_PRIMARY),
                opacity=0.55,
                hoverinfo="text",
                text=hover,
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scattergeo(
                lon=[ax],
                lat=[ay],
                mode="markers",
                marker=dict(size=8, color=RED_PRIMARY, symbol="triangle-up"),
                hoverinfo="text",
                text=hover,
                showlegend=False,
            )
        )

    # Origins (open circles) vs asylum (filled)
    origins = (
        flows[["origin_lat", "origin_lon", o_name]]
        .rename(columns={"origin_lat": "lat", "origin_lon": "lon", o_name: "name"})
        .dropna()
        .drop_duplicates()
    )
    asylums = (
        flows[["asylum_lat", "asylum_lon", a_name]]
        .rename(columns={"asylum_lat": "lat", "asylum_lon": "lon", a_name: "name"})
        .dropna()
        .drop_duplicates()
    )
    if not origins.empty:
        fig.add_trace(
            go.Scattergeo(
                lon=origins["lon"],
                lat=origins["lat"],
                text=origins["name"].map(
                    lambda n: f"{'Origin' if lang == 'en' else 'Origine'}: {n}"
                ),
                mode="markers",
                marker=dict(
                    size=8,
                    color="#FFFFFF",
                    line=dict(width=2, color=BLUE_PRIMARY),
                ),
                hoverinfo="text",
                name="Origin" if lang == "en" else "Origine",
            )
        )
    if not asylums.empty:
        fig.add_trace(
            go.Scattergeo(
                lon=asylums["lon"],
                lat=asylums["lat"],
                text=asylums["name"].map(
                    lambda n: f"{'Asylum' if lang == 'en' else 'Asile'}: {n}"
                ),
                mode="markers",
                marker=dict(size=9, color=BLUE_PRIMARY, line=dict(width=1, color="white")),
                hoverinfo="text",
                name="Asylum" if lang == "en" else "Asile",
            )
        )

    apply_unhcr_layout(fig, title=title)
    fig.update_layout(
        height=560,
        margin=dict(l=0, r=0, t=56, b=0),
        legend=dict(orientation="h", y=1.02, x=0),
        geo=dict(
            projection_type="natural earth",
            showland=True,
            landcolor="#F7FBFE",
            showcountries=True,
            countrycolor="#7A7A7A",
            countrywidth=0.8,
            showcoastlines=True,
            coastlinecolor="#8FC1E1",
            coastlinewidth=0.6,
            showlakes=False,
            showframe=False,
            bgcolor="rgba(0,0,0,0)",
            fitbounds="locations",
            lonaxis=dict(range=[-30, 60]),
            lataxis=dict(range=[-35, 40]),
        ),
    )
    return fig


def forecast_lines(forecast: pd.DataFrame, lang: str) -> go.Figure:
    d = forecast.copy()
    title = (
        "Illustrative scenario projection to 2036"
        if lang == "en"
        else "Projection illustrative de scénarios jusqu'en 2036"
    )
    y_lbl = _total_label(lang)
    color_map = {k: SCENARIO_COLORS.get(k, BLUE_PRIMARY) for k in d["scenario"].unique()}
    fig = px.line(
        d,
        x="year",
        y="total",
        color="scenario",
        line_dash="kind",
        markers=True,
        color_discrete_map=color_map,
        labels={
            "year": "Year" if lang == "en" else "Année",
            "total": y_lbl,
            "scenario": "Scenario" if lang == "en" else "Scénario",
        },
        title=title,
    )
    apply_unhcr_layout(fig)
    fig.update_layout(height=460)
    return fig


def accommodation_bar(df: pd.DataFrame, lang: str) -> go.Figure:
    from src.config import ACCOMMODATION_LABELS

    title = (
        "Total population by accommodation type"
        if lang == "en"
        else "Population totale par type d'hébergement"
    )
    if df is None or df.empty:
        fig = go.Figure()
        apply_unhcr_layout(fig, title=title)
        return fig
    d = df.copy()
    d["accommodation"] = d["accommodation_type"].map(
        lambda x: ACCOMMODATION_LABELS.get(x, {}).get(lang, x)
    )
    agg = d.groupby("accommodation", as_index=False)["total"].sum().sort_values("total")
    fig = px.bar(
        agg,
        x="total",
        y="accommodation",
        orientation="h",
        text_auto=".2s",
        title=title,
        labels={"total": _total_label(lang), "accommodation": ""},
        color_discrete_sequence=[BLUE_PRIMARY],
    )
    apply_unhcr_layout(fig)
    fig.update_layout(height=360, showlegend=False)
    return fig


def hotspot_bar(df: pd.DataFrame, lang: str) -> go.Figure:
    title = (
        "Admin1 hotspots — largest MoM absolute change"
        if lang == "en"
        else "Hotspots Admin1 — plus fortes variations MoM (abs.)"
    )
    if df is None or df.empty:
        fig = go.Figure()
        apply_unhcr_layout(fig, title=title)
        return fig
    d = df.copy()
    name = "asylum_name_fr" if lang == "fr" else "asylum_name_en"
    d["label"] = d["coa_admin1"].astype(str) + " (" + d[name].astype(str) + ")"
    d = d.sort_values("mom_abs")
    colors = [RED_PRIMARY if v < 0 else BLUE_PRIMARY for v in d["mom_abs"]]
    fig = go.Figure(
        go.Bar(
            x=d["mom_abs"],
            y=d["label"],
            orientation="h",
            marker_color=colors,
            text=[f"{v:+,.0f}" for v in d["mom_abs"]],
            textposition="outside",
            cliponaxis=False,
        )
    )
    apply_unhcr_layout(fig, title=title)
    fig.update_layout(
        height=480,
        xaxis_title="MoM" if lang == "en" else "Variation MoM",
        yaxis_title="",
        showlegend=False,
    )
    return fig


def returns_trend_line(df: pd.DataFrame, lang: str) -> go.Figure:
    title = (
        "Returnee flows (RET / RDP) — monthly"
        if lang == "en"
        else "Flux de retours (RET / RDP) — mensuel"
    )
    if df is None or df.empty:
        fig = go.Figure()
        apply_unhcr_layout(fig, title=title)
        return fig
    d = df.copy()
    d["pop"] = d["pop_code"].map(lambda c: _pop_name(c, lang))
    color_map = {_pop_name(c, lang): pop_color(c) for c in d["pop_code"].unique()}
    fig = px.line(
        d,
        x="date",
        y="total",
        color="pop",
        markers=True,
        color_discrete_map=color_map,
        title=title,
        labels={"date": "Date", "total": _total_label(lang), "pop": ""},
    )
    apply_unhcr_layout(fig)
    fig.update_layout(height=380, legend_title_text="")
    return fig


def psn_needs_bar(df: pd.DataFrame, lang: str) -> go.Figure:
    from src.config import PSN_NEED_LABELS

    title = (
        "Persons with specific needs by category"
        if lang == "en"
        else "Personnes ayant des besoins spécifiques par catégorie"
    )
    if df is None or df.empty:
        fig = go.Figure()
        apply_unhcr_layout(fig, title=title)
        return fig
    d = df.copy()
    d["need"] = d["sn_code"].map(
        lambda c: PSN_NEED_LABELS.get(c, {}).get(lang, c)
    )
    d = d.sort_values("total").tail(12)
    fig = px.bar(
        d,
        x="total",
        y="need",
        orientation="h",
        text_auto=".2s",
        title=title,
        labels={"total": _total_label(lang), "need": ""},
        color_discrete_sequence=[YELLOW_PRIMARY],
    )
    apply_unhcr_layout(fig)
    fig.update_layout(height=420, showlegend=False)
    return fig


def adult_age_detail_bar(df: pd.DataFrame, lang: str) -> go.Figure:
    """Complementary view of adult sub-bands 18-24 / 25-49 / 50-59."""
    title = (
        "Adult age detail (18–24 / 25–49 / 50–59)"
        if lang == "en"
        else "Détail des âges adultes (18–24 / 25–49 / 50–59)"
    )
    if df is None or df.empty:
        fig = go.Figure()
        apply_unhcr_layout(fig, title=title)
        return fig
    d = df.copy()
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Female" if lang == "en" else "Femmes",
            x=d["age_band"],
            y=d["female"],
            marker_color=RED_PRIMARY,
        )
    )
    fig.add_trace(
        go.Bar(
            name="Male" if lang == "en" else "Hommes",
            x=d["age_band"],
            y=d["male"],
            marker_color=BLUE_PRIMARY,
        )
    )
    apply_unhcr_layout(fig, title=title)
    fig.update_layout(barmode="group", height=360, yaxis_title=_total_label(lang))
    return fig


def accommodation_share_pie(df: pd.DataFrame, lang: str) -> go.Figure:
    from src.config import ACCOMMODATION_LABELS

    title = (
        "REF + ASY — share living in camps vs out of camp"
        if lang == "en"
        else "REF + ASY — part vivant en camp vs hors camp"
    )
    if df is None or df.empty:
        fig = go.Figure()
        apply_unhcr_layout(fig, title=title)
        return fig
    d = df.copy()
    d["label"] = d["accommodation_type"].map(
        lambda x: ACCOMMODATION_LABELS.get(x, {}).get(lang, x)
    )
    fig = px.pie(
        d,
        names="label",
        values="total",
        color="accommodation_type",
        color_discrete_map={
            "camp": RED_PRIMARY,
            "out-of-camp": BLUE_PRIMARY,
            "unknown": "#BFBFBF",
        },
        title=title,
        hole=0.35,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    apply_unhcr_layout(fig, title=title)
    fig.update_layout(height=400, showlegend=True)
    return fig


def registration_share_pie(df: pd.DataFrame, lang: str) -> go.Figure:
    """REF + ASY individually registered vs not (ActivityInfo basis)."""
    title = (
        "REF + ASY — individual registration status"
        if lang == "en"
        else "REF + ASY — statut d'enregistrement individuel"
    )
    if df is None or df.empty:
        fig = go.Figure()
        apply_unhcr_layout(fig, title=title)
        return fig
    labels = {
        "registered": (
            "Individually registered" if lang == "en" else "Enregistrés individuellement"
        ),
        "not_registered": (
            "Not individually registered"
            if lang == "en"
            else "Non enregistrés individuellement"
        ),
    }
    d = df.copy()
    d["label"] = d["registration_status"].map(lambda x: labels.get(x, x))
    fig = px.pie(
        d,
        names="label",
        values="total",
        color="registration_status",
        color_discrete_map={
            "registered": BLUE_06,
            "not_registered": BLUE_02,
        },
        title=title,
        hole=0.35,
    )
    fig.update_traces(textposition="inside", textinfo="percent")
    apply_unhcr_layout(fig, title=title)
    fig.update_layout(height=400, showlegend=True)
    return fig


def _composition_color(code: str) -> str:
    if code in _POP_ORDER:
        return _COMPOSITION_BLUE_RAMP[_POP_ORDER.index(code) % len(_COMPOSITION_BLUE_RAMP)]
    return BLUE_03


def _svg_composition_pie(
    parts: list[tuple[float, str]],
    size: int,
) -> str:
    """Build an SVG pie from (value, color) slices."""
    total = sum(v for v, _ in parts) or 1.0
    r = size / 2.0
    cx = cy = r
    angle = -math.pi / 2.0
    paths: list[str] = []
    positive = [(v, c) for v, c in parts if v > 0]
    if len(positive) == 1:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 {size} {size}" style="display:block;filter:drop-shadow(0 1px 2px rgba(11,55,84,.25))">'
            f'<circle cx="{cx}" cy="{cy}" r="{r - 0.5}" fill="{positive[0][1]}" '
            f'stroke="#FFFFFF" stroke-width="1.2"/></svg>'
        )
    for val, color in positive:
        sweep = 2.0 * math.pi * (val / total)
        x1 = cx + r * math.cos(angle)
        y1 = cy + r * math.sin(angle)
        angle2 = angle + sweep
        x2 = cx + r * math.cos(angle2)
        y2 = cy + r * math.sin(angle2)
        large = 1 if sweep > math.pi else 0
        paths.append(
            f'<path d="M{cx:.2f},{cy:.2f} L{x1:.2f},{y1:.2f} '
            f'A{r:.2f},{r:.2f} 0 {large},1 {x2:.2f},{y2:.2f} Z" '
            f'fill="{color}" stroke="#FFFFFF" stroke-width="0.9"/>'
        )
        angle = angle2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" style="display:block;filter:drop-shadow(0 1px 2px rgba(11,55,84,.25))">'
        f'{"".join(paths)}</svg>'
    )


def hosts_composition_pie_map(
    composition_df: pd.DataFrame,
    lang: str,
    wca_iso3: list[str] | None = None,
) -> folium.Map:
    """
    WCA host map with composition pie markers (blue ramp dark→light) and rich hover.
    `composition_df` from indicators.country_composition_geo.
    """
    title = (
        "Composition by population type (host countries)"
        if lang == "en"
        else "Composition par type de population (pays d'asile)"
    )
    d = composition_df.copy() if composition_df is not None else pd.DataFrame()
    if not d.empty and wca_iso3:
        d = d[d["asylum_iso3"].isin(wca_iso3)]
    d = d.dropna(subset=["lat", "lon"]) if not d.empty else d

    fmap = folium.Map(
        location=[8.0, 5.0],
        zoom_start=4,
        tiles="CartoDB positron",
        control_scale=True,
    )
    # Prevent browser/Leaflet rectangular focus ring when clicking countries or pies
    fmap.get_root().header.add_child(
        folium.Element(
            """
            <style>
              .leaflet-container path:focus,
              .leaflet-container path:focus-visible,
              .leaflet-interactive:focus,
              .leaflet-interactive:focus-visible,
              .leaflet-marker-icon:focus,
              .leaflet-marker-icon:focus-visible,
              .leaflet-marker-icon:active {
                outline: none !important;
                box-shadow: none !important;
              }
            </style>
            """
        )
    )
    _add_wca_region_layer(fmap, wca_iso3)
    if d.empty:
        return fmap

    skip = {"asylum_iso3", "country_name", "total", "lat", "lon"}
    ordered_cols = [c for c in _POP_ORDER if c in d.columns]
    ordered_cols += [
        c
        for c in d.columns
        if c not in skip
        and c not in ordered_cols
        and pd.api.types.is_numeric_dtype(d[c])
    ]

    max_total = float(d["total"].max() or 1.0)
    legend_items: list[tuple[str, str]] = []
    for code in ordered_cols:
        if float(d[code].sum()) <= 0:
            continue
        legend_items.append((_pop_name(code, lang), _composition_color(code)))

    for _, row in d.iterrows():
        total = float(row.get("total") or 0)
        if total <= 0:
            continue
        parts: list[tuple[float, str]] = []
        hover_lines = [
            f"<b>{row.get('country_name') or row.get('asylum_iso3')}</b>",
            f"{_total_label(lang)}: {total:,.0f}",
        ]
        for code in ordered_cols:
            val = float(row.get(code) or 0)
            if val <= 0:
                continue
            parts.append((val, _composition_color(code)))
            share = val / total
            hover_lines.append(
                f"{_pop_name(code, lang)}: {val:,.0f} ({share * 100:.1f}%)"
            )
        if not parts:
            continue
        size = int(28 + 36 * math.sqrt(total / max_total))
        size = max(28, min(size, 68))
        svg = _svg_composition_pie(parts, size)
        html = (
            f'<div style="width:{size}px;height:{size}px;margin-left:-{size // 2}px;'
            f'margin-top:-{size // 2}px;">{svg}</div>'
        )
        tooltip = folium.Tooltip("<br>".join(hover_lines), sticky=True)
        popup = folium.Popup("<br>".join(hover_lines), max_width=280)
        folium.Marker(
            location=[float(row["lat"]), float(row["lon"])],
            icon=folium.DivIcon(html=html, icon_size=(size, size), icon_anchor=(0, 0)),
            tooltip=tooltip,
            popup=popup,
        ).add_to(fmap)

    # Fit bounds
    lats = d["lat"].astype(float).tolist()
    lons = d["lon"].astype(float).tolist()
    if lats and lons:
        fmap.fit_bounds([[min(lats) - 2, min(lons) - 2], [max(lats) + 2, max(lons) + 2]])

    region_note = (
        "WCA highlighted · outside greyed"
        if lang == "en"
        else "Région WCA délimitée · hors région grisé"
    )
    legend_rows = "".join(
        f'<div style="margin:2px 0;"><span style="display:inline-block;width:12px;height:12px;'
        f'background:{color};margin-right:6px;border-radius:2px;"></span>{label}</div>'
        for label, color in legend_items
    )
    legend = folium.Element(
        f"""
        <div style="position: fixed; bottom: 28px; left: 12px; z-index: 9999;
                    background: rgba(255,255,255,0.95); padding: 8px 12px;
                    border-left: 4px solid #0072BC; border-radius: 2px;
                    font-family: Lato, Arial, sans-serif; font-size: 13px;
                    color: #0B3754; box-shadow: 0 1px 4px rgba(0,0,0,.12); max-width: 280px;">
          <div style="font-weight: 700; margin-bottom: 4px;">{title}</div>
          <div style="font-size: 11px; color: #737373; margin-bottom: 6px;">{region_note}</div>
          {legend_rows}
        </div>
        """
    )
    fmap.get_root().html.add_child(legend)
    return fmap


def admin2_residence_map(points: pd.DataFrame, lang: str, country_name: str) -> go.Figure:
    level = None
    if points is not None and not points.empty and "geo_level" in points.columns:
        levels = points["geo_level"].dropna().astype(str).tolist()
        if levels:
            # Prefer the finest level present among points
            if "admin2" in levels:
                level = "admin2"
            elif "admin1" in levels:
                level = "admin1"
            else:
                level = "country"
    level_lbl = {
        "admin2": "Admin2",
        "admin1": "Admin1",
        "country": "pays" if lang == "fr" else "country",
    }.get(level or "", "")
    if lang == "en":
        title = (
            f"Residence areas ({level_lbl}) — {country_name}"
            if level_lbl
            else f"Residence areas — {country_name}"
        )
    else:
        title = (
            f"Zones de résidence ({level_lbl}) — {country_name}"
            if level_lbl
            else f"Zones de résidence — {country_name}"
        )
    if points is None or points.empty:
        fig = go.Figure()
        apply_unhcr_layout(fig, title=title)
        fig.update_layout(height=480)
        return fig
    d = points.copy()
    d["pop"] = d["pop_code"].map(lambda c: _pop_name(c, lang))
    color_map = {_pop_name(c, lang): pop_color(c) for c in d["pop_code"].unique()}
    fig = px.scatter_geo(
        d,
        lat="lat",
        lon="lon",
        size="total",
        color="pop",
        hover_name="label",
        hover_data={"total": ":,.0f", "lat": False, "lon": False, "pop": True},
        color_discrete_map=color_map,
        projection="natural earth",
        title=title,
        size_max=36,
    )
    apply_unhcr_layout(fig, title=title)

    # Zoom on country: fitbounds when several locations, else center + scale
    n_locs = d[["lat", "lon"]].drop_duplicates().shape[0]
    geo_kw: dict = {
        "showcountries": True,
        "countrycolor": "#7A7A7A",
        "showland": True,
        "landcolor": "#F7FBFE",
        "bgcolor": "rgba(0,0,0,0)",
        "showframe": False,
        "resolution": 50,
    }
    if n_locs >= 2:
        geo_kw["fitbounds"] = "locations"
    else:
        clat = float(d["lat"].mean())
        clon = float(d["lon"].mean())
        geo_kw["center"] = dict(lat=clat, lon=clon)
        geo_kw["projection_scale"] = 4.5
        geo_kw["lonaxis"] = dict(range=[clon - 12, clon + 12])
        geo_kw["lataxis"] = dict(range=[clat - 10, clat + 10])

    fig.update_layout(
        height=480,
        margin=dict(l=0, r=0, t=56, b=0),
        geo=geo_kw,
        legend_title_text="",
    )
    return fig
