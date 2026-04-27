import json
from typing import Dict, Any, List
from jinja2 import Template
from app.services.prompt_service import PromptService
from app.services.verification_service import VerificationService

class AssemblyService:

    def __init__(self):
        self.prompt_service = PromptService()
        self.verifier = VerificationService()

    def assemble_document(self, domain: str, doc_type: str, data: Dict[str, Any]) -> str:
        clauses = self.prompt_service.get_document_clauses(domain, doc_type)
        if not clauses:
            raise ValueError(f'No clauses found for {domain} - {doc_type}')
        full_text = []
        for clause in clauses:
            if not clause.get('IsMandatory', True):
                pass
            raw_text = clause.get('ClauseText', '')
            clause_id = float(clause.get('ClauseID', 0))
            title = clause.get('ClauseTitle', '')
            try:
                template = Template(raw_text)
                rendered_chunk = template.render(**data)
            except Exception as e:
                rendered_chunk = f'[ERROR RENDER: {str(e)}]'
            is_major_heading = clause_id % 1.0 == 0
            if is_major_heading:
                if title.lower() in ['title', 'header']:
                    final_chunk = f'# {rendered_chunk}'
                else:
                    final_chunk = f'## {int(clause_id)}. {title.upper()}\n{rendered_chunk}'
            else:
                final_chunk = f'**{clause_id}** {rendered_chunk}'
            full_text.append(final_chunk)
        final_doc = '\n\n'.join(full_text)
        missing_vars = self.verifier.verify_variables_filled(final_doc)
        if missing_vars:
            final_doc += f"\n\n[SYSTEM WARNING: Missing Variables: {', '.join(missing_vars)}]"
        return final_doc