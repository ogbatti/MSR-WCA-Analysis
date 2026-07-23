"""Tests for analytical aggregation and data-trust helpers (Phase 1)."""
from __future__ import annotations

import pandas as pd

from src.data_loader import analytical_subset, format_data_version
from src.indicators import aggregation_gap_alerts, quality_banner_items


def _rows(records: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(records)


def test_analytical_subset_prefers_detailed_per_type():
    df = _rows(
        [
            {"pop_code": "REF", "aggregation_type": "detailed", "total": 100},
            {"pop_code": "REF", "aggregation_type": "total", "total": 999},
            {"pop_code": "IDP", "aggregation_type": "total", "total": 50},
            {"pop_code": "IDP", "aggregation_type": "male_female", "total": 40},
        ]
    )
    out = analytical_subset(df)
    assert set(out["pop_code"]) == {"REF", "IDP"}
    ref = out[out["pop_code"] == "REF"]
    idp = out[out["pop_code"] == "IDP"]
    assert list(ref["aggregation_type"].unique()) == ["detailed"]
    assert float(ref["total"].sum()) == 100
    assert list(idp["aggregation_type"].unique()) == ["total"]
    assert float(idp["total"].sum()) == 50


def test_analytical_subset_does_not_mix_levels_within_type():
    df = _rows(
        [
            {"pop_code": "ASY", "aggregation_type": "detailed", "total": 10},
            {"pop_code": "ASY", "aggregation_type": "detailed", "total": 5},
            {"pop_code": "ASY", "aggregation_type": "total", "total": 1000},
        ]
    )
    out = analytical_subset(df)
    assert (out["aggregation_type"] == "detailed").all()
    assert float(out["total"].sum()) == 15


def test_aggregation_gap_alerts_flags_large_gap():
    df = _rows(
        [
            {
                "pop_code": "REF",
                "year_month": "2025-01",
                "aggregation_type": "detailed",
                "total": 100,
            },
            {
                "pop_code": "REF",
                "year_month": "2025-01",
                "aggregation_type": "total",
                "total": 200,
            },
            {
                "pop_code": "IDP",
                "year_month": "2025-01",
                "aggregation_type": "detailed",
                "total": 50,
            },
            {
                "pop_code": "IDP",
                "year_month": "2025-01",
                "aggregation_type": "total",
                "total": 51,
            },
        ]
    )
    gaps = aggregation_gap_alerts(df, "2025-01", threshold=0.05)
    assert list(gaps["pop_code"]) == ["REF"]
    assert float(gaps.iloc[0]["gap_rel"]) == 0.5


def test_quality_banner_low_sex_coverage():
    current = _rows(
        [
            {
                "pop_code": "REF",
                "total": 100,
                "female": 0,
                "male": 0,
                "children": 0,
                "aggregation_type": "detailed",
            }
        ]
    )
    items = quality_banner_items(current)
    codes = [i["code"] for i in items]
    assert "quality_low_sex" in codes


def test_format_data_version_fr_en():
    meta = {
        "extracted_at": "2026-07-23T10:00:00Z",
        "source": "api",
        "n_rows": 1200,
        "date_min": "2024-01-01",
        "date_max": "2026-06-01",
    }
    fr = format_data_version(meta, "fr")
    en = format_data_version(meta, "en")
    assert "ActivityInfo" in en or "extracted" in en
    assert "Données ActivityInfo" in fr
    assert "1200" in fr.replace(" ", "") or "1 200" in fr
