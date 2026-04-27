"""
Drafting Wizard API Routes
Powers the 4-step legal document drafting wizard UI.
Endpoints: categories, documents, AI questions, document generation, translation.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Dict, Optional
import logging
import json
import re
import time

from app.core.dependencies import get_prompts, get_generator
from app.services.prompt_service import PromptService
from app.ai_core.llm.gemini_client import GeminiClient
from app.ai_core.workflows.document_generation import DocumentGenerator

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Pydantic models ──────────────────────────────────────────────

class QuestionRequest(BaseModel):
    domain: str
    category: str
    document: str
    language: str = "English"


class DraftGenerateRequest(BaseModel):
    domain: str
    category: str
    document: str
    answers: Dict[str, str]
    language: str = "English"


class TranslateRequest(BaseModel):
    content: str
    from_language: str
    to_language: str = "English"


# ── Category / Document helpers ──────────────────────────────────
# Forvyn's PromptService maps domain → document (flat).
# We derive categories by grouping document names heuristically.

DOMAIN_CATEGORY_MAP = {
    "Family Law": {
        "Marriage": ["Marriage Certificate", "Pre-Nuptial Agreement", "Marriage Affidavit"],
        "Divorce": ["Mutual Consent Divorce Petition", "Contested Divorce Petition",
                     "Divorce Settlement Agreement", "Divorce"],
        "Custody": ["Child Custody Agreement", "Guardianship Petition",
                     "Custody Modification Request"],
        "Adoption": ["Adoption Deed", "Adoption Petition", "Consent for Adoption", "Adoption"],
    },
    "Contract Law": {
        "Service Agreements": ["Service Agreement", "Professional Services Agreement"],
        "Employment Contracts": ["Employment Contract"],
        "Confidentiality Agreements": ["Non-Disclosure Agreement"],
        "Property Agreements": ["Lease Agreement", "Lease Deed"],
        "Business Agreements": ["Partnership Deed"],
        "Sale Agreements": ["Sale Agreement"],
        "Financial Agreements": ["Loan Agreement", "Indeminity Agreement", "Pledge Agreement"],
        "General Contracts": ["Contract Agreement"],
    },
    "Intellectual Property Law": {
        "Trademark": ["Trademark Registration Application", "Trademark Assignment Deed",
                       "Trademark License Agreement"],
        "Patent": ["Patent Application", "Patent Assignment Agreement",
                    "Patent License Agreement"],
        "Copyright": ["Copyright Registration Application", "Copyright Assignment Deed",
                       "Copyright License Agreement"],
        "Design": ["Design"],
    },
}


def _get_categories(domain: str, prompt_service: PromptService):
    """Return categories for a domain, merging static map with live PromptService data."""
    available_docs = set(prompt_service.get_documents(domain))
    static_map = DOMAIN_CATEGORY_MAP.get(domain, {})

    if static_map:
        cats = list(static_map.keys())
        # Also add an "Other" category for any documents not in the map
        mapped_docs = set()
        for docs in static_map.values():
            mapped_docs.update(d.lower() for d in docs)
        unmapped = [d for d in available_docs if d.lower() not in mapped_docs]
        if unmapped:
            cats.append("Other")
        return cats
    else:
        return ["General"]


def _get_documents(domain: str, category: str, prompt_service: PromptService):
    """Return document types for a domain+category."""
    available_docs = set(prompt_service.get_documents(domain))
    static_map = DOMAIN_CATEGORY_MAP.get(domain, {})

    if category == "Other" or category == "General":
        # Return everything not already in a named category
        mapped_docs = set()
        for docs in static_map.values():
            mapped_docs.update(d.lower() for d in docs)
        return sorted([d for d in available_docs if d.lower() not in mapped_docs])

    cat_docs = static_map.get(category, [])
    # Filter to only docs that exist in the prompt service
    result = [d for d in cat_docs if d in available_docs]
    # Also check case-insensitive
    if not result:
        avail_lower = {d.lower(): d for d in available_docs}
        result = [avail_lower[d.lower()] for d in cat_docs if d.lower() in avail_lower]
    return result


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/drafting/categories")
def get_categories(
    domain: str = Query(...),
    prompt_service: PromptService = Depends(get_prompts)
):
    """Return available categories for a legal domain."""
    categories = _get_categories(domain, prompt_service)
    return {"categories": categories}


@router.get("/drafting/documents")
def get_documents(
    domain: str = Query(...),
    category: str = Query(...),
    prompt_service: PromptService = Depends(get_prompts)
):
    """Return document types for a domain + category."""
    documents = _get_documents(domain, category, prompt_service)
    return {"documents": documents}


@router.post("/drafting/questions")
def generate_questions(req: QuestionRequest):
    """Use Gemini to generate context-aware questions for a legal document."""
    logger.info(f"Generating questions for {req.domain}/{req.category}/{req.document} in {req.language}")

    gemini = GeminiClient()

    lang_instruction = ""
    if req.language != "English":
        lang_instruction = f"\n\nCRITICAL: Generate ALL questions in {req.language} language. Every question must be written in {req.language}."

    prompt = f"""You are an expert Indian legal document assistant.

