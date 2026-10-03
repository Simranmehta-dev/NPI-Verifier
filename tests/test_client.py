import pytest
import requests

from npi_verifier.client import NppesClient, RegistryError


class FakeResponse:
    def __init__(self, status=200, body=None):
        self.status_code, self._body = status, body or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


SAMPLE = {"result_count": 1, "results": [{
    "number": "1234567893", "enumeration_type": "NPI-1",
    "basic": {"first_name": "ASHA", "last_name": "VERMA"},
    "taxonomies": [{"desc": "Other", "primary": False, "state": "NY"},
                   {"desc": "Medical Oncology", "primary": True, "state": "CA"}]}]}


def make(responses, retries=3):
    return NppesClient(session=FakeSession(responses), retries=retries, backoff=0)


def test_parses_primary_taxonomy():
    p = make([FakeResponse(body=SAMPLE)]).lookup("1234567893")
    assert (p.last_name, p.specialty, p.state, p.is_individual) == ("VERMA", "Medical Oncology", "CA", True)


def test_no_results_returns_none():
    assert make([FakeResponse(body={"result_count": 0})]).lookup("1234567893") is None


def test_retries_then_succeeds():
    client = make([requests.ConnectionError("down"), FakeResponse(503), FakeResponse(body=SAMPLE)])
    assert client.lookup("1234567893") is not None
    assert client._session.calls == 3


def test_gives_up_after_retries():
    client = make([requests.Timeout("slow")] * 3)
    with pytest.raises(RegistryError):
        client.lookup("1234567893")
