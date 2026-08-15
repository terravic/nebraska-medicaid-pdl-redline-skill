"""
Unit and Integration Tests for Nebraska Medicaid PDL Redline Skill
"""

import os
import sys
import tempfile
import pytest
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.extract_redline_pdl import (
    is_red_color,
    is_non_drug_note,
    clean_text_formatting,
    parse_line_characters,
    cluster_chars_into_lines,
    extract_pdl_redline,
    parse_page_range,
)
from scripts.generate_sample_pdf import create_sample_pdl


# ----------------------------------------------------------------------
# 1. Color Filtering Unit Tests
# ----------------------------------------------------------------------
def test_is_red_color_rgb():
    assert is_red_color((1.0, 0.0, 0.0)) is True
    assert is_red_color((0.9, 0.05, 0.05)) is True
    assert is_red_color((255, 0, 0)) is True
    assert is_red_color((230, 20, 20)) is True

    # Non-red colors
    assert is_red_color((0.0, 0.0, 0.0)) is False # Black
    assert is_red_color((0.0, 0.0, 1.0)) is False # Blue
    assert is_red_color((0.0, 0.8, 0.0)) is False # Green
    assert is_red_color((0.95, 0.95, 0.95)) is False # Light gray
    assert is_red_color(None) is False
    assert is_red_color(0.5) is False
    assert is_red_color("red") is False


def test_is_red_color_cmyk():
    assert is_red_color((0.0, 1.0, 1.0, 0.0)) is True # Pure CMYK red
    assert is_red_color((0.0, 0.0, 0.0, 1.0)) is False # Black
    assert is_red_color((1.0, 0.0, 0.0, 0.0)) is False # Cyan


# ----------------------------------------------------------------------
# 2. Text Formatting & Note Exclusion Unit Tests
# ----------------------------------------------------------------------
def test_is_non_drug_note():
    assert is_non_drug_note("Highlights") is True
    assert is_non_drug_note("Highlights indicate change from previous posting") is True
    assert is_non_drug_note("Only those products for review are listed.") is True
    assert is_non_drug_note("consult the Drug Lookup on the Nebraska Medicaid website") is True
    assert is_non_drug_note("Unless otherwise specified, the listing of a particular brand") is True

    # Valid drug names must NOT be excluded
    assert is_non_drug_note("buprenorphine PATCH") is False
    assert is_non_drug_note("tapentadol SOLN") is False
    assert is_non_drug_note("ALBENZA (albendazole)") is False
    assert is_non_drug_note("LIPFENDRA (enlicitide) TAB") is False


def test_clean_text_formatting():
    assert clean_text_formatting("tapentadol   SOLN") == "tapentadol SOLN"
    assert clean_text_formatting("LASOLEX(clotrimazole)") == "LASOLEX (clotrimazole)"
    assert clean_text_formatting("(clotrimazole)SOLN") == "(clotrimazole) SOLN"
    assert clean_text_formatting("  URSOLIGN (ursodiol) CAP  ") == "URSOLIGN (ursodiol) CAP"


# ----------------------------------------------------------------------
# 3. Superscript & Line Character Splitting Unit Tests
# ----------------------------------------------------------------------
def test_parse_line_characters_trailing_suffix():
    # Base: 'tapentadol SOLN' (size=10.0, y0=100.0)
    # Suffix: 'NR' (size=6.5, y0=103.5)
    chars = []
    x = 10.0
    for ch in "tapentadol SOLN":
        chars.append({"text": ch, "size": 10.0, "y0": 100.0, "x0": x})
        x += 6.0
    for ch in "NR":
        chars.append({"text": ch, "size": 6.5, "y0": 103.5, "x0": x})
        x += 4.0

    name, suffix = parse_line_characters(chars)
    assert name == "tapentadol SOLN"
    assert suffix == "NR"


