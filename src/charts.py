"""Plotly chart helpers — UNHCR brand styling."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.config import POP_TYPE_LABELS
from src.theme import (
    BLUE_PRIMARY,
    CHOROPLETH_BLUES,
    RED_PRIMARY,
    SCENARIO_COLORS,
    YELLOW_PRIMARY,
    apply_unhcr_layout,
    pop_color,
)


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
    d = trend.dropna(subset=["mom"]).copy()
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=d["year_month"],
            y=d["mom"] * 100,
            name="MoM %",
            marker_color=BLUE_PRIMARY,
        )
    )
    if d["yoy"].notna().any():
        fig.add_trace(
            go.Bar(
                x=d["year_month"],
                y=d["yoy"] * 100,
                name="YoY %",
                marker_color=YELLOW_PRIMARY,
            )
        )
    y_title = "Variation (%)" if lang == "fr" else "Change (%)"
    title = "MoM / YoY changes" if lang == "en" else "Variations MoM / YoY"
    fig.update_layout(barmode="group", height=380, yaxis_title=y_title, xaxis_title="")
    apply_unhcr_layout(fig, title=title)
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
    """Horizontal age–sex pyramid (female left, male right)."""
    title = "Age–sex pyramid" if lang == "en" else "Pyramide des âges par sexe"
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
    title = "Displacement corridors" if lang == "en" else "Corridors de déplacement"
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
        width = 1 + 6 * (r["total"] / max_t)
        fig.add_trace(
            go.Scattergeo(
                lon=[r["origin_lon"], r["asylum_lon"]],
                lat=[r["origin_lat"], r["asylum_lat"]],
                mode="lines",
                line=dict(width=width, color=RED_PRIMARY),
                opacity=0.55,
                hoverinfo="text",
                text=f"{r.get(o_name)} → {r.get(a_name)}<br>{r.get('pop_code')}: {r['total']:,.0f}",
                showlegend=False,
            )
        )

    ends = pd.concat(
        [
            flows[["origin_lat", "origin_lon", o_name]].rename(
                columns={"origin_lat": "lat", "origin_lon": "lon", o_name: "name"}
            ),
            flows[["asylum_lat", "asylum_lon", a_name]].rename(
                columns={"asylum_lat": "lat", "asylum_lon": "lon", a_name: "name"}
            ),
        ]
    ).dropna().drop_duplicates()
    fig.add_trace(
        go.Scattergeo(
            lon=ends["lon"],
            lat=ends["lat"],
            text=ends["name"],
            mode="markers",
            marker=dict(size=8, color=BLUE_PRIMARY, line=dict(width=1, color="white")),
            hoverinfo="text",
            showlegend=False,
        )
    )
    apply_unhcr_layout(fig, title=title)
    # Wider than WCA so external origins (Sudan, Syria, etc.) remain visible
    fig.update_layout(
        height=540,
        margin=dict(l=0, r=0, t=56, b=0),
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
