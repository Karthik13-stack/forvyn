from app.ai_core.llm.gemini_client import GeminiClient
from app.ai_core.prompts import MASTER_SYSTEM_PROMPT
import json

class ChatService:

    @staticmethod
    def handle_message(user_message: str):
        try:
            response = GeminiClient.generate(system_prompt=MASTER_SYSTEM_PROMPT, user_prompt=user_message)
            return json.loads(response)
        except Exception as e:
            print(f"Chat error: {e}")
            return {'identified_domain': 'UNKNOWN', 'identified_document_type': 'UNKNOWN', 'confidence': 'low', 'redirect_action': 'NONE', 'reasoning': 'Unable to confidently map request'}