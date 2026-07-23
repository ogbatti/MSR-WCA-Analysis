"""Phase 3 — assistant intents and grounded answers."""
from __future__ import annotations

import pandas as pd

from src.assistant import AssistantContext, answer_question, detect_intent


def _ctx(lang: str = "fr") -> AssistantContext:
    current = pd.DataFrame(
        [
            {
                "asylum_iso3": "CMR",
                "asylum_name_en": "Cameroon",
                "asylum_name_fr": "Cameroun",
                "asylum_hcr3": "CMR",
                "origin_hcr3": "NGA",
                "origin_iso3": "NGA",
                "origin_name_en": "Nigeria",
                "origin_name_fr": "Nigeria",
                "pop_code": "REF",
                "total": 1000,
                "female": 400,
                "male": 600,
                "children": 200,
                "accommodation_type": "camp",
                "asylum_lat": 7.0,
                "asylum_lon": 12.0,
            },
            {
                "asylum_iso3": "TCD",
                "asylum_name_en": "Chad",
                "asylum_name_fr": "Tchad",
                "asylum_hcr3": "TCD",
                "origin_hcr3": "SDN",
                "origin_iso3": "SDN",
                "origin_name_en": "Sudan",
                "origin_name_fr": "Soudan",
                "pop_code": "ASY",
                "total": 500,
                "female": 200,
                "male": 300,
                "children": 100,
                "accommodation_type": "out-of-camp",
                "asylum_lat": 15.0,
                "asylum_lon": 19.0,
            },
        ]
    )
    previous = current.copy()
    previous["total"] = previous["total"] * 0.9
    return AssistantContext(
        lang=lang,
        month="2025-01",
        month_label="janvier 2025",
        compare_month="2024-12",
        current=current,
        previous=previous,
        pop_codes=["REF", "ASY"],
        host_map={"CMR": "Cameroun", "TCD": "Tchad"},
        data_version="test extract",
    )


def test_detect_intent_kpi_and_help():
    assert detect_intent("Combien de population totale ?", "fr") == "kpi_total"
    assert detect_intent("Que signifie MoM ?", "fr") == "glossary"
    assert detect_intent("Comment utiliser les onglets ?", "fr") == "help_nav"
    assert detect_intent("Top pays d'asile", "fr") == "top_hosts"


def test_answer_kpi_is_grounded_and_numeric():
    reply = answer_question("Quel est le total ce mois ?", _ctx("fr"))
    assert reply.grounded
    assert reply.intent == "kpi_total"
    assert "1 500" in reply.text or "1500" in reply.text.replace(" ", "")


def test_unknown_does_not_invent_numbers():
    reply = answer_question("Quelle est la capitale de la France ?", _ctx("fr"))
    assert reply.intent == "unknown"
    assert "invente" in reply.text.lower() or "chiffres" in reply.text.lower()
