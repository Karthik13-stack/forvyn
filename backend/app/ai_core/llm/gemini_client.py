from typing import List
try:
    import google.generativeai as genai
except Exception:
    genai = None
from app.ai_core.prompts import MASTER_SYSTEM_PROMPT
from app.core.config import settings

class GeminiClient:

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = None
        self.is_available = bool(self.api_key) and genai is not None

        if not self.is_available:
            print('Gemini unavailable: running in local fallback mode.')
            return

        print('\n=== Initializing GeminiClient ===')
        print('GEMINI_API_KEY found:', bool(self.api_key))

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=MASTER_SYSTEM_PROMPT)
        print('Gemini model initialized successfully')

    def generate_content(self, prompt: str):
        if not self.model:
            return {'text': ''}
        return self.model.generate_content(prompt)

    @staticmethod
    def _extract_text(response) -> str:
        text = getattr(response, 'text', None)
        if callable(text):
            text = text()
        if isinstance(text, str) and text.strip():
            return text.strip()
        if isinstance(response, dict):
            val = response.get('text')
            if isinstance(val, str):
                return val.strip()
        return ''

    def rewrite_clause(self, clause_text: str, intent: str, context: List[str]=[]) -> str:
        import time
        if not self.model:
            return clause_text.strip()

        print('\n===== GEMINI CALL START =====')
        start = time.time()
        context_str = '\n'.join([f'- {c}' for c in context]) if context else 'None'
        prompt = f'\nRewrite the following legal clause based on the user intent.\n\nRULES:\n- Output ONLY the rewritten clause\n- Do not add explanations\n- Preserve all facts and numbers\n\nContext:\n{context_str}\n\nClause:\n{clause_text}\n\nIntent:\n{intent}\n\nRewritten clause:\n'
        response = self.model.generate_content(prompt)
        end = time.time()
        print('===== GEMINI CALL END =====')
        print('Gemini latency:', round(end - start, 2), 'seconds')
        text = self._extract_text(response) or clause_text
        print('Gemini output preview:', text[:300])
        return text

    def advanced_clause_rewrite(self, text: str, action: str, target_language: str = "English") -> str:
        import time
        if not self.model:
            return text.strip()

        print('\n===== GEMINI ADVANCED REWRITE CALL START =====')
        start = time.time()
        
        if action == "emphasize":
            prompt_instruction = "Strengthen the wording of this legal clause to add more firm, assertive legal weight."
        elif action == "translate":
            prompt_instruction = f"Translate the legal clause to {target_language} while preserving all intrinsic legal binding accuracy."
        else:
            prompt_instruction = "Rewrite the legal clause specifically to simplify it and improve its clarity."
            
        prompt = f'''
Perform the following action on the provided legal clause: {action.upper()}

INSTRUCTIONS:
{prompt_instruction}

RULES:
- Output ONLY the result text. Do not include any explanations, greetings, or formatting wrappers like markdown blocks unless it is part of the original clause formatting.
- Preserve all facts, numbers, sections, and structural intent.

Clause:
{text}

Result:
'''
        
        response = self.model.generate_content(prompt)
        end = time.time()
        print('===== GEMINI ADVANCED REWRITE CALL END =====')
        print('Latency:', round(end - start, 2), 'seconds')
        res_text = self._extract_text(response) or text
        print('Output preview:', res_text[:300])
        return res_text