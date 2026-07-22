"""Compare total_psn form vs population aggregation strategies."""
import json
import urllib.request
from collections import defaultdict

TOKEN = "f41a159db82745fd5df797a6a0d4d55c"
BASE = "https://www.activityinfo.org/resources"


def post(form_id, columns, filt=None):
    body = {"rowSources": [{"rootFormId": form_id}], "columns": columns}
    if filt:
        body["filter"] = filt
    req = urllib.request.Request(
        f"{BASE}/query/rows",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


# total_psn latest month
tpsn = post(
    "cakhipjmnrpazba5v",
    [
        {"id": "date", "expression": "date"},
        {"id": "country", "expression": "country"},
        {"id": "iso3", "expression": "asylum.iso3"},
        {"id": "name_en", "expression": "asylum.name_en"},
        {"id": "pop", "expression": "population_type.Code"},
        {"id": "origin", "expression": "origin"},
        {"id": "total", "expression": "total_psn"},
    ],
)

dates = sorted({r["date"] for r in tpsn if r["date"]})
print("total_psn dates", dates[0], "->", dates[-1], "n_months", len(dates), "rows", len(tpsn))
latest = dates[-1]
rows = [r for r in tpsn if r["date"] == latest]
print("latest", latest, "rows", len(rows))

by_pop = defaultdict(float)
by_country_ref = defaultdict(float)
for r in rows:
    by_pop[r["pop"]] += r["total"] or 0
    if r["pop"] == "REF":
        by_country_ref[r["country"] or r["iso3"]] += r["total"] or 0

print("by pop", dict(sorted(by_pop.items(), key=lambda x: -x[1])))
print("REF by country", sorted(by_country_ref.items(), key=lambda x: -x[1]))
print("REF total", sum(by_country_ref.values()))

# Check duplicates in total_psn
from collections import Counter

keys = Counter((r["country"], r["pop"], r["origin"]) for r in rows)
dups = [(k, v) for k, v in keys.items() if v > 1]
print("dup keys", len(dups), "sample", dups[:5])

# Population detailed with better dedup: group by origin,admin1,admin2,acc take max?
pop = post(
    "cae6v67mnrh690es",
    [
        {"id": "country", "expression": "country"},
        {"id": "pop", "expression": "population_type.Code"},
        {"id": "agg", "expression": "aggregation_type"},
        {"id": "admin1", "expression": "coa_admin1"},
        {"id": "admin2", "expression": "coa_admin2"},
        {"id": "origin", "expression": "origin"},
        {"id": "acc", "expression": "accommodation_type"},
        {"id": "source", "expression": "source"},
        {"id": "basis", "expression": "basis"},
        {"id": "total", "expression": "total"},
        {"id": "female", "expression": "female"},
        {"id": "male", "expression": "male"},
        {"id": "f04", "expression": "[f_0-4]"},
        {"id": "f511", "expression": "[f_5-11]"},
        {"id": "f1217", "expression": "[f_12-17]"},
        {"id": "m04", "expression": "[m_0-4]"},
        {"id": "m511", "expression": "[m_5-11]"},
        {"id": "m1217", "expression": "[m_12-17]"},
    ],
    f'date == DATE({int(latest[0:4])}, {int(latest[5:7])}, {int(latest[8:10])}) && aggregation_type == "detailed"',
)

print("detailed rows latest", len(pop))
# Why duplicates?
cmr = [r for r in pop if r["country"] == "CMR" and r["pop"] == "REF"]
keys2 = Counter((r["origin"], r["admin1"], r["admin2"], r["acc"]) for r in cmr)
dup_key = next(k for k, v in keys2.items() if v > 1)
print("example dup key", dup_key)
for r in cmr:
    if (r["origin"], r["admin1"], r["admin2"], r["acc"]) == dup_key:
        print(r)
