"""Data loading, caching and normalization."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.activityinfo_client import ActivityInfoClient
from src.config import (
    CACHE_DIR,
    FORM_COUNTRIES,
    FORM_GEOLOC,
    FORM_POPULATION,
    FORM_POP_TYPES,
    FORM_PSN,
    FORM_TOTAL_PSN,
    POP_COLUMNS,
)


def _cache_path(name: str) -> Path:
    return CACHE_DIR / name


@st.cache_data(show_spinner=False, ttl=3600)
def load_countries() -> pd.DataFrame:
    client = ActivityInfoClient()
    rows = client.query_form_default(FORM_COUNTRIES)
    df = pd.DataFrame(rows)
    keep = [
        "country_hcr3",
        "iso2",
        "iso3",
        "name_fr",
        "name_en",
        "capital",
        "latitude",
        "longitude",
    ]
    df = df[[c for c in keep if c in df.columns]].dropna(subset=["country_hcr3"])
    df = df.drop_duplicates(subset=["country_hcr3"])
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=3600)
def load_population_types() -> pd.DataFrame:
    client = ActivityInfoClient()
    rows = client.query_form_default(FORM_POP_TYPES)
    df = pd.DataFrame(rows)
    df = df.rename(
        columns={"Code": "pop_code", "Label (Description)": "pop_label_fr"}
    )
    return df[["pop_code", "pop_label_fr"]].drop_duplicates().reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=3600)
def load_geoloc() -> pd.DataFrame:
    client = ActivityInfoClient()
    rows = client.query_form_default(FORM_GEOLOC)
    df = pd.DataFrame(rows)
    rename = {
        "country_hcr3.iso3": "iso3",
        "country_hcr3.country_hcr3": "country_hcr3",
        "country_hcr3.name_en": "name_en",
        "country_hcr3.name_fr": "name_fr",
    }
    df = df.rename(columns=rename)
    cols = [
        "country_hcr3",
        "iso3",
        "name_en",
        "name_fr",
        "admin1_name",
        "admin2_name",
        "admin3_name",
        "level",
        "latitude",
        "longitude",
        "flag_geocoded",
    ]
    return df[[c for c in cols if c in df.columns]].copy()


def _origin_lookup(countries: pd.DataFrame) -> pd.DataFrame:
    """WCA countries + major external origins (Sudan, Rwanda, etc.)."""
    from src.reference_data import EXTERNAL_ORIGINS

    origin_rows = []
    for _, r in countries.iterrows():
        origin_rows.append(
            {
                "origin_hcr3": r["country_hcr3"],
                "origin_iso3": r.get("iso3"),
                "origin_name_en": r.get("name_en"),
                "origin_name_fr": r.get("name_fr"),
                "origin_lat": r.get("latitude"),
                "origin_lon": r.get("longitude"),
            }
        )
    known = {r["origin_hcr3"] for r in origin_rows}
    for hcr3, meta in EXTERNAL_ORIGINS.items():
        if hcr3 not in known:
            origin_rows.append(
                {
                    "origin_hcr3": hcr3,
                    "origin_iso3": meta["iso3"],
                    "origin_name_en": meta["name_en"],
                    "origin_name_fr": meta["name_fr"],
                    "origin_lat": meta["latitude"],
                    "origin_lon": meta["longitude"],
                }
            )
    return pd.DataFrame(origin_rows).drop_duplicates("origin_hcr3").set_index("origin_hcr3")


def _apply_origin_enrichment(df: pd.DataFrame, countries: pd.DataFrame) -> pd.DataFrame:
    """(Re)attach origin names / coordinates, including external origins."""
    if "origin_hcr3" not in df.columns:
        return df
    origin_map = _origin_lookup(countries)
    out = df.drop(
        columns=[c for c in df.columns if c.startswith("origin_") and c != "origin_hcr3"],
        errors="ignore",
    )
    out = out.merge(origin_map, left_on="origin_hcr3", right_index=True, how="left")
    out["origin_name_en"] = out["origin_name_en"].fillna(out["origin_hcr3"])
    out["origin_name_fr"] = out["origin_name_fr"].fillna(out["origin_hcr3"])
    return out


def _normalize_population(df: pd.DataFrame, countries: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    num_cols = [
        c
        for c in df.columns
        if c
        in {
            "female",
            "male",
            "total",
            "f_0_4",
            "f_5_11",
            "f_12_17",
            "f_18_24",
            "f_25_49",
            "f_50_59",
            "f_60",
            "m_0_4",
            "m_5_11",
            "m_12_17",
            "m_18_24",
            "m_25_49",
            "m_50_59",
            "m_60",
            "asylum_lat",
            "asylum_lon",
        }
    ]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    df = _apply_origin_enrichment(df, countries)

    df["children"] = (
        df["f_0_4"]
        + df["f_5_11"]
        + df["f_12_17"]
        + df["m_0_4"]
        + df["m_5_11"]
        + df["m_12_17"]
    )
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    df["year"] = df["date"].dt.year
    return df


@st.cache_data(show_spinner="Loading population data from ActivityInfo…", ttl=3600)
def load_population(force_refresh: bool = False) -> pd.DataFrame:
    parquet = _cache_path("population.parquet")
    countries = load_countries()

    if parquet.exists() and not force_refresh:
        df = pd.read_parquet(parquet)
        df["date"] = pd.to_datetime(df["date"])
        # Re-enrich so external-origin centroids stay up to date without full API reload
        df = _apply_origin_enrichment(df, countries)
        if "year_month" not in df.columns:
            df["year_month"] = df["date"].dt.to_period("M").astype(str)
        if "year" not in df.columns:
            df["year"] = df["date"].dt.year
        return df

    client = ActivityInfoClient()
    rows = client.query_rows(FORM_POPULATION, POP_COLUMNS)
    df = pd.DataFrame(rows)
    df = _normalize_population(df, countries)
    df.to_parquet(parquet, index=False)
    return df


@st.cache_data(show_spinner=False, ttl=3600)
def load_total_psn() -> pd.DataFrame:
    client = ActivityInfoClient()
    rows = client.query_form_default(FORM_TOTAL_PSN)
    df = pd.DataFrame(rows)
    rename = {
        "population_type.Code": "pop_code",
        "population_type.Label (Description)": "pop_label",
        "asylum.iso3": "asylum_iso3",
        "asylum.country_hcr3": "asylum_hcr3",
        "asylum.name_en": "asylum_name_en",
        "asylum.name_fr": "asylum_name_fr",
        "total_psn": "total",
    }
    df = df.rename(columns=rename)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0.0)
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    return df


@st.cache_data(show_spinner=False, ttl=3600)
def load_psn() -> pd.DataFrame:
    client = ActivityInfoClient()
    rows = client.query_form_default(FORM_PSN)
    df = pd.DataFrame(rows)
    rename = {
        "population_type.Code": "pop_code",
        "asylum.iso3": "asylum_iso3",
        "asylum.country_hcr3": "asylum_hcr3",
        "asylum.name_en": "asylum_name_en",
        "asylum.name_fr": "asylum_name_fr",
    }
    df = df.rename(columns=rename)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in ["female", "male", "total"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    return df


def analytical_subset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prefer `detailed` rows when a population type has them (admin-level grain).
    Fall back to `total`, then `male_female`, for types like IDP/STA that are
    only reported at coarser aggregation levels.
    """
    if df.empty or "aggregation_type" not in df.columns:
        return df.copy()

    preference = ["detailed", "total", "male_female", "male_female_18_59"]
    frames: list[pd.DataFrame] = []
    for _, group in df.groupby("pop_code", dropna=False):
        available = set(group["aggregation_type"].dropna().unique())
        chosen = next((a for a in preference if a in available), None)
        if chosen is None:
            frames.append(group)
        else:
            frames.append(group[group["aggregation_type"] == chosen])
    return pd.concat(frames, ignore_index=True) if frames else df.iloc[0:0].copy()


def filter_population(
    df: pd.DataFrame,
    *,
    months: list[str] | None = None,
    pop_codes: list[str] | None = None,
    asylum_iso3: list[str] | None = None,
    origin_hcr3: list[str] | None = None,
    aggregation: str | None = "auto",
) -> pd.DataFrame:
    out = df.copy()
    if aggregation == "auto":
        out = analytical_subset(out)
    elif aggregation:
        out = out[out["aggregation_type"] == aggregation]
    if months:
        out = out[out["year_month"].isin(months)]
    if pop_codes:
        out = out[out["pop_code"].isin(pop_codes)]
    if asylum_iso3:
        out = out[out["asylum_iso3"].isin(asylum_iso3)]
    if origin_hcr3:
        out = out[out["origin_hcr3"].isin(origin_hcr3)]
    return out
