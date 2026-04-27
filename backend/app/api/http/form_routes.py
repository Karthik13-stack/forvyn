from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any
import traceback
import logging
from app.core.dependencies import get_prompts, get_generator, PromptService
from app.ai_core.workflows.document_generation import DocumentGenerator
import json
from datetime import datetime
from pathlib import Path
router = APIRouter()
logger = logging.getLogger(__name__)
DEFAULT_DOC_FIELD_MAP = {'Contract Agreement': [{'key': 'party_a_name', 'label': 'Party A Name', 'required': True, 'type': 'text'}, {'key': 'party_b_name', 'label': 'Party B Name', 'required': True, 'type': 'text'}, {'key': 'effective_date', 'label': 'Effective Date', 'required': True, 'type': 'date'}, {'key': 'contract_value', 'label': 'Contract Value (INR)', 'required': False, 'type': 'number'}], 'Loan Agreement': [{'key': 'lender_name', 'label': 'Lender Name', 'required': True, 'type': 'text'}, {'key': 'borrower_name', 'label': 'Borrower Name', 'required': True, 'type': 'text'}, {'key': 'loan_amount', 'label': 'Loan Amount (INR)', 'required': True, 'type': 'number'}, {'key': 'repayment_terms', 'label': 'Repayment Terms', 'required': False, 'type': 'textarea'}], 'Lease Deed': [{'key': 'landlord_name', 'label': 'Landlord Name', 'required': True, 'type': 'text'}, {'key': 'tenant_name', 'label': 'Tenant Name', 'required': True, 'type': 'text'}, {'key': 'property_address', 'label': 'Property Address', 'required': True, 'type': 'textarea'}, {'key': 'rent_amount', 'label': 'Monthly Rent (INR)', 'required': True, 'type': 'number'}, {'key': 'lease_start_date', 'label': 'Lease Start Date', 'required': True, 'type': 'date'}], 'Divorce': [{'key': 'husband_name', 'label': 'Husband Full Name', 'required': True, 'type': 'text'}, {'key': 'wife_name', 'label': 'Wife Full Name', 'required': True, 'type': 'text'}, {'key': 'marriage_date', 'label': 'Date of Marriage', 'required': True, 'type': 'date'}], 'Indeminity Agreement': [{'key': 'indemnifier_name', 'label': 'Indemnifier Name', 'required': True, 'type': 'text'}, {'key': 'indemnitee_name', 'label': 'Indemnitee Name', 'required': True, 'type': 'text'}, {'key': 'indemnity_scope', 'label': 'Scope of Indemnity', 'required': True, 'type': 'textarea'}, {'key': 'effective_date', 'label': 'Effective Date', 'required': True, 'type': 'date'}], 'Pledge Agreement': [{'key': 'pledgor_name', 'label': 'Pledgor Name', 'required': True, 'type': 'text'}, {'key': 'pledgee_name', 'label': 'Pledgee Name', 'required': True, 'type': 'text'}, {'key': 'secured_amount', 'label': 'Secured Amount (INR)', 'required': True, 'type': 'number'}, {'key': 'security_description', 'label': 'Description of Security', 'required': False, 'type': 'textarea'}], 'Professional Services Agreement': [{'key': 'service_provider', 'label': 'Service Provider', 'required': True, 'type': 'text'}, {'key': 'client_name', 'label': 'Client Name', 'required': True, 'type': 'text'}, {'key': 'scope_of_services', 'label': 'Scope of Services', 'required': True, 'type': 'textarea'}, {'key': 'fees', 'label': 'Fees (INR)', 'required': False, 'type': 'number'}], 'Adoption': [{'key': 'applicant_name', 'label': 'Applicant Name', 'required': True, 'type': 'text'}, {'key': 'child_name', 'label': 'Child Name', 'required': True, 'type': 'text'}, {'key': 'adoption_date', 'label': 'Adoption Date', 'required': True, 'type': 'date'}], 'Design': [{'key': 'applicant_name', 'label': 'Applicant Name', 'required': True, 'type': 'text'}, {'key': 'design_title', 'label': 'Design Title', 'required': True, 'type': 'text'}, {'key': 'description', 'label': 'Brief Description', 'required': False, 'type': 'textarea'}]}

