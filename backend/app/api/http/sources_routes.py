from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from typing import List, Optional
from app.services import source_service
router = APIRouter(prefix='/sources', tags=['sources'])

@router.post('/upload', status_code=201)
async def upload_source(
    file: UploadFile = File(...),
    category: str = Form(''),
    notes: str = Form(''),
    source_type: str = Form(''),
):
    try:
        record = source_service.save_source(
            file.filename,
            file.file,
            category=category,
            notes=notes,
            source_type=source_type,
        )
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/')
async def list_sources():
    return source_service.list_sources()


@router.get('/search')
async def search_sources(q: str = ''):
    return source_service.search_sources(q)


@router.get('/{name}')
async def get_source(name: str):
    record = source_service.get_source(name)
    if not record:
        raise HTTPException(status_code=404, detail='not found')
    return record


@router.get('/{name}/preview')
async def preview_source(name: str):
    path = source_service.get_source_path(name)
    if not path:
        raise HTTPException(status_code=404, detail='not found')
    try:
        with open(path, 'rb') as handle:
            raw = handle.read(8000)
        try:
            text = raw.decode('utf-8')
        except Exception:
            text = raw.decode('latin-1', errors='ignore')
        return {'name': name, 'preview': text[:8000]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch('/{name}')
async def update_source(name: str, payload: dict):
    record = source_service.update_source_metadata(
        name,
        category=payload.get('category'),
        notes=payload.get('notes'),
        source_type=payload.get('source_type'),
    )
    if not record:
        raise HTTPException(status_code=404, detail='not found')
    return record

@router.get('/download/{name}')
async def download_source(name: str):
    path = source_service.get_source_path(name)
    if not path:
        raise HTTPException(status_code=404, detail='not found')
    return FileResponse(path, filename=name, media_type='application/octet-stream')

@router.delete('/{name}', status_code=204)
async def delete_source(name: str):
    ok = source_service.delete_source(name)
    if not ok:
        raise HTTPException(status_code=404, detail='not found')
    return {}