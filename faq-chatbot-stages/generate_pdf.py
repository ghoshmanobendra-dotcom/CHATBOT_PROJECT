import json
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        footer_text = f"GCECT B.Tech IT — PC(IT)513 Object Oriented Programming Question Bank | Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 36, 25, footer_text)
        self.restoreState()


def build_pdf(json_path: str, output_pdf_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    questions = data.get("questions", [])

    # Group by level: easy, medium, hard
    levels_order = ["easy", "medium", "hard"]
    level_titles = {
        "easy": "Section 1: Easy Level Questions (2-Mark Short & Objective Questions)",
        "medium": "Section 2: Medium Level Questions (5-Mark Conceptual, Differences & Code Tracing)",
        "hard": "Section 3: Hard Level Questions (10-Mark Detailed Theory, Debugging & Complete Programs)"
    }
    grouped = {lvl: [] for lvl in levels_order}
    for q in questions:
        lvl = q.get("level", "easy").lower()
        if lvl in grouped:
            grouped[lvl].append(q)
        else:
            grouped["easy"].append(q)

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e293b'),
        alignment=1, # Center
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=15
    )

    sec_header_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    q_title_style = ParagraphStyle(
        'QTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e3a8a')
    )

    q_text_style = ParagraphStyle(
        'QText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=2,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'CodeStyleCustom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=3,
        spaceAfter=4
    )

    ans_style = ParagraphStyle(
        'AnsStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#166534'),
        spaceAfter=2
    )

    tip_style = ParagraphStyle(
        'TipStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#854d0e'),
        spaceAfter=2
    )

    story = []

    # Title & Header
    story.append(Paragraph("Government College of Engineering &amp; Ceramic Technology", title_style))
    story.append(Paragraph("Department of Information Technology · B.Tech IT Semester 5", subtitle_style))
    story.append(Paragraph("<b>Course PC(IT)513: Object Oriented Programming (Java)</b><br/>Comprehensive Question Bank &amp; Complete Model Answer Key", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3b82f6"), spaceAfter=15))

    # Meta Summary Box
    summary_html = (
        f"<b>Total Questions:</b> {len(questions)} &nbsp;|&nbsp; "
        f"<b>Easy (2M):</b> {len(grouped['easy'])} &nbsp;|&nbsp; "
        f"<b>Medium (5M):</b> {len(grouped['medium'])} &nbsp;|&nbsp; "
        f"<b>Hard (10M):</b> {len(grouped['hard'])}<br/>"
        "<b>Modules Covered:</b> Module 1 to Module 6 (Complete Syllabus + Classic Exam Traps &amp; Output Tracing)"
    )
    summary_table = Table([[Paragraph(summary_html, body_style)]], colWidths=[540])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bfdbfe')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    def escape_xml(s):
        if not s:
            return ""
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")

    for lvl in levels_order:
        q_list = grouped[lvl]
        if not q_list:
            continue
        
        story.append(Paragraph(level_titles[lvl], sec_header_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#94a3b8"), spaceAfter=10))

        for idx, q in enumerate(q_list, 1):
            qid = q.get("id", "")
            mod = q.get("module", "")
            topic = q.get("topic", "")
            qtype = q.get("type", "").upper()
            marks = q.get("marks", "")
            question_text = q.get("question", "")
            code = q.get("code")
            options = q.get("options")
            answer = q.get("answer", "")
            explanation = q.get("explanation", "")
            exam_tip = q.get("exam_tip", "")

            item_elements = []

            # Question Header Line
            q_header = f"<b>Q{idx}. [{qid}] Module {mod}: {escape_xml(topic)}</b> &nbsp;·&nbsp; <i>Type: {qtype}</i> &nbsp;·&nbsp; <b>[{marks} Marks]</b>"
            item_elements.append(Paragraph(q_header, q_title_style))

            # Question Statement
            item_elements.append(Paragraph(escape_xml(question_text), q_text_style))

            # Code if any
            if code:
                code_table = Table([[Paragraph(f"<font face='Courier'>{escape_xml(code)}</font>", code_style)]], colWidths=[520])
                code_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 8),
                    ('RIGHTPADDING', (0,0), (-1,-1), 8),
                ]))
                item_elements.append(code_table)
                item_elements.append(Spacer(1, 3))

            # Options if MCQ
            if options and isinstance(options, dict):
                opt_lines = []
                for k in ["A", "B", "C", "D"]:
                    if k in options:
                        opt_lines.append(f"<b>({k})</b> {escape_xml(options[k])}")
                item_elements.append(Paragraph(" &nbsp;&nbsp;&nbsp; ".join(opt_lines), body_style))

            # Model Answer & Explanation
            item_elements.append(Paragraph(f"<b>Model Answer:</b><br/>{escape_xml(answer)}", ans_style))
            if explanation:
                item_elements.append(Paragraph(f"<b>Explanation:</b> {escape_xml(explanation)}", body_style))
            if exam_tip:
                item_elements.append(Paragraph(f"<b>💡 Exam Scoring Tip:</b> {escape_xml(exam_tip)}", tip_style))
            item_elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceBefore=4, spaceAfter=8))

            for el in item_elements:
                story.append(el)

        story.append(Spacer(1, 15))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {output_pdf_path} ({os.path.getsize(output_pdf_path)} bytes)")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "oops_bank.json")
    static_dir = os.path.join(base_dir, "static")
    os.makedirs(static_dir, exist_ok=True)
    pdf_path = os.path.join(static_dir, "GCECT_OOP_Question_Bank.pdf")
    build_pdf(json_path, pdf_path)
