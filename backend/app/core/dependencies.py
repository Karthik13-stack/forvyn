from fastapi import Request
from app.services.prompt_service import PromptService, get_prompt_service
from app.ai_core.rag.vector_service import VectorService
from app.ai_core.workflows.clause_rewriter import ClauseRewriter
from app.ai_core.workflows.document_generation import DocumentGenerator
import logging
logger = logging.getLogger(__name__)
_prompt_service = get_prompt_service()
_vector_service = None
_clause_rewriter = None
_document_generator = None

def init_services():
    global _vector_service, _clause_rewriter, _document_generator
    logger.info('Initializing VectorService...')
    _vector_service = VectorService(_prompt_service)
    logger.info('Initializing AI Workflows...')
    _clause_rewriter = ClauseRewriter(_vector_service)
    _document_generator = DocumentGenerator(_vector_service)
    return _vector_service

def get_prompts() -> PromptService:
    return _prompt_service

def get_vectors() -> VectorService:
    if not _vector_service:
        raise RuntimeError('VectorService not initialized')
    return _vector_service

def get_rewriter() -> ClauseRewriter:
    if not _clause_rewriter:
        raise RuntimeError('ClauseRewriter not initialized')
    return _clause_rewriter

def get_generator() -> DocumentGenerator:
    if not _document_generator:
        raise RuntimeError('DocumentGenerator not initialized')
    return _document_generator