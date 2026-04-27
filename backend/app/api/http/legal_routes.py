"""
Legal Features API Routes
Provides endpoints for IPC to BNS mapping, Explain Legal Provision, and Summarize Judgement.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import json
import logging

from app.ai_core.llm.gemini_client import GeminiClient
from app.services.legal.ipc_bns_converter import get_ipc_bns_converter
from app.services.legal.judgement_summarizer import get_judgement_summarizer, SummaryType

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency for Gemini Client
def get_gemini_client() -> GeminiClient:
    return GeminiClient()

# ==========================================
# REQUEST / RESPONSE MODELS
# ==========================================

class IPCConversionRequest(BaseModel):
    ipc_section: str = Field(..., description="IPC section number to convert")

class ExplainProvisionRequest(BaseModel):
    provision_text: str = Field(..., description="The legal provision or clause text to explain")

class JudgementSummaryRequest(BaseModel):
    judgement_text: str = Field(..., description="The full text of the court judgement")
    summary_type: SummaryType = Field(default=SummaryType.STANDARD, description="Type of summary to generate")

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/ipc-to-bns")
async def convert_ipc_to_bns(request: IPCConversionRequest):
    """
    Convert an IPC section to its BNS equivalent using the static map.
    """
    try:
        converter = get_ipc_bns_converter()
        result = converter.convert_ipc_to_bns(request.ipc_section)
        
        return {
            "ipc_section": result.ipc_section,
            "bns_section": result.bns_section,
            "status": result.status.value,
            "ipc_title": result.ipc_title,
            "bns_title": result.bns_title,
            "notes": result.notes,
            "changes_summary": result.changes_summary
        }
    except Exception as e:
        logger.error(f"Error converting IPC to BNS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/explain-provision")
async def explain_provision(
    request: ExplainProvisionRequest,
    gemini: GeminiClient = Depends(get_gemini_client)
):
    """
    Provide a clear, plain-English explanation of a legal provision using Gemini.
    """
    try:
        if not request.provision_text or len(request.provision_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Provision text is too short.")

        prompt = f"""You are an expert Indian Legal Assistant. 
Please explain the following legal provision or clause in simple, plain English so that a common person can understand it easily.

<REQUIREMENTS>
1. Break down complex legal jargon into everyday language.
2. Provide a brief summary of what the provision means.
3. List 2-3 practical examples or scenarios where this provision applies.
4. Keep the explanation concise and structured.
</REQUIREMENTS>

<PROVISION_TEXT>
{request.provision_text}
</PROVISION_TEXT>

<OUTPUT_FORMAT>
Your response must be entirely in JSON format matching the structure below:
{{
    "summary": "Clear, plain English summary of the provision",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "examples": ["Example scenario 1", "Example scenario 2"]
}}
</OUTPUT_FORMAT>
"""
        response = gemini.model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        
        try:
            parsed_json = json.loads(text)
            return parsed_json
        except json.JSONDecodeError:
             return {"error": "Failed to parse JSON", "raw_response": text}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining provision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize-judgment")
async def summarize_judgment(
    request: JudgementSummaryRequest,
    gemini: GeminiClient = Depends(get_gemini_client)
):
    """
    Generate a structured summary of a court judgement using Gemini.
    """
    try:
        if not request.judgement_text or len(request.judgement_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Judgement text is too short to summarize.")

        summarizer = get_judgement_summarizer(llm_service=gemini)
        
        summary = await summarizer.summarize(
            judgement_text=request.judgement_text,
            summary_type=request.summary_type
        )
        
        return summarizer.format_summary_for_display(summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing judgement: {e}")
        raise HTTPException(status_code=500, detail=str(e))
