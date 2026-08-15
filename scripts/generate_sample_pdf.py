#!/usr/bin/env python3
"""
Generate a realistic sample Nebraska Medicaid PDL PDF document.
Mimics the typography, 3-column table structure, RGB red highlighting,
and superscript reason codes used by Nebraska DHHS PDL publications.
"""

import os
import sys

# Prevent bytecode compilation from writing .pyc files
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_sample_pdl(output_path: str = "examples/sample_pdl.pdf"):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter # 612 x 792

    # Color definitions
    black = (0.0, 0.0, 0.0)
    pure_red = (1.0, 0.0, 0.0)
    dark_blue = (0.02, 0.39, 0.76)

    # -------------------------------------------------------------
    # PAGE 1: COVER PAGE
    # -------------------------------------------------------------
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(*black)
    c.drawString(40, 740, "Nebraska Medicaid")
    c.drawString(40, 722, "Preferred Drug List")
    c.setFont("Helvetica", 11)
    c.drawString(40, 706, "with Prior Authorization Criteria")
    c.drawString(40, 690, "August 2026 PDL")

    # Header change notice with red Highlights
    c.setFont("Helvetica", 9)
    c.drawString(40, 660, "PDL updated August 3, 2026, ")
    c.setFillColorRGB(*pure_red)
    c.drawString(165, 660, "Highlights")
    c.setFillColorRGB(*black)
    c.drawString(212, 660, "indicate change from previous posting")

    c.drawString(40, 630, "For the most up to date list of covered drugs consult the Drug Lookup on the Nebraska Medicaid website at")
    c.setFillColorRGB(*dark_blue)
    c.drawString(40, 616, "https://ne.primetherapeutics.com/drug-lookup")

    c.setFillColorRGB(*black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, 580, "General Information & Policies")
    c.setFont("Helvetica", 9)
    c.drawString(40, 560, "• PDMP Check Requirements: Providers are required to check prescription history.")
    c.drawString(40, 542, "• Opioids: Maximum dose covered is 90 MME per day.")
    c.drawString(40, 524, "• Non-Preferred Drug Coverage requires therapeutic trial and failure of preferred agents.")

    # Page 1 Footer
    c.setFont("Helvetica", 8)
    c.drawString(40, 40, "Unless otherwise specified, the listing of a particular brand or generic name includes all dosage forms.")
    c.drawString(40, 28, "CL – Prior Authorization / Class Criteria apply   QL – Quantity/Duration Limit   AL – Age Limit   NR – Not Reviewed")
    c.drawRightString(572, 28, "Page 1 of 3")
    c.showPage()

    # -------------------------------------------------------------
    # PAGE 2: ANALGESICS & ANTHELMINTICS TABLE
    # -------------------------------------------------------------
    # Page Header
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(*black)
    c.drawString(40, 760, "Nebraska Medicaid Preferred Drug List with Prior Authorization Criteria")
    c.setFont("Helvetica", 8)
    c.drawString(40, 748, "PDL Update August 3, 2026, ")
    c.setFillColorRGB(*pure_red)
    c.drawString(150, 748, "Highlights")
    c.setFillColorRGB(*black)
    c.drawString(190, 748, "indicate change from previous posting")

    # Category 1 Header
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(*black)
    c.drawString(40, 715, "ANALGESICS, OPIOID SHORT-ACTING")

    # 3-Column Table Headers
    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, 690, "Preferred Agents")
    c.drawString(226, 690, "Non-Preferred Agents")
    c.drawString(402, 690, "Prior Authorization/Class Criteria")

    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.line(40, 684, 572, 684)

    # Row 1: Black Preferred / Black Non-Preferred / Criteria
    y = 668
    c.setFont("Helvetica", 9.5)
    c.setFillColorRGB(*black)
    c.drawString(40, y, "amoxicillin CAP")
    c.drawString(226, y, "tramadol ER TAB")
    c.setFont("Helvetica", 6.5)
    c.drawString(306, y + 3.5, "CL")
    c.setFont("Helvetica", 8)
    c.drawString(402, y, "Trial of 2 preferred agents")

    # Row 2: RED Preferred Agent with single Suffix (buprenorphine PATCH^QL)
    y = 648
    c.setFont("Helvetica", 9.5)
    c.setFillColorRGB(*pure_red)
    c.drawString(40, y, "buprenorphine PATCH")
    c.setFont("Helvetica", 6.5)
    c.drawString(145, y + 3.5, "QL")

    # Row 2 Non-Preferred: Black (oxycodone CR TAB)
    c.setFont("Helvetica", 9.5)
    c.setFillColorRGB(*black)
    c.drawString(226, y, "oxycodone CR TAB")
    c.setFont("Helvetica", 8)
    c.drawString(402, y, "Max 30 days initial supply")

    # Row 3: Black Preferred (cephalexin SUSP) / RED Non-Preferred with Suffix (tapentadol SOLN^NR)
    y = 628
    c.setFont("Helvetica", 9.5)
    c.setFillColorRGB(*black)
    c.drawString(40, y, "cephalexin SUSP")

    c.setFillColorRGB(*pure_red)
    c.drawString(226, y, "tapentadol SOLN")
    c.setFont("Helvetica", 6.5)
    c.drawString(306, y + 3.5, "NR")

    # Row 4: Black Preferred / RED Non-Preferred with Embedded Multi-Suffix (LIPFENDRA (enlicitide)^NR,QL TAB)
    y = 608
    c.setFont("Helvetica", 9.5)
    c.setFillColorRGB(*black)
    c.drawString(40, y, "ibuprofen 800MG TAB")

    c.setFillColorRGB(*pure_red)
    c.drawString(226, y, "LIPFENDRA (enlicitide)")
    c.setFont("Helvetica", 6.5)
    c.drawString(331, y + 3.5, "NR,QL")
    c.setFont("Helvetica", 9.5)
    c.drawString(356, y, "TAB")

    # Category 2 Header on Page 2
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(*black)
    c.drawString(40, 570, "ANTHELMINTICS")

    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, 550, "Preferred Agents")
    c.drawString(226, 550, "Non-Preferred Agents")
    c.drawString(402, 550, "Prior Authorization/Class Criteria")
    c.line(40, 544, 572, 544)

    # Row 5: Black Preferred (ivermectin TAB) / RED Non-Preferred without Suffix (ALBENZA (albendazole))
    y = 528
    c.setFont("Helvetica", 9.5)
    c.setFillColorRGB(*black)
    c.drawString(40, y, "ivermectin TAB")

    c.setFillColorRGB(*pure_red)
    c.drawString(226, y, "ALBENZA (albendazole)")

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*black)
    c.drawString(402, y, "Requires medical justification")

    # Page 2 Footer
    c.setFont("Helvetica", 8)
    c.drawString(40, 40, "Unless otherwise specified, the listing of a particular brand or generic name includes all dosage forms.")
    c.drawString(40, 28, "CL – Prior Authorization / Class Criteria apply   QL – Quantity/Duration Limit   AL – Age Limit   NR – Not Reviewed")
    c.drawRightString(572, 28, "Page 2 of 3")
    c.showPage()

    # -------------------------------------------------------------
    # PAGE 3: ADVANCED CASES (MULTI-LINE, CONSECUTIVE RED, NOTES)
    # -------------------------------------------------------------
    # Page Header
    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(*black)
    c.drawString(40, 760, "Nebraska Medicaid Preferred Drug List with Prior Authorization Criteria")
    c.setFont("Helvetica", 8)
    c.drawString(40, 748, "PDL Update August 3, 2026, Highlights indicate change from previous posting")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, 715, "ANTIDIABETICS & DERMATOLOGY")

    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, 690, "Preferred Agents")
    c.drawString(226, 690, "Non-Preferred Agents")
    c.drawString(402, 690, "Prior Authorization/Class Criteria")
    c.line(40, 684, 572, 684)

    # Row 1-2: Multi-line Red Drug: AWIQLI (insulin icodec-abae) \n FLEXTOUCH PEN^NR
    c.setFont("Helvetica", 9.5)
    c.setFillColorRGB(*black)
    c.drawString(40, 668, "metformin TAB")

    c.setFillColorRGB(*pure_red)
    c.drawString(226, 668, "AWIQLI (insulin icodec-abae)")
    c.drawString(244, 656, "FLEXTOUCH PEN")
    c.setFont("Helvetica", 6.5)
    c.drawString(330, 659.5, "NR")

    # Row 3-4: Consecutive Independent Red Lines (LASOLEX and MICOCLEAR)
    y1 = 626
    c.setFont("Helvetica", 9.5)
    c.setFillColorRGB(*black)
    c.drawString(40, y1, "clotrimazole CREAM (OTC)")

    c.setFillColorRGB(*pure_red)
    c.drawString(226, y1, "LASOLEX (clotrimazole)")
    c.setFont("Helvetica", 6.5)
    c.drawString(334, y1 + 3.5, "NR")
    c.setFont("Helvetica", 9.5)
    c.drawString(352, y1, "SOLN (OTC)")

    y2 = 606
    c.drawString(226, y2, "MICOCLEAR (clotrimazole)")
    c.setFont("Helvetica", 6.5)
    c.drawString(346, y2 + 3.5, "NR")
    c.setFont("Helvetica", 9.5)
    c.drawString(364, y2, "CREAM")

    # Row 5: Multi-line multi-code Suffix:
    # methylphenidate ER ODT (generic \n COTEMPLA XR)^AL,NR,QL
    y3 = 566
    c.setFont("Helvetica", 9.5)
    c.setFillColorRGB(*black)
    c.drawString(40, y3, "QUILLIVANT XR SUSP")

    c.setFillColorRGB(*pure_red)
    c.drawString(226, y3, "methylphenidate ER ODT (generic")
    c.drawString(238, 554, "COTEMPLA XR)")
    c.setFont("Helvetica", 6.5)
    c.drawString(316, 557.5, "AL,NR,QL")

    # Row 6: Non-drug Red Note to test exclusion
    y4 = 510
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColorRGB(*pure_red)
    c.drawString(40, y4, "Only those products for review are listed.")

    # Page 3 Footer
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*black)
    c.drawString(40, 40, "Unless otherwise specified, the listing of a particular brand or generic name includes all dosage forms.")
    c.drawString(40, 28, "CL – Prior Authorization / Class Criteria apply   QL – Quantity/Duration Limit   AL – Age Limit   NR – Not Reviewed")
    c.drawRightString(572, 28, "Page 3 of 3")
    c.showPage()

    c.save()
    print(f"Sample PDL PDF generated at: {output_path}")


if __name__ == "__main__":
    create_sample_pdl()
