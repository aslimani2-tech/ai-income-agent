import os
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ============================================================
# V10: STRUCTURED CLIENT REPORT -> PROFESSIONAL PDF
# ============================================================

INPUT_FILE = "reports/la_jabotte_v7_audit.txt"
OUTPUT_FILE = "reports/la_jabotte_v10_audit.pdf"

PAGE_W, PAGE_H = A4
MARGIN_X = 18 * mm
MARGIN_TOP = 20 * mm
MARGIN_BOTTOM = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X


# ------------------------------------------------------------
# FONT
# ------------------------------------------------------------

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

font_pairs = [
    (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf",
     "V10Arial", "V10ArialBold"),
    (r"C:\Windows\Fonts\calibri.ttf", r"C:\Windows\Fonts\calibrib.ttf",
     "V10Calibri", "V10CalibriBold"),
]

for regular, bold, name, bold_name in font_pairs:
    if os.path.exists(regular):
        pdfmetrics.registerFont(TTFont(name, regular))
        FONT = name
        if os.path.exists(bold):
            pdfmetrics.registerFont(TTFont(bold_name, bold))
            FONT_BOLD = bold_name
        break


# ------------------------------------------------------------
# COLORS
# ------------------------------------------------------------

NAVY = colors.HexColor("#182235")
BLUE = colors.HexColor("#2563EB")
BLUE_LIGHT = colors.HexColor("#EFF6FF")
TEXT = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#64748B")
BORDER = colors.HexColor("#D8DEE8")
ROW_ALT = colors.HexColor("#F8FAFC")
WHITE = colors.white


# ------------------------------------------------------------
# STYLES
# ------------------------------------------------------------

cover_title = ParagraphStyle(
    "CoverTitle", fontName=FONT_BOLD, fontSize=25, leading=30,
    alignment=TA_CENTER, textColor=NAVY, spaceAfter=8
)
cover_subtitle = ParagraphStyle(
    "CoverSubtitle", fontName=FONT, fontSize=12, leading=17,
    alignment=TA_CENTER, textColor=MUTED, spaceAfter=5
)
section_style = ParagraphStyle(
    "Section", fontName=FONT_BOLD, fontSize=15, leading=19,
    textColor=NAVY, spaceBefore=3, spaceAfter=9, keepWithNext=True
)
body_style = ParagraphStyle(
    "Body", fontName=FONT, fontSize=9.2, leading=13.2,
    textColor=TEXT, spaceAfter=5
)
table_header = ParagraphStyle(
    "TableHeader", fontName=FONT_BOLD, fontSize=7.7, leading=9.4,
    textColor=WHITE
)
table_body = ParagraphStyle(
    "TableBody", fontName=FONT, fontSize=7.45, leading=9.7,
    textColor=TEXT
)
source_title = ParagraphStyle(
    "SourceTitle", fontName=FONT_BOLD, fontSize=9.5, leading=12,
    textColor=NAVY, spaceAfter=2
)
source_link = ParagraphStyle(
    "SourceLink", fontName=FONT, fontSize=7.8, leading=10.5,
    textColor=BLUE, spaceAfter=7
)


# ------------------------------------------------------------
# SANITIZATION
# ------------------------------------------------------------

