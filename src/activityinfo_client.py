"""ActivityInfo REST API client."""
from __future__ import annotations

import json
from typing import Any

import requests

from src.config import ACTIVITYINFO_BASE_URL, ACTIVITYINFO_TOKEN


class ActivityInfoClient:
    def __init__(
        self,
        token: str | None = None,
        base_url: str | None = None,
        timeout: int = 300,
    ) -> None:
        self.token = token or ACTIVITYINFO_TOKEN
        self.base_url = (base_url or ACTIVITYINFO_BASE_URL).rstrip("/")
        self.timeout = timeout
        if not self.token:
            raise ValueError(
                "ACTIVITYINFO_TOKEN is missing. "
                "Local: copy .env.example to .env and set your token. "
                "Streamlit Cloud: App settings → Secrets → "
                'ACTIVITYINFO_TOKEN = "your_token".'
            )

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_json(self, path: str) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = requests.get(url, headers=self._headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def query_form_default(self, form_id: str) -> list[dict[str, Any]]:
        return self.get_json(f"form/{form_id}/query")

    def query_rows(
        self,
        form_id: str,
        columns: list[dict[str, str]],
        filter_expr: str | None = None,
    ) -> list[dict[str, Any]]:
        body: dict[str, Any] = {
            "rowSources": [{"rootFormId": form_id}],
            "columns": columns,
        }
        if filter_expr:
            body["filter"] = filter_expr
        url = f"{self.base_url}/query/rows"
        resp = requests.post(
            url, headers=self._headers, data=json.dumps(body), timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()
