from npi_verifier.validation import clean_npi, is_valid_npi, with_check_digit


def test_known_valid_npi():
    assert is_valid_npi("1234567893")  # standard CMS example


def test_bad_check_digit():
    assert not is_valid_npi("1234567890")


def test_wrong_length_and_prefix():
    assert not is_valid_npi("12345")
    assert not is_valid_npi("3234567893")


def test_clean_strips_formatting():
    assert clean_npi(" 1234-567-893 ") == "1234567893"
    assert clean_npi(None) == ""


def test_with_check_digit_roundtrip():
    assert is_valid_npi(with_check_digit("123456789"))
