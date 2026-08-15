# Nebraska DHHS Preferred Drug List Reason Codes Reference

Nebraska Medicaid defines standard clinical reason codes printed as superscript suffixes alongside drug listings in the Preferred Drug List (PDL).

---

## Standard Reason Codes & Descriptions

| Code | Full Name / Description | Clinical Meaning | Example Suffix |
| :--- | :--- | :--- | :--- |
| **NR** | **Not Reviewed** | Product was not reviewed during the standard P&T cycle; New Drug criteria apply. | `tapentadol SOLNNR` |
| **CL** | **Class Criteria** | Prior Authorization / Class Criteria apply before coverage is approved. | `tramadol ER TABCL` |
| **QL** | **Quantity / Duration Limit** | Specific dispensing quantity or duration limitations apply per prescription/month. | `buprenorphine PATCHQL` |
| **AL** | **Age Limit** | Drug coverage is subject to specific patient age constraints (e.g. pediatric/geriatric). | `atomoxetine (generic ATONCY)AL,NR` |
| **PA** | **Prior Authorization** | General prior authorization approval required. | `specialty productPA` |
| **ST** | **Step Therapy** | Prerequisite trial of first-line agents required. | `second-line agentST` |
| **MB** | **Medical Billing** | Covered under medical benefit rather than pharmacy benefit. | `injectable agentMB` |

---

## Multi-Code Combinations

Drugs may have multiple applicable reason codes concatenated with commas or spaces in superscript:

- `NR, QL` (e.g., `LIPFENDRA (enlicitide)NR,QL TAB`): Not Reviewed and Quantity Limit.
- `AL, NR` (e.g., `atomoxetine (generic ATONCY)AL,NR`): Age Limit and Not Reviewed.
- `AL, NR, QL` (e.g., `methylphenidate ER ODT (generic COTEMPLA XR)AL,NR,QL`): Age Limit, Not Reviewed, and Quantity Limit.
- `None` (e.g., `ALBENZA (albendazole)`): No reason code suffix present; drug is printed in red to denote a status change without additional suffix restrictions.
