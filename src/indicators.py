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
    """Build standard UNHCR age/sex pyramid (0-4, 5-11, 12-17, 18-59, 60+)."""
    from src.reference_data import AGE_BANDS

    if df.empty:
        return pd.DataFrame(columns=["age_band", "female", "male"])

    def _sum_cols(frame: pd.DataFrame, cols) -> float:
        if isinstance(cols, str):
            cols = [cols]
        return float(sum(frame[c].sum() for c in cols if c in frame.columns))

    rows = []
    for label, f_cols, m_cols in AGE_BANDS:
        rows.append(
            {
                "age_band": label,
                "female": _sum_cols(df, f_cols),
                "male": _sum_cols(df, m_cols),
            }
        )
    return pd.DataFrame(rows)


def age_adult_detail(df: pd.DataFrame) -> pd.DataFrame:
    """Adult sub-bands 18-24 / 25-49 / 50-59 for complementary analysis."""
    from src.reference_data import AGE_BANDS_ADULT_DETAIL

    if df.empty:
        return pd.DataFrame(columns=["age_band", "female", "male", "total"])
    rows = []
    for label, f_col, m_col in AGE_BANDS_ADULT_DETAIL:
        female = float(df[f_col].sum()) if f_col in df.columns else 0.0
        male = float(df[m_col].sum()) if m_col in df.columns else 0.0
        rows.append(
            {"age_band": label, "female": female, "male": male, "total": female + male}
        )
    return pd.DataFrame(rows)


def accommodation_share_ref_asy(df: pd.DataFrame) -> pd.DataFrame:
    """Camp vs out-of-camp shares for REF and ASY only."""
    if df.empty or "accommodation_type" not in df.columns:
        return pd.DataFrame()
    out = df[df["pop_code"].isin(["REF", "ASY"])].copy()
    if out.empty:
        return pd.DataFrame()
    out["accommodation_type"] = (
        out["accommodation_type"].fillna("unknown").replace("", "unknown")
    )
    g = out.groupby("accommodation_type", as_index=False)["total"].sum()
    tot = float(g["total"].sum()) or 1.0
    g["share"] = g["total"] / tot
    return g.sort_values("total", ascending=False)


