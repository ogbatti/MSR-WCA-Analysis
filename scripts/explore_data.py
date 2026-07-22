"""Explore population data shape, date range, and reference resolution."""
import json
import urllib.request
from collections import Counter

TOKEN = "f41a159db82745fd5df797a6a0d4d55c"
BASE = "https://www.activityinfo.org/resources"


def post_rows(form_id: str, columns: list[dict], filter_expr: str | None = None):
    body = {
        "rowSources": [{"rootFormId": form_id}],
        "columns": columns,
    }
    if filter_expr:
        body["filter"] = filter_expr
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/query/rows",
        data=data,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_default(form_id: str):
    req = urllib.request.Request(
        f"{BASE}/form/{form_id}/query",
        headers={"Authorization": f"Bearer {TOKEN}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    pop_types = get_default("cxmho36mnrg1bl3b")
    print("POP TYPES:")
    for r in pop_types:
        print(" ", r)
    with open("ref_pop_types.json", "w", encoding="utf-8") as f:
        json.dump(pop_types, f, ensure_ascii=False, indent=2)

    countries = get_default("c3lb2j7mo4v30bp7")
    print("\nCOUNTRIES:", len(countries))
    for r in countries:
        print(" ", r.get("iso3"), r.get("name_en"), r.get("name_fr"))
    with open("ref_countries.json", "w", encoding="utf-8") as f:
        json.dump(countries, f, ensure_ascii=False, indent=2)

    # Resolve references via path formulas
    cols = [
        {"id": "date", "expression": "date"},
        {"id": "origin", "expression": "origin"},
        {"id": "asylum_code", "expression": "asylum.[Country Code]"},
        {"id": "asylum_name", "expression": "asylum.[Country Name]"},
        {"id": "pop_code", "expression": "population_type.Code"},
        {"id": "pop_label", "expression": "population_type.[Label (Description)]"},
        {"id": "coa_admin1", "expression": "coa_admin1"},
        {"id": "coa_admin2", "expression": "coa_admin2"},
        {"id": "accommodation_type", "expression": "accommodation_type"},
        {"id": "aggregation_type", "expression": "aggregation_type"},
        {"id": "source", "expression": "source"},
        {"id": "basis", "expression": "basis"},
        {"id": "female", "expression": "female"},
        {"id": "male", "expression": "male"},
        {"id": "total", "expression": "total"},
        {"id": "country", "expression": "country"},
        {"id": "f_0_4", "expression": "[f_0-4]"},
        {"id": "f_5_11", "expression": "[f_5-11]"},
        {"id": "f_12_17", "expression": "[f_12-17]"},
        {"id": "m_0_4", "expression": "[m_0-4]"},
        {"id": "m_5_11", "expression": "[m_5-11]"},
        {"id": "m_12_17", "expression": "[m_12-17]"},
    ]
    print("\nFetching population sample (all rows, selected columns)...")
    rows = post_rows("cae6v67mnrh690es", cols)
    print("rows:", len(rows))
    print("sample:", json.dumps(rows[0], ensure_ascii=False, indent=2))

    dates = [r.get("date") for r in rows if r.get("date")]
    print("date min/max:", min(dates), max(dates))
    print("pop codes:", Counter(r.get("pop_code") for r in rows).most_common())
    print("aggregation:", Counter(r.get("aggregation_type") for r in rows).most_common())
    print("source:", Counter(r.get("source") for r in rows).most_common(10))
    print("basis:", Counter(r.get("basis") for r in rows).most_common(10))
    print("asylum top:", Counter(r.get("asylum_name") for r in rows).most_common(15))
    print("admin1 non-null:", sum(1 for r in rows if r.get("coa_admin1")))
    print("admin2 non-null:", sum(1 for r in rows if r.get("coa_admin2")))

    # Save a compact parquet-like csv via json for later? Too big.
    # Save metadata only
    meta = {
        "n_rows": len(rows),
        "date_min": min(dates),
        "date_max": max(dates),
        "pop_codes": Counter(r.get("pop_code") for r in rows).most_common(),
        "aggregation": Counter(r.get("aggregation_type") for r in rows).most_common(),
        "sample": rows[:3],
    }
    with open("population_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # Also check total_psn and psn sizes
    for fid, name in [
        ("cakhipjmnrpazba5v", "total_psn"),
        ("ce0uuhmmnrp3hie5c", "psn"),
        ("cu9g9jgmnrn5mu62l", "education"),
        ("cawax4bmo5ipjj11f", "geoloc"),
    ]:
        d = get_default(fid)
        print(f"{name}: {len(d)} rows, keys={list(d[0].keys()) if d else None}")
        if d:
            with open(f"sample_{name}.json", "w", encoding="utf-8") as f:
                json.dump(d[:5], f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
