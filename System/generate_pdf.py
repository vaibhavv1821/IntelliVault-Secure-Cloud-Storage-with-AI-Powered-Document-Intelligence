"""
IntelliVault ~ Master Technical Documentation PDF Generator
Converts System/IntelliVault_Documentation.md into System/IntelliVault_Documentation.pdf
using ReportLab with clean styling, headers, footers, tables, and page numbering.
"""

import os
import re
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic total page count in header/footer."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "IntelliVault ~ Master Technical Documentation")
            self.drawRightString(612 - 54, 750, "Confidential - System Architecture")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 36, footer_text)
        self.drawString(54, 36, "IntelliVault Engineering | Zero-Knowledge Document AI")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 612 - 54, 48)

        self.restoreState()


def escape_xml(text):
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def inline_markdown_to_reportlab(text):
    """Converts markdown inline bold, italics, code to reportlab XML tags."""
    # Escape raw XML chars first
    text = escape_xml(text)
    # Bold: **bold** or __bold__
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic: *italic* or _italic_
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    # Inline code: `code`
    text = re.sub(r'`(.+?)`', r'<font face="Courier" color="#0f766e"><b>\1</b></font>', text)
    return text


def build_pdf(md_path, pdf_path):
    print(f"Reading markdown source from {md_path}...")
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=64,
        bottomMargin=64
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    code_block_style = ParagraphStyle(
        'DocCode',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=3,
        spaceAfter=5
    )

    table_cell_style = ParagraphStyle(
        'DocTableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )

    table_cell_header = ParagraphStyle(
        'DocTableHead',
        parent=table_cell_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []

    i = 0
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.rstrip('\r\n')

        # Code blocks ```
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                in_code_block = False
                code_text = "\n".join(code_lines)
                escaped_code = escape_xml(code_text)
                p = Preformatted(escaped_code, code_block_style)
                # Wrap code block in a nice light table
                code_table = Table([[p]], colWidths=[504])
                code_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(code_table)
                story.append(Spacer(1, 4))
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Markdown tables
        if line.strip().startswith('|') and line.strip().endswith('|'):
            if not in_table:
                in_table = True
                table_rows = []

            # Check if it's separator row | :--- | :--- |
            if re.match(r'^\|[\s:-]+\|$', line.replace(' ', '')):
                i += 1
                continue

            raw_cells = [c.strip() for c in line.strip().strip('|').split('|')]
            table_rows.append(raw_cells)
            i += 1
            continue
        elif in_table:
            # End of table
            in_table = False
            if table_rows:
                # Format cells
                formatted_data = []
                for r_idx, row in enumerate(table_rows):
                    row_cells = []
                    for cell in row:
                        cell_p = Paragraph(
                            inline_markdown_to_reportlab(cell),
                            table_cell_header if r_idx == 0 else table_cell_style
                        )
                        row_cells.append(cell_p)
                    formatted_data.append(row_cells)

                num_cols = max(len(r) for r in table_rows)
                col_width = 504 / num_cols if num_cols > 0 else 504
                t = Table(formatted_data, colWidths=[col_width] * num_cols)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ]))
                story.append(t)
                story.append(Spacer(1, 6))

        # Horizontal rule
        if line.strip() in ['---', '***', '___']:
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6, spaceBefore=4))
            i += 1
            continue

        # Document Header / Subtitle
        if line.startswith('# '):
            title_text = inline_markdown_to_reportlab(line[2:].strip())
            story.append(Paragraph(title_text, title_style))
            i += 1
            continue

        if line.startswith('## '):
            h1_text = inline_markdown_to_reportlab(line[3:].strip())
            story.append(Paragraph(h1_text, h1_style))
            i += 1
            continue

        if line.startswith('### '):
            h2_text = inline_markdown_to_reportlab(line[4:].strip())
            story.append(Paragraph(h2_text, h2_style))
            i += 1
            continue

        # Bullets
        if line.strip().startswith(('* ', '- ')):
            bullet_text = inline_markdown_to_reportlab(line.strip()[2:])
            p = Paragraph(f"• {bullet_text}", bullet_style)
            story.append(p)
            i += 1
            continue

        # Numbered lists
        m_num = re.match(r'^\s*(\d+)\.\s+(.*)$', line)
        if m_num:
            num = m_num.group(1)
            content = inline_markdown_to_reportlab(m_num.group(2))
            p = Paragraph(f"<b>{num}.</b> {content}", bullet_style)
            story.append(p)
            i += 1
            continue

        # Empty lines
        if not line.strip():
            story.append(Spacer(1, 3))
            i += 1
            continue

        # Regular paragraph
        para_text = inline_markdown_to_reportlab(line.strip())
        story.append(Paragraph(para_text, body_style))
        i += 1

    print("Compiling PDF with NumberedCanvas...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {pdf_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    md_file = os.path.join(base_dir, "IntelliVault_Documentation.md")
    pdf_file = os.path.join(base_dir, "IntelliVault_Documentation.pdf")
    build_pdf(md_file, pdf_file)
