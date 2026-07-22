"""Key indicator calculations."""
from __future__ import annotations

import pandas as pd


def monthly_stock(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate stock by month and population type."""
    if df.empty:
        return pd.DataFrame(
            columns=["year_month", "date", "pop_code", "total", "female", "male", "children"]
        )
    g = (
        df.groupby(["year_month", "pop_code"], as_index=False)
        .agg(
            date=("date", "max"),
            total=("total", "sum"),
            female=("female", "sum"),
            male=("male", "sum"),
            children=("children", "sum"),
        )
        .sort_values(["year_month", "pop_code"])
    )
    return g


def country_stock(df: pd.DataFrame, name_col: str = "asylum_name_en") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    group_cols = [
        "asylum_iso3",
        "asylum_hcr3",
        "asylum_name_en",
        "asylum_name_fr",
        "pop_code",
    ]
    group_cols = [c for c in group_cols if c in df.columns]
    return (
        df.groupby(group_cols, as_index=False, dropna=False)
        .agg(
            total=("total", "sum"),
            female=("female", "sum"),
            male=("male", "sum"),
            children=("children", "sum"),
            asylum_lat=("asylum_lat", "first"),
            asylum_lon=("asylum_lon", "first"),
        )
        .sort_values("total", ascending=False)
    )


def origin_stock(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby(
            ["origin_hcr3", "origin_iso3", "origin_name_en", "origin_name_fr", "pop_code"],
            as_index=False,
        )
        .agg(total=("total", "sum"), female=("female", "sum"), male=("male", "sum"))
        .sort_values("total", ascending=False)
    )


def corridor_flows(
    df: pd.DataFrame,
    top_n: int = 25,
    wca_iso3: list[str] | None = None,
    extra_external: int = 12,
) -> pd.DataFrame:
    """
    Top displacement corridors. Always includes the strongest corridors from
    non-WCA origins (when wca_iso3 is provided) so Sudan, Rwanda, etc. appear.
    """
    if df.empty:
        return pd.DataFrame()
    cols = [
        "origin_hcr3",
        "origin_iso3",
        "origin_name_en",
        "origin_name_fr",
        "origin_lat",
        "origin_lon",
        "asylum_iso3",
        "asylum_name_en",
        "asylum_name_fr",
        "asylum_lat",
        "asylum_lon",
        "pop_code",
    ]
    cols = [c for c in cols if c in df.columns]
    flows = (
        df.groupby(cols, as_index=False, dropna=False)
        .agg(total=("total", "sum"))
        .sort_values("total", ascending=False)
    )
    # Drop same-country "corridors" (typical for IDP)
    if "origin_iso3" in flows.columns and "asylum_iso3" in flows.columns:
        cross = flows[
            flows["origin_iso3"].fillna("") != flows["asylum_iso3"].fillna("")
        ]
        if not cross.empty:
            flows = cross

    top = flows.head(top_n)
    if wca_iso3 and "origin_iso3" in flows.columns and extra_external > 0:
        external = flows[~flows["origin_iso3"].isin(wca_iso3)].head(extra_external)
        top = (
            pd.concat([top, external], ignore_index=True)
            .drop_duplicates()
            .sort_values("total", ascending=False)
        )
    return top


def admin1_stock(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = df.dropna(subset=["coa_admin1"]).copy()
    return (
        out.groupby(
            ["asylum_iso3", "asylum_name_en", "asylum_name_fr", "coa_admin1", "pop_code"],
            as_index=False,
        )
        .agg(total=("total", "sum"), female=("female", "sum"), children=("children", "sum"))
        .sort_values("total", ascending=False)
    )


def admin2_stock(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = df.dropna(subset=["coa_admin2"]).copy()
    return (
        out.groupby(
            [
                "asylum_iso3",
                "asylum_name_en",
                "asylum_name_fr",
                "coa_admin1",
                "coa_admin2",
                "pop_code",
            ],
            as_index=False,
        )
        .agg(total=("total", "sum"), female=("female", "sum"), children=("children", "sum"))
        .sort_values("total", ascending=False)
    )


def mom_yoy(monthly: pd.DataFrame, pop_codes: list[str] | None = None) -> pd.DataFrame:
    """Compute MoM and YoY on total stock for selected population types."""
    if monthly.empty:
        return pd.DataFrame()
    m = monthly.copy()
    if pop_codes:
        m = m[m["pop_code"].isin(pop_codes)]
    totals = (
        m.groupby("year_month", as_index=False)
        .agg(date=("date", "max"), total=("total", "sum"), female=("female", "sum"), children=("children", "sum"))
        .sort_values("year_month")
    )
    totals["mom"] = totals["total"].pct_change()
    totals["mom_abs"] = totals["total"].diff()
    totals["yoy"] = totals["total"].pct_change(12)
    totals["yoy_abs"] = totals["total"].diff(12)
    # Shares vs total only when disaggregation is present in the monthly sum
    totals["female_share"] = totals["female"] / totals["total"].where(totals["female"] > 0, pd.NA)
    totals["children_share"] = totals["children"] / totals["total"].where(
        totals["children"] > 0, pd.NA
    )
    return totals


def kpi_snapshot(df: pd.DataFrame, prev_df: pd.DataFrame | None = None) -> dict:
    total = float(df["total"].sum()) if not df.empty else 0.0
    female = float(df["female"].sum()) if not df.empty else 0.0
    male = float(df["male"].sum()) if not df.empty else 0.0
    children = float(df["children"].sum()) if not df.empty else 0.0
    prev_total = float(prev_df["total"].sum()) if prev_df is not None and not prev_df.empty else None
    mom = ((total - prev_total) / prev_total) if prev_total else None

    # Shares only over rows with sex / age disaggregation
    sex_mask = (df["female"].fillna(0) + df["male"].fillna(0)) > 0 if not df.empty else pd.Series(dtype=bool)
    age_mask = df["children"].fillna(0) > 0 if not df.empty else pd.Series(dtype=bool)
    sex_den = float(df.loc[sex_mask, "total"].sum()) if not df.empty and sex_mask.any() else 0.0
    age_den = float(df.loc[age_mask, "total"].sum()) if not df.empty and age_mask.any() else 0.0
    female_share = (float(df.loc[sex_mask, "female"].sum()) / sex_den) if sex_den else None
    children_share = (float(df.loc[age_mask, "children"].sum()) / age_den) if age_den else None

    def _sum_codes(codes: list[str]) -> float:
        if df.empty or "pop_code" not in df.columns:
            return 0.0
        return float(df.loc[df["pop_code"].isin(codes), "total"].sum())

    return {
        "total": total,
        "ref_asy": _sum_codes(["REF", "ASY"]),
        "idp": _sum_codes(["IDP"]),
        "sta": _sum_codes(["STA"]),
        "returns": _sum_codes(["RET", "RDP"]),
        "female": female,
        "male": male,
        "children": children,
        "female_share": female_share,
        "children_share": children_share,
        "sex_coverage": (sex_den / total) if total else None,
        "age_coverage": (age_den / total) if total else None,
        "mom": mom,
        "mom_abs": (total - prev_total) if prev_total is not None else None,
        "countries": int(df["asylum_iso3"].nunique()) if not df.empty else 0,
        "origins": int(df["origin_hcr3"].nunique()) if not df.empty else 0,
    }


def data_quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Coverage of sex/age and aggregation level used per population type."""
    if df.empty:
        return pd.DataFrame()
    rows = []
    for code, g in df.groupby("pop_code", dropna=False):
        tot = float(g["total"].sum())
        sex_tot = float(g.loc[(g["female"].fillna(0) + g["male"].fillna(0)) > 0, "total"].sum())
        age_tot = float(g.loc[g["children"].fillna(0) > 0, "total"].sum())
        agg = (
            g["aggregation_type"].dropna().mode().iloc[0]
            if "aggregation_type" in g.columns and g["aggregation_type"].notna().any()
            else "—"
        )
        rows.append(
            {
                "pop_code": code,
                "total": tot,
                "sex_coverage": (sex_tot / tot) if tot else 0.0,
                "age_coverage": (age_tot / tot) if tot else 0.0,
                "aggregation": agg,
            }
        )
    return pd.DataFrame(rows).sort_values("total", ascending=False)


def accommodation_stock(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "accommodation_type" not in df.columns:
        return pd.DataFrame()
    out = df.copy()
    out["accommodation_type"] = out["accommodation_type"].fillna("unknown").replace("", "unknown")
    return (
        out.groupby(["accommodation_type", "pop_code"], as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
    )


def admin1_hotspots(
    current: pd.DataFrame, previous: pd.DataFrame, top_n: int = 15
) -> pd.DataFrame:
    """Admin1 areas with largest absolute MoM change."""
    if current.empty:
        return pd.DataFrame()
    name_cols = ["asylum_iso3", "asylum_name_en", "asylum_name_fr", "coa_admin1"]
    name_cols = [c for c in name_cols if c in current.columns]
    cur = (
        current.dropna(subset=["coa_admin1"])
        .groupby(name_cols, as_index=False)["total"]
        .sum()
        .rename(columns={"total": "total_now"})
    )
    if previous is None or previous.empty:
        cur["total_prev"] = 0.0
        cur["mom_abs"] = cur["total_now"]
        cur["mom"] = None
        return cur.sort_values("total_now", ascending=False).head(top_n)

    prev = (
        previous.dropna(subset=["coa_admin1"])
        .groupby(name_cols, as_index=False)["total"]
        .sum()
        .rename(columns={"total": "total_prev"})
    )
    m = cur.merge(prev, on=name_cols, how="outer").fillna(0.0)
    m["mom_abs"] = m["total_now"] - m["total_prev"]
    m["mom"] = m["mom_abs"] / m["total_prev"].where(m["total_prev"] > 0, pd.NA)
    m["abs_change"] = m["mom_abs"].abs()
    return m.sort_values("abs_change", ascending=False).head(top_n)


def returns_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly totals for returnee flows (RET / RDP)."""
    if df.empty:
        return pd.DataFrame()
    r = df[df["pop_code"].isin(["RET", "RDP"])]
    if r.empty:
        return pd.DataFrame()
    return (
        r.groupby(["year_month", "date", "pop_code"], as_index=False)["total"]
        .sum()
        .sort_values(["year_month", "pop_code"])
    )


def psn_by_country(psn_df: pd.DataFrame, lang: str = "fr") -> pd.DataFrame:
    if psn_df is None or psn_df.empty:
        return pd.DataFrame()
    d = psn_df.copy()
    if "year_month" not in d.columns and "date" in d.columns:
        d["year_month"] = pd.to_datetime(d["date"]).dt.to_period("M").astype(str)
    name_col = "asylum_name_fr" if lang == "fr" else "asylum_name_en"
    cols = [c for c in ["asylum_iso3", name_col, "pop_code"] if c in d.columns]
    return (
        d.groupby(cols, as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
    )


def psn_by_need(psn_df: pd.DataFrame) -> pd.DataFrame:
    if psn_df is None or psn_df.empty or "sn_code" not in psn_df.columns:
        return pd.DataFrame()
    return (
        psn_df.groupby("sn_code", as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
    )


def annual_stock(df: pd.DataFrame, pop_codes: list[str] | None = None) -> pd.DataFrame:
    """Year-end (latest month in year) stock by population type."""
    if df.empty:
        return pd.DataFrame()
    m = df.copy()
    if pop_codes:
        m = m[m["pop_code"].isin(pop_codes)]
    # Take latest available month per year
    latest_per_year = (
        m.groupby("year", as_index=False)["date"].max().rename(columns={"date": "year_end"})
    )
    m = m.merge(latest_per_year, on="year")
    m = m[m["date"] == m["year_end"]]
    out = (
        m.groupby(["year", "pop_code"], as_index=False)
        .agg(total=("total", "sum"))
        .sort_values(["year", "pop_code"])
    )
    out["year"] = out["year"].astype(int)
    return out


def age_sex_pyramid(df: pd.DataFrame) -> pd.DataFrame:
    """Build age/sex pyramid totals from detailed age columns."""
    from src.reference_data import AGE_BANDS

    if df.empty:
        return pd.DataFrame(columns=["age_band", "female", "male"])

    rows = []
    for label, f_col, m_col in AGE_BANDS:
        female = float(df[f_col].sum()) if f_col in df.columns else 0.0
        male = float(df[m_col].sum()) if m_col in df.columns else 0.0
        rows.append({"age_band": label, "female": female, "male": male})
    return pd.DataFrame(rows)


def country_pop_breakdown(df: pd.DataFrame, lang: str = "fr") -> pd.DataFrame:
    """
    One row per asylum country with total and one column per population type.
    Used for map hover labels (no ISO code).
    """
    from src.config import POP_TYPE_LABELS

    if df.empty:
        return pd.DataFrame()

    name_col = "asylum_name_fr" if lang == "fr" else "asylum_name_en"
    pivot = (
        df.groupby(["asylum_iso3", name_col, "pop_code"], as_index=False)["total"]
        .sum()
        .pivot_table(
            index=["asylum_iso3", name_col],
            columns="pop_code",
            values="total",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
    )
    pop_cols = [c for c in pivot.columns if c not in {"asylum_iso3", name_col}]
    pivot["total"] = pivot[pop_cols].sum(axis=1)
    # Friendly column names for hover
    rename = {c: POP_TYPE_LABELS.get(c, {}).get(lang, c) for c in pop_cols}
    pivot = pivot.rename(columns=rename)
    pivot = pivot.rename(columns={name_col: "country_name"})
    return pivot.sort_values("total", ascending=False)
