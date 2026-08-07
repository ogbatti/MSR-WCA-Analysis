"""Extended country reference for WCA + major external origins."""
from __future__ import annotations

# Extra origins frequently seen in WCA MSR data (HCR3 → metadata).
# Used to plot corridors from outside the WCA region.
EXTERNAL_ORIGINS = {
    "SUD": {
        "iso3": "SDN",
        "name_en": "Sudan",
        "name_fr": "Soudan",
        "latitude": 15.5,
        "longitude": 32.5,
    },
    "SSD": {
        "iso3": "SSD",
        "name_en": "South Sudan",
        "name_fr": "Soudan du Sud",
        "latitude": 6.88,
        "longitude": 31.3,
    },
    "RWA": {
        "iso3": "RWA",
        "name_en": "Rwanda",
        "name_fr": "Rwanda",
        "latitude": -1.94,
        "longitude": 29.87,
    },
    "BDI": {
        "iso3": "BDI",
        "name_en": "Burundi",
        "name_fr": "Burundi",
        "latitude": -3.37,
        "longitude": 29.36,
    },
    "SYR": {
        "iso3": "SYR",
        "name_en": "Syria",
        "name_fr": "Syrie",
        "latitude": 34.8,
        "longitude": 38.0,
    },
    "ERT": {
        "iso3": "ERI",
        "name_en": "Eritrea",
        "name_fr": "Érythrée",
        "latitude": 15.18,
        "longitude": 39.78,
    },
    "SOM": {
        "iso3": "SOM",
        "name_en": "Somalia",
        "name_fr": "Somalie",
        "latitude": 5.15,
        "longitude": 46.2,
    },
    "ETH": {
        "iso3": "ETH",
        "name_en": "Ethiopia",
        "name_fr": "Éthiopie",
        "latitude": 9.15,
        "longitude": 40.49,
    },
    "ANG": {
        "iso3": "AGO",
        "name_en": "Angola",
        "name_fr": "Angola",
        "latitude": -11.2,
        "longitude": 17.87,
    },
    "TUR": {
        "iso3": "TUR",
        "name_en": "Türkiye",
        "name_fr": "Türkiye",
        "latitude": 39.0,
        "longitude": 35.0,
    },
    "PAK": {
        "iso3": "PAK",
        "name_en": "Pakistan",
        "name_fr": "Pakistan",
        "latitude": 30.4,
        "longitude": 69.3,
    },
    "YEM": {
        "iso3": "YEM",
        "name_en": "Yemen",
        "name_fr": "Yémen",
        "latitude": 15.55,
        "longitude": 48.5,
    },
    "LEB": {
        "iso3": "LBN",
        "name_en": "Lebanon",
        "name_fr": "Liban",
        "latitude": 33.85,
        "longitude": 35.86,
    },
    "UGA": {
        "iso3": "UGA",
        "name_en": "Uganda",
        "name_fr": "Ouganda",
        "latitude": 1.37,
        "longitude": 32.29,
    },
    "LBY": {
        "iso3": "LBY",
        "name_en": "Libya",
        "name_fr": "Libye",
        "latitude": 26.3,
        "longitude": 17.2,
    },
    "ALG": {
        "iso3": "DZA",
        "name_en": "Algeria",
        "name_fr": "Algérie",
        "latitude": 28.0,
        "longitude": 2.0,
    },
    "EGY": {
        "iso3": "EGY",
        "name_en": "Egypt",
        "name_fr": "Égypte",
        "latitude": 26.8,
        "longitude": 30.8,
    },
    "GAZ": {
        "iso3": "PSE",
        "name_en": "Gaza Strip",
        "name_fr": "Bande de Gaza",
        "latitude": 31.4,
        "longitude": 34.4,
    },
    "ARE": {
        "iso3": "ARE",
        "name_en": "United Arab Emirates",
        "name_fr": "Émirats arabes unis",
        "latitude": 23.4,
        "longitude": 53.8,
    },
    "SUR": {
        "iso3": "SUR",
        "name_en": "Suriname",
        "name_fr": "Suriname",
        "latitude": 3.9,
        "longitude": -56.0,
    },
}

