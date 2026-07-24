# MSR WCA — Forced Displacement & Statelessness Analysis

Interactive bilingual (FR/EN) Streamlit dashboard for monthly statistics on forcibly displaced and stateless populations in West & Central Africa, sourced from the **ActivityInfo** database *WCA DIMA - Statistics & Analysis*.

## Features

- Dynamic KPIs: total stock, MoM change, female/children shares, host & origin rankings
- Charts: stock by population type, monthly trends, MoM/YoY
- Maps: country choropleth (asylum) + displacement corridors
- Admin1 / Admin2 breakdowns
- Narrative interpretations (FR/EN)
- Scenario projections to **2036** (growth / conflict shock / returns)

## Setup

```bash
cd "MSR Analysis"
python -m venv .venv

# Windows — use the Python launcher if `pip` / `python` are not in PATH
py -3 -m venv .venv
.venv\Scripts\activate
py -3 -m pip install -r requirements.txt

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

copy .env.example .env   # or: cp .env.example .env
```

Edit `.env` and set your ActivityInfo token:

```
ACTIVITYINFO_TOKEN=your_token_here
ACTIVITYINFO_DATABASE_ID=c6whbx9kv7zwnux3
```

## Run

```bash
py -3 -m streamlit run app.py
# or, if port 8501 is already used:
py -3 -m streamlit run app.py --server.port 8502
```
First load pulls ~175k population rows from ActivityInfo and caches them as `data/cache/population.parquet`. Use the sidebar **Refresh API data** button to force a reload.

## Streamlit Community Cloud

1. Deploy from GitHub repo `ogbatti/MSR-WCA-Analysis` (`app.py`, branch `master`).
2. In **App settings → Secrets**, add:

```toml
ACTIVITYINFO_TOKEN = "your_activityinfo_token"
ACTIVITYINFO_DATABASE_ID = "c6whbx9kv7zwnux3"

# Invitation-only access (no public sign-up)
AUTH_ENABLED = "true"
AUTH_ADMIN_EMAIL = "you@unhcr.org"
AUTH_ADMIN_PASSWORD = "ChangeMe_now_8chars"
AUTH_ADMIN_NAME = "DIMA Admin"
APP_PUBLIC_URL = "https://dimawca.app"

# Optional — email invite on account creation
SMTP_HOST = "smtp.office365.com"
SMTP_PORT = "587"
SMTP_USER = "you@unhcr.org"
SMTP_PASSWORD = "app-password-or-mailbox-password"
SMTP_FROM = "DIMA WCA <you@unhcr.org>"
SMTP_STARTTLS = "true"
```

See `.streamlit/secrets.auth.example.toml` for the full auth example.

### Access control (invitation accounts)

- No public registration: an **admin** creates users in **Informations → Gestion des accès**.
- At creation, the admin can tick **send email notification** (URL, login, temporary password).
- Users can **change their password** from the sidebar (**Mon compte**).
- First admin is bootstrapped from `AUTH_ADMIN_*` secrets when `data/auth/users.json` is empty.
- User store file: `data/auth/users.json` (gitignored; password hashes only).

**Streamlit Cloud note:** the app filesystem is ephemeral. For durable accounts on Cloud, keep a private copy of `users.json` (or re-create users after redeploy), or later plug a persistent store. Locally, password changes persist in `users.json`.

The `.env` file is local-only and is not published to GitHub.

## Data notes

| Form | Role |
|------|------|
| `population` | Main monthly stocks (sex/age, admin1/2, origin × asylum) |
| `total_psn` / `psn` | Persons with specific needs (not overall stock) |
| `wca_countries_reference` | HCR3 ↔ ISO3 country mapping |

Analytical totals prefer `aggregation_type = detailed` when available (REF, ASY, …). For types only published as `total` (notably **IDP** and **STA**), the dashboard falls back to those rows. Aggregation levels are never mixed within the same population type.

Population types: REF, ASY, IDP, STA, RET, RDP, OOC, NOC.

## Projection model

\[
S_{t+1} = S_t \times (1 + g + c) \times (1 - r)
\]

where \(g\) = residual growth, \(c\) = conflict shock, \(r\) = return/solutions rate. Default scenarios: optimistic / baseline / pessimistic, plus a custom slider scenario.

## Project layout

```
app.py                 # Streamlit entrypoint
src/
  activityinfo_client.py
  config.py
  data_loader.py
  indicators.py
  charts.py
  narratives.py
  forecasting.py
  i18n.py
data/cache/            # parquet cache (gitignored)
```
