---
name: nebraska-medicaid-pdl-redline
description: >-
  Analyze Nebraska DHHS Preferred Drug List (PDL) PDFs, extract red-text drug names
  with superscript reason codes (e.g., NR, CL, QL, AL), classify drugs by Preferred vs.
  Non-Preferred category, and export structured tables to CSV or Excel.
---

# Nebraska Medicaid PDL Redline Extraction Skill

Extracts all redline drug additions, status changes, and superscript suffix reason codes from the Nebraska Department of Health and Human Services (DHHS) Preferred Drug List (PDL) PDF.

---

## Privacy & Synthetic Data Notice

> [!IMPORTANT]
> **Protected Health Information (PHI) Disclaimer:**
> Any references to patient data, clinical scenarios, or sample PDF fixtures in this SKILL and repository are **entirely synthetic in nature** to ensure privacy compliance and protect this SKILL.

---

## 1. Overview & Capability

Official Nebraska Medicaid PDL publications highlight status changes and new drug additions in **pure red text** (`RGB: (1.0, 0.0, 0.0)`). Superscript reason codes (e.g., `NR`, `CL`, `QL`, `AL`) are printed in smaller font sizes with elevated baselines at the end of or embedded within drug names.

This skill automates:
1. **Character-Level Color Filtering**: Isolates red characters using PDF graphic-state fill colors (`pdfplumber` / `pdfminer`).
2. **Superscript & Suffix Splitting**: Separates base drug names from superscript reason codes (drop `>= 1.5pt` font size or baseline elevation `>= 1.8pt`).
3. **Table & Column Categorization**: Maps drug positions to `"Preferred Agents"` or `"Non-Preferred Agents"` while filtering out non-drug criteria and notes.
4. **Multi-line Reconstruction**: Assembles wrapped drug names and dosage forms without erroneously merging consecutive independent red rows.
5. **Structured Table Export**: Outputs clean tables to CSV (`.csv`) or Excel (`.xlsx`).

---

## 2. Output Schema

The extracted table contains the following columns:

| Column Name | Type | Description | Example Values |
| :--- | :--- | :--- | :--- |
| **`Page Number`** | Integer | Physical PDF page number (1-indexed) | `6`, `17`, `41` |
| **`Drug Name`** | String | Plain-text normalized drug name | `"tapentadol SOLN"`, `"buprenorphine PATCH"` |
| **`Reason Code / Suffix`** | String / None | Extracted reason code(s), or `None` if absent | `"NR"`, `"QL"`, `"NR, QL"`, `"AL, NR, QL"`, `None` |
| **`Column Category`** | String | Column category where drug was located | `"Preferred Agents"`, `"Non-Preferred Agents"` |

---

## 3. Quick Start & Execution

### Option A: Automatically Discover & Extract the Latest Monthly Release
```bash
# Automatically finds and downloads the newest published monthly PDL
python3 scripts/extract_redline_pdl.py -o redline_drugs.csv --summary
```

### Option B: Extract from a Specific PDF URL or Local File
```bash
python3 scripts/extract_redline_pdl.py "https://nebraska.fhsc.com/downloads/PDL/NE_PDL-20260803.pdf" -o redline_drugs.csv --summary
# or for a local file:
python3 scripts/extract_redline_pdl.py path/to/pdl.pdf -o redline_drugs.xlsx --excel --summary
```

### Option C: Extract Specific Page Ranges
```bash
python3 scripts/extract_redline_pdl.py sample_real_pdl.pdf --pages 1-15,41,63 -o output.csv
```

---

## 4. Python API Usage

You can invoke the extraction logic directly within Python scripts or agent tools:

```python
from scripts.extract_redline_pdl import extract_pdl_redline

# Extract from URL, local file path, or bytes
df = extract_pdl_redline("https://nebraska.fhsc.com/downloads/PDL/NE_PDL-20260803.pdf")

# Export to CSV or Excel
df.to_csv("nebraska_pdl_redline.csv", index=False)
df.to_excel("nebraska_pdl_redline.xlsx", index=False, engine="openpyxl")

# Access records
for _, row in df.iterrows():
    print(f"Page {row['Page Number']}: [{row['Column Category']}] {row['Drug Name']} (Suffix: {row['Reason Code / Suffix']})")
```

---

## 5. Helper Scripts & Test Suite

- **License**: [LICENSE](./LICENSE) (Apache License 2.0)
- **Code of Conduct**: [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)
- **Extraction CLI Script**: [extract_redline_pdl.py](./scripts/extract_redline_pdl.py)
- **Sample Mock PDL Generator**: [generate_sample_pdf.py](./scripts/generate_sample_pdf.py)
- **Direct Test Runner**: [run_tests.py](./scripts/run_tests.py)
- **Comprehensive Unit/Integration Test Suite**: [test_pdl_extractor.py](./tests/test_pdl_extractor.py)

### Running Direct Tests
Execute the entire test suite via pytest or the test runner:
```bash
python3 scripts/run_tests.py
# or
pytest -v tests/test_pdl_extractor.py
```

### Generating / Refreshing the Mock Sample PDF
```bash
python3 scripts/generate_sample_pdf.py
```

---

## 6. Reference Documentation

- [PDL Layout & Coordinate Specification](./references/pdl_format_spec.md)
- [DHHS Reason Codes Reference Guide](./references/reason_codes.md)
- [Sample Mock PDF](./examples/sample_pdl.pdf)
- [Sample CSV Output](./examples/sample_output.csv)
- [Sample Excel Output](./examples/sample_output.xlsx)
