#!/usr/bin/env python3
"""
Nebraska Medicaid Preferred Drug List (PDL) Redline Extractor
-------------------------------------------------------------
Analyzes Nebraska DHHS PDL PDFs, extracts drug names printed in red text,
separates drug names from superscript reason codes (e.g., NR, CL, QL, AL),
classifies them by Preferred vs. Non-Preferred category, and exports to CSV/Excel.

Includes automatic discovery to find the newest monthly release dynamically.
"""

import argparse
import os
import re
import sys
import tempfile
import urllib.request
from urllib.parse import urljoin

# Prevent bytecode compilation from writing .pyc files
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import pdfplumber

# Common Nebraska DHHS PDL Reason Codes
KNOWN_REASON_CODES = {"NR", "CL", "QL", "AL", "PA", "ST", "MB"}

# Official Nebraska DHHS PDL Portal URL
NEBRASKA_PDL_LISTINGS_URL = "https://nebraska.fhsc.com/PDL/PDLlistings.asp"

# Fallback known URL in case portal is temporarily offline
FALLBACK_PDL_URL = "https://nebraska.fhsc.com/downloads/PDL/NE_PDL-20260803.pdf"

# Default column horizontal split boundaries (for standard 612pt Letter width)
DEFAULT_PREF_MAX_X = 218.0
DEFAULT_NONPREF_MAX_X = 398.0

# Vertical page margins to exclude headers and footers
DEFAULT_TOP_MARGIN = 100.0
DEFAULT_BOTTOM_MARGIN = 720.0


