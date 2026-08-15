# Nebraska Medicaid Preferred Drug List (PDL) PDF Specification & Parsing Guide

This reference document describes the layout structure, typography, color-coding conventions, and character-level geometry of the official Nebraska Department of Health and Human Services (DHHS) Preferred Drug List (PDL) PDF documents.

---

## 1. Page Layout & Coordinate System

- **Page Dimensions**: Standard US Letter (612.0 pt width × 792.0 pt height).
- **Coordinate Origin**:
  - `pdfplumber` / top-down: `(0, 0)` at top-left.
  - `pdfminer` / bottom-up: `(0, 0)` at bottom-left (`y0` represents baseline / bottom).

### Vertical Page Margins (Header & Footer Exclusions)
- **Top Header Margin**: `top < 100.0 pt` (Contains DHHS title, publication update notice, and header red text such as `"Highlights"`).
- **Table Column Headers**: `130.0 pt <= top <= 160.0 pt` (Contains column title strings).
- **Table Body Area**: `160.0 pt <= top <= 720.0 pt` (Drug rows and clinical criteria).
- **Page Footer Margin**: `top > 720.0 pt` (Contains MAC policy disclaimer, footnote legend for reason codes, and page numbers `Page X of Y`).

---

## 2. Table Column Boundaries

Most listing pages consist of a borderless 3-column table:

| Column Index | Column Name | Typical X-Range (x0) | Content Description |
| :--- | :--- | :--- | :--- |
| **Column 1** | `Preferred Agents` | `36.0 pt - 218.0 pt` | Covered preferred drugs without special prior authorization requirements. |
| **Column 2** | `Non-Preferred Agents` | `218.0 pt - 398.0 pt` | Non-preferred drugs requiring trial/failure of preferred agents or PA. |
| **Column 3** | `Prior Authorization/Class Criteria` | `398.0 pt - 580.0 pt` | Clinical criteria, quantity limits, and age rules. |

---

## 3. Color Space & Redline Encoding

- **Standard Text**: Rendered in black (`RGB: (0.0, 0.0, 0.0)` or `DeviceGray: (0.0,)`).
- **Redline Highlight Text**: Drugs with changed status, newly added products, or modified criteria are printed in pure red (`RGB: (1.0, 0.0, 0.0)` or CMYK `(0.0, 1.0, 1.0, 0.0)`).
- **Color Threshold Filter**:
  ```python
  def is_red(color):
      if isinstance(color, (tuple, list)) and len(color) == 3:
          r, g, b = color
          if max(r, g, b) > 1.0:
              r, g, b = r / 255.0, g / 255.0, b / 255.0
          return r >= 0.75 and g <= 0.25 and b <= 0.25
      elif isinstance(color, (tuple, list)) and len(color) == 4:
          c, m, y, k = color
          if max(c, m, y, k) > 1.0:
              c, m, y, k = c / 255.0, m / 255.0, y / 255.0, k / 255.0
          return c <= 0.25 and m >= 0.75 and y >= 0.75 and k <= 0.25
      return False
  ```

---

## 4. Superscript Suffix & Drug Name Separation

Nebraska PDL embeds superscript reason codes at the end of drug names or between the brand/generic name and the dosage form.

### Physical Characteristics:
1. **Font Size Drop**:
   - Base drug characters: `9.5 pt - 10.0 pt` (e.g. `ArialMT`, `Arial-BoldMT`).
   - Superscript characters: `6.0 pt - 6.5 pt` (Drop of `>= 1.5 pt`).
2. **Baseline Elevation Shift**:
   - Base characters baseline: `y0` (e.g., `294.12 pt`).
   - Superscript characters baseline: `y0 + 3.73 pt` (e.g., `297.85 pt`).
3. **Character Sorting Rule**:
   - Within a line, characters MUST be sorted strictly from left to right (`x0` ascending).
   - Do NOT sort characters primarily by `top` coordinate within a line; superscripts have a smaller `top` coordinate and will otherwise precede the base drug text.

### Parsing Examples:
- **Trailing Suffix**: `tapentadol SOLNNR`
  - Base (10pt): `tapentadol SOLN`
  - Superscript (6.5pt): `NR`
  - Result: Drug Name = `tapentadol SOLN`, Suffix = `NR`
- **Embedded Suffix**: `LIPFENDRA (enlicitide)NR,QL TAB`
  - Base (10pt): `LIPFENDRA (enlicitide) TAB`
  - Superscript (6.5pt): `NR,QL`
  - Result: Drug Name = `LIPFENDRA (enlicitide) TAB`, Suffix = `NR, QL`
- **No Suffix**: `ALBENZA (albendazole)`
  - Base (10pt): `ALBENZA (albendazole)`
  - Superscript: None
  - Result: Drug Name = `ALBENZA (albendazole)`, Suffix = `None`

---

## 5. Multi-line & Consecutive Entry Handling

- **Multi-line Drug Name Wrapping**:
  - Example: Line 1: `AWIQLI (insulin icodec-abae)`, Line 2: `FLEXTOUCH PENNR`
  - Joined as: `AWIQLI (insulin icodec-abae) FLEXTOUCH PEN` with suffix `NR`.
- **Consecutive Red Lines**:
  - Example: Line 1: `LASOLEX (clotrimazole)NR SOLN (OTC)`, Line 2: `MICOCLEAR (clotrimazole)NR CREAM`
  - Preserved as two distinct rows by vertical line clustering (`vertical distance >= 10.0 pt` or non-continuation).
