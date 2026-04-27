from fastapi import APIRouter
from app.services.document.versioning_service import VersioningService
from app.utils.text_diff import diff
router = APIRouter()
versioning = VersioningService()

@router.get('/documents/{doc_id}/versions')
def get_versions(doc_id: str):
    return versioning.get_versions(doc_id)

@router.get('/documents/{doc_id}/diff')
def get_diff(doc_id: str):
    versions = versioning.get_versions(doc_id)
    if len(versions) < 2:
        return ''
    return diff(versions[-2]['content'], versions[-1]['content'])