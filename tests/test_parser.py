from src.parser import extract_addresses, normalize_body_for_matching, normalize_subject


def test_subject_normalization_removes_reply_and_forward_prefixes():
    assert normalize_subject("Re: Fwd: Meeting Update") == "meeting update"


def test_subject_normalization_handles_extra_spaces():
    assert normalize_subject("  RE:   Budget Review   ") == "budget review"


def test_subject_normalization_handles_empty_subject():
    assert normalize_subject(None) == ""


def test_extract_addresses_handles_display_names():
    addresses = extract_addresses("John Doe <john@example.com>, jane@example.com")

    assert "john@example.com" in addresses
    assert "jane@example.com" in addresses


def test_body_normalization_collapses_whitespace():
    body = "Hello,\n\n   This   is a test."
    assert normalize_body_for_matching(body) == "hello, this is a test."