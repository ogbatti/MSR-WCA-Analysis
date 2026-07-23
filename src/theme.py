"""UNHCR brand & data-visualization colour palette.

Source: UNHCR Data Visualization Guidelines — https://dataviz.unhcr.org/
"""

from __future__ import annotations

# Brand colours
BLUE = "#0072BC"
YELLOW_BRAND = "#FAEB00"
BLACK = "#000000"
WHITE = "#FFFFFF"

# Data colours (primary)
BLUE_PRIMARY = "#0072BC"
YELLOW_PRIMARY = "#FFC740"
GREEN_PRIMARY = "#32C189"
CYAN_PRIMARY = "#6CD8FD"
RED_PRIMARY = "#D25A45"
PURPLE_PRIMARY = "#A097E3"
BROWN_PRIMARY = "#7C3C36"
GREY_PRIMARY = "#BFBFBF"

# Blue ramp (light → dark)
BLUE_01 = "#CDE3F1"
BLUE_02 = "#8FC1E1"
BLUE_03 = "#4F9ED0"
BLUE_04 = "#0072BC"
BLUE_05 = "#05568B"
BLUE_06 = "#0B3754"

# Grey ramp
GREY_01 = "#E5E5E5"
GREY_02 = "#BFBFBF"
GREY_03 = "#999999"
GREY_04 = "#737373"
GREY_05 = "#4D4D4D"
GREY_06 = "#262626"

CATEGORICAL = [
    BLUE_PRIMARY,
    YELLOW_PRIMARY,
    GREEN_PRIMARY,
    CYAN_PRIMARY,
    RED_PRIMARY,
    PURPLE_PRIMARY,
    BROWN_PRIMARY,
    GREY_PRIMARY,
]

POPULATION_COLORS = {
    "REF": BLUE_PRIMARY,
    "ASY": CYAN_PRIMARY,
    "IDP": YELLOW_PRIMARY,
    "STA": PURPLE_PRIMARY,
    "RET": BLUE_PRIMARY,  # refugee returnees — blue
    "RDP": RED_PRIMARY,  # IDP returnees — red/coral (clearly distinct)
    "OOC": BROWN_PRIMARY,
    "NOC": GREY_PRIMARY,
}

SCENARIO_COLORS = {
    "historical": GREY_05,
    "baseline": BLUE_PRIMARY,
    "optimistic": GREEN_PRIMARY,
    "pessimistic": RED_PRIMARY,
    "custom": YELLOW_PRIMARY,
}

CHOROPLETH_BLUES = [BLUE_01, BLUE_02, BLUE_03, BLUE_04, BLUE_05, BLUE_06]

FONT_FAMILY = "Lato, Arial, Helvetica, sans-serif"
TEXT_COLOR = GREY_06
GRID_COLOR = GREY_01
PAPER_BG = WHITE
PLOT_BG = WHITE

