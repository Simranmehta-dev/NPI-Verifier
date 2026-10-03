from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Status(str, Enum):
    VERIFIED = "verified"
    NAME_MISMATCH = "name_mismatch"
    NOT_FOUND = "not_found"
    INVALID_FORMAT = "invalid_format"
    LOOKUP_ERROR = "lookup_error"


@dataclass(frozen=True)
class Respondent:
    """One row of input: who the survey says this person is."""
    npi: str
    first_name: str
    last_name: str


@dataclass(frozen=True)
class Provider:
    """What the registry says about an NPI."""
    npi: str
    first_name: str
    last_name: str
    specialty: str
    state: str
    is_individual: bool = True


@dataclass(frozen=True)
class Result:
    respondent: Respondent
    status: Status
    registry_name: str = ""
    specialty: str = ""
    detail: str = ""
