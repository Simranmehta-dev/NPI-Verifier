from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, Optional, Protocol

from .client import RegistryError
from .models import Provider, Respondent, Result, Status
from .validation import clean_npi, is_valid_npi


class Registry(Protocol):
    """Anything with lookup(npi) works: the live client, a demo registry, a test fake."""
    def lookup(self, npi: str) -> Optional[Provider]: ...


def _norm(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def names_match(respondent: Respondent, provider: Provider) -> bool:
    return (_norm(respondent.first_name) == _norm(provider.first_name)
            and _norm(respondent.last_name) == _norm(provider.last_name))


class Verifier:
    def __init__(self, registry: Registry, max_workers: int = 5):
        self._registry = registry
        self._max_workers = max_workers

    def verify(self, respondent: Respondent) -> Result:
        npi = clean_npi(respondent.npi)
        if not is_valid_npi(npi):
            return Result(respondent, Status.INVALID_FORMAT,
                          detail="Not 10 digits or fails the check digit")
        try:
            provider = self._registry.lookup(npi)
        except RegistryError as exc:
            return Result(respondent, Status.LOOKUP_ERROR, detail=str(exc))
        if provider is None:
            return Result(respondent, Status.NOT_FOUND, detail="NPI not in registry")
        registry_name = f"{provider.first_name} {provider.last_name}".strip()
        if not provider.is_individual:
            return Result(respondent, Status.NAME_MISMATCH, specialty=provider.specialty,
                          detail="NPI belongs to an organization, not a person")
        if names_match(respondent, provider):
            return Result(respondent, Status.VERIFIED, registry_name, provider.specialty)
        return Result(respondent, Status.NAME_MISMATCH, registry_name, provider.specialty,
                      detail=f"Registry lists {registry_name}")

    def verify_many(self, respondents: Iterable[Respondent]) -> list[Result]:
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            return list(pool.map(self.verify, respondents))  # map keeps input order