def registration_share_ref_asy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Individual registration status for REF + ASY (ActivityInfo `basis`).
    `registration` = individually registered; all other / missing = not registered.
    """
    if df.empty or "basis" not in df.columns or "pop_code" not in df.columns:
        return pd.DataFrame()
    out = df[df["pop_code"].isin(["REF", "ASY"])].copy()
    if out.empty:
        return pd.DataFrame()
    basis = out["basis"].fillna("").astype(str).str.strip().str.lower()
    out["registration_status"] = basis.map(
        lambda b: "registered" if b == "registration" else "not_registered"
    )
    g = out.groupby("registration_status", as_index=False)["total"].sum()
    tot = float(g["total"].sum()) or 1.0
    g["share"] = g["total"] / tot
    return g.sort_values("total", ascending=False)


def country_composition_geo(df: pd.DataFrame, lang: str = "fr") -> pd.DataFrame:
    """
    One row per asylum country with lat/lon, total, and one column per pop_code.
    Used for composition pie markers on the map.
    """
    if df.empty:
        return pd.DataFrame()

    name_col = "asylum_name_fr" if lang == "fr" else "asylum_name_en"
    if name_col not in df.columns:
        name_col = "asylum_iso3"

    group_keys = ["asylum_iso3", name_col, "pop_code"]
    group_keys = [c for c in group_keys if c in df.columns]
    pivot = (
        df.groupby(group_keys, as_index=False)["total"]
        .sum()
        .pivot_table(
            index=["asylum_iso3", name_col] if name_col in group_keys else ["asylum_iso3"],
            columns="pop_code",
            values="total",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
    )
    pop_cols = [c for c in pivot.columns if c not in {"asylum_iso3", name_col}]
    pivot["total"] = pivot[pop_cols].sum(axis=1)
    pivot = pivot.rename(columns={name_col: "country_name"})

    coords = (
        df.groupby("asylum_iso3", as_index=False)
        .agg(lat=("asylum_lat", "first"), lon=("asylum_lon", "first"))
        if "asylum_lat" in df.columns and "asylum_lon" in df.columns
        else pd.DataFrame(columns=["asylum_iso3", "lat", "lon"])
    )
    if not coords.empty:
        pivot = pivot.merge(coords, on="asylum_iso3", how="left")
    else:
        pivot["lat"] = None
        pivot["lon"] = None

    return pivot.sort_values("total", ascending=False)


def _country_centroid(
    pop_df: pd.DataFrame,
    geoloc_df: pd.DataFrame,
    asylum_iso3: str,
    countries_df: pd.DataFrame | None = None,
) -> tuple[float, float] | None:
    """Resolve host-country lat/lon: geoloc admin0 → admin1 mean → countries → asylum coords."""
    geo = geoloc_df if geoloc_df is not None and not geoloc_df.empty else pd.DataFrame()
    if not geo.empty and "iso3" in geo.columns:
        g_iso = geo[geo["iso3"].astype(str).str.upper() == str(asylum_iso3).upper()]
        if "level" in g_iso.columns:
            g0 = g_iso[g_iso["level"] == "admin0"]
            if not g0.empty and pd.notna(g0.iloc[0].get("latitude")):
                return float(g0.iloc[0]["latitude"]), float(g0.iloc[0]["longitude"])
            g1 = g_iso[g_iso["level"] == "admin1"].dropna(subset=["latitude", "longitude"])
            if not g1.empty:
                return float(g1["latitude"].mean()), float(g1["longitude"].mean())
        # Any geocoded row for that ISO
        any_g = g_iso.dropna(subset=["latitude", "longitude"])
        if not any_g.empty:
            return float(any_g.iloc[0]["latitude"]), float(any_g.iloc[0]["longitude"])

    if countries_df is not None and not countries_df.empty and "iso3" in countries_df.columns:
        c = countries_df[
            countries_df["iso3"].astype(str).str.upper() == str(asylum_iso3).upper()
        ]
        if (
            not c.empty
            and "latitude" in c.columns
            and pd.notna(c.iloc[0].get("latitude"))
            and pd.notna(c.iloc[0].get("longitude"))
        ):
            return float(c.iloc[0]["latitude"]), float(c.iloc[0]["longitude"])

    if (
        not pop_df.empty
        and "asylum_lat" in pop_df.columns
        and "asylum_lon" in pop_df.columns
    ):
        sub = pop_df.dropna(subset=["asylum_lat", "asylum_lon"])
        if not sub.empty:
            return float(sub.iloc[0]["asylum_lat"]), float(sub.iloc[0]["asylum_lon"])
    return None


def admin1_map_points(
    pop_df: pd.DataFrame,
    geoloc_df: pd.DataFrame,
    asylum_iso3: str,
    countries_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Map points for a host country profile at Admin1 level.

    Aggregate by Admin1 × population type, geocode via Admin1 centroids,
    fall back to country centroid when Admin1 coords are missing.
    """
    if pop_df.empty:
        return pd.DataFrame()

    focus = pop_df[pop_df["asylum_iso3"] == asylum_iso3].copy()
    if focus.empty:
        return pd.DataFrame()

    preferred = focus[focus["pop_code"].isin(["REF", "ASY", "IDP", "STA"])]
    focus = preferred if not preferred.empty else focus

    geo = geoloc_df.copy() if geoloc_df is not None and not geoloc_df.empty else pd.DataFrame()
    if not geo.empty and "iso3" in geo.columns:
        geo = geo[geo["iso3"].astype(str).str.upper() == str(asylum_iso3).upper()]
    g1 = (
        geo[geo["level"] == "admin1"].copy()
        if not geo.empty and "level" in geo.columns
        else pd.DataFrame()
    )
    country_xy = _country_centroid(focus, geoloc_df, asylum_iso3, countries_df)
    country_lat = country_xy[0] if country_xy else None
    country_lon = country_xy[1] if country_xy else None

    def _match_name(frame: pd.DataFrame, col: str, name: object) -> pd.DataFrame:
        if frame.empty or col not in frame.columns or name is None or pd.isna(name):
            return pd.DataFrame()
        return frame[
            frame[col].astype(str).str.strip().str.lower() == str(name).strip().lower()
        ]

    rows: list[dict] = []
    if "coa_admin1" not in focus.columns:
        by_a1 = pd.DataFrame()
    else:
        a1 = focus["coa_admin1"].fillna("").astype(str).str.strip()
        by_a1 = (
            focus.loc[a1 != ""]
            .assign(coa_admin1=a1[a1 != ""])
            .groupby(["coa_admin1", "pop_code"], as_index=False)["total"]
            .sum()
        )
    for _, r in by_a1.iterrows():
        match1 = _match_name(g1, "admin1_name", r["coa_admin1"])
        if not match1.empty:
            lat = float(match1.iloc[0]["latitude"])
            lon = float(match1.iloc[0]["longitude"])
        elif country_lat is not None:
            lat, lon = country_lat, country_lon
        else:
            continue
        rows.append(
            {
                "label": f"{r['coa_admin1']} ({r['pop_code']})",
                "admin2": None,
                "admin1": r["coa_admin1"],
                "pop_code": r["pop_code"],
                "total": r["total"],
                "lat": lat,
                "lon": lon,
                "geo_level": "admin1",
            }
        )

    if rows:
        return pd.DataFrame(rows).sort_values("total", ascending=False)

    # Last resort: one bubble per pop type at country centroid
    if country_lat is None:
        return pd.DataFrame()
    by_pop = focus.groupby("pop_code", as_index=False)["total"].sum()
    for _, r in by_pop.iterrows():
        rows.append(
            {
                "label": f"{asylum_iso3} ({r['pop_code']})",
                "admin2": None,
                "admin1": None,
                "pop_code": r["pop_code"],
                "total": r["total"],
                "lat": country_lat,
                "lon": country_lon,
                "geo_level": "country",
            }
        )
    return pd.DataFrame(rows).sort_values("total", ascending=False) if rows else pd.DataFrame()