def sanitize(text):
    if not text:
        return ""

    text = str(text).strip()

    # Repair common mojibake.
    fixes = {
        "â€“": "–", "â€”": "—", "â€˜": "‘", "â€™": "’",
        "â€œ": "“", "â€": "”", "â€¦": "…",
        "â‚¬": "€", "â€¢": "•", "â€¯": " ",
        "Â": "", "�": "", "□": "",
    }
    for old, new in fixes.items():
        text = text.replace(old, new)

    # Remove internal citation artifacts.
    text = re.sub(r"\d+†L\d+(?:-L\d+)?(?:†L\d+(?:-L\d+)?)*", "", text)
    text = re.sub(r"\[\d+\]", "", text)

    # Remove Markdown syntax.
    text = re.sub(r"^\s*#+\s*", "", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)

    # Never expose internal implementation details to a client.
    internal_phrases = [
        "AI Income Research Agent",
        "builtin GPT",
        "built-in GPT",
        "simple webhooks",
        "free or lowcost tools",
        "free or low-cost tools",
    ]
    for phrase in internal_phrases:
        text = re.sub(
            re.escape(phrase) + r".*?(?:\.|$)",
            "",
            text,
            flags=re.IGNORECASE,
        )

    # Replace remaining unsupported control/non-printing chars.
    text = "".join(
        ch for ch in text
        if ch in "\n\t" or ord(ch) >= 32
    )

    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def para(text, style=body_style):
    return Paragraph(escape(sanitize(text)), style)


# ------------------------------------------------------------
# SOURCE EXTRACTION
# ------------------------------------------------------------

def extract_sources(lines):
    sources = []
    in_sources = False

    for raw in lines:
        line = sanitize(raw)

        if re.match(r"^5\.\s*SOURCES\b", line, re.I):
            in_sources = True
            continue

        if not in_sources or not line:
            continue

        if line.startswith("*"):
            continue

        line = re.sub(r"^\d+\.\s*", "", line)

        match = re.search(r"https?://\S+", line)
        if not match:
            continue

        url = match.group(0).rstrip(".,)")
        label = line[:match.start()].strip(" :-")

        # Clean common labels.
        label = re.sub(r"\s+", " ", label)
        if not label:
            label = "Source"

        sources.append((label, url))

    # Deduplicate while preserving order.
    seen = set()
    unique = []
    for label, url in sources:
        if url not in seen:
            unique.append((label, url))
            seen.add(url)

    return unique


# ------------------------------------------------------------
# TABLE PARSER
# ------------------------------------------------------------

def is_table_line(line):
    return line.strip().startswith("|") and "|" in line


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [sanitize(x) for x in line.split("|")]


def separator_row(row):
    return bool(row) and all(
        re.fullmatch(r":?-+:?", cell.strip()) for cell in row
    )


def table_widths(n):
    if n == 3:
        return [CONTENT_W * .24, CONTENT_W * .48, CONTENT_W * .28]
    if n == 4:
        return [CONTENT_W * .18, CONTENT_W * .29, CONTENT_W * .31, CONTENT_W * .22]
    return [CONTENT_W / n] * n


def make_table(rows):
    if not rows:
        return None

    n = max(len(r) for r in rows)
    data = []

    for ri, row in enumerate(rows):
        row = row + [""] * (n - len(row))
        style = table_header if ri == 0 else table_body
        data.append([Paragraph(escape(sanitize(x)), style) for x in row])

    t = Table(
        data,
        colWidths=table_widths(n),
        repeatRows=1,
        splitByRow=1,
        hAlign="LEFT",
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), .35, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


# ------------------------------------------------------------
# SECTION PARSER
# ------------------------------------------------------------

def parse_sections(lines):
    """
    Parse the existing report into structured sections.
    This is deliberately deterministic: the PDF layout never
    depends on Markdown formatting quirks.
    """

    sections = []
    current = None
    i = 0

    while i < len(lines):
        raw = lines[i].strip()
        line = sanitize(raw)

        if not line:
            i += 1
            continue

        # Ignore report title/date because the PDF has a cover.
        if line.startswith("Digital Presence Audit") or line.startswith("Prepared:"):
            i += 1
            continue

        if line in ("---", "***", "___"):
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s+(.+)$", line)
        if m:
            title = sanitize(m.group(2))
            title = re.sub(r"\s*\(Beginner\s*level\)", "", title, flags=re.I)

            current = {"number": m.group(1), "title": title, "blocks": []}
            sections.append(current)
            i += 1
            continue

        if current is None:
            i += 1
            continue

        if re.search(r"AI Income Research Agent|builtin GPT|built-in GPT|simple webhooks|free or low[- ]?cost tools",
                     line, re.I):
            i += 1
            continue

        if is_table_line(raw):
            rows = []
            while i < len(lines) and is_table_line(lines[i].strip()):
                row = split_row(lines[i])
                if not separator_row(row):
                    rows.append(row)
                i += 1
            if rows:
                current["blocks"].append(("table", rows))
            continue

        if re.match(r"^[-*]\s+", line):
            bullet = re.sub(r"^[-*]\s+", "", line)
            current["blocks"].append(("bullet", bullet))
        else:
            current["blocks"].append(("text", line))

        i += 1

    # Remove Sources from normal sections; it is rendered separately.
    sections = [
        s for s in sections
        if not re.match(r"5\.\s*SOURCES", s["title"], re.I)
    ]
    return sections


