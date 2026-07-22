"""Scenario-based forecasting of stocks to 2036."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ScenarioAssumptions:
    name: str
    annual_growth: float  # baseline natural / residual growth
    conflict_shock: float  # additive annual shock as share of stock (new displacements)
    return_rate: float  # annual share leaving stock via returns/solutions
    description_en: str
    description_fr: str


DEFAULT_SCENARIOS = [
    ScenarioAssumptions(
        name="baseline",
        annual_growth=0.015,
        conflict_shock=0.02,
        return_rate=0.025,
        description_en="Moderate residual growth, limited new conflict, gradual returns.",
        description_fr="Croissance résiduelle modérée, conflits limités, retours progressifs.",
    ),
    ScenarioAssumptions(
        name="optimistic",
        annual_growth=0.005,
        conflict_shock=0.005,
        return_rate=0.05,
        description_en="Stabilisation and stronger solutions/returns.",
        description_fr="Stabilisation et solutions/retours plus robustes.",
    ),
    ScenarioAssumptions(
        name="pessimistic",
        annual_growth=0.02,
        conflict_shock=0.06,
        return_rate=0.01,
        description_en="Recurring conflict shocks and weak return conditions.",
        description_fr="Chocs conflictuels récurrents et conditions de retour faibles.",
    ),
]


def net_annual_rate(s: ScenarioAssumptions) -> float:
    return (1 + s.annual_growth + s.conflict_shock) * (1 - s.return_rate) - 1


def project_stock(
    history_annual: pd.DataFrame,
    pop_code: str,
    horizon_year: int = 2036,
    scenarios: list[ScenarioAssumptions] | None = None,
    custom: ScenarioAssumptions | None = None,
) -> pd.DataFrame:
    """
    Project year-end stock for one population type.

    history_annual: columns year, pop_code, total (one row per year)
    """
    scenarios = list(scenarios or DEFAULT_SCENARIOS)
    if custom is not None:
        scenarios = [s for s in scenarios if s.name != custom.name] + [custom]

    hist = history_annual[history_annual["pop_code"] == pop_code].sort_values("year")
    if hist.empty:
        return pd.DataFrame()

    last_year = int(hist["year"].max())
    last_value = float(hist.loc[hist["year"] == last_year, "total"].iloc[0])

    rows: list[dict] = []
    for _, r in hist.iterrows():
        rows.append(
            {
                "year": int(r["year"]),
                "pop_code": pop_code,
                "scenario": "historical",
                "total": float(r["total"]),
                "kind": "historical",
            }
        )

    for sc in scenarios:
        value = last_value
        rate = net_annual_rate(sc)
        for year in range(last_year + 1, horizon_year + 1):
            value = max(0.0, value * (1 + rate))
            rows.append(
                {
                    "year": year,
                    "pop_code": pop_code,
                    "scenario": sc.name,
                    "total": value,
                    "kind": "forecast",
                    "net_rate": rate,
                    "annual_growth": sc.annual_growth,
                    "conflict_shock": sc.conflict_shock,
                    "return_rate": sc.return_rate,
                }
            )

    return pd.DataFrame(rows)


def project_multi(
    history_annual: pd.DataFrame,
    pop_codes: list[str],
    horizon_year: int = 2036,
    growth: float = 0.015,
    conflict: float = 0.02,
    returns: float = 0.025,
) -> pd.DataFrame:
    custom = ScenarioAssumptions(
        name="custom",
        annual_growth=growth,
        conflict_shock=conflict,
        return_rate=returns,
        description_en="User-defined business assumptions.",
        description_fr="Hypothèses métier définies par l'utilisateur.",
    )
    frames = [
        project_stock(history_annual, code, horizon_year=horizon_year, custom=custom)
        for code in pop_codes
    ]
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def scenario_table(lang: str = "fr") -> pd.DataFrame:
    rows = []
    for s in DEFAULT_SCENARIOS:
        rows.append(
            {
                "scenario": s.name,
                "description": s.description_fr if lang == "fr" else s.description_en,
                "annual_growth": s.annual_growth,
                "conflict_shock": s.conflict_shock,
                "return_rate": s.return_rate,
                "net_rate": net_annual_rate(s),
            }
        )
    return pd.DataFrame(rows)