def _admin_filled(series: pd.Series | None) -> bool:
    if series is None:
        return False
    s = series.fillna("").astype(str).str.strip()
    return bool((s != "").any())


def residence_map_points(
    pop_df: pd.DataFrame,
    geoloc_df: pd.DataFrame,
    asylum_iso3: str,
    countries_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Residence map points with cascade:
    Admin2 (if filled) → Admin1 (if filled) → whole country.
    """
    if pop_df.empty:
        return pd.DataFrame()

    focus = pop_df[pop_df["asylum_iso3"] == asylum_iso3].copy()
    if focus.empty:
        return pd.DataFrame()

    preferred = focus[focus["pop_code"].isin(["REF", "ASY", "IDP", "STA"])]
    focus = preferred if not preferred.empty else focus

    has_admin2 = _admin_filled(focus["coa_admin2"]) if "coa_admin2" in focus.columns else False
    has_admin1 = _admin_filled(focus["coa_admin1"]) if "coa_admin1" in focus.columns else False

    if has_admin2:
        geo = geoloc_df.copy() if geoloc_df is not None and not geoloc_df.empty else pd.DataFrame()
        if not geo.empty and "iso3" in geo.columns:
            geo = geo[geo["iso3"].astype(str).str.upper() == str(asylum_iso3).upper()]
        g2 = (
            geo[geo["level"] == "admin2"].copy()
            if not geo.empty and "level" in geo.columns
            else pd.DataFrame()
        )
        g1 = (
            geo[geo["level"] == "admin1"].copy()
            if not geo.empty and "level" in geo.columns
            else pd.DataFrame()
        )
        country_xy = _country_centroid(focus, geoloc_df, asylum_iso3, countries_df)
        country_lat = country_xy[0] if country_xy else None
        country_lon = country_xy[1] if country_xy else None

        def _match_name(frame: pd.DataFrame, col: str, name: object) -> pd.DataFrame:
            if frame.empty or col not in frame.columns or name is None or pd.isna(name):
                return pd.DataFrame()
            return frame[
                frame[col].astype(str).str.strip().str.lower()
                == str(name).strip().lower()
            ]

        a2_mask = focus["coa_admin2"].fillna("").astype(str).str.strip() != ""
        subset = focus.loc[a2_mask].copy()
        subset["coa_admin2"] = subset["coa_admin2"].astype(str).str.strip()
        group_cols = ["asylum_iso3", "coa_admin2", "pop_code"]
        if "coa_admin1" in subset.columns:
            group_cols.insert(1, "coa_admin1")
        by_a2 = subset.groupby(group_cols, as_index=False, dropna=False)["total"].sum()
        rows: list[dict] = []
        for _, r in by_a2.iterrows():
            lat = lon = None
            match2 = _match_name(g2, "admin2_name", r["coa_admin2"])
            if not match2.empty:
                lat = float(match2.iloc[0]["latitude"])
                lon = float(match2.iloc[0]["longitude"])
            else:
                match1 = _match_name(g1, "admin1_name", r.get("coa_admin1"))
                if not match1.empty:
                    lat = float(match1.iloc[0]["latitude"])
                    lon = float(match1.iloc[0]["longitude"])
                elif country_lat is not None:
                    lat, lon = country_lat, country_lon
            if lat is None:
                continue
            rows.append(
                {
                    "label": f"{r['coa_admin2']} ({r['pop_code']})",
                    "admin2": r["coa_admin2"],
                    "admin1": r.get("coa_admin1"),
                    "pop_code": r["pop_code"],
                    "total": r["total"],
                    "lat": lat,
                    "lon": lon,
                    # Aggregation level chosen by cascade (not geocode match quality)
                    "geo_level": "admin2",
                }
            )
        if rows:
            return pd.DataFrame(rows).sort_values("total", ascending=False)
        # Admin2 names present but no geocode → try Admin1 / country
        if has_admin1:
            return admin1_map_points(pop_df, geoloc_df, asylum_iso3, countries_df)

    if has_admin1:
        return admin1_map_points(pop_df, geoloc_df, asylum_iso3, countries_df)

    # Neither Admin1 nor Admin2: whole country
    country_xy = _country_centroid(focus, geoloc_df, asylum_iso3, countries_df)
    if country_xy is None:
        return pd.DataFrame()
    country_lat, country_lon = country_xy
    rows = []
    for _, r in focus.groupby("pop_code", as_index=False)["total"].sum().iterrows():
        rows.append(
            {
                "label": f"{asylum_iso3} ({r['pop_code']})",
                "admin2": None,
                "admin1": None,
                "pop_code": r["pop_code"],
                "total": r["total"],
                "lat": country_lat,
                "lon": country_lon,
                "geo_level": "country",
            }
        )
    return pd.DataFrame(rows).sort_values("total", ascending=False) if rows else pd.DataFrame()


def admin2_map_points(
    pop_df: pd.DataFrame,
    geoloc_df: pd.DataFrame,
    asylum_iso3: str,
    countries_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Alias — cascade Admin2 → Admin1 → country (see residence_map_points)."""
    return residence_map_points(pop_df, geoloc_df, asylum_iso3, countries_df)


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
