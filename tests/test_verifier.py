from npi_verifier.client import RegistryError
from npi_verifier.models import Provider, Respondent, Status
from npi_verifier.validation import with_check_digit
from npi_verifier.verifier import Verifier

GOOD = with_check_digit("100000001")


class FakeRegistry:
    def __init__(self, provider=None, error=None):
        self.provider, self.error = provider, error

    def lookup(self, npi):
        if self.error:
            raise self.error
        return self.provider


def provider(**kw):
    base = dict(npi=GOOD, first_name="Asha", last_name="Verma", specialty="Oncology", state="CA")
    return Provider(**{**base, **kw})


def run(reg, first="Asha", last="Verma", npi=GOOD):
    return Verifier(reg).verify(Respondent(npi, first, last))


def test_verified_ignores_case_and_punctuation():
    assert run(FakeRegistry(provider()), "asha", "VERMA").status == Status.VERIFIED


def test_name_mismatch():
    assert run(FakeRegistry(provider()), "Bob", "Smith").status == Status.NAME_MISMATCH


def test_not_found():
    assert run(FakeRegistry(None)).status == Status.NOT_FOUND


def test_invalid_format_skips_registry():
    reg = FakeRegistry(error=AssertionError("registry should not be called"))
    assert run(reg, npi="123").status == Status.INVALID_FORMAT


def test_registry_failure_is_reported_not_raised():
    assert run(FakeRegistry(error=RegistryError("boom"))).status == Status.LOOKUP_ERROR


def test_organization_npi_is_flagged():
    assert run(FakeRegistry(provider(is_individual=False))).status == Status.NAME_MISMATCH


def test_verify_many_keeps_order():
    people = [Respondent(GOOD, "Asha", "Verma"), Respondent("1", "X", "Y")]
    out = Verifier(FakeRegistry(provider())).verify_many(people)
    assert [r.status for r in out] == [Status.VERIFIED, Status.INVALID_FORMAT]
