from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    identified_domain: str
    identified_document_type: str
    confidence: str
    redirect_action: str
    reasoning: str
    extracted_fields: Optional[dict] = None