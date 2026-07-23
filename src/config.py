"""Application configuration."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def _setting(name: str, default: str = "") -> str:
    """Read from environment (.env) first, then Streamlit secrets (Cloud)."""
    value = os.getenv(name, "")
    if value:
        return value
    try:
        import streamlit as st

        secrets = getattr(st, "secrets", None)
        if secrets is not None and name in secrets:
            return str(secrets[name])
    except Exception:
        pass
    return default


ACTIVITYINFO_TOKEN = _setting("ACTIVITYINFO_TOKEN", "")
# "staging" on develop branch apps; set to "prod" only when merging to master
APP_CHANNEL = _setting("MSR_CHANNEL", "staging")
ACTIVITYINFO_BASE_URL = _setting(
    "ACTIVITYINFO_BASE_URL", "https://www.activityinfo.org/resources"
).rstrip("/")
DATABASE_ID = _setting("ACTIVITYINFO_DATABASE_ID", "c6whbx9kv7zwnux3")

# Form IDs — WCA DIMA Statistics & Analysis
FORM_POPULATION = "cae6v67mnrh690es"
FORM_TOTAL_PSN = "cakhipjmnrpazba5v"
FORM_PSN = "ce0uuhmmnrp3hie5c"
FORM_EDUCATION = "cu9g9jgmnrn5mu62l"
FORM_COUNTRIES = "c3lb2j7mo4v30bp7"
FORM_POP_TYPES = "cxmho36mnrg1bl3b"
FORM_GEOLOC = "cawax4bmo5ipjj11f"

CACHE_DIR = ROOT / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

POP_COLUMNS = [
    {"id": "date", "expression": "date"},
    {"id": "origin_hcr3", "expression": "origin"},
    {"id": "asylum_hcr3", "expression": "asylum.country_hcr3"},
    {"id": "asylum_iso3", "expression": "asylum.iso3"},
    {"id": "asylum_iso2", "expression": "asylum.iso2"},
    {"id": "asylum_name_en", "expression": "asylum.name_en"},
    {"id": "asylum_name_fr", "expression": "asylum.name_fr"},
    {"id": "asylum_lat", "expression": "asylum.latitude"},
    {"id": "asylum_lon", "expression": "asylum.longitude"},
    {"id": "pop_code", "expression": "population_type.Code"},
    {"id": "pop_label", "expression": "population_type.[Label (Description)]"},
    {"id": "coa_admin1", "expression": "coa_admin1"},
    {"id": "coa_admin2", "expression": "coa_admin2"},
    {"id": "coa_admin3", "expression": "coa_admin3"},
    {"id": "accommodation_type", "expression": "accommodation_type"},
    {"id": "aggregation_type", "expression": "aggregation_type"},
    {"id": "source", "expression": "source"},
    {"id": "basis", "expression": "basis"},
    {"id": "female", "expression": "female"},
    {"id": "male", "expression": "male"},
    {"id": "total", "expression": "total"},
    {"id": "f_0_4", "expression": "[f_0-4]"},
    {"id": "f_5_11", "expression": "[f_5-11]"},
    {"id": "f_12_17", "expression": "[f_12-17]"},
    {"id": "f_18_24", "expression": "[f_18-24]"},
    {"id": "f_25_49", "expression": "[f_25-49]"},
    {"id": "f_50_59", "expression": "[f_50-59]"},
    {"id": "f_60", "expression": "[f_60]"},
    {"id": "m_0_4", "expression": "[m_0-4]"},
    {"id": "m_5_11", "expression": "[m_5-11]"},
    {"id": "m_12_17", "expression": "[m_12-17]"},
    {"id": "m_18_24", "expression": "[m_18-24]"},
    {"id": "m_25_49", "expression": "[m_25-49]"},
    {"id": "m_50_59", "expression": "[m_50-59]"},
    {"id": "m_60", "expression": "[m_60]"},
]

POP_TYPE_LABELS = {
    "REF": {"en": "Refugees", "fr": "Réfugiés"},
    "ASY": {"en": "Asylum-seekers", "fr": "Demandeurs d'asile"},
    "IDP": {"en": "IDPs", "fr": "PDI"},
    "STA": {"en": "Stateless persons", "fr": "Apatrides"},
    "RET": {"en": "Refugee returnees", "fr": "Rapatriés"},
    "RDP": {"en": "IDP returnees", "fr": "PDI de retour"},
    "OOC": {"en": "Others of concern", "fr": "Autres (OOC)"},
    "NOC": {"en": "Not of concern", "fr": "Hors mandat (NOC)"},
}

# Persons with Specific Needs — common ActivityInfo sn_code labels
PSN_NEED_LABELS = {
    "WR": {"en": "Woman at risk", "fr": "Femme à risque"},
    "CR": {"en": "Child at risk", "fr": "Enfant à risque"},
    "SC": {"en": "Unaccompanied / separated child", "fr": "Enfant non accompagné / séparé"},
    "ER": {"en": "Older person at risk", "fr": "Personne âgée à risque"},
    "DS": {"en": "Disability", "fr": "Handicap"},
    "SM": {"en": "Serious medical condition", "fr": "Problème médical grave"},
    "SV": {"en": "SGBV survivor", "fr": "Survivant(e) VBG"},
    "TR": {"en": "Torture survivor", "fr": "Survivant(e) de torture"},
    "LP": {"en": "Specific legal / physical protection", "fr": "Protection juridique / physique"},
    "SP": {"en": "Single parent / caregiver", "fr": "Parent / aidant seul(e)"},
    "FU": {"en": "Family unity", "fr": "Unité familiale"},
}

ACCOMMODATION_LABELS = {
    "camp": {"en": "Camp", "fr": "Camp"},
    "out-of-camp": {"en": "Out of camp", "fr": "Hors camp"},
    "unknown": {"en": "Unknown / not reported", "fr": "Inconnu / non renseigné"},
}
