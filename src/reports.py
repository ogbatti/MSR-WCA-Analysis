"""PDF report generators for MSR WCA (fpdf2)."""
from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd
from fpdf import FPDF

from src.config import ACCOMMODATION_LABELS, POP_TYPE_LABELS, PSN_NEED_LABELS
from src.indicators import (
    accommodation_share_ref_asy,
    age_sex_pyramid,
    corridor_flows,
    country_stock,
    data_quality_summary,
    kpi_snapshot,
    mom_yoy,
    monthly_stock,
    origin_stock,
    psn_by_country,
    psn_by_need,
    returns_monthly,
)
from src.narratives import pop_label
from src.reference_data import format_month_label
from src.theme import (
    BLUE_PRIMARY,
    CYAN_PRIMARY,
    GREY_PRIMARY,
    POPULATION_COLORS,
    RED_PRIMARY,
    YELLOW_PRIMARY,
)

# Report order requested by user: 1, 2, 6, 3, 7, 4, 5
REPORT_CATALOG = [
    {
        "id": "flash",
        "order": 1,
        "title": {
            "fr": "1. MSR flash mensuel",
            "en": "1. Monthly MSR flash",
        },
        "desc": {
            "fr": "KPI du mois, variation MoM, top pays d'asile/origine, pyramide des âges.",
            "en": "Month KPIs, MoM change, top asylum/origin countries, age–sex pyramid.",
        },
    },
    {
        "id": "country",
        "order": 2,
        "title": {
            "fr": "2. Profil pays",
            "en": "2. Country profile",
        },
        "desc": {
            "fr": "Fiche d'un pays d'asile : totaux par type, origines, Admin1, hébergement.",
            "en": "Country of asylum brief: totals by type, origins, Admin1, accommodation.",
        },
        "needs_country": True,
    },
    {
        "id": "trend",
        "order": 3,
        "title": {
            "fr": "3. Tendance régionale",
            "en": "3. Regional trend",
        },
        "desc": {
            "fr": "Évolution multi-mois, variation nette, flux de retours RET/RDP.",
            "en": "Multi-month evolution, net change, RET/RDP returnee flows.",
        },
    },
    {
        "id": "corridors",
        "order": 4,
        "title": {
            "fr": "4. Corridors & origines",
            "en": "4. Corridors & origins",
        },
        "desc": {
            "fr": "Top corridors REF/ASY et principales origines (y compris hors WCA).",
            "en": "Top REF/ASY corridors and main origins (including outside WCA).",
        },
    },
    {
        "id": "methodology",
        "order": 5,
        "title": {
            "fr": "5. Annexe méthodologique",
            "en": "5. Methodological annex",
        },
        "desc": {
            "fr": "Agrégation detailed/total, couverture sexe/âge, sources et définitions.",
            "en": "detailed/total aggregation, sex/age coverage, sources and definitions.",
        },
    },
    {
        "id": "shelter",
        "order": 6,
        "title": {
            "fr": "6. Hébergement REF/ASY",
            "en": "6. REF/ASY accommodation",
        },
        "desc": {
            "fr": "Part camp vs hors camp / urbain pour réfugiés et demandeurs d'asile.",
            "en": "Camp vs out-of-camp / urban share for refugees and asylum-seekers.",
        },
    },
    {
        "id": "psn",
        "order": 7,
        "title": {
            "fr": "7. Personnes ayant des besoins spécifiques (PSN)",
            "en": "7. Persons with Specific Needs (PSN)",
        },
        "desc": {
            "fr": "Totaux PSN, catégories de besoins et répartition par pays.",
            "en": "PSN totals, need categories and distribution by country.",
        },
    },
]


def _fmt(n: float | None) -> str:
    if n is None or (isinstance(n, float) and n != n):
        return "-"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:,.1f} M".replace(",", " ")
    if abs(n) >= 1_000:
        return f"{n:,.0f}".replace(",", " ")
    return f"{n:,.0f}".replace(",", " ")


def _pct(n: float | None) -> str:
    if n is None or (isinstance(n, float) and n != n):
        return "-"
    return f"{n * 100:.1f}%"


def _font_paths() -> tuple[str | None, str | None]:
    """Locate DejaVu fonts shipped with fpdf2 or common system fonts."""
    try:
        import fpdf

        root = Path(fpdf.__file__).resolve().parent
        regular = root / "font" / "DejaVuSans.ttf"
        bold = root / "font" / "DejaVuSans-Bold.ttf"
        if regular.exists():
            return str(regular), str(bold) if bold.exists() else str(regular)
    except Exception:
        pass
    windir = Path(r"C:\Windows\Fonts")
    for reg, bold in (
        (windir / "arial.ttf", windir / "arialbd.ttf"),
        (windir / "calibri.ttf", windir / "calibrib.ttf"),
    ):
        if reg.exists():
            return str(reg), str(bold if bold.exists() else reg)
    return None, None


