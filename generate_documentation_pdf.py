# -*- coding: utf-8 -*-
"""
REDCap Newborn Follow-up Dashboard — Standard Operating Procedure (SOP) Generator (V3.0)
Generates an official, comprehensive SOP PDF document covering data architecture,
column mapping reference tables, cleansing algorithms, 7-step chronological SNCU matching,
multi-variable linking decision trees, and exhaustive specifications for Form 1 and Form 2 data validation rules.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and draw 'Page X of Y' 
    along with running headers and lines on all pages except the cover page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super().showPage()
        super().save()

    def draw_page_elements(self, page_count):
        if self._pageNumber == 1:
            # Draw decorative side accent on Title Page
            self.saveState()
            self.setFillColor(colors.HexColor("#0D9488")) # Teal Accent
            self.rect(0, 0, 18, 792, fill=True, stroke=False)
            self.setFillColor(colors.HexColor("#1E3A8A")) # Deep Navy Accent
            self.rect(18, 0, 6, 792, fill=True, stroke=False)
            self.restoreState()
            return
            
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#4B5563")) # Cool Gray Text
        
        # Header text
        self.drawString(54, 752, "REDCap Newborn Follow-up Dashboard — Standard Operating Procedure (SOP V3.0)")
        
        # Header line
        self.setStrokeColor(colors.HexColor("#D1D5DB")) # Light gray line
        self.setLineWidth(0.5)
        self.line(54, 745, 558, 745)
        
        # Footer line
        self.line(54, 52, 558, 52)
        
        # Footer text
        self.drawString(54, 40, "Confidential — Standard Operating Procedure — Internal Health Program Evaluation")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        
        self.restoreState()

def build_pdf(filename="REDCap_Newborn_Followup_Dashboard_Documentation.pdf"):
    # Target page width = 612, height = 792 (Letter)
    # Margins: 0.75 in (54 pt) all around. Printable width = 504 pt.
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Palette
    c_primary = colors.HexColor("#1E3A8A")   # Deep Blue
    c_secondary = colors.HexColor("#0D9488") # Teal
    c_dark = colors.HexColor("#1F2937")      # Dark text
    c_bg = colors.HexColor("#F9FAFB")        # Light table/box background
    c_border = colors.HexColor("#E5E7EB")    # Border gray
    c_code_bg = colors.HexColor("#F3F4F6")
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'SOPTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=24, leading=28,
        textColor=c_primary, spaceAfter=8
    )
    
    subtitle_style = ParagraphStyle(
        'SOPSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=12, leading=16,
        textColor=c_secondary, spaceAfter=20
    )
    
    h1_style = ParagraphStyle(
        'SOPH1', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=14, leading=18,
        textColor=c_primary, spaceBefore=16, spaceAfter=8,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SOPH2', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, leading=14,
        textColor=c_secondary, spaceBefore=11, spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'SOPBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=12.5,
        textColor=c_dark, spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'SOPBullet', parent=body_style,
        leftIndent=12, firstLineIndent=-8, spaceAfter=4
    )

    table_header_style = ParagraphStyle(
        'SOPTableHeader', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=11,
        textColor=colors.white, alignment=0
    )

    table_cell_style = ParagraphStyle(
        'SOPTableCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=10.5,
        textColor=c_dark
    )

    table_cell_bold = ParagraphStyle(
        'SOPTableCellBold', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=10.5,
        textColor=c_primary
    )

    code_style = ParagraphStyle(
        'SOPCode', parent=styles['Normal'],
        fontName='Courier', fontSize=7, leading=9.5,
        textColor=colors.HexColor("#111827")
    )

    story = []

    # =========================================================================
    # TITLE / COVER SECTION
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("REDCap Newborn Follow-up Dashboard", title_style))
    story.append(Paragraph("Standard Operating Procedure (SOP) & Technical Reference Manual — Version 3.0", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=c_secondary, spaceAfter=12))

    meta_data = [
        [Paragraph("<b>Document Identifier:</b> SOP-NHRP-DASHBOARD-2026-V3.0", table_cell_style),
         Paragraph(f"<b>Effective Date:</b> September 2026", table_cell_style)],
        [Paragraph("<b>Target Audience:</b> Data Analysts, Telecallers, District Supervisors, State Coordinators", table_cell_style),
         Paragraph(f"<b>Operational Status:</b> Live Production Release", table_cell_style)]
    ]
    t_meta = Table(meta_data, colWidths=[260, 244])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    # =========================================================================
    # SECTION 1: EXECUTIVE OVERVIEW & PIPELINE ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("1. Executive Overview & System Architecture", h1_style))
    story.append(Paragraph(
        "This Standard Operating Procedure (SOP V3.0) defines the end-to-end data pipeline, column mappings, "
        "data cleansing algorithms, 7-step chronological cross-dataset matching criteria, and data validation rules for the "
        "<b>REDCap Newborn Follow-up Dashboard</b>. The system aggregates birth notification, registration, and telephonic follow-up "
        "data (60,000+ records) from REDCap alongside state ANMOL delivery reports and institutional SNCU admission datasets, "
        "providing real-time KPI monitoring, 1-click line-list filtering, and automated discrepancy reporting.", body_style
    ))
    
    pipeline_steps = [
        [Paragraph("<b>Stage</b>", table_header_style), Paragraph("<b>Data Source / Component</b>", table_header_style), Paragraph("<b>Description & Purpose</b>", table_header_style)],
        [Paragraph("1. Ingestion", table_cell_bold), Paragraph("REDCap, ANMOL, & SNCU Files", table_cell_style), Paragraph("Loads raw REDCap dataset (`NHRP update.xlsx`), ANMOL delivery line-lists, and SNCU admissions using Calamine engine.", table_cell_style)],
        [Paragraph("2. Standardization", table_cell_bold), Paragraph("Data Cleansing Modules", table_cell_style), Paragraph("Parses multi-format dates, swaps inverted day-month entries, standardizes blocks/villages, and validates 10-digit phones.", table_cell_style)],
        [Paragraph("3. Spatial Mapping", table_cell_bold), Paragraph("Location & Staff Directories", table_cell_style), Paragraph("Maps Block (Col AF) and Village to Subcentre, attaching ANM, CHO, and Telecaller coordinator metadata.", table_cell_style)],
        [Paragraph("4. ANMOL Match", table_cell_bold), Paragraph("4-Tier Matching Engine", table_cell_style), Paragraph("Cross-matches ANMOL home and out-of-district births with REDCap records via MPID, phone, and fuzzy name similarity.", table_cell_style)],
        [Paragraph("5. SNCU Match", table_cell_bold), Paragraph("7-Step Chronological Engine", table_cell_style), Paragraph("Cross-verifies SNCU neonatal deaths (<=28 days) with REDCap across 7 sequential criteria with dual record IDs.", table_cell_style)],
        [Paragraph("6. Validation", table_cell_bold), Paragraph("Form 1 & Form 2 Rules", table_cell_style), Paragraph("Evaluates 17 Form 1 checks (excluding pending cases in 1.9) and 7 Form 2 checks (evaluating Col XU/AAD/ACM).", table_cell_style)],
        [Paragraph("7. Standalone Build", table_cell_bold), Paragraph("HTML Generator (`generate_dashboard.py`)", table_cell_style), Paragraph("Bundles compressed JSON payload, Chart.js v4, and interactive UI into a self-contained offline HTML file.", table_cell_style)],
    ]
    t_pipe = Table(pipeline_steps, colWidths=[75, 140, 289])
    t_pipe.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg]),
    ]))
    story.append(t_pipe)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 2: INPUT DATA FILES & COLUMN MAPPINGS
    # =========================================================================
    story.append(Paragraph("2. Input Data Files & Column Mapping Reference", h1_style))
    story.append(Paragraph(
        "The dashboard generator integrates multiple heterogeneous datasets. Below are the exact Excel column headers, "
        "Excel column numbers, and operational roles used in the current version:", body_style
    ))
    
    redcap_cols = [
        [Paragraph("<b>Category</b>", table_header_style), Paragraph("<b>Column No. & Exact Header Name</b>", table_header_style), Paragraph("<b>Variable Description & Usage</b>", table_header_style)],
        [Paragraph("Record Key", table_cell_bold), Paragraph("`Record ID`", code_style), Paragraph("Primary key unique to each REDCap registration record.", table_cell_style)],
        [Paragraph("Block Hierarchy", table_cell_bold), Paragraph("<b>Col AF:</b> `Block / Taluk Name `", code_style), Paragraph("Administrative health block used for spatial filtering and match criteria Step 1.", table_cell_style)],
        [Paragraph("Delivery Place", table_cell_bold), Paragraph("<b>Col BY:</b> `Q43. If health facility, Delivery Place name (Public)23`", code_style), Paragraph("Public health facility name used for place filtering and match criteria Step 2.", table_cell_style)],
        [Paragraph("Telecallers", table_cell_bold), Paragraph("`Q10. TeleCaller/Data Collector ID`<br/><b>Col 639/700/761:</b> `Q10. TeleCaller ID410 / ID471 / ID532`", code_style), Paragraph("Assigned telecaller coordinators across registration and follow-up calls 1–3 (23 active coordinators).", table_cell_style)],
        [Paragraph("Delivery Dates", table_cell_bold), Paragraph("`Q33. Delivery Date`<br/><b>Col XO/ZX/ACG:</b> `Q9. Call Date_Time    409/470/531`", code_style), Paragraph("Delivery date and follow-up completion timestamps used for activity reporting.", table_cell_style)],
        [Paragraph("Follow-up Status", table_cell_bold), Paragraph("<b>Col XU/AAD/ACM:</b><br/>`Q15. Baby Current Status  415 / 476 / 537`", code_style), Paragraph("Final follow-up outcome status (Healthy, Dead, Sick, Completed) for Baby 1, 2, and 3.", table_cell_style)],
        [Paragraph("Mortality Data", table_cell_bold), Paragraph("`Q51 / Q57 / Q63`: Date of death<br/>`Q16. If baby died, Date of death...`<br/>`Q18` series: Place of death", code_style), Paragraph("Neonatal death dates, place of death (Hospital/Home/Way), and age at death (<= 28 days).", table_cell_style)],
    ]
    t_rc = Table(redcap_cols, colWidths=[85, 205, 214])
    t_rc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg]),
    ]))
    story.append(t_rc)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 3: 7-STEP CHRONOLOGICAL SNCU MATCHING HIERARCHY
    # =========================================================================
    story.append(Paragraph("3. 7-Step Chronological SNCU Neonatal Death Matching Engine", h1_style))
    story.append(Paragraph(
        "To cross-verify hospital-based neonatal mortality (SNCU DH Khargone) with community REDCap records, "
        "the pipeline applies a strict chronological 7-step criteria hierarchy. Expired cases with "
        "<code>0 ≤ Age at Death ≤ 28 days</code> (calculated from Date of Birth to Discharge Date) are evaluated:", body_style
    ))

    sncu_steps_table = [
        [Paragraph("<b>Step No.</b>", table_header_style), Paragraph("<b>Matching Field / Variable</b>", table_header_style), Paragraph("<b>REDCap Source Field</b>", table_header_style), Paragraph("<b>SNCU Admission Field</b>", table_header_style)],
        [Paragraph("Step 1", table_cell_bold), Paragraph("Block / Taluk Name", table_cell_style), Paragraph("<b>Col AF:</b> `Block / Taluk Name `", code_style), Paragraph("`Block Name`", code_style)],
        [Paragraph("Step 2", table_cell_bold), Paragraph("Place of Delivery", table_cell_style), Paragraph("<b>Col BY:</b> `Q43. Delivery Place name...`", code_style), Paragraph("`Place of Delivery`", code_style)],
        [Paragraph("Step 3", table_cell_bold), Paragraph("Delivery Date vs Date of Birth", table_cell_style), Paragraph("`Q33. Delivery Date`", code_style), Paragraph("`Date of Birth`", code_style)],
        [Paragraph("Step 4", table_cell_bold), Paragraph("Name of Mother & Father", table_cell_style), Paragraph("`Q2. Mother Name` / `Q3. Father Name`", code_style), Paragraph("`Mother Name` / `Father/Husband Name`", code_style)],
        [Paragraph("Step 5", table_cell_bold), Paragraph("Primary Contact Number", table_cell_style), Paragraph("`Q16. Family Mobile Number`", code_style), Paragraph("`Contact No.`", code_style)],
        [Paragraph("Step 6", table_cell_bold), Paragraph("Date of Death vs Discharge Date", table_cell_style), Paragraph("`Q51/Q57/Q63/Q16` (Date of Death)", code_style), Paragraph("`Discharge Date` (Expired date)", code_style)],
        [Paragraph("Step 7", table_cell_bold), Paragraph("Secondary Mobile Verification", table_cell_style), Paragraph("`Q17. Family 2nd Mobile Number`", code_style), Paragraph("`Contact No.`", code_style)],
    ]
    t_sncu = Table(sncu_steps_table, colWidths=[50, 140, 160, 154])
    t_sncu.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_secondary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg]),
    ]))
    story.append(t_sncu)
    story.append(Spacer(1, 8))

    sncu_kpi_rules = [
        "<b>• Accurately Recorded (≥ 5 Criteria Matched):</b> Cases matching on 5 or more criteria out of the 7 chronological steps.",
        "<b>• Recorded with Spelling Mismatch (< 5 Criteria Matched):</b> Cases established via DOB + Delivery Place with minor spelling differences in names/phone numbers.",
        "<b>• Not Recorded in REDCap:</b> Cases where no corresponding delivery record exists in the REDCap follow-up repository.",
        "<b>• Dual Record IDs:</b> Side-by-side display of <code>SNCU Admission ID</code> and <code>REDCap Record ID</code> in expandable inspection drawers.",
    ]
    for skr in sncu_kpi_rules:
        story.append(Paragraph(skr, bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 4: DATA VALIDATION RULES (FORM 1 & FORM 2)
    # =========================================================================
    story.append(Paragraph("4. Data Validation Quality Engine (Form 1 & Form 2 Rules)", h1_style))
    story.append(Paragraph(
        "Automated data quality checks evaluate registration completeness, gestational age consistency, "
        "and follow-up outcomes across Form 1 (1.1 to 1.17) and Form 2 (2.1 to 2.7):", body_style
    ))

    f1_rules = [
        [Paragraph("<b>Code</b>", table_header_style), Paragraph("<b>Validation Rule Name</b>", table_header_style), Paragraph("<b>Evaluation Formula & Operational Definition</b>", table_header_style)],
        [Paragraph("1.1", table_cell_bold), Paragraph("Delivery Date Missing", table_cell_style), Paragraph("`Q33. Delivery Date` is NaN or blank.", table_cell_style)],
        [Paragraph("1.2", table_cell_bold), Paragraph("Block Name Missing", table_cell_style), Paragraph("`Block / Taluk Name ` (Col AF) is NaN, blank, or 'Not Found'.", table_cell_style)],
        [Paragraph("1.3", table_cell_bold), Paragraph("Gestational Age Missing", table_cell_style), Paragraph("`Q38 (EDD)`, `Q32 (LMP)`, and `Q35/Q36 (Clinical GA)` are all blank.", table_cell_style)],
        [Paragraph("1.4", table_cell_bold), Paragraph("Gestational Age Mismatch", table_cell_style), Paragraph("Variance among derived GAs > 1.5 weeks (Priority: EDD > LMP > Clinical).", table_cell_style)],
        [Paragraph("1.5", table_cell_bold), Paragraph("Delivery Type Missing", table_cell_style), Paragraph("`Q39. Delivery type` is NaN or blank.", table_cell_style)],
        [Paragraph("1.6", table_cell_bold), Paragraph("Delivery Location Missing", table_cell_style), Paragraph("`Q41. Delivery Location` is NaN or blank.", table_cell_style)],
        [Paragraph("1.7", table_cell_bold), Paragraph("Number of Babies Delivered Missing", table_cell_style), Paragraph("`Q45. Number of baby delivered` is NaN or blank.", table_cell_style)],
        [Paragraph("1.8", table_cell_bold), Paragraph("Baby Not Registered after Notification", table_cell_style), Paragraph("`Q45` ≥ 1 baby, but `Q47 (Baby-1 Status)` is blank.", table_cell_style)],
        [Paragraph("1.9", table_cell_bold), Paragraph("Status of Baby at Birth Mismatched", table_cell_style), Paragraph("Stillbirth reported in `Q47`, but baby has completed follow-up status (Healthy/Dead/Sick) or death date (excludes Pending cases).", table_cell_style)],
        [Paragraph("1.10", table_cell_bold), Paragraph("Stillbirth GA < 28wks or Weight < 1000g", table_cell_style), Paragraph("`is_stillbirth` is True AND (`gestation` < 28 weeks OR `weight` < 1000g).", table_cell_style)],
        [Paragraph("1.11", table_cell_bold), Paragraph("Baby Gender Missing", table_cell_style), Paragraph("`Q48 / Q54 / Q60 (Sex)` is blank or 'Unknown'.", table_cell_style)],
        [Paragraph("1.12", table_cell_bold), Paragraph("Birth Weight Missing / 9999", table_cell_style), Paragraph("Birth weight is NaN, 9999, ≤ 0g, or > 8000g.", table_cell_style)],
        [Paragraph("1.13", table_cell_bold), Paragraph("Live Birth Gestational Age < 24wks", table_cell_style), Paragraph("`is_live_born` is True AND `gestation` < 24 weeks.", table_cell_style)],
        [Paragraph("1.14", table_cell_bold), Paragraph("Intergrowth Chart GA vs BW Mismatch", table_cell_style), Paragraph("Birthweight >200g outside -4SD to +4SD for GA 24–42 weeks.", table_cell_style)],
        [Paragraph("1.15", table_cell_bold), Paragraph("Mobile Number Issues", table_cell_style), Paragraph("Both phones missing OR primary phone fails 10-digit numeric check.", table_cell_style)],
        [Paragraph("1.16", table_cell_bold), Paragraph("Duplicate Entries", table_cell_style), Paragraph("Multiple rows share identical `(Mother Name, Mobile, Delivery Date)`.", table_cell_style)],
        [Paragraph("1.17", table_cell_bold), Paragraph("Future Date Issues", table_cell_style), Paragraph("`Delivery Date` > current system date.", table_cell_style)],
        [Paragraph("2.1", table_cell_bold), Paragraph("Day 29 Status Missing / Due", table_cell_style), Paragraph("Live birth ≥ 29 days old without completed status in Col XU/AAD/ACM.", table_cell_style)],
        [Paragraph("2.2", table_cell_bold), Paragraph("Date of Death Missing", table_cell_style), Paragraph("Baby reported Dead in calls, but `Date of Death` is NaN.", table_cell_style)],
        [Paragraph("2.3", table_cell_bold), Paragraph("Place of Death Missing", table_cell_style), Paragraph("Neonatal death confirmed, but `Place of Death` is Not Recorded.", table_cell_style)],
        [Paragraph("2.4", table_cell_bold), Paragraph("Age at Death Invalid", table_cell_style), Paragraph("`age_at_death` < 0 days OR `age_at_death` > 28 days.", table_cell_style)],
        [Paragraph("2.5", table_cell_bold), Paragraph("Factors Associated with ND Missing", table_cell_style), Paragraph("Neonatal death confirmed, but cause-of-death checkboxes unchecked.", table_cell_style)],
        [Paragraph("2.6", table_cell_bold), Paragraph("Call Date Before Delivery Date", table_cell_style), Paragraph("Any follow-up `call_date` < `delivery_date`.", table_cell_style)],
        [Paragraph("2.7", table_cell_bold), Paragraph("Death Timeline Issues", table_cell_style), Paragraph("Call 3 date > death date OR Call 3 status is Healthy/Sick for deceased baby.", table_cell_style)],
    ]
    t_f1 = Table(f1_rules, colWidths=[35, 175, 294])
    t_f1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg]),
    ]))
    story.append(t_f1)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 5: DASHBOARD UI CONTROLS & LINE LIST FILTERS
    # =========================================================================
    story.append(Paragraph("5. Interactive UI Controls & Line List Filtering", h1_style))
    story.append(Paragraph(
        "The web dashboard provides multi-layered filtering controls to support supervisory and field-level follow-up:", body_style
    ))

    ui_features = [
        "<b>1. Global Filter Bar:</b> Filter simultaneously by <b>Month</b>, <b>Block</b>, <b>Delivery Coordinator (Col 21)</b>, and <b>Follow-up Done By (Col 639/700/761)</b> across all tabs.",
        "<b>2. 1-Click Interactive KPI Cards:</b> Instant single-click filtering across Home Deliveries (All, Accurately Recorded, Spelling Mismatch, Unmatched), Out-of-District Deliveries, and SNCU Deaths.",
        "<b>3. Place of Delivery Sub-Filters:</b> Dedicated delivery location dropdowns in <b>Neonatal Deaths Registry (Col BY)</b>, <b>Khargone SNCU Deaths</b>, and <b>Khandwa SNCU Deaths</b> line-lists.",
        "<b>4. Inspection Drawers:</b> Clickable row drawers showing field-by-field verification matrices, health worker contact cards, and chronological comparison summaries.",
        "<b>5. Excel CSV Export:</b> One-click filtered data export with automatic file naming for ground-level distribution.",
    ]
    for uf in ui_features:
        story.append(Paragraph(uf, bullet_style))
    story.append(Spacer(1, 15))

    # Sign-off block
    sign_off = [
        [Paragraph("<b>Prepared By:</b> Technical Data Analyst Team", table_cell_style), Paragraph("<b>Approved By:</b> State Health Program Director", table_cell_style)],
        [Paragraph("<b>Signature:</b> ___________________________", table_cell_style), Paragraph("<b>Signature:</b> ___________________________", table_cell_style)],
        [Paragraph("<b>Date:</b> September 2026", table_cell_style), Paragraph("<b>Date:</b> September 2026", table_cell_style)],
    ]
    t_sign = Table(sign_off, colWidths=[250, 254])
    t_sign.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(KeepTogether(t_sign))

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] SOP PDF Document successfully generated: '{filename}'")

if __name__ == '__main__':
    build_pdf()
