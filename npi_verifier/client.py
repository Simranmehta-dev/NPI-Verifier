"""Thin client for the public NPPES NPI Registry API."""
from __future__ import annotations

import time
from typing import Optional

import requests

from .models import Provider


class RegistryError(Exception):
    """The registry could not be reached or returned something unusable."""


class NppesClient:
    BASE_URL = "https://npiregistry.cms.hhs.gov/api/"

    def __init__(self, session: Optional[requests.Session] = None,
                 timeout: float = 10.0, retries: int = 3, backoff: float = 1.0):
        self._session = session or requests.Session()
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def lookup(self, npi: str) -> Optional[Provider]:
        """Return the provider for this NPI, or None if the registry has no match."""
        payload = self._get({"version": "2.1", "number": npi})
        results = payload.get("results") or []
        if not results:
            return None
        return self._parse(results[0])

    def _get(self, params: dict) -> dict:
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                resp = self._session.get(self.BASE_URL, params=params, timeout=self.timeout)
                if resp.status_code >= 500:
                    raise RegistryError(f"server error {resp.status_code}")
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, RegistryError, ValueError) as exc:
                last_error = exc
                if attempt < self.retries - 1:
                    time.sleep(self.backoff * 2 ** attempt)  # 1s, 2s, 4s ...
        raise RegistryError(f"lookup failed after {self.retries} attempts: {last_error}")

    @staticmethod
    def _parse(result: dict) -> Provider:
        basic = result.get("basic") or {}
        taxonomies = result.get("taxonomies") or []
        primary = next((t for t in taxonomies if t.get("primary")),
                       taxonomies[0] if taxonomies else {})
        return Provider(
            npi=str(result.get("number", "")),
            first_name=basic.get("first_name", ""),
            last_name=basic.get("last_name", ""),
            specialty=primary.get("desc", ""),
            state=primary.get("state", ""),
            is_individual=result.get("enumeration_type") == "NPI-1",
        )
