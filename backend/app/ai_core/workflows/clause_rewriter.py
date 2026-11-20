from app.ai_core.rag.vector_service import VectorService
from app.ai_core.llm.gemini_client import GeminiClient

class ClauseRewriter:

    def __init__(self, vector_service: VectorService):
        self.vector_service = vector_service
        self.llm = GeminiClient()

    def process(self, text: str, intent: str, domain: str) -> str:
        sim_results = self.vector_service.search_similar_clauses(text, k=2)
        context = [r['text'] for r in sim_results]
        new_text = self.llm.rewrite_clause(text, intent, context)
        return new_text

    def process_rewrite(self, text: str, action_type: str, target_language: str) -> str:
        # Directly use Gemini advanced rewrite
        # action_type can be emphasize, rewrite, translate
        return self.llm.advanced_clause_rewrite(text, action_type, target_language)