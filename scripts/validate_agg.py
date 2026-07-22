"""Validate aggregation strategy for stock totals."""
import json
import urllib.request
from collections import Counter, defaultdict

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


rows = post(
    "cae6v67mnrh690es",
    [
        {"id": "country", "expression": "country"},
        {"id": "iso3", "expression": "asylum.iso3"},
        {"id": "pop", "expression": "population_type.Code"},
        {"id": "agg", "expression": "aggregation_type"},
        {"id": "admin1", "expression": "coa_admin1"},
        {"id": "admin2", "expression": "coa_admin2"},
        {"id": "origin", "expression": "origin"},
        {"id": "acc", "expression": "accommodation_type"},
        {"id": "total", "expression": "total"},
    ],
    'date == DATE(2026, 5, 30) && population_type.Code == "REF"',
)

print("REF rows", len(rows))
for c in ["CHD", "CMR", "NIG", "BKF", "MLI", "SEN", "GHA"]:
    sub = [r for r in rows if r["country"] == c]
    by_agg = defaultdict(float)
    for r in sub:
        by_agg[r["agg"]] += r["total"] or 0
    print(c, "iso", set(r["iso3"] for r in sub), "n", len(sub), dict(by_agg))

cmr = [r for r in rows if r["country"] == "CMR" and r["agg"] == "detailed"]
print("CMR detailed sum", sum(r["total"] or 0 for r in cmr), "rows", len(cmr))
keys = Counter((r["origin"], r["admin1"], r["admin2"], r["acc"]) for r in cmr)
print("dup keys", sum(1 for _, v in keys.items() if v > 1), "max", max(keys.values()) if keys else 0)

det = [r for r in rows if r["agg"] == "detailed"]
tot = [r for r in rows if r["agg"] == "total"]
print("ALL detailed sum", sum(r["total"] or 0 for r in det))
print("ALL total sum", sum(r["total"] or 0 for r in tot))
print("countries detailed", sorted({r["country"] for r in det}))
print("countries total", sorted({r["country"] for r in tot}))

stock = {}
for c in set(r["country"] for r in rows):
    t = [r for r in tot if r["country"] == c]
    if t:
        stock[c] = sum(r["total"] or 0 for r in t)
    else:
        stock[c] = sum(r["total"] or 0 for r in det if r["country"] == c)
print("hybrid stock", sorted(stock.items(), key=lambda x: -x[1]))
print("hybrid total", sum(stock.values()))

# Check CHD: total vs detailed by origin
chd_tot = [r for r in tot if r["country"] == "CHD"]
chd_det = [r for r in det if r["country"] == "CHD"]
print("CHD total by origin", Counter({r["origin"]: r["total"] for r in chd_tot}))
print(
    "CHD detailed by origin",
    {
        o: sum(r["total"] or 0 for r in chd_det if r["origin"] == o)
        for o in set(r["origin"] for r in chd_det)
    },
)
