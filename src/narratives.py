"""Narrative interpretation helpers (FR/EN)."""
from __future__ import annotations

from src.config import POP_TYPE_LABELS


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
) -> str:
    pops = ", ".join(pop_label(c, lang) for c in pop_codes)
    hosts = ", ".join(f"{n} ({_fmt(v)})" for n, v in top_hosts[:5])
    origins = ", ".join(f"{n} ({_fmt(v)})" for n, v in top_origins[:5])

    if lang == "fr":
        mom_txt = (
            f"La variation mensuelle (MoM) est de {_pct(kpi.get('mom'))} "
            f"({_fmt(kpi.get('mom_abs'))} personnes)."
            if kpi.get("mom") is not None
            else "La variation mensuelle n'est pas disponible pour ce point de comparaison."
        )
        return (
            f"### Lecture du mois {month}\n\n"
            f"Pour les populations sélectionnées (**{pops}**), la population totale régionale s'élève à "
            f"**{_fmt(kpi.get('total'))}** personnes dans **{kpi.get('countries', 0)}** pays d'asile, "
            f"issues de **{kpi.get('origins', 0)}** pays/territoires d'origine.\n\n"
            f"- Part des femmes : **{_pct(kpi.get('female_share'))}**\n"
            f"- Part des enfants (0–17, lorsque ventilé) : **{_pct(kpi.get('children_share'))}**\n"
            f"- {mom_txt}\n\n"
            f"**Principaux pays d'accueil :** {hosts or '—'}.\n\n"
            f"**Principaux pays d'origine :** {origins or '—'}.\n\n"
            f"_Note méthodologique : priorité à l'agrégation `detailed` (admin/localité) ; "
            f"bascule automatique sur `total` pour les types uniquement reportés à ce niveau "
            f"(ex. PDI, apatrides), sans mélanger les niveaux d'agrégation._"
        )

    mom_txt = (
        f"Month-on-month (MoM) change is {_pct(kpi.get('mom'))} "
        f"({_fmt(kpi.get('mom_abs'))} people)."
        if kpi.get("mom") is not None
        else "Month-on-month change is not available for this comparison point."
    )
    return (
        f"### Reading for {month}\n\n"
        f"For the selected populations (**{pops}**), the regional total population stands at "
        f"**{_fmt(kpi.get('total'))}** people across **{kpi.get('countries', 0)}** countries of asylum, "
        f"from **{kpi.get('origins', 0)}** countries/territories of origin.\n\n"
        f"- Female share: **{_pct(kpi.get('female_share'))}**\n"
        f"- Children share (0–17, when disaggregated): **{_pct(kpi.get('children_share'))}**\n"
        f"- {mom_txt}\n\n"
        f"**Top host countries:** {hosts or '—'}.\n\n"
        f"**Top countries of origin:** {origins or '—'}.\n\n"
        f"_Method note: prefer ActivityInfo `detailed` aggregation (admin/locality); "
        f"automatically fall back to `total` for types only reported at that level "
        f"(e.g. IDPs, stateless), without mixing aggregation levels._"
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
    if lang == "fr":
        direction = "en hausse" if delta > 0 else "en baisse" if delta < 0 else "stable"
        return (
            f"Entre **{first['year_month']}** et **{last['year_month']}**, la population totale "
            f"({focus_label}) est **{direction}** de {_fmt(delta)} personnes ({_pct(pct)}). "
            f"La dernière valeur observée est {_fmt(last['total'])}."
        )
    direction = "up" if delta > 0 else "down" if delta < 0 else "stable"
    return (
        f"Between **{first['year_month']}** and **{last['year_month']}**, the total population "
        f"({focus_label}) is **{direction}** by {_fmt(delta)} people ({_pct(pct)}). "
        f"The latest observed value is {_fmt(last['total'])}."
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
            "\nCes projections ne sont **pas des prévisions statistiques pures** : "
            "elles simulent l'effet combiné de la croissance résiduelle, des chocs de conflit "
            "et des taux de retour/solutions jusqu'en 2036."
        )
    else:
        lines.append(
            "\nThese projections are **not pure statistical forecasts**: "
            "they simulate the combined effect of residual growth, conflict shocks "
            "and return/solutions rates through 2036."
        )
    return "\n".join(lines)