def resolve_latest_pdl_url(
    portal_url: str = NEBRASKA_PDL_LISTINGS_URL,
) -> Tuple[str, Optional[str]]:
    """
    Dynamically discover the newest published Nebraska Medicaid PDL PDF URL
    by checking the official DHHS listings portal (https://nebraska.fhsc.com/PDL/PDLlistings.asp).

    Scrapes all 'NE_PDL-YYYYMMDD.pdf' links, parses the YYYYMMDD date,
    and returns the latest release URL and date string.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        req = urllib.request.Request(portal_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Find all href links matching NE_PDL-YYYYMMDD.pdf
        matches = re.findall(
            r'href=[\"\']([^\"\']*NE_PDL-(\d{8})\.pdf)[\"\']',
            html,
            re.IGNORECASE,
        )
        if matches:
            # Sort by date integer (YYYYMMDD) descending to get the newest file
            sorted_matches = sorted(matches, key=lambda m: int(m[1]), reverse=True)
            latest_href, latest_date = sorted_matches[0]
            latest_url = urljoin(portal_url, latest_href)
            return latest_url, latest_date
    except Exception as e:
        print(f"Notice: Dynamic portal resolution encountered: {e}. Using fallback URL.", file=sys.stderr)

    return FALLBACK_PDL_URL, None


def is_red_color(
    color: Any,
    r_min: float = 0.75,
    g_max: float = 0.25,
    b_max: float = 0.25,
) -> bool:
    """
    Determine whether a PDF character non_stroking_color represents Red.
    Handles RGB tuples (0.0-1.0 or 0-255) and CMYK tuples.
    """
    if color is None:
        return False
    if isinstance(color, (int, float)):
        return False
    if not isinstance(color, (tuple, list)):
        return False

    # Handle RGB (3 components)
    if len(color) == 3:
        r, g, b = color
        # Normalize if in 0-255 scale
        if max(r, g, b) > 1.0:
            r, g, b = r / 255.0, g / 255.0, b / 255.0
        return r >= r_min and g <= g_max and b <= b_max

    # Handle CMYK (4 components) - Pure red is C=0, M=1, Y=1, K=0
    elif len(color) == 4:
        c, m, y, k = color
        if max(c, m, y, k) > 1.0:
            c, m, y, k = c / 255.0, m / 255.0, y / 255.0, k / 255.0
        return c <= 0.25 and m >= 0.75 and y >= 0.75 and k <= 0.25

    return False


def is_non_drug_note(text: str) -> bool:
    """
    Check if the extracted text corresponds to a non-drug administrative note or header.
    """
    cleaned = text.strip().lower()
    if cleaned in {"highlight", "highlights"}:
        return True
    phrases_to_exclude = [
        "only those products",
        "highlights",
        "consult the drug lookup",
        "all reviewed agents",
        "prior authorization / class criteria",
        "preferred drug list",
        "nebraska medicaid",
        "unless otherwise specified",
    ]
    return any(p in cleaned for p in phrases_to_exclude)


def clean_text_formatting(text: str) -> str:
    """
    Normalize whitespace and ensure appropriate spacing around parentheses and punctuation.
    """
    text = re.sub(r"\s+", " ", text).strip()
    # Add space before opening parenthesis if preceded by alphanumeric
    text = re.sub(r"([A-Za-z0-9])\(", r"\1 (", text)
    # Add space after closing parenthesis if followed by alphanumeric
    text = re.sub(r"\)([A-Za-z0-9])", r") \1", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_line_characters(
    line_chars: List[Dict[str, Any]],
) -> Tuple[str, Optional[str]]:
    """
    Given a list of character objects on a single line sorted by x0 (left-to-right),
    split the base drug characters from the superscript suffix characters.

    Detection strategy:
    - Base font size: maximum font size among non-whitespace characters on the line.
    - Superscript character: font size <= (base_size - 1.5pt) OR baseline y0 >= (min_base_y0 + 1.8pt).
    - Drug name is reconstructed from base characters.
    - Suffix codes are reconstructed from superscript characters.
    """
    non_ws = [c for c in line_chars if c["text"].strip()]
    if not non_ws:
        return "", None

    base_size = max(c["size"] for c in non_ws)
    # Find baseline y0 for base size characters
    base_chars_y0 = [c["y0"] for c in non_ws if c["size"] >= base_size - 0.5]
    min_base_y0 = min(base_chars_y0) if base_chars_y0 else 0.0

    base_text_parts = []
    sup_text_parts = []

    for c in line_chars:
        # Whitespace characters inherit classification based on neighbors
        if not c["text"].strip():
            base_text_parts.append(c["text"])
            continue

        is_sup = False
        if base_size - c["size"] >= 1.5:
            is_sup = True
        elif (c["y0"] - min_base_y0) >= 1.8:
            is_sup = True

        if is_sup:
            sup_text_parts.append(c["text"])
        else:
            base_text_parts.append(c["text"])

    drug_name = "".join(base_text_parts).strip()
    sup_raw = "".join(sup_text_parts).strip()

    # Format suffix
    suffix = None
    if sup_raw:
        codes = [c.strip() for c in re.split(r"[,/\s]+", sup_raw) if c.strip()]
        if codes:
            suffix = ", ".join(codes)

    return drug_name, suffix


def cluster_chars_into_lines(
    chars: List[Dict[str, Any]],
    overlap_tolerance: float = 1.0,
) -> List[List[Dict[str, Any]]]:
    """
    Group character objects into visual horizontal lines.
    Uses vertical bounding-box overlap so that characters on the same line
    (including shifted superscripts) are grouped together, while characters
    on separate lines are kept distinct.
    """
    if not chars:
        return []

    # Sort characters from top to bottom
    chars_sorted = sorted(chars, key=lambda c: c["top"])
    lines: List[List[Dict[str, Any]]] = []

    for c in chars_sorted:
        placed = False
        for line in lines:
            avg_top = sum(ch["top"] for ch in line) / len(line)
            avg_bottom = sum(ch["bottom"] for ch in line) / len(line)
            # Check vertical overlap
            if not (
                c["bottom"] < avg_top + overlap_tolerance
                or c["top"] > avg_bottom - overlap_tolerance
            ):
                line.append(c)
                placed = True
                break
        if not placed:
            lines.append([c])

    # Sort lines by vertical position (min top coordinate)
    lines.sort(key=lambda l: min(c["top"] for c in l))
    return lines


def extract_red_drugs_from_page(
    page: pdfplumber.page.Page,
    page_num: int,
    top_margin: float = DEFAULT_TOP_MARGIN,
    bottom_margin: float = DEFAULT_BOTTOM_MARGIN,
    pref_max_x: float = DEFAULT_PREF_MAX_X,
    nonpref_max_x: float = DEFAULT_NONPREF_MAX_X,
    color_checker=is_red_color,
) -> List[Dict[str, Any]]:
    """
    Extract redline drug records from an individual PDF page.
    """
    words = page.extract_words()

    # Check whether this page contains a PDL drug table (requires column headers)
    upper_texts = [w["text"].upper() for w in words if w["top"] < 160]
    has_table_header = any("PREFERRED" in t for t in upper_texts) and (
        any("NON-PREFERRED" in t or "NON" in t for t in upper_texts)
        or any("AGENTS" in t for t in upper_texts)
    )
    if not has_table_header:
        return []

    # Extract all body characters matching red color
    red_chars = [
        c
        for c in page.chars
        if top_margin <= c["top"] <= bottom_margin
        and color_checker(c.get("non_stroking_color"))
    ]

    if not red_chars:
        return []

    # Cluster red characters into lines
    lines = cluster_chars_into_lines(red_chars)

    parsed_lines = []
    for line in lines:
        non_ws = [c for c in line if c["text"].strip()]
        if not non_ws:
            continue

        # Sort characters left-to-right (crucial for proper superscript handling)
        line.sort(key=lambda c: c["x0"])
        min_x = min(c["x0"] for c in non_ws)

        # Classify column
        if min_x < pref_max_x:
            col_cat = "Preferred Agents"
        elif min_x < nonpref_max_x:
            col_cat = "Non-Preferred Agents"
        else:
            # Skip Prior Authorization / Criteria column
            continue

        # Split base drug name and superscript suffix
        drug_name_part, suffix_part = parse_line_characters(line)

        # Exclude administrative / general note texts
        if is_non_drug_note(drug_name_part):
            continue
        if not drug_name_part and not suffix_part:
            continue

        parsed_lines.append(
            {
                "top": min(c["top"] for c in non_ws),
                "bottom": max(c["bottom"] for c in non_ws),
                "x0": min_x,
                "x1": max(c["x1"] for c in non_ws),
                "base_text": drug_name_part,
                "suffix": suffix_part,
                "column": col_cat,
            }
        )

    if not parsed_lines:
        return []

    # Merge multi-line drug entries (e.g. wrapped names or indented dosage forms)
    merged_entries: List[Dict[str, Any]] = []
    for pl in parsed_lines:
        if not merged_entries:
            merged_entries.append(pl)
            continue

        prev = merged_entries[-1]
        is_continuation = False

        # Must be in the same column and vertically adjacent (within 10pt)
        if pl["column"] == prev["column"] and 0 <= (pl["top"] - prev["bottom"]) < 10.0:
            if (
                prev["base_text"].count("(") > prev["base_text"].count(")")
                or prev["base_text"].endswith("-")
                or prev["base_text"].endswith("(")
                or pl["base_text"].startswith(")")
                or re.match(r"^(XR|ER|ODT|SOLN|SUSP|CAP|TAB|CREAM|PATCH|FLEXTOUCH|COTEMPLA)", pl["base_text"], re.IGNORECASE)
                or pl["x0"] > prev["x0"] + 4.0
            ):
                is_continuation = True

        if is_continuation:
            prev["base_text"] = (prev["base_text"] + " " + pl["base_text"]).strip()
            # Combine suffixes if both lines had parts
            if pl["suffix"]:
                prev["suffix"] = (
                    (prev["suffix"] + ", " if prev["suffix"] else "") + pl["suffix"]
                ).strip()
            prev["bottom"] = pl["bottom"]
        else:
            merged_entries.append(pl)

    # Format final records
    records = []
    for entry in merged_entries:
        drug_name = clean_text_formatting(entry["base_text"])
        if not drug_name or is_non_drug_note(drug_name):
            continue

        records.append(
            {
                "Page Number": page_num,
                "Drug Name": drug_name,
                "Reason Code / Suffix": entry["suffix"],
                "Column Category": entry["column"],
            }
        )

    return records


def extract_pdl_redline(
    source: Optional[Union[str, bytes]] = None,
    pages: Optional[List[int]] = None,
    top_margin: float = DEFAULT_TOP_MARGIN,
    bottom_margin: float = DEFAULT_BOTTOM_MARGIN,
    pref_max_x: float = DEFAULT_PREF_MAX_X,
    nonpref_max_x: float = DEFAULT_NONPREF_MAX_X,
) -> pd.DataFrame:
    """
    Extract all redline drugs from a Nebraska PDL PDF source.
    If source is None, empty, or 'latest', dynamically queries the Nebraska DHHS portal
    to locate and download the newest monthly PDF release.

    Returns a pandas DataFrame with columns:
      - Page Number
      - Drug Name
      - Reason Code / Suffix
      - Column Category
    """
    temp_file = None
    file_path = ""

    # If no source provided or 'latest', dynamically resolve newest monthly PDF
    if source is None or (isinstance(source, str) and source.strip().lower() in {"", "latest"}):
        print("Checking Nebraska DHHS portal for the latest monthly PDL release...", file=sys.stderr)
        resolved_url, release_date = resolve_latest_pdl_url()
        if release_date:
            print(f"Located latest release: {resolved_url} (Release: {release_date})", file=sys.stderr)
        else:
            print(f"Using default PDL URL: {resolved_url}", file=sys.stderr)
        source = resolved_url

    if isinstance(source, str) and (
        source.startswith("http://") or source.startswith("https://")
    ):
        print(f"Downloading PDL from: {source} ...", file=sys.stderr)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(source, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
        fd, temp_file = tempfile.mkstemp(suffix=".pdf")
        with open(fd, "wb") as f:
            f.write(content)
        file_path = temp_file
    elif isinstance(source, str):
        file_path = source
    elif isinstance(source, bytes):
        fd, temp_file = tempfile.mkstemp(suffix=".pdf")
        with open(fd, "wb") as f:
            f.write(source)
        file_path = temp_file

    all_records = []
    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            page_indices = range(total_pages) if pages is None else [p - 1 for p in pages if 1 <= p <= total_pages]

            for page_idx in page_indices:
                page_num = page_idx + 1
                page = pdf.pages[page_idx]
                page_records = extract_red_drugs_from_page(
                    page=page,
                    page_num=page_num,
                    top_margin=top_margin,
                    bottom_margin=bottom_margin,
                    pref_max_x=pref_max_x,
                    nonpref_max_x=nonpref_max_x,
                )
                all_records.extend(page_records)
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass

    columns = [
        "Page Number",
        "Drug Name",
        "Reason Code / Suffix",
        "Column Category",
    ]
    if not all_records:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(all_records, columns=columns)


def parse_page_range(arg: str) -> List[int]:
    """
    Parse a page range string like '1-5,8,11-15' into a list of integers.
    """
    pages = set()
    for part in arg.split(","):
        part = part.strip()
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
            pages.update(range(start, end + 1))
        elif part:
            pages.add(int(part))
    return sorted(pages)


def main():
    parser = argparse.ArgumentParser(
        description="Extract redline drug changes and superscript suffixes from Nebraska Medicaid PDL PDFs."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="latest",
        help="Path, URL, or 'latest' to automatically discover the newest Nebraska PDL PDF (default: 'latest').",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output CSV file path.",
    )
    parser.add_argument(
        "--excel",
        nargs="?",
        const="output.xlsx",
        help="Export output to Excel (.xlsx) file with optional path.",
    )
    parser.add_argument(
        "--pages",
        help="Specific pages to process, e.g. '1-10', '6,17,41', '1-5,8'.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display summary statistics of extracted records.",
    )

    args = parser.parse_args()

    pages = parse_page_range(args.pages) if args.pages else None

    df = extract_pdl_redline(args.input, pages=pages)

    print(f"Extraction complete. Found {len(df)} redline drug entries.\n", file=sys.stderr)

    if args.summary:
        print("=== REDLINE DRUGS SUMMARY ===")
        print(f"Total redline drugs: {len(df)}")
        if len(df) > 0:
            print("\nBy Column Category:")
            print(df["Column Category"].value_counts().to_string())
            print("\nBy Reason Code / Suffix:")
            print(df["Reason Code / Suffix"].fillna("None").value_counts().to_string())
            print("\nBy Page:")
            print(df["Page Number"].value_counts().sort_index().to_string())
        print("==============================\n")

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        if args.output.lower().endswith(".xlsx"):
            df.to_excel(args.output, index=False, engine="openpyxl")
            print(f"Successfully saved {len(df)} records to Excel: {args.output}")
        else:
            df.to_csv(args.output, index=False)
            print(f"Successfully saved {len(df)} records to CSV: {args.output}")

    if args.excel:
        excel_path = args.excel
        os.makedirs(os.path.dirname(os.path.abspath(excel_path)), exist_ok=True)
        df.to_excel(excel_path, index=False, engine="openpyxl")
        print(f"Successfully saved {len(df)} records to Excel: {excel_path}")

    if not args.output and not args.excel:
        if df.empty:
            print("No redline drugs found.")
        else:
            print(df.to_string(index=False))


if __name__ == "__main__":
    main()
