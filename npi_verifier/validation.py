"""Offline NPI checks. These need no network, so they run first and are free."""
from __future__ import annotations

import re

# CMS defines the NPI check digit as Luhn over the number prefixed with 80840.
NPI_PREFIX = "80840"


def clean_npi(raw: object) -> str:
    """Keep digits only, so '1234-567-893 ' and 1234567893 are treated alike."""
    return re.sub(r"\D", "", str(raw or ""))


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def is_valid_npi(npi: str) -> bool:
    """10 digits, starts with 1 or 2, and passes the check digit."""
    return (
        len(npi) == 10
        and npi.isdigit()
        and npi[0] in "12"
        and _luhn_ok(NPI_PREFIX + npi)
    )


def with_check_digit(first_nine: str) -> str:
    """Complete a 9 digit stem into a checksum-valid NPI (used for demo data and tests)."""
    for d in range(10):
        candidate = f"{first_nine}{d}"
        if _luhn_ok(NPI_PREFIX + candidate):
            return candidate
    raise ValueError("unreachable: some digit always satisfies Luhn")
