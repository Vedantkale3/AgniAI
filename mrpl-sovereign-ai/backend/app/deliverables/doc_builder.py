"""
REAL DELIVERABLE GENERATOR
=============================
Converts agent output into actual office files, not just chat text:
- Word (.docx) approval notes / correspondence
- PowerPoint (.pptx) board-style presentations
- Excel (.xlsx) calculation sheets with formulas preserved
"""
from docx import Document
from docx.shared import Pt, RGBColor
from pptx import Presentation
from pptx.util import Pt as PPt
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from pathlib import Path
from datetime import datetime
from app.config import settings
import uuid


def _out_path(prefix: str, ext: str) -> Path:
    fname = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.{ext}"
    return Path(settings.deliverable_dir) / fname


def build_approval_note_docx(title: str, ref_no: str, background: str,
                              findings: list[str], recommendation: str,
                              prepared_by: str = "AI Workbench (Draft - Pending Review)") -> str:
    doc = Document()

    header = doc.add_paragraph()
    header.add_run("MANGALORE REFINERY AND PETROCHEMICALS LIMITED").bold = True
    header.runs[0].font.size = Pt(14)
    doc.add_paragraph("Internal Approval Note").italic = True

    doc.add_paragraph(f"Ref No: {ref_no}    Date: {datetime.now().strftime('%d-%b-%Y')}")
    doc.add_heading(title, level=1)

    doc.add_heading("Background", level=2)
    doc.add_paragraph(background)

    doc.add_heading("Key Findings", level=2)
    for f in findings:
        doc.add_paragraph(f, style="List Bullet")

    doc.add_heading("Recommendation", level=2)
    doc.add_paragraph(recommendation)

    doc.add_paragraph("")
    sign = doc.add_paragraph(f"Prepared by: {prepared_by}")
    sign.runs[0].font.color.rgb = RGBColor(0x80, 0x80, 0x80)
    doc.add_paragraph("Reviewed by: _______________     Approved by: _______________")

    out = _out_path("approval_note", "docx")
    doc.save(str(out))
    return str(out)


def build_ppt_deck(title: str, subtitle: str, slides: list[dict]) -> str:
    """slides: [{"heading": str, "bullets": [str, ...]}, ...]"""
    prs = Presentation()
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    slide.shapes.title.text = title
    slide.placeholders[1].text = subtitle

    bullet_layout = prs.slide_layouts[1]
    for s in slides:
        slide = prs.slides.add_slide(bullet_layout)
        slide.shapes.title.text = s["heading"]
        body = slide.placeholders[1].text_frame
        body.clear()
        for i, bullet in enumerate(s["bullets"]):
            p = body.paragraphs[0] if i == 0 else body.add_paragraph()
            p.text = bullet
            p.font.size = PPt(18)

    out = _out_path("presentation", "pptx")
    prs.save(str(out))
    return str(out)


def build_calc_sheet_xlsx(title: str, headers: list[str], rows: list[list],
                           formula_notes: str | None = None) -> str:
    wb = Workbook()
    ws = wb.active
    ws.title = "Calculation"

    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=14)

    header_row = 3
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")

    for r_idx, row in enumerate(rows, start=header_row + 1):
        for c_idx, val in enumerate(row, start=1):
            ws.cell(row=r_idx, column=c_idx, value=val)

    if formula_notes:
        note_row = header_row + len(rows) + 2
        ws.cell(row=note_row, column=1, value=f"Notes: {formula_notes}")

    out = _out_path("calc_sheet", "xlsx")
    wb.save(str(out))
    return str(out)
