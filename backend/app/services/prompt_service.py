from pathlib import Path
try:
    import pandas as pd
except Exception:
    pd = None
import re
from collections import defaultdict
from zipfile import BadZipFile
import logging
import shutil
from datetime import datetime
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
APP_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = APP_DIR / 'services' / 'prompts'
_LOADED = False

class PromptService:

    def __init__(self):
        self.documents = defaultdict(lambda: defaultdict(list))
        self.schemas = defaultdict(lambda: defaultdict(list))
        self.load_stats = {'files_loaded': 0, 'files_failed': 0, 'total_clauses': 0}
        self.load_all_excels()

    def _normalize_column_name(self, col_name):
        if not isinstance(col_name, str):
            return col_name
        normalized = col_name.strip().lower()
        mapping = {'domain': 'domain', 'domains': 'domain', 'document': 'document', 'document_name': 'document', 'document name': 'document', 'doc_name': 'document', 'documenttype': 'document', 'document type': 'document', 'type of document': 'document', 'clause': 'clause', 'clauses': 'clause', 'clause_text': 'clause', 'clause text': 'clause', 'clausetext': 'clause', 'prompt': 'clause', 'clause title': 'clause_title', 'clausetitle': 'clause_title'}
        return mapping.get(normalized, col_name)

    def _find_header_row(self, df):
        for idx in range(min(5, len(df))):
            row = df.iloc[idx]
            row_str = ' '.join((str(v).lower() for v in row if pd.notna(v)))
            if any((keyword in row_str for keyword in ['domain', 'document', 's.no', 'clause'])):
                new_df = df.iloc[idx + 1:].reset_index(drop=True)
                new_df.columns = [self._normalize_column_name(col) for col in df.iloc[idx]]
                return (new_df, idx)
        return (df, 0)

    def _get_required_columns(self, df):
        normalized_cols = {}
        col_mapping = {}
        for col in df.columns:
            norm = self._normalize_column_name(col)
            normalized_cols[col] = norm
            if norm in ['domain', 'document', 'clause', 'clause_title']:
                col_mapping[norm] = col
        return (col_mapping, normalized_cols)

    def _guess_document_from_filename(self, filename):
        name = filename.replace('.xlsx', '').replace('.xls', '')
        import re
        name = re.sub('([a-z])([A-Z])', '\\1 \\2', name)
        return name

    def _load_excel_file(self, file_path):
        if pd is None:
            return (False, 0, 'pandas not installed; skipping Excel prompt load')
        try:
            df = pd.read_excel(file_path, header=None)
            df, header_idx = self._find_header_row(df)
            if df is None or len(df) == 0:
                return (False, 0, 'No data rows found after header')
            col_mapping, normalized = self._get_required_columns(df)
            has_domain = 'domain' in col_mapping
            has_document = 'document' in col_mapping
            has_clause = 'clause' in col_mapping
            if has_domain and has_clause:
                return self._load_structured_format(file_path, df, col_mapping, has_document)
            else:
                return self._load_prompt_based_format(file_path, df)
        except BadZipFile as e:
            return (False, 0, f'Corrupted Excel file (BadZipFile): {str(e)}')
        except pd.errors.ParserError as e:
            return (False, 0, f'Excel parsing error: {str(e)}')
        except Exception as e:
            return (False, 0, f'Unexpected error: {type(e).__name__}: {str(e)}')

    def _load_structured_format(self, file_path, df, col_mapping, has_document):
        domain_col = col_mapping.get('domain')
        doc_col = col_mapping.get('document')
        clause_col = col_mapping.get('clause')
        clause_title_col = col_mapping.get('clause_title')
        if not doc_col:
            document_fallback = self._guess_document_from_filename(file_path.name)
        clauses_count = 0
        for _, row in df.iterrows():
            domain = str(row[domain_col]).strip() if pd.notna(row[domain_col]) else ''
            if doc_col:
                document = str(row[doc_col]).strip() if pd.notna(row[doc_col]) else ''
            else:
                document = document_fallback
            clause = str(row[clause_col]).strip() if pd.notna(row[clause_col]) else ''
            if not domain or not document or (not clause):
                continue
            if clause_title_col and pd.notna(row[clause_title_col]):
                clause_title = str(row[clause_title_col]).strip()
                clause_text = f'[{clause_title}] {clause}'
            else:
                clause_text = clause
            self.documents[domain][document].append(clause_text)
            self._extract_schema(domain, document, clause_text)
            clauses_count += 1
        return (True, clauses_count, None)

    def _load_prompt_based_format(self, file_path, df):
        domain = self._guess_document_from_filename(file_path.name)
        clauses_count = 0
        category_col_idx = None
        for idx, col in enumerate(df.columns):
            col_lower = str(col).lower()
            if any((keyword in col_lower for keyword in ['category', 'prompt', 'type', 'design', 'marriage', 'professional'])):
                category_col_idx = idx
                break
        if category_col_idx is None:
            category_col_idx = 2 if len(df.columns) > 2 else 0
        prompt_col_idx = None
        for idx in range(len(df.columns) - 1, 4, -1):
            col = df.columns[idx]
            sample_vals = df.iloc[:min(3, len(df)), idx]
            avg_len = sum((len(str(v)) for v in sample_vals if pd.notna(v))) / max(len(sample_vals), 1)
            if avg_len > 50:
                prompt_col_idx = idx
                break
        if prompt_col_idx is None:
            prompt_col_idx = 5 if len(df.columns) > 5 else len(df.columns) - 1
        category_col = df.columns[category_col_idx] if category_col_idx < len(df.columns) else None
        prompt_col = df.columns[prompt_col_idx] if prompt_col_idx < len(df.columns) else None
        if category_col is None or prompt_col is None:
            return (False, 0, 'Could not identify category or prompt columns')
        for _, row in df.iterrows():
            doc_val = row[category_col]
            document = str(doc_val).strip() if pd.notna(doc_val) else 'General'
            if document.isdigit() or not document:
                continue
            clause = str(row[prompt_col]).strip() if pd.notna(row[prompt_col]) else ''
            if not clause or len(clause) < 50:
                continue
            self.documents[domain][document].append(clause)
            self._extract_schema(domain, document, clause)
            clauses_count += 1
        return (True, clauses_count, None)

    def load_all_excels(self):
        global _LOADED
        if _LOADED:
            logger.debug('Prompt service already loaded, skipping re-initialization')
            return
        if not PROMPTS_DIR.exists():
            logger.warning(f'⚠️  Prompts directory not found at {PROMPTS_DIR}')
            logger.warning('Server will continue but without legal prompts loaded')
            _LOADED = True
            return
        excel_files = sorted(PROMPTS_DIR.glob('*.xlsx'))
        if not excel_files:
            logger.warning(f'⚠️  No Excel files found in {PROMPTS_DIR}')
            _LOADED = True
            return
        logger.info(f'Loading {len(excel_files)} Excel files from {PROMPTS_DIR}')
        for file_path in excel_files:
            success, clauses_loaded, error_msg = self._load_excel_file(file_path)
            if success:
                self.load_stats['files_loaded'] += 1
                self.load_stats['total_clauses'] += clauses_loaded
                logger.info(f'✅ {file_path.name}: {clauses_loaded} clauses loaded')
            else:
                self.load_stats['files_failed'] += 1
                logger.warning(f'⚠️  {file_path.name}: {error_msg}')
                try:
                    if error_msg and 'Corrupted Excel file' in error_msg:
                        corrupt_dir = PROMPTS_DIR / 'corrupt'
                        corrupt_dir.mkdir(parents=True, exist_ok=True)
                        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                        dest = corrupt_dir / f'{file_path.stem}_{ts}{file_path.suffix}'
                        shutil.move(str(file_path), str(dest))
                        logger.info(f'Moved corrupted file {file_path.name} -> {dest}')
                except Exception:
                    logger.exception('Failed to move corrupted prompt file')
        if self.load_stats['files_loaded'] == 0:
            logger.warning(f'⚠️  No Excel files were successfully loaded')
            logger.warning('Server will continue without legal prompts')
        else:
            self.validate_and_print_summary()
        _LOADED = True

    def _extract_schema(self, domain, document, clause_text):
        matches = re.findall('{{\\s*(.*?)\\s*}}', clause_text)
        for var in matches:
            key = var.strip()
            existing = [f['key'] for f in self.schemas[domain][document]]
            if key not in existing:
                self.schemas[domain][document].append({'key': key, 'label': key.replace('_', ' ').title(), 'required': True, 'type': 'text'})

    def validate_and_print_summary(self):
        logger.info('=' * 60)
        logger.info('PROMPT SERVICE VALIDATION SUMMARY')
        logger.info('=' * 60)
        logger.info(f"Files loaded: {self.load_stats['files_loaded']}")
        logger.info(f"Files failed: {self.load_stats['files_failed']}")
        logger.info(f"Total clauses loaded: {self.load_stats['total_clauses']}")
        domains = self.get_domains()
        logger.info(f'Domains: {len(domains)}')
        for domain in domains:
            docs = self.get_documents(domain)
            total_docs = len(docs)
            total_clauses = sum((len(self.get_clauses(domain, doc)) for doc in docs))
            logger.info(f'  {domain}: {total_docs} documents, {total_clauses} clauses')
            for doc in docs:
                clauses = self.get_clauses(domain, doc)
                schema = self.get_schema(domain, doc)
                logger.info(f'    - {doc}: {len(clauses)} clauses, {len(schema)} schema fields')
        logger.info('=' * 60)

    def get_domains(self):
        return sorted(self.documents.keys())

    def get_documents(self, domain):
        return sorted(self.documents.get(domain, {}).keys())

    def get_schema(self, domain, document):
        return self.schemas.get(domain, {}).get(document, [])

    def get_clauses(self, domain, document):
        return self.documents.get(domain, {}).get(document, [])

    def get_documents_by_domain(self, domain):
        return self.get_documents(domain)

    def get_document_clauses(self, domain, document):
        clauses = self.get_clauses(domain, document)
        return [{'ClauseText': text, 'ClauseTitle': None, 'ClauseID': None, 'IsMandatory': None} for text in clauses]

    def get_all_data(self):
        return {'documents': self.documents, 'schemas': self.schemas}

    def get_load_stats(self):
        return self.load_stats
prompt_service = PromptService()

def get_prompt_service():
    return prompt_service
if __name__ == '__main__':
    ps = get_prompt_service()
    print('Domains:', ps.get_domains())
    for domain in ps.get_domains():
        print(f'  Documents in {domain}: {ps.get_documents(domain)}')
        for document in ps.get_documents(domain):
            print(f'    Schema for {document}: {ps.get_schema(domain, document)}')
            print(f'    Clauses for {document}: {ps.get_clauses(domain, document)}')