Generate exactly 6-10 specific, practical questions that a lawyer would need answered 
to draft a professional "{req.document}" document in the domain of {req.domain} 
(category: {req.category}).

Requirements:
1. Questions should cover all essential legal details needed
2. Include questions about parties involved, dates, amounts, terms
3. Include jurisdiction and compliance related questions
4. Be specific to Indian law requirements
5. Output ONLY a JSON array of question strings
6. No explanations, no numbering outside the JSON{lang_instruction}

Example output format:
["What is the full legal name of Party A?", "What is the address of Party A?"]

Generate the questions now:"""

    try:
        response = gemini.model.generate_content(prompt)
        text = response.text.strip()

        # Extract JSON array from response
        json_match = re.search(r'\[[\s\S]*?\]', text)
        if json_match:
            questions = json.loads(json_match.group())
        else:
            # Try parsing the whole text
            questions = json.loads(text)

        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("No questions generated")

        # Ensure all items are strings
        questions = [str(q) for q in questions if q]

        logger.info(f"Generated {len(questions)} questions")
        return {"questions": questions, "language": req.language}

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing AI response: {str(e)}")
    except Exception as e:
        logger.error(f"Question generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


@router.post("/drafting/generate")
def generate_document(
    req: DraftGenerateRequest,
    generator: DocumentGenerator = Depends(get_generator)
):
    """Generate a full legal document from AI-answered questions."""
    logger.info(f"Generating document: {req.domain}/{req.document} in {req.language}")

    # Format answers into form_data dict for the existing generator
    formatted_answers = "\n".join([f"Q: {q}\nA: {a}" for q, a in req.answers.items()])

    gemini = GeminiClient()

    # Build prompt with language support
    lang_block = ""
    if req.language != "English":
        lang_block = f"""
CRITICAL INSTRUCTION: YOU MUST WRITE THE ENTIRE DOCUMENT IN {req.language.upper()} LANGUAGE.
Every word, heading, clause, and section must be in {req.language}.
DO NOT write anything in English. The entire document must be in {req.language}."""

    # Try to get RAG context from the vector service
    rag_context = ""
    try:
        from app.core.dependencies import get_vectors
        vs = get_vectors()
        rag_hits = vs.search_similar_clauses(f"{req.document} {req.domain}", k=8)
        rag_context = "\n".join([c.get("text", "") for c in rag_hits])
        if len(rag_context) > 6000:
            rag_context = rag_context[:6000] + "\n\n[... truncated ...]"
    except Exception as e:
        logger.warning(f"RAG retrieval failed (proceeding without): {e}")

    # Get clause templates
    from app.services.prompt_service import get_prompt_service
    ps = get_prompt_service()
    clauses = ps.get_clauses(req.domain, req.document)
    clause_texts = "\n".join(clauses[:10])
    if len(clause_texts) > 8000:
        clause_texts = clause_texts[:8000] + "\n\n[... truncated ...]"

    prompt = f"""You are an expert legal document drafter specializing in Indian law.
Generate a complete, professional {req.document} based on the following information:

Domain: {req.domain}
Category: {req.category}
Document Type: {req.document}
{lang_block}

Information Provided:
{formatted_answers}

{"Legal clause templates:" if clause_texts else ""}
{clause_texts}

{"Real legal examples from database:" if rag_context else ""}
{rag_context}

Requirements:
1. Use proper legal language and formatting
2. Include all standard clauses for this type of document
3. Follow Indian legal standards and requirements
4. Include proper headings, sections, and numbering
5. Add placeholder [____] for any missing information
6. Include signature blocks at the end
7. Use professional legal document structure
8. Use Bharatiya Nyaya Sanhita (BNS) section references instead of IPC where applicable

Generate the complete document:"""

    try:
        response = gemini.model.generate_content(prompt)
        content = response.text.strip()

        if not content:
            raise ValueError("Gemini returned empty content")

        return {
            "content": content,
            "language": req.language,
            "domain": req.domain,
            "document": req.document,
        }

    except Exception as e:
        logger.error(f"Document generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")


@router.post("/drafting/translate")
def translate_content(req: TranslateRequest):
    """Translate document content between languages using Gemini."""
    logger.info(f"Translating from {req.from_language} to {req.to_language}")

    gemini = GeminiClient()

    prompt = f"""Translate the following legal document from {req.from_language} to {req.to_language}.

Important:
1. Maintain the exact same document structure and formatting
2. Preserve all legal terminology appropriately
3. Keep placeholders like [____] as is
4. Maintain all headings, numbering, and sections
5. Ensure the translation is legally accurate

Document to translate:
{req.content}

Provide the complete translated document:"""

    try:
        response = gemini.model.generate_content(prompt)
        translated = response.text.strip()

        if not translated:
            raise ValueError("Translation returned empty content")

        return {
            "translated_content": translated,
            "from_language": req.from_language,
            "to_language": req.to_language
        }

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error translating document: {str(e)}")
