from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

def generate_pdf(text: str) -> bytes:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    story = []
    for line in text.split('\n'):
        story.append(Paragraph(line, styles['Normal']))
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    doc.build(story)
    buffer.seek(0)
    return buffer.read()