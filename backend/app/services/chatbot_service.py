import json
import re
import logging
try:
    import google.generativeai as genai
except Exception:
    genai = None
from app.core.config import settings

logger = logging.getLogger(__name__)

CHATBOT_SYSTEM_PROMPT = """You are a helpful assistant for the Forvyn AI legal platform. Your role is to:
1. Help users navigate the platform
2. Answer simple legal questions concisely
3. Redirect complex legal queries to the appropriate platform feature

PLATFORM FEATURES AND ROUTES:
- Dashboard (home page): /
- Explain Legal Provision: /explain - Get plain language explanations of legal provisions
- IPC to BNS Mapping: /mapping - Map IPC sections to corresponding BNS sections
- Draft Legal Document: /draft - Generate legal drafts for professional review
- Summarize Judgment: /summarize - Get structured summaries of court judgments
- Analyze Legal Risks: /analyze-risks - Identify potential risks in legal documents
- Subscriptions & Billing: /billing - Manage Lite and Premium plans with dummy UPI checkout

INTENT CLASSIFICATION RULES:
You must classify every user query into exactly one of these intents:

1. "navigation" - When the user asks:
   - Where to find something on the platform
   - How to use a feature
   - How to upload, go to, or access something
    - Keywords: "where is", "how to use", "upload", "go to", "find", "navigate", "open", "take me", "billing", "payment", "subscription", "upi"

2. "simple_legal" - When the user asks:
   - Definition-based questions
   - Factual legal concepts
   - Short explanations of laws, articles, sections
   - Keywords: "what is", "define", "explain", "meaning of", "difference between"

3. "complex_legal" - When the user asks:
   - Document review or drafting
   - Risk analysis of documents
   - Legal advice for specific situations
   - Contract validation or review
   - Keywords: "review my", "draft a", "check my contract", "legal advice", "analyze", "risk"

RESPONSE RULES:

For "navigation" intent:
- Guide the user to the correct feature/page
- Keep response short and direct (1-2 sentences)
- Include the route in the action field

For "simple_legal" intent:
- Give a concise explanation (2-4 lines maximum)
- ALWAYS append this disclaimer: "This is general information, not legal advice."
- Do NOT include an action field

For "complex_legal" intent:
- Do NOT answer the legal question directly
- Redirect the user to the appropriate platform feature
- Include the route in the action field
- Suggest using: "Draft Legal Documents" (/draft) or "Analyze Legal Risks" (/analyze-risks)

OUTPUT FORMAT:
You MUST respond with valid JSON only. No markdown, no code fences. Example:
{"reply": "your message here", "intent": "navigation", "action": "navigate:draft-documents"}

The "action" field should be in format "navigate:<route-name>" where route-name is one of:
- dashboard
- explain-provision
- ipc-bns-mapping
- draft-documents
- summarize-judgment
- analyze-risks

Only include "action" for navigation and complex_legal intents. Omit it for simple_legal.
"""


class ChatbotService:

    _model = None

    @classmethod
    def _get_model(cls):
        if genai is None or not settings.GEMINI_API_KEY:
            return None
        if cls._model is None:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            cls._model = genai.GenerativeModel(
                'gemini-2.5-flash',
                system_instruction=CHATBOT_SYSTEM_PROMPT
            )
        return cls._model

    @classmethod
    def process_query(cls, message: str, context: str | None = None) -> dict:
        try:
            model = cls._get_model()
            if model is None:
                return cls._fallback_classify(message)

            user_prompt = message
            if context:
                user_prompt = f"[User is currently on page: {context}]\n\n{message}"

            response = model.generate_content(user_prompt)
            raw = response.text.strip()

            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)

            result = json.loads(raw)

            if result.get('intent') not in ('navigation', 'simple_legal', 'complex_legal'):
                result['intent'] = 'simple_legal'

            if 'reply' not in result:
                result['reply'] = 'I can help you navigate the platform. What would you like to do?'

            return result

        except Exception as e:
            logger.error(f"Chatbot AI error: {e}")
            return cls._fallback_classify(message)

    @classmethod
    def _fallback_classify(cls, message: str) -> dict:
        msg = message.lower().strip()

        nav_keywords = [
            'where', 'how to', 'upload', 'go to', 'navigate', 'find',
            'open', 'take me', 'page', 'section', 'feature', 'menu'
        ]

        complex_keywords = [
            'review my', 'draft a', 'check my', 'legal advice',
            'analyze my', 'contract', 'validate', 'risk analysis',
            'write a', 'create a'
        ]

        if any(kw in msg for kw in complex_keywords):
            if any(w in msg for w in ['risk', 'analyze', 'check', 'review']):
                return {
                    'reply': 'For contract and document risk analysis, please use the Analyze Legal Risks feature.',
                    'intent': 'complex_legal',
                    'action': 'navigate:analyze-risks'
                }
            return {
                'reply': 'For document drafting, please use the Draft Legal Document feature.',
                'intent': 'complex_legal',
                'action': 'navigate:draft-documents'
            }

        if any(kw in msg for kw in nav_keywords):
            route_map = {
                'draft': ('Draft Legal Document', 'navigate:draft-documents'),
                'risk': ('Analyze Legal Risks', 'navigate:analyze-risks'),
                'summar': ('Summarize Judgment', 'navigate:summarize-judgment'),
                'explain': ('Explain Legal Provision', 'navigate:explain-provision'),
                'mapping': ('IPC to BNS Mapping', 'navigate:ipc-bns-mapping'),
                'ipc': ('IPC to BNS Mapping', 'navigate:ipc-bns-mapping'),
                'bns': ('IPC to BNS Mapping', 'navigate:ipc-bns-mapping'),
                'home': ('Dashboard', 'navigate:dashboard'),
                'dashboard': ('Dashboard', 'navigate:dashboard'),
                'billing': ('Subscriptions & Billing', 'navigate:billing'),
                'payment': ('Subscriptions & Billing', 'navigate:billing'),
                'subscription': ('Subscriptions & Billing', 'navigate:billing'),
                'upi': ('Subscriptions & Billing', 'navigate:billing'),
            }

            for keyword, (name, action) in route_map.items():
                if keyword in msg:
                    return {
                        'reply': f'You can find the {name} feature on the platform. Let me take you there.',
                        'intent': 'navigation',
                        'action': action
                    }

            return {
                'reply': 'I can help you navigate. We have features for drafting documents, analyzing risks, summarizing judgments, explaining provisions, and IPC-BNS mapping. What are you looking for?',
                'intent': 'navigation'
            }

        return {
            'reply': f'I can help with that. For detailed legal assistance, please use our platform tools. This is general information, not legal advice.',
            'intent': 'simple_legal'
        }