def test_parse_line_characters_embedded_multi_suffix():
    # 'LIPFENDRA (enlicitide)' (10pt) + 'NR,QL' (6.5pt) + ' TAB' (10pt)
    chars = []
    x = 10.0
    for ch in "LIPFENDRA (enlicitide)":
        chars.append({"text": ch, "size": 10.0, "y0": 100.0, "x0": x})
        x += 6.0
    for ch in "NR,QL":
        chars.append({"text": ch, "size": 6.5, "y0": 103.5, "x0": x})
        x += 4.0
    for ch in " TAB":
        chars.append({"text": ch, "size": 10.0, "y0": 100.0, "x0": x})
        x += 6.0

    name, suffix = parse_line_characters(chars)
    assert name == "LIPFENDRA (enlicitide) TAB"
    assert suffix == "NR, QL"


def test_parse_line_characters_no_suffix():
    # 'ALBENZA (albendazole)' (all 10pt)
    chars = []
    x = 10.0
    for ch in "ALBENZA (albendazole)":
        chars.append({"text": ch, "size": 10.0, "y0": 100.0, "x0": x})
        x += 6.0

    name, suffix = parse_line_characters(chars)
    assert name == "ALBENZA (albendazole)"
    assert suffix is None


# ----------------------------------------------------------------------
# 4. Line Clustering Unit Tests
# ----------------------------------------------------------------------
def test_cluster_chars_into_lines():
    # Line 1 chars: top=200, bottom=210
    line1 = [{"text": "A", "top": 200.0, "bottom": 210.0, "x0": 10.0}]
    # Line 2 chars: top=230, bottom=240
    line2 = [{"text": "B", "top": 230.0, "bottom": 240.0, "x0": 10.0}]

    lines = cluster_chars_into_lines(line1 + line2)
    assert len(lines) == 2
    assert lines[0][0]["text"] == "A"
    assert lines[1][0]["text"] == "B"


def test_parse_page_range():
    assert parse_page_range("1-3,5,7-8") == [1, 2, 3, 5, 7, 8]
    assert parse_page_range("2") == [2]
    assert parse_page_range("4-6") == [4, 5, 6]


