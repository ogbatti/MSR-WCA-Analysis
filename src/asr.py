"""UNHCR Refugee Data Finder (ASR) annual population stocks."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

from src.config import CACHE_DIR

ASR_API_URL = "https://api.unhcr.org/population/v1/population/"
ASR_CACHE = CACHE_DIR / "asr_population.parquet"
ASR_YEAR_FROM = 2018

# Data Finder field → MSR pop_code
ASR_FIELD_MAP = {
    "refugees": "REF",
    "asylum_seekers": "ASY",
    "idps": "IDP",
    "returned_refugees": "RET",
    "returned_idps": "RDP",
    "stateless": "STA",
    "ooc": "OOC",
}


def _to_number(value) -> float:
    if value is None or value == "" or value == "-":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fetch_asr_pages(
    *,
    year_from: int,
    year_to: int,
    coa_iso3: list[str],
) -> list[dict]:
    if not coa_iso3:
        return []
    items: list[dict] = []
    page = 1
    coa = ",".join(sorted({c.strip().upper() for c in coa_iso3 if c}))
    while True:
        resp = requests.get(
            ASR_API_URL,
            params={
                "yearFrom": year_from,
                "yearTo": year_to,
                "coa": coa,
                "cf_type": "ISO",
                "limit": 1000,
                "page": page,
            },
            timeout=90,
        )
        resp.raise_for_status()
        payload = resp.json()
        batch = payload.get("items") or []
        items.extend(batch)
        max_pages = int(payload.get("maxPages") or 1)
        if page >= max_pages or not batch:
            break
        page += 1
    return items


def _fetch_asr_by_origin(
    *,
    year: int,
    coo_iso3: str,
) -> list[dict]:
    """Population rows for one origin, broken down by every asylum country."""
    coo = str(coo_iso3 or "").strip().upper()
    if not coo:
        return []
    items: list[dict] = []
    page = 1
    while True:
        resp = requests.get(
            ASR_API_URL,
            params={
                "yearFrom": year,
                "yearTo": year,
                "coo": coo,
                "coa_all": "true",
                "cf_type": "ISO",
                "limit": 1000,
                "page": page,
            },
            timeout=90,
        )
        resp.raise_for_status()
        payload = resp.json()
        batch = payload.get("items") or []
        items.extend(batch)
        max_pages = int(payload.get("maxPages") or 1)
        if page >= max_pages or not batch:
            break
        page += 1
    return items


@st.cache_data(show_spinner=False, ttl=24 * 3600)
def latest_asr_year() -> int:
    """Most recent Refugee Data Finder end-year with published population rows."""
    now = datetime.now(timezone.utc).year
    fallback = max(ASR_YEAR_FROM, now - 1)
    years: list[int] = []
    try:
        resp = requests.get(
            "https://api.unhcr.org/population/v1/years/",
            params={"limit": 300, "page": 1},
            timeout=60,
        )
        resp.raise_for_status()
        items = resp.json().get("items") or []
        years = sorted(
            {
                int(it["year"])
                for it in items
                if it.get("year") is not None and int(it["year"]) <= now
            },
            reverse=True,
        )
    except Exception:  # noqa: BLE001
        years = list(range(fallback, ASR_YEAR_FROM - 1, -1))

    for y in years:
        try:
            resp = requests.get(
                ASR_API_URL,
                params={
                    "yearFrom": y,
                    "yearTo": y,
                    "cf_type": "ISO",
                    "limit": 1,
                    "page": 1,
                },
                timeout=60,
            )
            resp.raise_for_status()
            if resp.json().get("items"):
                return int(y)
        except Exception:  # noqa: BLE001
            continue
    return fallback


def _items_to_long(items: list[dict]) -> pd.DataFrame:
    rows: list[dict] = []
    for it in items:
        year = it.get("year")
        coa = str(it.get("coa_iso") or "").upper()
        if not year or not coa or coa == "-":
            continue
        for field, code in ASR_FIELD_MAP.items():
            total = _to_number(it.get(field))
            if total <= 0:
                continue
            rows.append(
                {
                    "year": int(year),
                    "asylum_iso3": coa,
                    "pop_code": code,
                    "total": total,
                    "source": "asr",
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=["year", "asylum_iso3", "pop_code", "total", "source"]
        )
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False, ttl=24 * 3600)
def load_asr_population(
    coa_iso3: tuple[str, ...],
    year_from: int = ASR_YEAR_FROM,
    year_to: int | None = None,
) -> pd.DataFrame:
    """
    Annual ASR stocks for selected countries of asylum (ISO3).
    Cached in memory (24h) and on disk parquet for offline reuse.
    """
    codes = tuple(sorted({c.strip().upper() for c in coa_iso3 if c}))
    if not codes:
        return pd.DataFrame(
            columns=["year", "asylum_iso3", "pop_code", "total", "source"]
        )

    if year_to is None:
        # ASR end-year figures typically lag; request through previous calendar year
        year_to = max(year_from, datetime.now(timezone.utc).year - 1)

    # Disk cache key by year range + country set fingerprint
    fingerprint = f"{year_from}_{year_to}_{'-'.join(codes)}"
    disk = CACHE_DIR / f"asr_population_{fingerprint}.parquet"
    if disk.exists():
        try:
            cached = pd.read_parquet(disk)
            if not cached.empty:
                return cached
        except Exception:  # noqa: BLE001
            pass

    items = _fetch_asr_pages(
        year_from=year_from, year_to=year_to, coa_iso3=list(codes)
    )
    df = _items_to_long(items)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(disk, index=False)
        # Keep a latest convenience copy
        df.to_parquet(ASR_CACHE, index=False)
    except Exception:  # noqa: BLE001
        pass
    return df


@st.cache_data(show_spinner=False, ttl=24 * 3600)
def load_asr_origin_ref_asy(
    coo_iso3: str,
    year: int | None = None,
) -> pd.DataFrame:
    """
    Latest (or given) ASR year: REF + ASY stocks from ``coo_iso3`` by host country.

    Uses ``coa_all=true`` so asylum countries are not aggregated away.
    """
    empty = pd.DataFrame(
        columns=[
            "year",
            "origin_iso3",
            "asylum_iso3",
            "asylum_name_en",
            "asylum_name_fr",
            "refugees",
            "asylum_seekers",
            "total",
            "source",
        ]
    )
    coo = str(coo_iso3 or "").strip().upper()
    if not coo:
        return empty

    if year is None:
        year = latest_asr_year()

    # Walk back a few years if the preferred year has no REF/ASY hosts yet
    years_to_try = [int(year)]
    if year is not None:
        for back in range(1, 4):
            y = int(year) - back
            if y >= ASR_YEAR_FROM:
                years_to_try.append(y)

    last_empty = empty
    for y in years_to_try:
        disk = CACHE_DIR / f"asr_origin_ref_asy_{coo}_{y}.parquet"
        if disk.exists():
            try:
                cached = pd.read_parquet(disk)
                if not cached.empty:
                    return cached
            except Exception:  # noqa: BLE001
                pass

        items = _fetch_asr_by_origin(year=int(y), coo_iso3=coo)
        rows: list[dict] = []
        for it in items:
            coa = str(it.get("coa_iso") or "").upper()
            if not coa or coa == "-":
                continue
            if coa == coo:
                continue
            ref = _to_number(it.get("refugees"))
            asy = _to_number(it.get("asylum_seekers"))
            total = ref + asy
            if total <= 0:
                continue
            name_en = str(it.get("coa_name") or coa)
            rows.append(
                {
                    "year": int(it.get("year") or y),
                    "origin_iso3": coo,
                    "asylum_iso3": coa,
                    "asylum_name_en": name_en,
                    "asylum_name_fr": name_en,
                    "refugees": ref,
                    "asylum_seekers": asy,
                    "total": total,
                    "source": "asr",
                }
            )
        if not rows:
            continue

        df = (
            pd.DataFrame(rows)
            .groupby(
                [
                    "year",
                    "origin_iso3",
                    "asylum_iso3",
                    "asylum_name_en",
                    "asylum_name_fr",
                    "source",
                ],
                as_index=False,
            )
            .agg(
                refugees=("refugees", "sum"),
                asylum_seekers=("asylum_seekers", "sum"),
                total=("total", "sum"),
            )
            .sort_values("total", ascending=False)
            .reset_index(drop=True)
        )
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            df.to_parquet(disk, index=False)
        except Exception:  # noqa: BLE001
            pass
        return df

    return last_empty
