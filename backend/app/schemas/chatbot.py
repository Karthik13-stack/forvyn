from pydantic import BaseModel
from typing import Optional, Literal


class ChatbotRequest(BaseModel):
    message: str
    context: Optional[str] = None


class ChatbotResponse(BaseModel):
    reply: str
    intent: Literal["navigation", "simple_legal", "complex_legal"]
    action: Optional[str] = None
