from fastapi import APIRouter
from app.schemas.chatbot import ChatbotRequest, ChatbotResponse
from app.services.chatbot_service import ChatbotService

router = APIRouter()


@router.post('/chatbot/query', response_model=ChatbotResponse)
def chatbot_query(payload: ChatbotRequest):
    result = ChatbotService.process_query(payload.message, payload.context)
    return ChatbotResponse(**result)
