from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
router = APIRouter()

@router.post('/chat', response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    return ChatService.handle_message(payload.message)