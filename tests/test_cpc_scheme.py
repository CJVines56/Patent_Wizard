from backend.app.services.cpc_scheme import (
    describe_cpc_codes,
    describe_cpc_symbol,
    extract_cpc_codes,
    get_cpc_title,
)


def test_extract_cpc_codes_from_freeform_text():
    value = "Primary CPC: G06F17/30; backup A61K 31/00"
    codes = extract_cpc_codes(value)
    assert "G06F17/30" in codes
    assert "A61K31/00" in codes


def test_get_cpc_title_with_spacing_variants():
    # Accept codes with spaces; utility should normalize before lookup.
    title = get_cpc_title("A61K 31/00")
    assert isinstance(title, str)
    assert title.strip() != ""


def test_describe_cpc_symbol_returns_hierarchy_context():
    desc = describe_cpc_symbol("A01B1/022")
    assert desc["normalized"] == "A01B1/022"
    assert isinstance(desc["topic"], str)
    assert desc["topic"].strip() != ""
    hierarchy_codes = {row["code"] for row in desc["hierarchy"]}
    assert "A01B" in hierarchy_codes


def test_describe_cpc_codes_handles_iterables():
    payload = describe_cpc_codes(["G06F17/30", "H04W4/02"])
    assert len(payload) == 2
    assert payload[0]["normalized"] == "G06F17/30"
    assert payload[1]["normalized"] == "H04W4/02"
