from fastapi import APIRouter, HTTPException, Response, Body
from app.services.export_service import ExportService
from pydantic import BaseModel
router = APIRouter()
exporter = ExportService()

class ExportRequest(BaseModel):
    content: str
    filename: str = 'document'

@router.post('/export/pdf')
def export_pdf(req: ExportRequest):
    try:
        pdf_bytes = exporter.export_pdf(req.content)
        return Response(content=pdf_bytes, media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename={req.filename}.pdf'})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/export/docx')
def export_docx(req: ExportRequest):
    try:
        docx_bytes = exporter.export_docx(req.content)
        return Response(content=docx_bytes, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', headers={'Content-Disposition': f'attachment; filename={req.filename}.docx'})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))