# ----------------------------------------------------------------------
# 5. Integration Tests on Sample PDF
# ----------------------------------------------------------------------
@pytest.fixture(scope="session")
def sample_pdf_path(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "sample_pdl.pdf"
    create_sample_pdl(str(fn))
    return str(fn)


def test_sample_pdf_extraction(sample_pdf_path):
    df = extract_pdl_redline(sample_pdf_path)

    # Expected columns
    expected_cols = ["Page Number", "Drug Name", "Reason Code / Suffix", "Column Category"]
    assert list(df.columns) == expected_cols

    # Expected count: exactly 8 redline drugs (Page 1 cover excluded, Page 3 note excluded)
    assert len(df) == 8

    # Page distribution: 4 on page 2, 4 on page 3
    assert len(df[df["Page Number"] == 2]) == 4
    assert len(df[df["Page Number"] == 3]) == 4
    assert len(df[df["Page Number"] == 1]) == 0

    # Verify Page 2 items
    p2 = df[df["Page Number"] == 2].reset_index(drop=True)
    assert p2.loc[0, "Drug Name"] == "buprenorphine PATCH"
    assert p2.loc[0, "Reason Code / Suffix"] == "QL"
    assert p2.loc[0, "Column Category"] == "Preferred Agents"

    assert p2.loc[1, "Drug Name"] == "tapentadol SOLN"
    assert p2.loc[1, "Reason Code / Suffix"] == "NR"
    assert p2.loc[1, "Column Category"] == "Non-Preferred Agents"

    assert p2.loc[2, "Drug Name"] == "LIPFENDRA (enlicitide) TAB"
    assert p2.loc[2, "Reason Code / Suffix"] == "NR, QL"
    assert p2.loc[2, "Column Category"] == "Non-Preferred Agents"

    assert p2.loc[3, "Drug Name"] == "ALBENZA (albendazole)"
    assert pd.isna(p2.loc[3, "Reason Code / Suffix"]) or p2.loc[3, "Reason Code / Suffix"] is None
    assert p2.loc[3, "Column Category"] == "Non-Preferred Agents"

    # Verify Page 3 items
    p3 = df[df["Page Number"] == 3].reset_index(drop=True)
    # Multi-line item
    assert p3.loc[0, "Drug Name"] == "AWIQLI (insulin icodec-abae) FLEXTOUCH PEN"
    assert p3.loc[0, "Reason Code / Suffix"] == "NR"

    # Consecutive lines
    assert p3.loc[1, "Drug Name"] == "LASOLEX (clotrimazole) SOLN (OTC)"
    assert p3.loc[1, "Reason Code / Suffix"] == "NR"

    assert p3.loc[2, "Drug Name"] == "MICOCLEAR (clotrimazole) CREAM"
    assert p3.loc[2, "Reason Code / Suffix"] == "NR"

    # Multi-code suffix
    assert p3.loc[3, "Drug Name"] == "methylphenidate ER ODT (generic COTEMPLA XR)"
    assert p3.loc[3, "Reason Code / Suffix"] == "AL, NR, QL"


def test_page_filtering(sample_pdf_path):
    df_p2 = extract_pdl_redline(sample_pdf_path, pages=[2])
    assert len(df_p2) == 4
    assert all(df_p2["Page Number"] == 2)


def test_export_csv_and_excel(sample_pdf_path):
    df = extract_pdl_redline(sample_pdf_path)

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f_csv:
        csv_path = f_csv.name
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f_xlsx:
        xlsx_path = f_xlsx.name

    try:
        df.to_csv(csv_path, index=False)
        df.to_excel(xlsx_path, index=False, engine="openpyxl")

        # Verify CSV reload
        df_csv = pd.read_csv(csv_path)
        assert len(df_csv) == len(df)
        assert list(df_csv.columns) == list(df.columns)

        # Verify Excel reload
        df_xlsx = pd.read_excel(xlsx_path, engine="openpyxl")
        assert len(df_xlsx) == len(df)
        assert list(df_xlsx.columns) == list(df.columns)
    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)
        if os.path.exists(xlsx_path):
            os.remove(xlsx_path)


# ----------------------------------------------------------------------
# 6. Real PDL Verification (if downloaded)
# ----------------------------------------------------------------------
def test_real_pdl_extraction():
    real_pdf_path = "sample_real_pdl.pdf"
    if not os.path.exists(real_pdf_path):
        pytest.skip("sample_real_pdl.pdf not present in local workspace")

    df = extract_pdl_redline(real_pdf_path)
    assert len(df) == 14

    # Verify key known redline drugs in the 99-page Nebraska PDL
    drug_names = df["Drug Name"].tolist()
    assert "tapentadol SOLN" in drug_names
    assert "ALBENZA (albendazole)" in drug_names
    assert "LASOLEX (clotrimazole) SOLN (OTC)" in drug_names
    assert "MICOCLEAR (clotrimazole) CREAM" in drug_names
    assert "URSOLIGN (ursodiol) CAP" in drug_names
    assert "AWIQLI (insulin icodec-abae) FLEXTOUCH PEN" in drug_names
    assert "LIPFENDRA (enlicitide) TAB" in drug_names
    assert "VEPPANU (vepdegestrant)" in drug_names
    assert "CAVHANZA ODT (nilotinib)" in drug_names
    assert "AZENTRA" in drug_names
    assert "PRENOVA" in drug_names
    assert "methylphenidate ER ODT (generic COTEMPLA XR)" in drug_names
    assert "atomoxetine (generic ATONCY)" in drug_names
    assert "doxycycline hyclate 75MG CAPS" in drug_names


def test_resolve_latest_pdl_url():
    from scripts.extract_redline_pdl import resolve_latest_pdl_url
    url, date_str = resolve_latest_pdl_url()
    assert url.startswith("https://nebraska.fhsc.com/downloads/PDL/NE_PDL-")
    assert url.endswith(".pdf")
    if date_str:
        assert len(date_str) == 8
        assert date_str.isdigit()