# Standard UNHCR age bands for the pyramid
AGE_BANDS = [
    ("0-4", "f_0_4", "m_0_4"),
    ("5-11", "f_5_11", "m_5_11"),
    ("12-17", "f_12_17", "m_12_17"),
    ("18-59", ["f_18_24", "f_25_49", "f_50_59"], ["m_18_24", "m_25_49", "m_50_59"]),
    ("60+", "f_60", "m_60"),
]

# Detailed adult bands (useful for other response analysis)
AGE_BANDS_ADULT_DETAIL = [
    ("18-24", "f_18_24", "m_18_24"),
    ("25-49", "f_25_49", "m_25_49"),
    ("50-59", "f_50_59", "m_50_59"),
]

MONTH_NAMES = {
    "en": [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ],
    "fr": [
        "Janvier",
        "Février",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Août",
        "Septembre",
        "Octobre",
        "Novembre",
        "Décembre",
    ],
}


def format_month_label(year_month: str, lang: str) -> str:
    """Convert 'YYYY-MM' to 'May 2026' / 'Mai 2026'."""
    try:
        year_s, month_s = year_month.split("-")
        month_i = int(month_s)
        names = MONTH_NAMES["fr" if lang == "fr" else "en"]
        return f"{names[month_i - 1]} {year_s}"
    except Exception:
        return year_month


# Plural nationality adjectives for KPI labels (ISO3 → fr / en).
# French forms match “Réfugiés {adj} en AOC” (lowercase).
NATIONALITY_ADJECTIVES: dict[str, dict[str, str]] = {
    "BEN": {"fr": "béninois", "en": "Beninese"},
    "BFA": {"fr": "burkinabè", "en": "Burkinabe"},
    "CPV": {"fr": "cap-verdiens", "en": "Cabo Verdean"},
    "CMR": {"fr": "camerounais", "en": "Cameroonian"},
    "CAF": {"fr": "centrafricains", "en": "Central African"},
    "TCD": {"fr": "tchadiens", "en": "Chadian"},
    "COG": {"fr": "congolais", "en": "Congolese"},
    "COD": {"fr": "congolais", "en": "Congolese"},
    "CIV": {"fr": "ivoiriens", "en": "Ivorian"},
    "GNQ": {"fr": "équato-guinéens", "en": "Equatorial Guinean"},
    "GAB": {"fr": "gabonais", "en": "Gabonese"},
    "GMB": {"fr": "gambiens", "en": "Gambian"},
    "GHA": {"fr": "ghanéens", "en": "Ghanaian"},
    "GIN": {"fr": "guinéens", "en": "Guinean"},
    "GNB": {"fr": "bissau-guinéens", "en": "Bissau-Guinean"},
    "LBR": {"fr": "libériens", "en": "Liberian"},
    "MLI": {"fr": "maliens", "en": "Malian"},
    "MRT": {"fr": "mauritaniens", "en": "Mauritanian"},
    "NER": {"fr": "nigériens", "en": "Nigerien"},
    "NGA": {"fr": "nigérians", "en": "Nigerian"},
    "STP": {"fr": "santoméens", "en": "Sao Tomean"},
    "SEN": {"fr": "sénégalais", "en": "Senegalese"},
    "SLE": {"fr": "sierra-léonais", "en": "Sierra Leonean"},
    "TGO": {"fr": "togolais", "en": "Togolese"},
}


def nationality_adjective(iso3: str, lang: str) -> str | None:
    """Return plural nationality adjective for a country ISO3, or None if unknown."""
    if not iso3:
        return None
    row = NATIONALITY_ADJECTIVES.get(str(iso3).strip().upper())
    if not row:
        return None
    return row.get("fr" if lang == "fr" else "en")


def year_month_from_label(label: str, lang: str) -> str | None:
    """Reverse of format_month_label."""
    try:
        parts = label.rsplit(" ", 1)
        if len(parts) != 2:
            return None
        name, year_s = parts
        names = MONTH_NAMES["fr" if lang == "fr" else "en"]
        month_i = names.index(name) + 1
        return f"{year_s}-{month_i:02d}"
    except Exception:
        return None
