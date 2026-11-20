from docx import Document
from io import BytesIO

def generate_docx(text: str) -> bytes:
    doc = Document()
    for line in text.split('\n'):
        doc.add_paragraph(line)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()