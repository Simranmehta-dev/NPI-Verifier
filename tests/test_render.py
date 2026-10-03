import pandas as pd

from npi_verifier.render import render_empty, render_results

SUMMARY = {"total": 2, "verified": 1, "flagged": 1, "rate": 50.0, "duplicates": 0}


def frame():
    return pd.DataFrame({
        "npi": ["1000000012", "1000000013"],
        "first_name": ["Asha", "<b>Ben</b>"],
        "last_name": ["Verma", "Carter"],
        "status": ["verified", "invalid_format"],
        "registry_name": ["Asha Verma", ""],
        "specialty": ["Medical Oncology", ""],
        "detail": ["", "Fails the check digit"],
        "duplicate_npi": [False, False],
    })


def test_shows_specialty_and_copy_button():
    html = render_results(frame(), SUMMARY)
    assert "Medical Oncology" in html and "Copy table" in html


def test_user_text_is_escaped():
    html = render_results(frame(), SUMMARY)
    assert "<b>Ben</b>" not in html and "&lt;b&gt;Ben" in html


def test_status_column_is_not_copied():
    assert 'class="nocopy"' in render_results(frame(), SUMMARY)


def test_verified_only_filters_rows():
    html = render_results(frame(), SUMMARY, verified_only=True)
    assert "Asha" in html and "Carter" not in html


def test_empty_state():
    assert "Run verification" in render_empty()
