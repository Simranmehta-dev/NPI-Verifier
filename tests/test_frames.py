import pandas as pd
import pytest

from npi_verifier.demo import DemoRegistry
from npi_verifier.frames import load_respondents, results_to_frame, summarize
from npi_verifier.verifier import Verifier

SAMPLE = "data/sample_respondents.csv"


def test_missing_column_raises():
    with pytest.raises(ValueError, match="npi"):
        load_respondents(pd.DataFrame({"first_name": ["a"], "last_name": ["b"]}))


def test_sample_file_end_to_end():
    df_in = pd.read_csv(SAMPLE, dtype=str)
    out = results_to_frame(Verifier(DemoRegistry()).verify_many(load_respondents(df_in)))
    s = summarize(out)
    assert s["total"] == 11
    assert s["by_status"] == {"verified": 7, "name_mismatch": 1, "not_found": 1,
                              "invalid_format": 2, "lookup_error": 0}
    assert s["duplicates"] == 4  # Asha twice, Mei twice (one with messy formatting)


def test_flexible_headers_are_accepted():
    df = pd.DataFrame({"NPI": ["1000000012"], "First Name": ["Asha"], "Last-Name": ["Verma"]})
    r = load_respondents(df)[0]
    assert (r.npi, r.first_name, r.last_name) == ("1000000012", "Asha", "Verma")


def test_byte_order_mark_in_header_is_ignored():
    df = pd.DataFrame({"\ufeffnpi": ["1"], "first_name": ["a"], "last_name": ["b"]})
    assert load_respondents(df)[0].npi == "1"
