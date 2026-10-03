"""Internal registry: a local SQLite copy of doctors the live registry has confirmed."""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional

from .models import Provider
from .verifier import Registry

_SCHEMA = """
CREATE TABLE IF NOT EXISTS providers (
    npi TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, specialty TEXT,
    state TEXT, is_individual INTEGER, checked_at TEXT
)"""


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InternalRegistry:
    """Same lookup(npi) interface as the live client, so the Verifier can use either."""

    def __init__(self, path: str = ":memory:"):
        # Verification runs in worker threads, so share one connection behind a lock.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(_SCHEMA)
            self._conn.commit()

    def lookup(self, npi: str, max_age_days: Optional[int] = None) -> Optional[Provider]:
        """Return the saved provider. If max_age_days is set, older records count as a miss."""
        with self._lock:
            row = self._conn.execute(
                "SELECT first_name, last_name, specialty, state, is_individual, checked_at "
                "FROM providers WHERE npi = ?", (npi,)).fetchone()
        if row is None:
            return None
        age = _now() - datetime.fromisoformat(row[5])
        if max_age_days is not None and age > timedelta(days=max_age_days):
            return None
        return Provider(npi, row[0], row[1], row[2], row[3], bool(row[4]))

    def save(self, provider: Provider, checked_at: Optional[datetime] = None) -> None:
        stamp = (checked_at or _now()).isoformat()
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO providers VALUES (?, ?, ?, ?, ?, ?, ?)",
                (provider.npi, provider.first_name, provider.last_name, provider.specialty,
                 provider.state, int(provider.is_individual), stamp))
            self._conn.commit()

    def count(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM providers").fetchone()[0]


class CachedRegistry:
    """Look in the internal registry first (if the record is fresh), else ask the live registry
    and save what it finds. Records are refreshed from live once they are older than max_age_days."""

    def __init__(self, internal: InternalRegistry, live: Registry, max_age_days: int = 30):
        self._internal, self._live, self._max_age_days = internal, live, max_age_days
        self.internal_hits = 0
        self.live_hits = 0
        self._lock = threading.Lock()

    def lookup(self, npi: str) -> Optional[Provider]:
        provider = self._internal.lookup(npi, self._max_age_days)
        if provider is not None:
            with self._lock:
                self.internal_hits += 1
            return provider
        provider = self._live.lookup(npi)  # RegistryError propagates, and nothing gets saved
        if provider is not None:
            self._internal.save(provider)
            with self._lock:
                self.live_hits += 1
        return provider
