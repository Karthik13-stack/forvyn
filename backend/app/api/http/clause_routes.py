from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from typing import Optional
from app.ai_core.workflows.clause_rewriter import ClauseRewriter
from app.core.dependencies import get_rewriter
router = APIRouter()

class RewriteRequest(BaseModel):
    clause_text: str
    intent: str
    domain: Optional[str] = 'General'

class AdvancedRewriteRequest(BaseModel):
    selected_text: str
    action_type: str
    target_language: str = "English"

@router.post('/clause/rewrite')
def rewrite_clause(req: RewriteRequest, rewriter: ClauseRewriter=Depends(get_rewriter)):
    try:
        new_text = rewriter.process(req.clause_text, req.intent, req.domain)
        return {'rewritten_text': new_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/rewrite-clause')
def advanced_rewrite_clause(req: AdvancedRewriteRequest, rewriter: ClauseRewriter=Depends(get_rewriter)):
    try:
        new_text = rewriter.process_rewrite(req.selected_text, req.action_type, req.target_language)
        return {'rewritten_text': new_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))