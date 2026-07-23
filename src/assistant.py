"""MSR WCA conversational assistant (Phase 3).

Numbers always come from indicator tools / in-memory dataframes — never invented by an LLM.
Optional LLM (OpenAI-compatible) only rephrases when ASSISTANT_LLM=on and an API key exists.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd

from src.indicators import (
    accommodation_share_ref_asy,
    country_stock,
    kpi_snapshot,
    origin_stock,
)
from src.narratives import pop_label
from src.reference_data import format_month_label


@dataclass
class AssistantContext:
    lang: str
    month: str
    month_label: str
    compare_month: str
    current: pd.DataFrame
    previous: pd.DataFrame
    pop_codes: list[str]
    host_map: dict[str, str]
    data_version: str = ""


@dataclass
class AssistantReply:
    text: str
    intent: str
    used_tools: list[str]
    grounded: bool  # True if figures come from tools


def _fmt_int(n: float | None) -> str:
    if n is None or (isinstance(n, float) and n != n):
        return "—"
    return f"{n:,.0f}".replace(",", " ")


def _fmt_pct(n: float | None) -> str:
    if n is None or (isinstance(n, float) and n != n):
        return "—"
    return f"{n * 100:.1f}%"


def _norm(q: str) -> str:
    return re.sub(r"\s+", " ", q.strip().lower())


# ── Intent detection ─────────────────────────────────────────────────────────


def detect_intent(question: str, lang: str) -> str:
    q = _norm(question)
    if not q:
        return "empty"

    help_kw = (
        "comment",
        "où",
        "ou trouver",
        "aide",
        "utiliser",
        "onglet",
        "filtre",
        "how",
        "where",
        "help",
        "tab",
        "filter",
        "navigate",
    )
    gloss_kw = (
        "signifie",
        "définition",
        "definition",
        "glossary",
        "glossaire",
        "qu'est-ce",
        "what is",
        "msr",
        "mom",
        "yoy",
        "detailed",
        "aggregation",
        "agrégation",
        "ref",
        "asy",
        "idp",
        "pdi",
        "psn",
    )
    camp_kw = ("camp", "hors camp", "out of camp", "hébergement", "accommodation", "shelter")
    origin_kw = ("origine", "origin", "provenan")
    host_kw = ("asile", "accueil", "host", "asylum", "pays d'asile")
    mom_kw = ("mom", "variation", "évolution", "evolution", "change", "mois précédent", "previous month")
    total_kw = ("total", "combien", "how many", "effectif", "population", "kpi", "stock")

    if any(k in q for k in help_kw) and not any(k in q for k in total_kw):
        return "help_nav"
    if any(k in q for k in gloss_kw):
        return "glossary"
    if any(k in q for k in camp_kw):
        return "accommodation"
    if any(k in q for k in origin_kw):
        return "top_origins"
    if any(k in q for k in host_kw):
        return "top_hosts"
    if any(k in q for k in mom_kw):
        return "mom"
    if any(k in q for k in total_kw):
        return "kpi_total"
    return "unknown"


# ── Tool implementations (grounded) ──────────────────────────────────────────


def tool_kpi(ctx: AssistantContext) -> tuple[str, dict[str, Any]]:
    kpi = kpi_snapshot(ctx.current, ctx.previous)
    payload = {
        "total": kpi.get("total"),
        "ref_asy": kpi.get("ref_asy"),
        "idp": kpi.get("idp"),
        "sta": kpi.get("sta"),
        "mom": kpi.get("mom"),
        "mom_abs": kpi.get("mom_abs"),
        "female_share": kpi.get("female_share"),
        "children_share": kpi.get("children_share"),
        "month": ctx.month_label,
        "compare": format_month_label(ctx.compare_month, ctx.lang),
        "types": ", ".join(pop_label(c, ctx.lang) for c in ctx.pop_codes),
    }
    if ctx.lang == "fr":
        text = (
            f"Pour **{payload['month']}** (types : {payload['types']}) :\n"
            f"- Population totale : **{_fmt_int(payload['total'])}**\n"
            f"- REF + ASY : **{_fmt_int(payload['ref_asy'])}**\n"
            f"- PDI : **{_fmt_int(payload['idp'])}** · Apatrides : **{_fmt_int(payload['sta'])}**\n"
            f"- MoM vs {payload['compare']} : **{_fmt_pct(payload['mom'])}** "
            f"({_fmt_int(payload['mom_abs'])} personnes)\n"
            f"- Parts (populations ventilées) — femmes : {_fmt_pct(payload['female_share'])}, "
            f"enfants : {_fmt_pct(payload['children_share'])}."
        )
    else:
        text = (
            f"For **{payload['month']}** (types: {payload['types']}):\n"
            f"- Total population: **{_fmt_int(payload['total'])}**\n"
            f"- REF + ASY: **{_fmt_int(payload['ref_asy'])}**\n"
            f"- IDP: **{_fmt_int(payload['idp'])}** · Stateless: **{_fmt_int(payload['sta'])}**\n"
            f"- MoM vs {payload['compare']}: **{_fmt_pct(payload['mom'])}** "
            f"({_fmt_int(payload['mom_abs'])} people)\n"
            f"- Shares (disaggregated only) — female: {_fmt_pct(payload['female_share'])}, "
            f"children: {_fmt_pct(payload['children_share'])}."
        )
    if ctx.data_version:
        text += f"\n\n_{ctx.data_version}_"
    return text, payload


def tool_top_hosts(ctx: AssistantContext, n: int = 8) -> tuple[str, dict[str, Any]]:
    host_col = "asylum_name_fr" if ctx.lang == "fr" else "asylum_name_en"
    hosts = country_stock(ctx.current, name_col=host_col)
    if hosts.empty:
        msg = "Aucune donnée pays d'asile." if ctx.lang == "fr" else "No asylum-country data."
        return msg, {}
    agg = (
        hosts.groupby(["asylum_iso3", host_col], as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
        .head(n)
    )
    lines = [f"- {r[host_col]} : **{_fmt_int(r['total'])}**" for _, r in agg.iterrows()]
    title = (
        f"Top {n} pays d'asile — {ctx.month_label} :"
        if ctx.lang == "fr"
        else f"Top {n} countries of asylum — {ctx.month_label}:"
    )
    return title + "\n" + "\n".join(lines), {"rows": agg.to_dict("records")}


def tool_top_origins(ctx: AssistantContext, n: int = 8) -> tuple[str, dict[str, Any]]:
    o_col = "origin_name_fr" if ctx.lang == "fr" else "origin_name_en"
    origins = origin_stock(ctx.current)
    if origins.empty:
        msg = "Aucune donnée d'origine." if ctx.lang == "fr" else "No origin data."
        return msg, {}
    agg = (
        origins.groupby(["origin_hcr3", o_col], as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
        .head(n)
    )
    lines = [f"- {r[o_col]} : **{_fmt_int(r['total'])}**" for _, r in agg.iterrows()]
    title = (
        f"Top {n} origines — {ctx.month_label} :"
        if ctx.lang == "fr"
        else f"Top {n} origins — {ctx.month_label}:"
    )
    return title + "\n" + "\n".join(lines), {"rows": agg.to_dict("records")}


def tool_accommodation(ctx: AssistantContext) -> tuple[str, dict[str, Any]]:
    share = accommodation_share_ref_asy(ctx.current)
    if share.empty:
        msg = (
            "Pas de données d'hébergement REF/ASY pour la sélection."
            if ctx.lang == "fr"
            else "No REF/ASY accommodation data for the selection."
        )
        return msg, {}
    labels = {
        "camp": "Camp" if ctx.lang == "en" else "Camp",
        "out-of-camp": "Out of camp" if ctx.lang == "en" else "Hors camp",
        "unknown": "Unknown" if ctx.lang == "en" else "Inconnu",
    }
    lines = []
    for _, r in share.iterrows():
        lab = labels.get(str(r["accommodation_type"]), str(r["accommodation_type"]))
        lines.append(f"- {lab} : **{_fmt_pct(r['share'])}** ({_fmt_int(r['total'])})")
    title = (
        f"Hébergement REF+ASY — {ctx.month_label} :"
        if ctx.lang == "fr"
        else f"REF+ASY accommodation — {ctx.month_label}:"
    )
    return title + "\n" + "\n".join(lines), {"rows": share.to_dict("records")}


def tool_help_nav(ctx: AssistantContext) -> tuple[str, dict[str, Any]]:
    if ctx.lang == "fr":
        text = (
            "Parcours recommandé :\n"
            "1. **Vue d'ensemble** — KPI flash du mois + qualité des données\n"
            "2. **Fiche pays** — zoom asile / Admin1-2\n"
            "3. **Tendances** — série mensuelle et retours RET/RDP\n"
            "4. **Rapports** — PDF institutionnels (version des données en en-tête)\n\n"
            "Filtres à gauche : mois de référence, MoM (mois précédent par défaut), "
            "types de population, pays d'asile et origines.\n"
            "Bouton **Rafraîchir** pour recharger ActivityInfo."
        )
    else:
        text = (
            "Recommended path:\n"
            "1. **Overview** — month flash KPIs + data quality\n"
            "2. **Country profile** — asylum / Admin1-2 zoom\n"
            "3. **Trends** — monthly series and RET/RDP returns\n"
            "4. **Reports** — institutional PDFs (data version in header)\n\n"
            "Left filters: reference month, MoM (defaults to previous month), "
            "population types, asylum countries and origins.\n"
            "**Refresh** reloads ActivityInfo."
        )
    return text, {}


def tool_glossary(ctx: AssistantContext, question: str) -> tuple[str, dict[str, Any]]:
    q = _norm(question)
    entries_fr = {
        "msr": "**MSR** — Monthly Statistical Report / Rapport statistique mensuel UNHCR.",
        "mom": "**MoM** — variation d'un mois sur l'autre (Month-over-Month).",
        "yoy": "**YoY** — variation d'une année sur l'autre (Year-over-Year).",
        "detailed": "**detailed** — lignes au grain admin/localité ; prioritaire dans l'agrégation analytique.",
        "total": "**total** — agrégation nationale/coarser ; utilisée si detailed absent pour un type.",
        "ref": "**REF** — réfugiés.",
        "asy": "**ASY** — demandeurs d'asile.",
        "idp": "**IDP / PDI** — personnes déplacées internes.",
        "pdi": "**IDP / PDI** — personnes déplacées internes.",
        "sta": "**STA** — apatrides.",
        "psn": "**PSN** — Persons with Specific Needs (sous-ensemble à besoins spécifiques, pas le stock global).",
        "ret": "**RET** — réfugiés rapatriés.",
        "rdp": "**RDP** — PDI de retour.",
    }
    entries_en = {
        "msr": "**MSR** — Monthly Statistical Report of UNHCR.",
        "mom": "**MoM** — Month-over-Month change.",
        "yoy": "**YoY** — Year-over-Year change.",
        "detailed": "**detailed** — admin/locality grain; preferred in analytical aggregation.",
        "total": "**total** — coarser national aggregation; used when detailed is missing for a type.",
        "ref": "**REF** — refugees.",
        "asy": "**ASY** — asylum-seekers.",
        "idp": "**IDP** — internally displaced persons.",
        "sta": "**STA** — stateless persons.",
        "psn": "**PSN** — Persons with Specific Needs (subset, not the overall stock).",
        "ret": "**RET** — refugee returnees.",
        "rdp": "**RDP** — IDP returnees.",
    }
    entries = entries_fr if ctx.lang == "fr" else entries_en
    hits = [entries[k] for k in entries if k in q]
    if not hits:
        if ctx.lang == "fr":
            return (
                "Glossaire rapide : MSR, MoM, YoY, REF, ASY, IDP/PDI, STA, PSN, RET, RDP, "
                "detailed/total. Posez une question du type « Que signifie MoM ? ».",
                {},
            )
        return (
            "Quick glossary: MSR, MoM, YoY, REF, ASY, IDP, STA, PSN, RET, RDP, "
            "detailed/total. Try e.g. “What does MoM mean?”.",
            {},
        )
    return "\n\n".join(hits), {"matched": True}


def tool_unknown(ctx: AssistantContext) -> tuple[str, dict[str, Any]]:
    if ctx.lang == "fr":
        text = (
            "Je peux répondre sur :\n"
            "- les **effectifs / KPI** du mois filtré\n"
            "- le **MoM**, top **pays d'asile / origines**, **camp vs hors camp**\n"
            "- le **glossaire** et **l'utilisation** de l'application\n\n"
            "Je ne invente pas de chiffres : ils viennent des calculs MSR chargés. "
            "Reformulez votre question ou précisez un indicateur."
        )
    else:
        text = (
            "I can help with:\n"
            "- **totals / KPIs** for the filtered month\n"
            "- **MoM**, top **asylum / origin** countries, **camp vs out of camp**\n"
            "- **glossary** and **how to use** the app\n\n"
            "I do not invent figures: they come from the loaded MSR calculations. "
            "Please rephrase or name an indicator."
        )
    return text, {}


TOOLS: dict[str, Callable[..., tuple[str, dict[str, Any]]]] = {
    "kpi_total": lambda ctx, q: tool_kpi(ctx),
    "mom": lambda ctx, q: tool_kpi(ctx),
    "top_hosts": lambda ctx, q: tool_top_hosts(ctx),
    "top_origins": lambda ctx, q: tool_top_origins(ctx),
    "accommodation": lambda ctx, q: tool_accommodation(ctx),
    "help_nav": lambda ctx, q: tool_help_nav(ctx),
    "glossary": lambda ctx, q: tool_glossary(ctx, q),
    "unknown": lambda ctx, q: tool_unknown(ctx),
    "empty": lambda ctx, q: (
        ("Posez une question." if ctx.lang == "fr" else "Please ask a question."),
        {},
    ),
}


def answer_question(question: str, ctx: AssistantContext) -> AssistantReply:
    intent = detect_intent(question, ctx.lang)
    fn = TOOLS.get(intent, TOOLS["unknown"])
    text, _payload = fn(ctx, question)
    grounded = intent not in {"help_nav", "glossary", "unknown", "empty"}
    # Optional LLM rephrase (never for inventing numbers — only polish grounded text)
    text = maybe_rephrase(text, question=question, ctx=ctx, grounded=grounded)
    return AssistantReply(
        text=text,
        intent=intent,
        used_tools=[intent],
        grounded=grounded or intent in {"glossary", "help_nav"},
    )


def maybe_rephrase(
    text: str, *, question: str, ctx: AssistantContext, grounded: bool
) -> str:
    """Optionally polish wording via OpenAI-compatible API; figures stay from tools."""
    from src.config import _setting

    if (_setting("ASSISTANT_LLM", "off") or "off").lower() not in {"on", "1", "true"}:
        return text
    api_key = _setting("OPENAI_API_KEY") or _setting("AZURE_OPENAI_API_KEY")
    if not api_key:
        return text
    try:
        import json
        import urllib.request

        base = _setting("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        model = _setting("OPENAI_MODEL", "gpt-4o-mini")
        system = (
            "You rephrase an assistant answer for UNHCR DIMA. "
            "Do NOT change any numbers, percentages, country names, or dates. "
            "Keep the same language as the answer. Be concise and institutional."
            if ctx.lang == "en"
            else
            "Tu reformules une réponse d'assistant pour le DIMA HCR. "
            "Ne modifie AUCUN chiffre, pourcentage, nom de pays ou date. "
            "Garde la même langue. Ton concis et institutionnel."
        )
        body = {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nAnswer to rephrase:\n{text}",
                },
            ],
        }
        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        polished = data["choices"][0]["message"]["content"].strip()
        return polished or text
    except Exception:  # noqa: BLE001
        return text