# ------------------------------------------------------------
# PAGE FOOTER
# ------------------------------------------------------------

def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
    canvas.line(MARGIN_X, 13 * mm, PAGE_W - MARGIN_X, 13 * mm)
    canvas.setFont(FONT, 7)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(PAGE_W / 2, 8 * mm, str(doc.page))
    canvas.restoreState()


# ------------------------------------------------------------
# COVER
# ------------------------------------------------------------

def add_cover(story):
    story.append(Spacer(1, 46 * mm))
    story.append(Paragraph("DIGITAL PRESENCE AUDIT", cover_title))
    story.append(Paragraph("La Jabotte Hotel", cover_subtitle))
    story.append(Paragraph("Antibes, France", cover_subtitle))
    story.append(Spacer(1, 13 * mm))
    story.append(Paragraph("Prepared for the hotel owner", cover_subtitle))
    story.append(Paragraph("25 August 2026", cover_subtitle))
    story.append(Spacer(1, 22 * mm))

    box = Table([[
        Paragraph(
            "Digital visibility, website performance and "
            "AI opportunity assessment",
            body_style,
        )
    ]], colWidths=[125 * mm])

    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT),
        ("BOX", (0, 0), (-1, -1), .6, colors.HexColor("#BFDBFE")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(box)
    story.append(PageBreak())


# ------------------------------------------------------------
# SECTION RENDERING
# ------------------------------------------------------------

def add_section(story, section):
    """
    Render each section as a coherent unit.
    Heading is kept with the first block, but large tables are
    allowed to split naturally across pages.
    """

    title = f"{section['number']}. {section['title']}"
    blocks = section["blocks"]

    story.append(Paragraph(title, section_style))

    first_block = True

    for block_type, content in blocks:

        if block_type == "table":
            table = make_table(content)
            if table:
                story.append(table)
                story.append(Spacer(1, 8))

        elif block_type == "bullet":
            p = Paragraph("• " + escape(sanitize(content)), body_style)
            story.append(p)

        else:
            p = para(content)
            story.append(p)

        first_block = False


# ------------------------------------------------------------
# SOURCES PAGE
# ------------------------------------------------------------

def add_sources(story, sources):
    story.append(PageBreak())
    story.append(Paragraph("SOURCES", section_style))
    story.append(Paragraph(
        "Public sources used during the research.",
        body_style,
    ))

    for number, (label, url) in enumerate(sources, 1):
        story.append(Paragraph(f"{number}. {escape(label)}", source_title))

        # Short visible label, full URL behind the link.
        display = "Open source"
        safe_url = escape(url)

        story.append(Paragraph(
            f'<link href="{safe_url}" color="#2563EB">{display}</link>',
            source_link,
        ))


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def create_pdf():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Input report not found: {INPUT_FILE}")

    os.makedirs("reports", exist_ok=True)

    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    sections = parse_sections(lines)
    sources = extract_sources(lines)

    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title="Digital Presence Audit - La Jabotte Hotel",
        author="",
    )

    story = []
    add_cover(story)

    for section in sections:
        add_section(story, section)

    if sources:
        add_sources(story, sources)

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    print(f"PDF CREATED: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_pdf()
