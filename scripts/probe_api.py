"""Probe ActivityInfo API endpoints for WCA DIMA database."""
import json
import urllib.error
import urllib.request

TOKEN = "f41a159db82745fd5df797a6a0d4d55c"
BASE = "https://www.activityinfo.org/resources"


def request(method: str, path: str, body: dict | None = None):
    url = f"{BASE}{path}"
    data = None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            print(f"OK {method} {path} status={resp.status} bytes={len(raw)}")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"ERR {method} {path} status={e.code}")
        print(err[:1000])
        return None


def main():
    # 1) Default query form endpoint variants
    for path in [
        "/query/form/cxmho36mnrg1bl3b",
        "/form/cxmho36mnrg1bl3b/query",
        "/query/v43/form/cxmho36mnrg1bl3b",
    ]:
        request("GET", path)

    # 2) Modern query/rows with rowSources + expression
    body = {
        "rowSources": [{"rootFormId": "cxmho36mnrg1bl3b"}],
        "columns": [
            {"id": "code", "expression": "Code"},
            {"id": "label", "expression": "[Label (Description)]"},
        ],
    }
    rows = request("POST", "/query/rows", body)
    if rows is not None:
        with open("probe_pop_types.json", "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print("pop types sample:", rows[:5] if isinstance(rows, list) else type(rows))

    # 3) Legacy formId + formula
    body2 = {
        "formId": "cxmho36mnrg1bl3b",
        "columns": [
            {"id": "code", "formula": "Code"},
            {"id": "label", "formula": "[Label (Description)]"},
        ],
    }
    request("POST", "/query/rows", body2)

    # 4) Population sample with selected columns
    pop_body = {
        "rowSources": [{"rootFormId": "cae6v67mnrh690es"}],
        "columns": [
            {"id": "date", "expression": "date"},
            {"id": "country", "expression": "country"},
            {"id": "origin", "expression": "origin"},
            {"id": "asylum", "expression": "asylum"},
            {"id": "population_type", "expression": "population_type"},
            {"id": "coa_admin1", "expression": "coa_admin1"},
            {"id": "coa_admin2", "expression": "coa_admin2"},
            {"id": "female", "expression": "female"},
            {"id": "male", "expression": "male"},
            {"id": "total", "expression": "total"},
            {"id": "f_0_4", "expression": "[f_0-4]"},
            {"id": "m_0_4", "expression": "[m_0-4]"},
        ],
    }
    pop = request("POST", "/query/rows", pop_body)
    if pop is not None:
        with open("probe_population_sample.json", "w", encoding="utf-8") as f:
            json.dump(pop[:20] if isinstance(pop, list) else pop, f, ensure_ascii=False, indent=2)
        print("population rows:", len(pop) if isinstance(pop, list) else pop)


if __name__ == "__main__":
    main()
