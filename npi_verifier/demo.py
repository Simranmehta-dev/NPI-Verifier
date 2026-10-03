"""Offline registry with synthetic people so the dashboard runs without internet."""
from __future__ import annotations

from typing import Optional

from .models import Provider
from .validation import with_check_digit

_PEOPLE = [
    ("100000001", "Asha", "Verma", "Medical Oncology", "CA"),
    ("100000002", "Daniel", "Okafor", "Hematology", "TX"),
    ("100000003", "Mei", "Lin", "Neurology", "NY"),
    ("100000004", "Lucas", "Moreau", "Radiation Oncology", "IL"),
    ("100000005", "Priya", "Nair", "Internal Medicine", "FL"),
    ("100000006", "Tom", "Becker", "Neurology", "WA"),
]

DEMO_PROVIDERS = {
    with_check_digit(stem): Provider(with_check_digit(stem), first, last, spec, state)
    for stem, first, last, spec, state in _PEOPLE
}


class DemoRegistry:
    def lookup(self, npi: str) -> Optional[Provider]:
        return DEMO_PROVIDERS.get(npi)
