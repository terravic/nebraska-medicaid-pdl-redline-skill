# Healthcare Data Ethics, Privacy & Code of Conduct

## 1. Purpose & Healthcare Data Pledge

The **Nebraska Medicaid PDL Redline Extraction Skill** project is dedicated to providing open, reliable, and privacy-first tools for analyzing public formulary publications. 

Contributors, maintainers, and users of this project pledge to uphold the highest standards of **healthcare data ethics, information privacy, and responsible software development**.

---

## 2. Core Healthcare & Data Protection Standards

### 2.1 Public Formulary Scope Only
* This project, skill, and associated scripts are designed solely for processing **publicly accessible state Medicaid Preferred Drug Lists (PDL)**, formulary notices, and public health agency PDF reference tables.
* The tools in this repository are intended for administrative, formulary research, and health plan operational transparency.

### 2.2 Strict Zero-PHI / Zero-PII Policy
* **No Protected Health Information**: Under no circumstances should real Protected Health Information (PHI) as defined under HIPAA, patient prescription records, medical histories, or Personally Identifiable Information (PII) be introduced, committed, or transmitted to this repository, issue tracker, or community channels.
* Any contribution containing real patient data will be immediately rejected and expunged.

### 2.3 Synthetic Test Data Mandate
* All test fixtures, mock PDF files (such as `sample_pdl.pdf`), unit test cases, and documentation examples must remain **100% synthetic in nature**.
* Mock drug items, reason codes, and dosage formats must represent synthetic illustrations to protect this SKILL and ensure complete privacy compliance.

### 2.4 Clinical Verification Disclaimer
* This skill is an automated document parsing and table extraction utility. It does not provide clinical diagnosis, medical advice, or substitute for professional medical judgment.
* Formulary coverage decisions must always be verified against official state Medicaid DHHS publications and prescribing guidelines.

---

## 3. Acceptable vs. Unacceptable Practices

### Acceptable Practices:
* Contributing parsing heuristics, regex enhancements, and coordinate-clustering improvements for public PDF formulary documents.
* Submitting synthetic test cases and edge cases to improve redline text extraction.
* Reporting layout changes in official state Medicaid publications.
* Ensuring all data exports remain clean, structured, and auditable.

### Unacceptable Practices:
* Attempting to ingest, attach, or process confidential patient medical records or individual prescription claim histories through this repository.
* Sharing proprietary, non-public health plan confidential data without authorization.
* Modifying the skill or test fixtures to include real patient identifiers.

---

## 4. Privacy Incident Reporting & Remediation

If any contributor or user suspects that sensitive health information or non-public data has been inadvertently submitted:
1. **Immediate Notification**: Notify project maintainers immediately through repository issue tracking or security reporting channels.
2. **Immediate Redaction**: Project maintainers will promptly purge, redact, or overwrite the affected commits, issues, or log artifacts from version control and discussion records.
3. **Audit**: Maintainers will review project fixtures to confirm 100% synthetic compliance.

---

## 5. Governance & Maintainer Responsibilities

Project maintainers are responsible for:
* Enforcing data privacy boundaries and ensuring zero real PHI enters the codebase.
* Reviewing pull requests and sample fixtures for synthetic compliance before merging.
* Maintaining transparent, auditable extraction logic for public formulary analysis.
