from app.ai_core.llm.gemini_client import GeminiClient
from app.ai_core.rag.vector_service import VectorService
from app.services.prompt_service import get_prompt_service
import time
import json
import logging
logger = logging.getLogger(__name__)

class DocumentGenerator:

    def __init__(self, vector_service):
        self.vector_service = vector_service
        self.gemini = GeminiClient()
        self.prompt_service = get_prompt_service()

    def generate(self, domain: str, doc_type: str, form_data: dict):
        clauses = self.prompt_service.get_document_clauses(domain, doc_type)
        clause_texts = '\n'.join([c.get('ClauseText') or '' for c in clauses])
        rag_hits = self.vector_service.search_similar_clauses(f'{doc_type} contract {domain}', k=8)
        rag_context = '\n'.join([c.get('text') or '' for c in rag_hits])
        if not self.gemini.is_available:
            return self._build_fallback_document(domain, doc_type, form_data, clauses)
        if len(clause_texts) > 8000:
            clause_texts = clause_texts[:8000] + '\n\n[... truncated ...]'
        if len(rag_context) > 6000:
            rag_context = rag_context[:6000] + '\n\n[... truncated ...]'
        prompt = f'\nDraft a complete {doc_type} for the domain {domain}.\n\nUser provided:\n{form_data}\n\nUse these official clause templates:\n{clause_texts}\n\nUse these real legal examples:\n{rag_context}\n\nRules:\n- Output a full legal document\n- Use professional legal structure\n- No explanations\n- No markdown\n\nFinal Document:\n'
        last_exc = None
        for attempt in range(1, 4):
            try:
                response = self.gemini.generate_content(prompt)
                text = None
                try:
                    text = getattr(response, 'text', None)
                    if callable(text):
                        text = text()
                except Exception:
                    text = None
                if not text:
                    try:
                        if isinstance(response, dict):
                            for k in ('text', 'output', 'content', 'results'):
                                v = response.get(k)
                                if isinstance(v, str) and v.strip():
                                    text = v
                                    break
                            if not text and response.get('candidates'):
                                for c in response.get('candidates'):
                                    if isinstance(c, dict):
                                        for k2 in ('content', 'text', 'output'):
                                            v2 = c.get(k2)
                                            if isinstance(v2, str) and v2.strip():
                                                text = v2
                                                break
                                        if text:
                                            break
                    except Exception:
                        pass
                if not text and getattr(response, 'candidates', None):
                    try:
                        cands = getattr(response, 'candidates')
                        for c in cands:
                            v = None
                            if isinstance(c, dict):
                                v = c.get('content') or c.get('text') or c.get('output')
                            else:
                                v = getattr(c, 'content', None) or getattr(c, 'text', None) or getattr(c, 'output', None)
                            if isinstance(v, str) and v.strip():
                                text = v
                                break
                    except Exception:
                        pass
                if text and isinstance(text, str) and text.strip():
                    return text.strip()
                reason = ''
                try:
                    pf = getattr(response, 'prompt_feedback', None)
                    if pf and getattr(pf, 'block_reason', None):
                        reason = getattr(pf, 'block_reason')
                except Exception:
                    pass
                try:
                    if not reason and getattr(response, 'candidates', None):
                        c0 = response.candidates[0]
                        reason = getattr(c0, 'finish_reason', None) or getattr(c0, 'reason', '') or ''
                except Exception:
                    pass
                if attempt == 3:
                    try:
                        try:
                            serial = json.dumps(response, default=lambda o: getattr(o, '__dict__', repr(o)), indent=2)
                            logger.warning('Gemini returned no text. Reason: %s. Raw response: %s', reason, serial)
                        except Exception:
                            logger.warning('Gemini returned no text. Reason: %s. Raw response repr: %s', reason, repr(response))
                    except Exception:
                        logger.exception('Failed to log Gemini raw response')
                    raise ValueError(f'Gemini returned no text. {reason}'.strip())
                wait = attempt * 1.0
                time.sleep(wait)
            except ValueError:
                raise
            except Exception as e:
                last_exc = e
                if attempt == 3:
                    raise RuntimeError(f'Document generation failed after retries: {e}') from e
                time.sleep(attempt * 0.8)
        if last_exc:
            raise RuntimeError(f'Document generation failed: {last_exc}') from last_exc
        raise RuntimeError('Document generation failed: unknown error')

    def _build_fallback_document(self, domain: str, doc_type: str, form_data: dict, clauses: list) -> str:
        header = f'{doc_type.upper()} ({domain})\n'
        header += '=' * max(len(header) - 1, 10)
        body_lines = [header, '', 'User Inputs:']
        for key, value in form_data.items():
            body_lines.append(f'- {key}: {value}')
        body_lines.append('')
        body_lines.append('Template Clauses:')
        for idx, clause in enumerate(clauses, start=1):
            title = clause.get('ClauseTitle') or f'Clause {idx}'
            text = clause.get('ClauseText') or ''
            body_lines.append(f'{idx}. {title}')
            if text:
                body_lines.append(text)
            body_lines.append('')
        return '\n'.join(body_lines).strip()