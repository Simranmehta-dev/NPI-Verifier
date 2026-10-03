from datetime import datetime, timedelta, timezone

import pytest

from npi_verifier.client import RegistryError
from npi_verifier.models import Provider, Respondent, Status
from npi_verifier.store import CachedRegistry, InternalRegistry
from npi_verifier.validation import with_check_digit
from npi_verifier.verifier import Verifier

NPI = with_check_digit("100000001")
DOC = Provider(NPI, "Asha", "Verma", "Medical Oncology", "CA")


class CountingLive:
    def __init__(self, provider=DOC, error=None):
        self.provider, self.error, self.calls = provider, error, 0

    def lookup(self, npi):
        self.calls += 1
        if self.error:
            raise self.error
        return self.provider


def test_save_and_lookup_roundtrip():
    store = InternalRegistry()
    store.save(DOC)
    assert store.lookup(NPI) == DOC and store.count() == 1


def test_unknown_npi_is_a_miss():
    assert InternalRegistry().lookup(NPI) is None


def test_old_records_expire_only_when_max_age_is_set():
    store = InternalRegistry()
    store.save(DOC, checked_at=datetime.now(timezone.utc) - timedelta(days=60))
    assert store.lookup(NPI, max_age_days=30) is None
    assert store.lookup(NPI) == DOC


def test_cache_misses_go_live_then_hits_stay_local():
    store, live = InternalRegistry(), CountingLive()
    cache = CachedRegistry(store, live)
    assert cache.lookup(NPI) == DOC and cache.lookup(NPI) == DOC
    assert live.calls == 1
    assert (cache.live_hits, cache.internal_hits) == (1, 1)


def test_stale_record_is_refreshed_from_live():
    store, live = InternalRegistry(), CountingLive()
    store.save(DOC, checked_at=datetime.now(timezone.utc) - timedelta(days=90))
    CachedRegistry(store, live, max_age_days=30).lookup(NPI)
    assert live.calls == 1


def test_not_found_is_not_saved():
    store = InternalRegistry()
    assert CachedRegistry(store, CountingLive(provider=None)).lookup(NPI) is None
    assert store.count() == 0


def test_live_failure_propagates_and_saves_nothing():
    store = InternalRegistry()
    with pytest.raises(RegistryError):
        CachedRegistry(store, CountingLive(error=RegistryError("down"))).lookup(NPI)
    assert store.count() == 0


def test_works_from_many_threads_through_the_verifier():
    store, live = InternalRegistry(), CountingLive()
    verifier = Verifier(CachedRegistry(store, live), max_workers=8)
    out = verifier.verify_many([Respondent(NPI, "Asha", "Verma")] * 40)
    assert all(r.status == Status.VERIFIED for r in out)
    assert store.count() == 1