APP_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;600;700&display=swap');

  :root {
    --unhcr-blue: #0072BC;
    --unhcr-blue-dark: #0B3754;
    --unhcr-blue-mid: #05568B;
    --unhcr-blue-light: #CDE3F1;
    --unhcr-yellow: #FFC740;
    --unhcr-yellow-brand: #FAEB00;
    --unhcr-text: #262626;
    --unhcr-grey: #E5E5E5;
    --unhcr-grey-mid: #999999;
  }

  html, body, [class*="css"] {
    font-family: Lato, Arial, Helvetica, sans-serif;
  }

  .stApp { background-color: #FFFFFF; color: var(--unhcr-text); }

  /* Hide Streamlit chrome noise */
  #MainMenu { visibility: hidden; }
  footer { visibility: hidden; }

  h1, h2, h3 { color: var(--unhcr-blue-dark) !important; font-weight: 700 !important; }

  [data-testid="stSidebar"] {
    background-color: #F7FBFE;
    border-right: 1px solid var(--unhcr-blue-light);
  }
  .lang-flag {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0 0 0.15rem 0;
  }
  .lang-flag img {
    width: 26px;
    height: 17px;
    object-fit: cover;
    border-radius: 2px;
    border: 1px solid #BFBFBF;
    box-shadow: none;
  }
  /* Compact FR / EN language buttons */
  [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"]:has(.lang-flag) button {
    min-height: 1.6rem !important;
    height: 1.6rem !important;
    padding: 0 0.4rem !important;
    font-size: 0.72rem !important;
    line-height: 1.2 !important;
  }
  [data-testid="stSidebar"] div[data-testid="stHorizontalBlock"]:has(.lang-flag) {
    gap: 0.35rem !important;
  }
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3 {
    color: var(--unhcr-blue) !important;
  }

  .brand-header {
    display: flex;
    align-items: center;
    gap: 1.1rem;
    padding: 0.35rem 0 0.85rem 0;
    border-bottom: 3px solid var(--unhcr-blue);
    margin-bottom: 1.1rem;
  }
  .brand-header img {
    height: 58px;
    width: auto;
    object-fit: contain;
  }
  .brand-header .brand-text { flex: 1; min-width: 0; }
  .brand-header .brand-kicker {
    color: var(--unhcr-blue);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 0 0 0.2rem 0;
  }
  .brand-header h1 {
    margin: 0 !important;
    padding: 0 !important;
    font-size: 1.55rem !important;
    line-height: 1.25 !important;
    color: var(--unhcr-blue-dark) !important;
  }
  .brand-header .brand-sub {
    margin: 0.25rem 0 0 0;
    color: var(--unhcr-grey-mid);
    font-size: 0.95rem;
  }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin: 0.35rem 0 1.1rem 0;
  }
  @media (max-width: 1100px) {
    .kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  }
  @media (max-width: 700px) {
    .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  }
  .kpi-card {
    background: var(--unhcr-blue-light);
    border-left: 4px solid var(--unhcr-blue);
    padding: 0.75rem 0.9rem;
    border-radius: 0 4px 4px 0;
  }
  .kpi-card .kpi-label {
    color: var(--unhcr-blue-dark);
    font-size: 0.82rem;
    font-weight: 600;
    margin-bottom: 0.3rem;
    line-height: 1.25;
  }
  .kpi-card .kpi-value {
    color: var(--unhcr-text);
    font-size: 1.28rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    letter-spacing: -0.01em;
  }
  .kpi-card .kpi-delta {
    margin-top: 0.2rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--unhcr-blue-mid);
  }

  .section-card {
    background: #FFFFFF;
    border: 1px solid var(--unhcr-grey);
    border-top: 3px solid var(--unhcr-blue);
    border-radius: 0 0 4px 4px;
    padding: 0.85rem 1rem 0.4rem 1rem;
    margin-bottom: 0.85rem;
  }
  .section-card h3 {
    margin-top: 0 !important;
    font-size: 1.05rem !important;
  }

  .narrative-box {
    background: #F7FBFE;
    border-left: 4px solid var(--unhcr-yellow);
    padding: 0.85rem 1rem;
    border-radius: 0 4px 4px 0;
    margin: 0.6rem 0 1rem 0;
  }

  .data-version-banner {
    background: #F7FBFE;
    border: 1px solid #CDE3F1;
    border-left: 4px solid var(--unhcr-blue);
    padding: 0.55rem 0.85rem;
    border-radius: 0 4px 4px 0;
    margin: 0.4rem 0 0.85rem 0;
    font-size: 0.85rem;
    color: var(--unhcr-text);
  }
  .data-version-banner strong {
    color: var(--unhcr-blue-dark);
  }

  .quality-banner {
    background: #FFFDF5;
    border: 1px solid #FFE9A8;
    border-left: 4px solid var(--unhcr-yellow);
    padding: 0.65rem 0.85rem;
    border-radius: 0 4px 4px 0;
    margin: 0 0 0.9rem 0;
    font-size: 0.88rem;
  }
  .quality-banner ul {
    margin: 0.35rem 0 0 1.1rem;
    padding: 0;
  }
  .quality-banner .qb-warn { color: #7C3C36; }
  .quality-banner .qb-ok { color: #05568B; }

  .staging-banner {
    background: #FFF8E6;
    border: 1px solid #FFC740;
    color: #0B3754;
    padding: 0.45rem 0.75rem;
    border-radius: 4px;
    margin: 0 0 0.75rem 0;
    font-size: 0.84rem;
    font-weight: 600;
  }

  .stButton > button {
    background-color: var(--unhcr-blue);
    color: #FFFFFF;
    border: 1px solid var(--unhcr-blue);
    border-radius: 2px;
    font-weight: 600;
  }
  .stButton > button:hover {
    background-color: var(--unhcr-blue-mid);
    border-color: var(--unhcr-blue-mid);
    color: #FFFFFF;
  }

  .stTabs [aria-selected="true"] {
    color: var(--unhcr-blue) !important;
    border-bottom-color: var(--unhcr-blue) !important;
    font-weight: 700 !important;
  }
  .stTabs [data-baseweb="tab-list"] {
    gap: 0.4rem;
    border-bottom: 1px solid var(--unhcr-grey);
  }

  hr { border-color: var(--unhcr-grey); }

  .footer-credit {
    margin-top: 1.5rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--unhcr-grey);
    color: var(--unhcr-grey-mid);
    font-size: 0.82rem;
  }
</style>
"""


def apply_unhcr_layout(fig, *, title: str | None = None) -> None:
    """Apply shared UNHCR layout styling to a Plotly figure."""
    title_text = "" if title is None else title
    # If caller already set a px title and passes title=None, keep it;
    # pass title="" explicitly to hide (avoid Streamlit/Plotly double titles).
    if title is None and fig.layout.title and fig.layout.title.text:
        title_text = fig.layout.title.text
    fig.update_layout(
        font=dict(family=FONT_FAMILY, color=TEXT_COLOR, size=13),
        title=dict(
            text=title_text,
            font=dict(family=FONT_FAMILY, color=BLUE_06, size=15),
            x=0.0,
            xanchor="left",
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(size=12, color=TEXT_COLOR),
        ),
        colorway=CATEGORICAL,
        hoverlabel=dict(bgcolor=WHITE, font_size=12, font_family=FONT_FAMILY),
        margin=dict(l=40, r=20, t=48 if title_text else 24, b=40),
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID_COLOR, zeroline=False, linecolor=GREY_03)
    fig.update_yaxes(showgrid=True, gridcolor=GRID_COLOR, zeroline=False, linecolor=GREY_03)


def pop_color(code: str) -> str:
    return POPULATION_COLORS.get(code, BLUE_PRIMARY)