class MsrPdf(FPDF):
    def __init__(
        self, lang: str, report_title: str, data_version: str | None = None
    ) -> None:
        super().__init__(format="A4")
        self.lang = lang
        self.report_title = report_title
        self.data_version = data_version or ""
        self.set_auto_page_break(auto=True, margin=18)
        reg, bold = _font_paths()
        if reg:
            self.add_font("Body", "", reg)
            self.add_font("Body", "B", bold or reg)
            self.font_family = "Body"
        else:
            self.font_family = "Helvetica"
        self.add_page()

    def header(self) -> None:
        self.set_font(self.font_family, "B", 10)
        self.set_text_color(0, 114, 188)
        self.cell(0, 6, "UNHCR · RBWCA · DIMA · MSR WCA", ln=True)
        self.set_font(self.font_family, "", 8)
        self.set_text_color(80, 80, 80)
        self.cell(0, 5, self.report_title, ln=True)
        if self.data_version:
            self.set_text_color(100, 100, 100)
            self.multi_cell(0, 4, self.data_version[:160])
        self.ln(2)
        self.set_draw_color(0, 114, 188)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font(self.font_family, "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(
            0,
            8,
            f"© UNHCR · {date.today().isoformat()} · {self.page_no()}",
            align="C",
        )

    def h1(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font(self.font_family, "B", 14)
        self.set_text_color(11, 55, 84)
        self.multi_cell(0, 8, text)
        self.ln(2)

    def h2(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font(self.font_family, "B", 11)
        self.set_text_color(0, 114, 188)
        self.multi_cell(0, 7, text)
        self.ln(1)

    def p(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font(self.font_family, "", 10)
        self.set_text_color(38, 38, 38)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font(self.font_family, "", 10)
        self.set_text_color(38, 38, 38)
        self.multi_cell(0, 5.5, f"- {text}")

    def kv(self, label: str, value: str) -> None:
        self.set_x(self.l_margin)
        self.set_font(self.font_family, "B", 10)
        self.set_text_color(38, 38, 38)
        self.cell(70, 6, label)
        self.set_font(self.font_family, "", 10)
        self.multi_cell(0, 6, value)
        self.ln(0.5)

    def table(self, headers: list[str], rows: list[list[str]], col_widths: list[float] | None = None) -> None:
        if not rows:
            self.p("-")
            return
        n = len(headers)
        widths = col_widths or [180 / n] * n
        self.set_x(self.l_margin)
        self.set_font(self.font_family, "B", 9)
        self.set_fill_color(205, 227, 241)
        self.set_text_color(11, 55, 84)
        for i, h in enumerate(headers):
            self.cell(widths[i], 7, h, border=1, fill=True)
        self.ln()
        self.set_font(self.font_family, "", 9)
        self.set_text_color(38, 38, 38)
        fill = False
        for row in rows:
            if self.get_y() > 270:
                self.add_page()
            self.set_x(self.l_margin)
            self.set_fill_color(247, 251, 254)
            for i, cell in enumerate(row):
                self.cell(widths[i], 6, str(cell)[:48], border=1, fill=fill)
            self.ln()
            fill = not fill
        self.ln(2)

    def chart(self, png: bytes | None, width: float = 180) -> None:
        """Embed a PNG chart; start a new page if little vertical space remains."""
        if not png:
            return
        if self.get_y() > 155:
            self.add_page()
        self.image(BytesIO(png), x=self.l_margin, w=width)
        self.ln(4)

    def to_bytes(self) -> bytes:
        out = self.output()
        if isinstance(out, (bytes, bytearray)):
            return bytes(out)
        return str(out).encode("latin-1", errors="replace")


def _host_name(df: pd.DataFrame, lang: str) -> str:
    col = "asylum_name_fr" if lang == "fr" else "asylum_name_en"
    return col if col in df.columns else "asylum_name_en"


def _origin_name(lang: str) -> str:
    return "origin_name_fr" if lang == "fr" else "origin_name_en"


# ── Chart helpers (matplotlib → PNG for fpdf2) ──────────────────────────────


def _fig_to_png(fig: plt.Figure) -> bytes:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()


def _style_ax(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors="#262626", labelsize=8)
    ax.yaxis.label.set_color("#262626")
    ax.xaxis.label.set_color("#262626")
    ax.grid(axis="x", color="#E5E5E5", linewidth=0.6)
    ax.set_axisbelow(True)


def _hbar_png(
    labels: list[str],
    values: list[float],
    *,
    title: str = "",
    color: str = BLUE_PRIMARY,
    colors: list[str] | None = None,
) -> bytes | None:
    if not labels or not values:
        return None
    labels = [str(x)[:36] for x in labels]
    n = len(labels)
    fig_h = max(2.2, 0.38 * n + 0.8)
    fig, ax = plt.subplots(figsize=(7.2, fig_h))
    y = np.arange(n)
    bar_colors = colors if colors and len(colors) == n else [color] * n
    ax.barh(y, values, color=bar_colors, height=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    if title:
        ax.set_title(title, fontsize=10, color="#0B3754", pad=8, loc="left")
    _style_ax(ax)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return _fig_to_png(fig)


def _vbar_png(
    labels: list[str],
    values: list[float],
    *,
    title: str = "",
    colors: list[str] | None = None,
) -> bytes | None:
    if not labels or not values:
        return None
    labels = [str(x)[:28] for x in labels]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    x = np.arange(len(labels))
    bar_colors = colors or [BLUE_PRIMARY] * len(labels)
    ax.bar(x, values, color=bar_colors, width=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    if title:
        ax.set_title(title, fontsize=10, color="#0B3754", pad=8, loc="left")
    _style_ax(ax)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color="#E5E5E5", linewidth=0.6)
    fig.tight_layout()
    return _fig_to_png(fig)


def _line_png(
    x_labels: list[str],
    series: dict[str, list[float]],
    *,
    title: str = "",
    colors: dict[str, str] | None = None,
) -> bytes | None:
    if not x_labels or not series:
        return None
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    x = np.arange(len(x_labels))
    default_palette = [BLUE_PRIMARY, RED_PRIMARY, YELLOW_PRIMARY, CYAN_PRIMARY]
    for i, (name, vals) in enumerate(series.items()):
        c = (colors or {}).get(name, default_palette[i % len(default_palette)])
        ax.plot(x, vals, color=c, linewidth=2.0, marker="o", markersize=3.5, label=name)
    step = max(1, len(x_labels) // 8)
    ticks = list(range(0, len(x_labels), step))
    ax.set_xticks(ticks)
    ax.set_xticklabels([x_labels[i] for i in ticks], rotation=30, ha="right")
    if title:
        ax.set_title(title, fontsize=10, color="#0B3754", pad=8, loc="left")
    if len(series) > 1:
        ax.legend(frameon=False, fontsize=8, loc="best")
    _style_ax(ax)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color="#E5E5E5", linewidth=0.6)
    fig.tight_layout()
    return _fig_to_png(fig)


def _pie_png(
    labels: list[str],
    values: list[float],
    *,
    title: str = "",
    colors: list[str] | None = None,
) -> bytes | None:
    if not labels or not values or sum(values) <= 0:
        return None
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    palette = colors or [BLUE_PRIMARY, RED_PRIMARY, GREY_PRIMARY, YELLOW_PRIMARY]
    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        colors=palette[: len(values)],
        autopct=lambda p: f"{p:.1f}%" if p >= 3 else "",
        startangle=90,
        pctdistance=0.72,
        wedgeprops=dict(width=0.55, edgecolor="white", linewidth=1.5),
    )
    for t in autotexts:
        t.set_fontsize(8)
        t.set_color("#262626")
    ax.legend(
        wedges,
        [str(l)[:40] for l in labels],
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        frameon=False,
        fontsize=8,
    )
    if title:
        ax.set_title(title, fontsize=10, color="#0B3754", pad=8, loc="left")
    fig.tight_layout()
    return _fig_to_png(fig)


def _pyramid_png(
    age_bands: list[str],
    female: list[float],
    male: list[float],
    *,
    title: str = "",
    lang: str = "fr",
) -> bytes | None:
    if not age_bands:
        return None
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    y = np.arange(len(age_bands))
    f_vals = [-abs(float(v)) for v in female]
    m_vals = [abs(float(v)) for v in male]
    ax.barh(y, f_vals, color="#D25A45", height=0.75, label="Femmes" if lang == "fr" else "Female")
    ax.barh(y, m_vals, color=BLUE_PRIMARY, height=0.75, label="Hommes" if lang == "fr" else "Male")
    ax.set_yticks(y)
    ax.set_yticklabels(age_bands)
    ax.axvline(0, color="#737373", linewidth=0.8)
    xmax = max(max(abs(v) for v in f_vals + m_vals) or 1, 1)
    ax.set_xlim(-xmax * 1.15, xmax * 1.15)
    xticks = ax.get_xticks()
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{abs(t):,.0f}" for t in xticks])
    if title:
        ax.set_title(title, fontsize=10, color="#0B3754", pad=8, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    _style_ax(ax)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return _fig_to_png(fig)


def _stacked_hbar_png(
    categories: list[str],
    series: dict[str, list[float]],
    *,
    title: str = "",
    colors: dict[str, str] | None = None,
) -> bytes | None:
    if not categories or not series:
        return None
    n = len(categories)
    fig_h = max(2.4, 0.4 * n + 0.9)
    fig, ax = plt.subplots(figsize=(7.2, fig_h))
    y = np.arange(n)
    left = np.zeros(n)
    default = {
        "camp": RED_PRIMARY,
        "out-of-camp": BLUE_PRIMARY,
        "unknown": GREY_PRIMARY,
    }
    for name, vals in series.items():
        c = (colors or default).get(name, BLUE_PRIMARY)
        ax.barh(y, vals, left=left, color=c, height=0.7, label=name)
        left = left + np.array(vals, dtype=float)
    ax.set_yticks(y)
    ax.set_yticklabels([str(c)[:32] for c in categories])
    ax.invert_yaxis()
    if title:
        ax.set_title(title, fontsize=10, color="#0B3754", pad=8, loc="left")
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    _style_ax(ax)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return _fig_to_png(fig)


def _pop_colors(codes: list[str]) -> list[str]:
    return [POPULATION_COLORS.get(c, BLUE_PRIMARY) for c in codes]


def build_flash_pdf(
    *,
    lang: str,
    month: str,
    month_label: str,
    current: pd.DataFrame,
    previous: pd.DataFrame,
    pop_codes: list[str],
    data_version: str | None = None,
) -> bytes:
    title = REPORT_CATALOG[0]["title"][lang]
    pdf = MsrPdf(lang, title, data_version=data_version)
    pdf.h1(title)
    pdf.p(
        f"{'Reference month' if lang == 'en' else 'Mois de référence'} : {month_label}"
    )
    kpi = kpi_snapshot(current, previous)
    pdf.h2("Key indicators" if lang == "en" else "Indicateurs clés")
    pdf.kv("Total population" if lang == "en" else "Population totale", _fmt(kpi["total"]))
    pdf.kv("REF + ASY", _fmt(kpi.get("ref_asy")))
    pdf.kv("IDP" if lang == "en" else "PDI", _fmt(kpi.get("idp")))
    pdf.kv("Stateless" if lang == "en" else "Apatrides", _fmt(kpi.get("sta")))
    pdf.kv("MoM", f"{_pct(kpi.get('mom'))} ({_fmt(kpi.get('mom_abs'))})")
    pdf.kv(
        "Female / children*" if lang == "en" else "Femmes / enfants*",
        f"{_pct(kpi.get('female_share'))} / {_pct(kpi.get('children_share'))}",
    )
    pdf.p(
        "* Shares on disaggregated populations only."
        if lang == "en"
        else "* Parts calculées uniquement sur les populations ventilées."
    )

    host_col = _host_name(current, lang)
    hosts = (
        country_stock(current)
        .groupby(["asylum_iso3", host_col], as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
        .head(8)
    )
    pdf.h2("Top countries of asylum" if lang == "en" else "Top pays d'asile")
    pdf.chart(
        _hbar_png(
            [str(r[host_col]) for _, r in hosts.iterrows()],
            [float(r["total"]) for _, r in hosts.iterrows()],
            title="Top pays d'asile" if lang == "fr" else "Top countries of asylum",
        )
    )
    pdf.table(
        ["Country" if lang == "en" else "Pays", "Total"],
        [[str(r[host_col]), _fmt(r["total"])] for _, r in hosts.iterrows()],
        [120, 60],
    )

    o_col = _origin_name(lang)
    origins = (
        origin_stock(current)
        .groupby(["origin_hcr3", o_col], as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
        .head(8)
    )
    pdf.h2("Top countries of origin" if lang == "en" else "Top pays d'origine")
    pdf.chart(
        _hbar_png(
            [str(r[o_col]) for _, r in origins.iterrows()],
            [float(r["total"]) for _, r in origins.iterrows()],
            title="Top pays d'origine" if lang == "fr" else "Top countries of origin",
            color=CYAN_PRIMARY,
        )
    )
    pdf.table(
        ["Origin" if lang == "en" else "Origine", "Total"],
        [[str(r[o_col]), _fmt(r["total"])] for _, r in origins.iterrows()],
        [120, 60],
    )

    pyr = age_sex_pyramid(current)
    if not pyr.empty:
        pdf.h2("Age–sex pyramid (UNHCR bands)" if lang == "en" else "Pyramide des âges (tranches HCR)")
        pdf.chart(
            _pyramid_png(
                [str(r["age_band"]) for _, r in pyr.iterrows()],
                [float(r["female"]) for _, r in pyr.iterrows()],
                [float(r["male"]) for _, r in pyr.iterrows()],
                title="Pyramide des âges" if lang == "fr" else "Age–sex pyramid",
                lang=lang,
            )
        )
        pdf.table(
            ["Age", "Female" if lang == "en" else "Femmes", "Male" if lang == "en" else "Hommes"],
            [
                [r["age_band"], _fmt(r["female"]), _fmt(r["male"])]
                for _, r in pyr.iterrows()
            ],
            [40, 70, 70],
        )
    pdf.p(
        f"{'Selected types' if lang == 'en' else 'Types sélectionnés'} : "
        + ", ".join(pop_label(c, lang) for c in pop_codes)
    )
    return pdf.to_bytes()


def build_country_pdf(
    *,
    lang: str,
    month_label: str,
    country_iso3: str,
    country_name: str,
    current: pd.DataFrame,
    previous: pd.DataFrame,
    data_version: str | None = None,
) -> bytes:
    title = REPORT_CATALOG[1]["title"][lang]
    pdf = MsrPdf(lang, f"{title} — {country_name}", data_version=data_version)
    pdf.h1(f"{title} — {country_name}")
    pdf.p(f"{'Month' if lang == 'en' else 'Mois'} : {month_label}")
    cdf = current[current["asylum_iso3"] == country_iso3]
    pdf_prev = previous[previous["asylum_iso3"] == country_iso3]
    kpi = kpi_snapshot(cdf, pdf_prev)
    pdf.h2("Overview" if lang == "en" else "Vue d'ensemble")
    pdf.kv("Total", _fmt(kpi["total"]))
    pdf.kv("REF + ASY", _fmt(kpi.get("ref_asy")))
    pdf.kv("IDP" if lang == "en" else "PDI", _fmt(kpi.get("idp")))
    pdf.kv("MoM", f"{_pct(kpi.get('mom'))} ({_fmt(kpi.get('mom_abs'))})")

    by_type = cdf.groupby("pop_code", as_index=False)["total"].sum().sort_values("total", ascending=False)
    pdf.h2("By population type" if lang == "en" else "Par type de population")
    pdf.chart(
        _vbar_png(
            [pop_label(r["pop_code"], lang) for _, r in by_type.iterrows()],
            [float(r["total"]) for _, r in by_type.iterrows()],
            title="Par type de population" if lang == "fr" else "By population type",
            colors=_pop_colors([str(r["pop_code"]) for _, r in by_type.iterrows()]),
        )
    )
    pdf.table(
        ["Type", "Total"],
        [[pop_label(r["pop_code"], lang), _fmt(r["total"])] for _, r in by_type.iterrows()],
        [120, 60],
    )

    o_col = _origin_name(lang)
    origins = (
        origin_stock(cdf)
        .groupby(["origin_hcr3", o_col], as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
        .head(10)
    )
    pdf.h2("Top origins" if lang == "en" else "Principales origines")
    pdf.chart(
        _hbar_png(
            [str(r[o_col]) for _, r in origins.iterrows()],
            [float(r["total"]) for _, r in origins.iterrows()],
            title="Principales origines" if lang == "fr" else "Top origins",
            color=CYAN_PRIMARY,
        )
    )
    pdf.table(
        ["Origin" if lang == "en" else "Origine", "Total"],
        [[str(r[o_col]), _fmt(r["total"])] for _, r in origins.iterrows()],
        [120, 60],
    )

    if "coa_admin1" in cdf.columns:
        a1 = (
            cdf.dropna(subset=["coa_admin1"])
            .groupby("coa_admin1", as_index=False)["total"]
            .sum()
            .sort_values("total", ascending=False)
            .head(12)
        )
        if not a1.empty:
            pdf.h2("Admin1")
            pdf.chart(
                _hbar_png(
                    [str(r["coa_admin1"]) for _, r in a1.iterrows()],
                    [float(r["total"]) for _, r in a1.iterrows()],
                    title="Admin1",
                )
            )
            pdf.table(
                ["Admin1", "Total"],
                [[str(r["coa_admin1"]), _fmt(r["total"])] for _, r in a1.iterrows()],
                [120, 60],
            )

    acc = accommodation_share_ref_asy(cdf)
    if not acc.empty:
        pdf.h2("REF/ASY accommodation" if lang == "en" else "Hébergement REF/ASY")
        acc_colors = {
            "camp": RED_PRIMARY,
            "out-of-camp": BLUE_PRIMARY,
            "unknown": GREY_PRIMARY,
        }
        labels = [
            ACCOMMODATION_LABELS.get(r["accommodation_type"], {}).get(
                lang, r["accommodation_type"]
            )
            for _, r in acc.iterrows()
        ]
        pdf.chart(
            _pie_png(
                labels,
                [float(r["total"]) for _, r in acc.iterrows()],
                title="Hébergement REF/ASY" if lang == "fr" else "REF/ASY accommodation",
                colors=[
                    acc_colors.get(str(r["accommodation_type"]), GREY_PRIMARY)
                    for _, r in acc.iterrows()
                ],
            )
        )
        rows = []
        for _, r in acc.iterrows():
            lab = ACCOMMODATION_LABELS.get(r["accommodation_type"], {}).get(
                lang, r["accommodation_type"]
            )
            rows.append([lab, _fmt(r["total"]), _pct(r["share"])])
        pdf.table(
            ["Type", "Total", "%"],
            rows,
            [80, 50, 50],
        )
    return pdf.to_bytes()


def build_trend_pdf(
    *,
    lang: str,
    filtered_all: pd.DataFrame,
    pop_codes: list[str],
    base: pd.DataFrame,
    selected_hosts: list[str] | None,
    data_version: str | None = None,
) -> bytes:
    title = REPORT_CATALOG[2]["title"][lang]
    pdf = MsrPdf(lang, title, data_version=data_version)
    pdf.h1(title)
    monthly = monthly_stock(filtered_all)
    trend = mom_yoy(monthly, pop_codes=pop_codes)
    if trend.empty or len(trend) < 2:
        pdf.p("Insufficient series." if lang == "en" else "Série insuffisante.")
        return pdf.to_bytes()

    first, last = trend.iloc[0], trend.iloc[-1]
    delta = last["total"] - first["total"]
    pct = delta / first["total"] if first["total"] else None
    start = format_month_label(str(first["year_month"]), lang)
    end = format_month_label(str(last["year_month"]), lang)
    direction = (
        ("up" if delta > 0 else "down" if delta < 0 else "stable")
        if lang == "en"
        else ("en hausse" if delta > 0 else "en baisse" if delta < 0 else "stable")
    )
    pdf.h2("Summary" if lang == "en" else "Synthèse")
    if lang == "fr":
        pdf.p(
            f"Entre {start.lower()} et {end.lower()}, la population totale "
            f"({', '.join(pop_label(c, lang) for c in pop_codes)}) est {direction} "
            f"de {_fmt(delta)} personnes ({_pct(pct)})."
        )
    else:
        pdf.p(
            f"Between {start} and {end}, the total population "
            f"({', '.join(pop_label(c, lang) for c in pop_codes)}) is {direction} "
            f"by {_fmt(delta)} people ({_pct(pct)})."
        )

    pdf.h2("Monthly series" if lang == "en" else "Série mensuelle")
    month_labs = [format_month_label(str(r["year_month"]), lang) for _, r in trend.iterrows()]
    pdf.chart(
        _line_png(
            month_labs,
            {"Total": [float(r["total"]) for _, r in trend.iterrows()]},
            title="Évolution mensuelle" if lang == "fr" else "Monthly evolution",
            colors={"Total": BLUE_PRIMARY},
        )
    )
    rows = []
    for _, r in trend.iterrows():
        rows.append(
            [
                format_month_label(str(r["year_month"]), lang),
                _fmt(r["total"]),
                _fmt(r.get("mom_abs")),
                _pct(r.get("mom")),
            ]
        )
    pdf.table(
        [
            "Month" if lang == "en" else "Mois",
            "Total",
            "Δ MoM",
            "MoM %",
        ],
        rows,
        [55, 45, 40, 40],
    )

    ret_src = base[base["pop_code"].isin(["RET", "RDP"])]
    if selected_hosts:
        ret_src = ret_src[ret_src["asylum_iso3"].isin(selected_hosts)]
    ret = returns_monthly(ret_src)
    if not ret.empty:
        pdf.h2("Returnee flows (RET / RDP)" if lang == "en" else "Flux de retours (RET / RDP)")
        pivot = (
            ret.pivot_table(
                index="year_month", columns="pop_code", values="total", aggfunc="sum"
            )
            .fillna(0)
            .reset_index()
            .sort_values("year_month")
        )
        cols = [c for c in ["RET", "RDP"] if c in pivot.columns]
        ret_labs = [format_month_label(str(ym), lang) for ym in pivot["year_month"]]
        series = {c: [float(v) for v in pivot[c].tolist()] for c in cols}
        pdf.chart(
            _line_png(
                ret_labs,
                series,
                title="Flux RET / RDP" if lang == "fr" else "RET / RDP flows",
                colors={"RET": BLUE_PRIMARY, "RDP": RED_PRIMARY},
            )
        )
        pdf.table(
            ["Month" if lang == "en" else "Mois"] + cols,
            [
                [format_month_label(str(r["year_month"]), lang)]
                + [_fmt(r[c]) for c in cols]
                for _, r in pivot.iterrows()
            ],
            [60] + [60] * len(cols),
        )
    return pdf.to_bytes()


def build_corridors_pdf(
    *,
    lang: str,
    month_label: str,
    current: pd.DataFrame,
    wca_iso3: list[str] | None,
    data_version: str | None = None,
) -> bytes:
    title = REPORT_CATALOG[3]["title"][lang]
    pdf = MsrPdf(lang, title, data_version=data_version)
    pdf.h1(title)
    pdf.p(f"{'Month' if lang == 'en' else 'Mois'} : {month_label}")
    src = current[current["pop_code"].isin(["REF", "ASY"])]
    if src.empty:
        src = current
    flows = corridor_flows(src, top_n=25, wca_iso3=wca_iso3, extra_external=12)
    o_col = _origin_name(lang)
    a_col = _host_name(current, lang)
    pdf.h2("Top corridors (origin → asylum)" if lang == "en" else "Top corridors (origine → asile)")
    if flows.empty:
        pdf.p("—")
    else:
        top_flows = flows.head(12)
        corridor_labels = [
            f"{r.get(o_col, r.get('origin_hcr3'))} → {r.get(a_col, r.get('asylum_iso3'))}"
            for _, r in top_flows.iterrows()
        ]
        pdf.chart(
            _hbar_png(
                corridor_labels,
                [float(r["total"]) for _, r in top_flows.iterrows()],
                title="Top corridors" if lang == "en" else "Top corridors",
                colors=[
                    POPULATION_COLORS.get(str(r.get("pop_code", "")), BLUE_PRIMARY)
                    for _, r in top_flows.iterrows()
                ],
            )
        )
        rows = []
        for _, r in flows.iterrows():
            rows.append(
                [
                    f"{r.get(o_col, r.get('origin_hcr3'))} → {r.get(a_col, r.get('asylum_iso3'))}",
                    str(r.get("pop_code", "")),
                    _fmt(r["total"]),
                ]
            )
        pdf.table(
            ["Corridor", "Type", "Total"],
            rows,
            [110, 30, 40],
        )

    o_col = _origin_name(lang)
    origins = (
        origin_stock(src)
        .groupby(["origin_hcr3", o_col], as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
        .head(15)
    )
    pdf.h2("Main origins" if lang == "en" else "Principales origines")
    pdf.chart(
        _hbar_png(
            [str(r[o_col]) for _, r in origins.iterrows()],
            [float(r["total"]) for _, r in origins.iterrows()],
            title="Principales origines" if lang == "fr" else "Main origins",
            color=CYAN_PRIMARY,
        )
    )
    pdf.table(
        ["Origin" if lang == "en" else "Origine", "Total"],
        [[str(r[o_col]), _fmt(r["total"])] for _, r in origins.iterrows()],
        [120, 60],
    )
    return pdf.to_bytes()


def build_methodology_pdf(
    *, lang: str, current: pd.DataFrame, data_version: str | None = None
) -> bytes:
    title = REPORT_CATALOG[4]["title"][lang]
    pdf = MsrPdf(lang, title, data_version=data_version)
    pdf.h1(title)
    if lang == "fr":
        pdf.h2("Source")
        pdf.p(
            "Base ActivityInfo « WCA DIMA Statistics & Analysis », formulaire population "
            "(effectifs mensuels par type, sexe/âge, origine × asile, Admin1/2)."
        )
        pdf.h2("Agrégation")
        pdf.p(
            "Priorité aux lignes « detailed » (admin/localité). Bascule automatique sur "
            "« total » pour les types uniquement reportés à ce niveau (ex. PDI, apatrides), "
            "sans mélanger les niveaux d'agrégation au sein d'un même type."
        )
        pdf.h2("Indicateurs démographiques")
        pdf.p(
            "Les parts femmes/enfants sont calculées uniquement sur les populations "
            "ventilées par sexe/âge (souvent REF/ASY). Les PDI et apatrides sont souvent "
            "reportés sans ventilation."
        )
        pdf.h2("Acronymes")
        for code, labels in POP_TYPE_LABELS.items():
            pdf.bullet(f"{code} — {labels['fr']}")
    else:
        pdf.h2("Source")
        pdf.p(
            "ActivityInfo database “WCA DIMA Statistics & Analysis”, population form "
            "(monthly figures by type, sex/age, origin × asylum, Admin1/2)."
        )
        pdf.h2("Aggregation")
        pdf.p(
            "Prefer “detailed” rows (admin/locality). Automatically fall back to “total” "
            "for types only reported at that level (e.g. IDPs, stateless), without mixing "
            "aggregation levels within a type."
        )
        pdf.h2("Demographic indicators")
        pdf.p(
            "Female/children shares are computed only on populations with sex/age "
            "disaggregation (often REF/ASY). IDPs and stateless are often reported without "
            "disaggregation."
        )
        pdf.h2("Acronyms")
        for code, labels in POP_TYPE_LABELS.items():
            pdf.bullet(f"{code} — {labels['en']}")

    q = data_quality_summary(current)
    if not q.empty:
        pdf.h2("Data quality (selected month)" if lang == "en" else "Qualité des données (mois)")
        pdf.chart(
            _vbar_png(
                [pop_label(r["pop_code"], lang) for _, r in q.iterrows()],
                [float(r["sex_coverage"] or 0) * 100 for _, r in q.iterrows()],
                title=(
                    "Couverture sexe (%)" if lang == "fr" else "Sex coverage (%)"
                ),
                colors=_pop_colors([str(r["pop_code"]) for _, r in q.iterrows()]),
            )
        )
        pdf.table(
            ["Type", "Total", "% sex" if lang == "en" else "% sexe", "% age", "Agg."],
            [
                [
                    pop_label(r["pop_code"], lang),
                    _fmt(r["total"]),
                    _pct(r["sex_coverage"]),
                    _pct(r["age_coverage"]),
                    str(r["aggregation"]),
                ]
                for _, r in q.iterrows()
            ],
            [50, 40, 30, 30, 30],
        )
    return pdf.to_bytes()


def build_shelter_pdf(
    *,
    lang: str,
    month_label: str,
    current: pd.DataFrame,
    data_version: str | None = None,
) -> bytes:
    title = REPORT_CATALOG[5]["title"][lang]
    pdf = MsrPdf(lang, title, data_version=data_version)
    pdf.h1(title)
    pdf.p(f"{'Month' if lang == 'en' else 'Mois'} : {month_label}")
    share = accommodation_share_ref_asy(current)
    pdf.h2("REF + ASY overall" if lang == "en" else "REF + ASY — ensemble")
    if share.empty:
        pdf.p("—")
    else:
        acc_colors = {
            "camp": RED_PRIMARY,
            "out-of-camp": BLUE_PRIMARY,
            "unknown": GREY_PRIMARY,
        }
        labels = [
            ACCOMMODATION_LABELS.get(r["accommodation_type"], {}).get(
                lang, r["accommodation_type"]
            )
            for _, r in share.iterrows()
        ]
        pdf.chart(
            _pie_png(
                labels,
                [float(r["total"]) for _, r in share.iterrows()],
                title="Camp vs hors camp" if lang == "fr" else "Camp vs out of camp",
                colors=[
                    acc_colors.get(str(r["accommodation_type"]), GREY_PRIMARY)
                    for _, r in share.iterrows()
                ],
            )
        )
        rows = []
        for _, r in share.iterrows():
            lab = ACCOMMODATION_LABELS.get(r["accommodation_type"], {}).get(
                lang, r["accommodation_type"]
            )
            rows.append([lab, _fmt(r["total"]), _pct(r["share"])])
        pdf.table(["Type", "Total", "%"], rows, [80, 50, 50])

    host_col = _host_name(current, lang)
    ref_asy = current[current["pop_code"].isin(["REF", "ASY"])].copy()
    if not ref_asy.empty and "accommodation_type" in ref_asy.columns:
        ref_asy["accommodation_type"] = (
            ref_asy["accommodation_type"].fillna("unknown").replace("", "unknown")
        )
        by_c = (
            ref_asy.groupby([host_col, "accommodation_type"], as_index=False)["total"]
            .sum()
        )
        pivot = by_c.pivot_table(
            index=host_col, columns="accommodation_type", values="total", aggfunc="sum"
        ).fillna(0)
        pivot["total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("total", ascending=False).head(15)
        pdf.h2("By country of asylum" if lang == "en" else "Par pays d'asile")
        cols = [c for c in ["camp", "out-of-camp", "unknown"] if c in pivot.columns]
        series = {
            ACCOMMODATION_LABELS.get(c, {}).get(lang, c): [
                float(pivot.loc[name, c]) for name in pivot.index
            ]
            for c in cols
        }
        color_map = {
            ACCOMMODATION_LABELS.get("camp", {}).get(lang, "camp"): RED_PRIMARY,
            ACCOMMODATION_LABELS.get("out-of-camp", {}).get(lang, "out-of-camp"): BLUE_PRIMARY,
            ACCOMMODATION_LABELS.get("unknown", {}).get(lang, "unknown"): GREY_PRIMARY,
        }
        pdf.chart(
            _stacked_hbar_png(
                [str(n) for n in pivot.index],
                series,
                title=(
                    "Hébergement par pays" if lang == "fr" else "Accommodation by country"
                ),
                colors=color_map,
            )
        )
        headers = ["Country" if lang == "en" else "Pays"] + [
            ACCOMMODATION_LABELS.get(c, {}).get(lang, c) for c in cols
        ] + ["Total"]
        rows = []
        for name, r in pivot.iterrows():
            rows.append(
                [str(name)] + [_fmt(r[c]) for c in cols] + [_fmt(r["total"])]
            )
        width = 180 / max(len(headers), 1)
        pdf.table(headers, rows, [width] * len(headers))
    return pdf.to_bytes()


def build_psn_pdf(
    *,
    lang: str,
    month: str,
    month_label: str,
    psn_raw: pd.DataFrame,
    total_psn_raw: pd.DataFrame,
    selected_hosts: list[str] | None,
    data_version: str | None = None,
) -> bytes:
    title = REPORT_CATALOG[6]["title"][lang]
    pdf = MsrPdf(lang, title, data_version=data_version)
    pdf.h1(title)
    pdf.p(f"{'Month' if lang == 'en' else 'Mois'} : {month_label}")
    pdf.p(
        "PSN are subsets with specific needs, not the overall population stock."
        if lang == "en"
        else "Les PSN sont des sous-ensembles à besoins spécifiques, pas le stock global."
    )

    psn_m = (
        psn_raw[psn_raw["year_month"] == month]
        if not psn_raw.empty and "year_month" in psn_raw.columns
        else pd.DataFrame()
    )
    tpsn_m = (
        total_psn_raw[total_psn_raw["year_month"] == month]
        if not total_psn_raw.empty and "year_month" in total_psn_raw.columns
        else pd.DataFrame()
    )
    if selected_hosts:
        if not psn_m.empty:
            psn_m = psn_m[psn_m["asylum_iso3"].isin(selected_hosts)]
        if not tpsn_m.empty:
            tpsn_m = tpsn_m[tpsn_m["asylum_iso3"].isin(selected_hosts)]

    total_val = float(tpsn_m["total"].sum()) if not tpsn_m.empty else (
        float(psn_m["total"].sum()) if not psn_m.empty else 0.0
    )
    pdf.kv("Total PSN", _fmt(total_val))

    needs = psn_by_need(psn_m)
    if not needs.empty:
        pdf.h2("By need category" if lang == "en" else "Par catégorie de besoin")
        top_n = needs.head(12)
        pdf.chart(
            _hbar_png(
                [
                    PSN_NEED_LABELS.get(r["sn_code"], {}).get(lang, r["sn_code"])
                    for _, r in top_n.iterrows()
                ],
                [float(r["total"]) for _, r in top_n.iterrows()],
                title=(
                    "PSN par catégorie" if lang == "fr" else "PSN by need category"
                ),
                color=YELLOW_PRIMARY,
            )
        )
        pdf.table(
            ["Code", "Label", "Total"],
            [
                [
                    str(r["sn_code"]),
                    PSN_NEED_LABELS.get(r["sn_code"], {}).get(lang, r["sn_code"]),
                    _fmt(r["total"]),
                ]
                for _, r in needs.head(15).iterrows()
            ],
            [25, 105, 50],
        )

    by_c = psn_by_country(tpsn_m if not tpsn_m.empty else psn_m, lang=lang)
    if not by_c.empty:
        name_c = "asylum_name_fr" if lang == "fr" else "asylum_name_en"
        if name_c not in by_c.columns:
            name_c = next((c for c in by_c.columns if c.startswith("asylum_name")), None)
        if name_c:
            agg = (
                by_c.groupby(name_c, as_index=False)["total"]
                .sum()
                .sort_values("total", ascending=False)
                .head(15)
            )
            pdf.h2("By country of asylum" if lang == "en" else "Par pays d'asile")
            pdf.chart(
                _hbar_png(
                    [str(r[name_c]) for _, r in agg.iterrows()],
                    [float(r["total"]) for _, r in agg.iterrows()],
                    title="PSN par pays" if lang == "fr" else "PSN by country",
                )
            )
            pdf.table(
                ["Country" if lang == "en" else "Pays", "Total"],
                [[str(r[name_c]), _fmt(r["total"])] for _, r in agg.iterrows()],
                [120, 60],
            )
    return pdf.to_bytes()


BUILDERS: dict[str, Callable[..., bytes]] = {
    "flash": build_flash_pdf,
    "country": build_country_pdf,
    "trend": build_trend_pdf,
    "corridors": build_corridors_pdf,
    "methodology": build_methodology_pdf,
    "shelter": build_shelter_pdf,
    "psn": build_psn_pdf,
}
