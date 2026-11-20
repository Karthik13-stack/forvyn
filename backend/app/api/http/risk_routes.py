from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List
import json
import logging
import re
router = APIRouter()
logger = logging.getLogger(__name__)

def _find_phrase_offsets(content: str, phrase: str) -> List[tuple]:
    if not phrase or not phrase.strip():
        return []
    phrase = phrase.strip()
    out = []
    start = 0
    while True:
        idx = content.find(phrase, start)
        if idx == -1:
            break
        out.append((idx, idx + len(phrase)))
        start = idx + 1
        break
    return out

def _merge_overlapping(intervals: List[tuple]) -> List[tuple]:
    if not intervals:
        return []
    sorted_i = sorted(intervals, key=lambda x: (x[0], -x[1]))
    merged = []
    for s, e, level, reason in sorted_i:
        if merged and s <= merged[-1][1]:
            prev_s, prev_e, prev_l, prev_r = merged[-1]
            merged[-1] = (prev_s, max(prev_e, e), prev_l if prev_l == 'high' else level, prev_r)
        else:
            merged.append((s, e, level, reason))
    return merged

@router.post('/analyze-risks')
def analyze_risks(payload: Dict[str, Any]=Body(...)):
    content = payload.get('content') or ''
    if not content.strip():
        return {'risks': [], 'message': 'Document is empty.'}
    try:
        from app.ai_core.llm.gemini_client import GeminiClient
        gemini = GeminiClient()
    except Exception as e:
        logger.error(f'Gemini client init failed: {e}')
        raise HTTPException(status_code=500, detail='Risk analysis service unavailable.')
    prompt = f'You are a legal risk analyst for Indian law. Analyze the following legal document and identify specific clauses or phrases that pose risks.\n\nDocument:\n{content[:30000]}\n\nFor each risk, provide:\n1. The exact clause or phrase as it appears in the document (copy it verbatim).\n2. risk_level: "high" if it needs human review (ambiguity, missing obligation, unfair term, regulatory risk). "medium" for moderate concerns.\n3. A brief reason.\n\nReturn ONLY a valid JSON array of objects with keys: "text", "risk_level", "reason".\nExample:\n[{{"text": "the exact phrase from the document", "risk_level": "high", "reason": "Unclear liability."}}, {{"text": "another phrase", "risk_level": "medium", "reason": "Consider specifying timeline."}}]\n\nReturn ONLY the JSON array, no markdown or explanation:'
    try:
        response = gemini.model.generate_content(prompt)
        response_text = (response.text or '').strip()
    except Exception as e:
        logger.error(f'Gemini call failed: {e}')
        raise HTTPException(status_code=500, detail=f'Analysis failed: {str(e)}')
    if '```' in response_text:
        m = re.search('```(?:json)?\\s*([\\s\\S]*?)```', response_text)
        if m:
            response_text = m.group(1).strip()
    start_bracket = response_text.find('[')
    end_bracket = response_text.rfind(']')
    if start_bracket != -1 and end_bracket != -1 and (end_bracket > start_bracket):
        response_text = response_text[start_bracket:end_bracket + 1]
    try:
        items = json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.error(f'Invalid JSON from Gemini: {e}. Response: {response_text[:500]}')
        return {'risks': [], 'message': 'Could not parse risk analysis.'}
    if not isinstance(items, list):
        return {'risks': []}
    intervals = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = item.get('text') or ''
        level = (item.get('risk_level') or 'medium').lower()
        if level not in ('high', 'medium'):
            level = 'medium'
        reason = item.get('reason') or 'Potential risk'
        for start, end in _find_phrase_offsets(content, text):
            intervals.append((start, end, level, reason))
    merged = _merge_overlapping(intervals)
    risks = [{'start_index': s, 'end_index': e, 'risk_level': level, 'reason': reason, 'snippet': content[s:e][:200]} for s, e, level, reason in merged]
    logger.info(f'Risk analysis found {len(risks)} spans')
    return {'risks': risks}