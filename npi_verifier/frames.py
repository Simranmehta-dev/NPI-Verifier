"""Glue between pandas DataFrames and the verifier."""
from __future__ import annotations

import re

import pandas as pd

from .models import Respondent, Result, Status
from .validation import clean_npi

REQUIRED_COLUMNS = ["npi", "first_name", "last_name"]

# Header names people commonly use, mapped to the names the code expects.
_ALIASES = {
    "npi": {"npi", "npi_number", "npi_id", "npi_no"},
    "first_name": {"first_name", "first", "firstname", "given_name"},
    "last_name": {"last_name", "last", "lastname", "surname", "family_name"},
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Accept headers like 'NPI', 'First Name', 'last-name' by renaming them to the expected names."""
    rename: dict = {}
    for col in df.columns:
        key = re.sub(r"[^a-z0-9]+", "_", str(col).lower()).strip("_")  # also strips a BOM
        for target, names in _ALIASES.items():
            if key in names and target not in rename.values():
                rename[col] = target
    return df.rename(columns=rename)


def load_respondents(df: pd.DataFrame) -> list[Respondent]:
    df = normalize_columns(df)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing column(s): {', '.join(missing)}. Expected {REQUIRED_COLUMNS}")
    rows = df[REQUIRED_COLUMNS].fillna("").astype(str)
    return [Respondent(r.npi, r.first_name, r.last_name) for r in rows.itertuples(index=False)]


def results_to_frame(results: list[Result]) -> pd.DataFrame:
    df = pd.DataFrame({
        "npi": [r.respondent.npi for r in results],
        "first_name": [r.respondent.first_name for r in results],
        "last_name": [r.respondent.last_name for r in results],
        "status": [r.status.value for r in results],
        "registry_name": [r.registry_name for r in results],
        "specialty": [r.specialty for r in results],
        "detail": [r.detail for r in results],
    })
    # The same NPI appearing twice (after cleaning formatting) in one survey is worth flagging on its own.
    cleaned = df["npi"].map(clean_npi)
    df["duplicate_npi"] = cleaned.ne("") & cleaned.duplicated(keep=False)  # blanks are not duplicates
    return df


def summarize(df: pd.DataFrame) -> dict:
    counts = {s.value: int((df["status"] == s.value).sum()) for s in Status}
    total = len(df)
    verified = counts[Status.VERIFIED.value]
    return {
        "total": total,
        "verified": verified,
        "flagged": total - verified,
        "rate": (100 * verified / total) if total else 0.0,
        "duplicates": int(df["duplicate_npi"].sum()),
        "by_status": counts,
    }