@router.get('/meta/domains')
def get_domains(prompt_service: PromptService=Depends(get_prompts)):
    try:
        domains = prompt_service.get_domains()
        logger.info(f'GET /api/meta/domains -> {len(domains)} domains: {domains}')
        if not domains:
            logger.warning('No domains found in prompt_service')
        return domains if domains else []
    except Exception as e:
        logger.error(f'Error in get_domains: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=f'Error loading domains: {str(e)}')

@router.get('/meta/{domain}/documents')
def get_documents(domain: str, prompt_service: PromptService=Depends(get_prompts)):
    from urllib.parse import unquote
    domain = unquote(domain)
    logger.info(f'GET /api/meta/{domain}/documents')
    docs = prompt_service.get_documents(domain)
    if not docs:
        available_domains = prompt_service.get_domains()
        domain_lower = domain.lower()
        for avail_domain in available_domains:
            if avail_domain.lower() == domain_lower:
                docs = prompt_service.get_documents(avail_domain)
                logger.info(f"Matched domain '{avail_domain}' (case-insensitive)")
                break
        if not docs:
            logger.warning(f"Domain '{domain}' not found. Available: {available_domains}")
            raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found. Available: {available_domains}")
    logger.info(f'Returning {len(docs)} documents: {docs}')
    return docs

def _default_schema_for_document(domain: str, doc_type: str) -> list:
    if doc_type in DEFAULT_DOC_FIELD_MAP:
        return DEFAULT_DOC_FIELD_MAP[doc_type]
    doc_lower = doc_type.lower()
    domain_lower = (domain or '').lower()
    defaults = []
    if 'contract' in doc_lower or 'agreement' in doc_lower:
        defaults = [{'key': 'party_a_name', 'label': 'Party A Name', 'required': True, 'type': 'text'}, {'key': 'party_b_name', 'label': 'Party B Name', 'required': True, 'type': 'text'}, {'key': 'effective_date', 'label': 'Effective Date', 'required': True, 'type': 'date'}, {'key': 'contract_value', 'label': 'Contract Value / Amount (INR)', 'required': False, 'type': 'number'}, {'key': 'additional_terms', 'label': 'Additional Terms (if any)', 'required': False, 'type': 'textarea'}]
    elif 'divorce' in doc_lower or 'marriage' in doc_lower or 'family' in domain_lower:
        defaults = [{'key': 'husband_name', 'label': 'Husband Full Name', 'required': True, 'type': 'text'}, {'key': 'wife_name', 'label': 'Wife Full Name', 'required': True, 'type': 'text'}, {'key': 'marriage_date', 'label': 'Date of Marriage', 'required': True, 'type': 'date'}, {'key': 'place_of_marriage', 'label': 'Place of Marriage', 'required': False, 'type': 'text'}]
    elif 'lease' in doc_lower or 'rent' in doc_lower or 'real' in domain_lower:
        defaults = [{'key': 'landlord_name', 'label': 'Landlord Name', 'required': True, 'type': 'text'}, {'key': 'tenant_name', 'label': 'Tenant Name', 'required': True, 'type': 'text'}, {'key': 'property_address', 'label': 'Property Address', 'required': True, 'type': 'textarea'}, {'key': 'rent_amount', 'label': 'Monthly Rent (INR)', 'required': True, 'type': 'number'}, {'key': 'lease_start_date', 'label': 'Lease Start Date', 'required': True, 'type': 'date'}]
    elif 'ip' in domain_lower or 'patent' in doc_lower or 'trademark' in doc_lower or ('copyright' in doc_lower):
        defaults = [{'key': 'applicant_name', 'label': 'Applicant / Owner Name', 'required': True, 'type': 'text'}, {'key': 'title_or_work', 'label': 'Title / Work / Invention', 'required': True, 'type': 'text'}, {'key': 'description', 'label': 'Brief Description', 'required': False, 'type': 'textarea'}]
    else:
        defaults = [{'key': 'party_name', 'label': 'Party Name', 'required': True, 'type': 'text'}, {'key': 'document_date', 'label': 'Document Date', 'required': True, 'type': 'date'}, {'key': 'details', 'label': 'Relevant Details', 'required': False, 'type': 'textarea'}]
    return defaults

def _extract_json_array(text: str):
    import re
    text = text.strip()
    if '```' in text:
        match = re.search('```(?:json)?\\s*([\\s\\S]*?)```', text)
        if match:
            text = match.group(1).strip()
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1 and (end > start):
        return text[start:end + 1]
    return text

@router.get('/meta/{domain}/{doc_type}/schema')
def get_schema(domain: str, doc_type: str, prompt_service: PromptService=Depends(get_prompts)):
    from urllib.parse import unquote
    import json
    domain = unquote(domain)
    doc_type = unquote(doc_type)
    logger.info(f'GET /api/meta/{domain}/{doc_type}/schema')
    available_domains = prompt_service.get_domains()
    domain_lower = domain.lower()
    matched_domain = domain
    for avail_domain in available_domains:
        if avail_domain.lower() == domain_lower:
            matched_domain = avail_domain
            break
    docs = prompt_service.get_documents(matched_domain)
    doc_lower = doc_type.lower()
    matched_doc = doc_type
    for doc in docs:
        if doc.lower() == doc_lower:
            matched_doc = doc
            break
    if matched_doc not in docs:
        raise HTTPException(status_code=404, detail=f"Document type '{doc_type}' not found in domain '{domain}'. Available: {docs}")
    schema = prompt_service.get_schema(matched_domain, matched_doc)
    if schema:
        logger.info(f'Using extracted schema: {len(schema)} fields')
        return schema
    clauses = prompt_service.get_clauses(matched_domain, matched_doc)
    if clauses:
        all_prompts = '\n\n'.join(clauses[:10])
        if len(all_prompts) > 12000:
            all_prompts = all_prompts[:12000] + '\n\n[... truncated ...]'
        try:
            from app.ai_core.llm.gemini_client import GeminiClient
            gemini = GeminiClient()
            analysis_prompt = f'Analyze the following legal document prompts for "{matched_doc}" in {matched_domain}.\n\nIdentify required input fields a user must provide. Return ONLY a valid JSON array of objects with: "key" (snake_case), "label", "required" (true/false), "type" ("text"|"textarea"|"date"|"number"|"email").\n\nPrompts:\n{all_prompts}\n\nExample: [{{"key": "party_a_name", "label": "Party A Name", "required": true, "type": "text"}}]\nReturn ONLY the JSON array, no other text:'
            response = gemini.model.generate_content(analysis_prompt)
            try:
                response_text = (response.text or '').strip()
            except Exception:
                response_text = getattr(response, 'text', '') or ''
            response_text = _extract_json_array(response_text)
            schema = json.loads(response_text)
            if isinstance(schema, list) and schema:
                validated = []
                for field in schema:
                    if isinstance(field, dict) and field.get('key') and field.get('label'):
                        validated.append({'key': str(field.get('key', '')).strip(), 'label': str(field.get('label', '')).strip(), 'required': bool(field.get('required', True)), 'type': field.get('type') in ('text', 'textarea', 'date', 'number', 'email') and field.get('type') or 'text'})
                if validated:
                    logger.info(f'Gemini generated {len(validated)} fields for {matched_domain}/{matched_doc}')
                    return validated
        except Exception as e:
            try:
                raw = None
                try:
                    raw = json.dumps(response, default=lambda o: getattr(o, '__dict__', repr(o)))
                except Exception:
                    raw = repr(response)
                logs_dir = Path(__file__).resolve().parents[3] / 'logs'
                logs_dir.mkdir(parents=True, exist_ok=True)
                fname = logs_dir / f"gemini_schema_raw_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.log"
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(f'ERROR: {str(e)}\n\nRAW RESPONSE:\n{raw}\n')
                logger.warning(f'Gemini schema extraction failed: {e}. Raw response written to {fname}')
            except Exception:
                logger.exception('Failed while logging Gemini raw response')
    schema = _default_schema_for_document(matched_domain, matched_doc)
    logger.info(f'Using default schema: {len(schema)} fields for {matched_domain}/{matched_doc}')
    return schema

def _placeholder_document(domain: str, doc_type: str, form_data: dict) -> str:
    lines = [f'{doc_type.upper()}', f'Domain: {domain}', '', 'This is a placeholder. AI generation failed or was unavailable.', 'Please try again or check your connection and API key.', '', '--- Details you provided ---']
    for k, v in (form_data or {}).items():
        if v:
            lines.append(f'{k}: {v}')
    lines.append('')
    lines.append('--- End of placeholder ---')
    return '\n'.join(lines)

@router.post('/generate')
def generate_document(payload: Dict[str, Any]=Body(...), generator: DocumentGenerator=Depends(get_generator)):
    domain = payload.get('domain')
    doc_type = payload.get('doc_type')
    form_data = payload.get('form_data', {})
    if not domain or not doc_type:
        raise HTTPException(status_code=400, detail='Missing domain or doc_type')
    try:
        final_doc = generator.generate(domain, doc_type, form_data)
        return {'content': final_doc if final_doc is not None else '', 'error_message': None}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        logger.exception('Generate document failed')
        placeholder = _placeholder_document(domain, doc_type, form_data)
        return {'content': placeholder, 'error_message': str(e)}