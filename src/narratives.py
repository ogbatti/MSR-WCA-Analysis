"""Narrative interpretation helpers (FR/EN)."""
from __future__ import annotations

from src.config import POP_TYPE_LABELS
from src.reference_data import format_month_label


def _fmt(n: float | None, digits: int = 0) -> str:
    if n is None or (isinstance(n, float) and n != n):
        return "—"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:,.{digits}f}M".replace(",", " ")
    if abs(n) >= 1_000:
        return f"{n:,.0f}".replace(",", " ")
    return f"{n:.{digits}f}"


def _pct(n: float | None) -> str:
    if n is None or (isinstance(n, float) and n != n):
        return "—"
    return f"{n*100:.1f}%"


def pop_label(code: str, lang: str) -> str:
    return POP_TYPE_LABELS.get(code, {}).get(lang, code)


def build_overview_narrative(
    *,
    lang: str,
    month: str,
    kpi: dict,
    top_hosts: list[tuple[str, float]],
    top_origins: list[tuple[str, float]],
    pop_codes: list[str],
    by_type: list[tuple[str, float]] | None = None,
    registration: dict | None = None,
) -> str:
    pops = ", ".join(pop_label(c, lang) for c in pop_codes)
    hosts = ", ".join(f"{n} ({_fmt(v)})" for n, v in top_hosts[:5])
    origins = ", ".join(f"{n} ({_fmt(v)})" for n, v in top_origins[:5])
    total = kpi.get("total") or 0

    # Composition shares (inspired by regional overview dashboards; plain text, no colored figures)
    composition = ""
    if by_type and total:
        bits = []
        for code, val in by_type:
            share = (val / total) if total else 0.0
            bits.append(f"{pop_label(code, lang)} {_pct(share)} ({_fmt(val)})")
        composition = "; ".join(bits)

    reg_txt = ""
    if registration:
        reg_share = registration.get("registered_share")
        not_share = registration.get("not_registered_share")
        if lang == "fr":
            reg_txt = (
                f"\n- Enregistrement individuel REF+ASY : **{_pct(reg_share)}** enregistrés · "
                f"**{_pct(not_share)}** non enregistrés"
            )
        else:
            reg_txt = (
                f"\n- Individual registration REF+ASY: **{_pct(reg_share)}** registered · "
                f"**{_pct(not_share)}** not registered"
            )

    if lang == "fr":
        mom_txt = (
            f"La variation mensuelle (MoM) est de {_pct(kpi.get('mom'))} "
            f"({_fmt(kpi.get('mom_abs'))} personnes)."
            if kpi.get("mom") is not None
            else "La variation mensuelle n'est pas disponible pour ce point de comparaison."
        )
        comp_txt = (
            f"\n\n**Composition par type :** {composition}."
            if composition
            else ""
        )
        return (
            f"### Commentaires du mois {month}\n\n"
            f"Pour les populations sélectionnées (**{pops}**), la population totale régionale s'élève à "
            f"**{_fmt(kpi.get('total'))}** personnes dans **{kpi.get('countries', 0)}** pays d'asile, "
            f"issues de **{kpi.get('origins', 0)}** pays/territoires d'origine."
            f"{comp_txt}\n\n"
            f"- % Femmes* : **{_pct(kpi.get('female_share'))}**\n"
            f"- % Enfants* (0–17, lorsque ventilé) : **{_pct(kpi.get('children_share'))}**"
            f"{reg_txt}\n"
            f"- {mom_txt}\n\n"
            f"**Principaux pays d'accueil :** {hosts or '—'}.\n\n"
            f"**Principaux pays d'origine :** {origins or '—'}."
        )

    mom_txt = (
        f"Month-on-month (MoM) change is {_pct(kpi.get('mom'))} "
        f"({_fmt(kpi.get('mom_abs'))} people)."
        if kpi.get("mom") is not None
        else "Month-on-month change is not available for this comparison point."
    )
    comp_txt = (
        f"\n\n**Breakdown by type:** {composition}."
        if composition
        else ""
    )
    return (
        f"### Comments for {month}\n\n"
        f"For the selected populations (**{pops}**), the regional total population stands at "
        f"**{_fmt(kpi.get('total'))}** people across **{kpi.get('countries', 0)}** countries of asylum, "
        f"from **{kpi.get('origins', 0)}** countries/territories of origin."
        f"{comp_txt}\n\n"
        f"- % Female*: **{_pct(kpi.get('female_share'))}**\n"
        f"- % Children* (0–17, when disaggregated): **{_pct(kpi.get('children_share'))}**"
        f"{reg_txt}\n"
        f"- {mom_txt}\n\n"
        f"**Top host countries:** {hosts or '—'}.\n\n"
        f"**Top countries of origin:** {origins or '—'}."
    )


def build_trend_narrative(lang: str, trend_df, focus_label: str) -> str:
    if trend_df is None or trend_df.empty or len(trend_df) < 2:
        return (
            "_Série insuffisante pour une interprétation de tendance._"
            if lang == "fr"
            else "_Insufficient series for trend interpretation._"
        )
    first = trend_df.iloc[0]
    last = trend_df.iloc[-1]
    delta = last["total"] - first["total"]
    pct = delta / first["total"] if first["total"] else None
    start = format_month_label(str(first["year_month"]), lang)
    end = format_month_label(str(last["year_month"]), lang)
    if lang == "fr":
        direction = "en hausse" if delta > 0 else "en baisse" if delta < 0 else "stable"
        return (
            f"Entre **{start.lower()}** et **{end.lower()}**, la population totale "
            f"({focus_label}) est **{direction}** de {_fmt(delta)} personnes ({_pct(pct)})."
        )
    direction = "up" if delta > 0 else "down" if delta < 0 else "stable"
    return (
        f"Between **{start}** and **{end}**, the total population "
        f"({focus_label}) is **{direction}** by {_fmt(delta)} people ({_pct(pct)})."
    )


def build_forecast_narrative(lang: str, forecast_df, pop_code: str, horizon: int) -> str:
    if forecast_df is None or forecast_df.empty:
        return "_Aucune projection disponible._" if lang == "fr" else "_No projection available._"
    hist = forecast_df[forecast_df["kind"] == "historical"]
    if hist.empty:
        return "_Historique insuffisant._" if lang == "fr" else "_Insufficient history._"
    base_year = int(hist["year"].max())
    base_val = float(hist.loc[hist["year"] == base_year, "total"].iloc[0])
    label = pop_label(pop_code, lang)

    lines = []
    if lang == "fr":
        lines.append(
            f"À partir de la population totale de fin **{base_year}** ({_fmt(base_val)} {label}), "
            f"les scénarios métier projettent les niveaux suivants en **{horizon}** :"
        )
    else:
        lines.append(
            f"From the end-**{base_year}** total population ({_fmt(base_val)} {label}), "
            f"business scenarios project the following levels in **{horizon}**:"
        )

    for sc in ["optimistic", "baseline", "pessimistic", "custom"]:
        sub = forecast_df[(forecast_df["scenario"] == sc) & (forecast_df["year"] == horizon)]
        if sub.empty:
            continue
        val = float(sub["total"].iloc[0])
        lines.append(f"- **{sc}** : {_fmt(val)}")

    if lang == "fr":
        lines.append(
            "\n_Ces projections sont illustratives et reposent sur des hypothèses métier._"
        )
    else:
        lines.append(
            "\n_These projections are illustrative and rest on business assumptions._"
        )
    return "\n".join(lines)
