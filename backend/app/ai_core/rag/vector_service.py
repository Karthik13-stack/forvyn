import pickle
import re
from pathlib import Path
from typing import Dict, List

try:
    import numpy as np
except Exception:
    np = None

try:
    import faiss
except Exception:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

from app.services.prompt_service import PromptService

INDEX_DIR = Path(__file__).resolve().parent / 'data'
INDEX_PATH = INDEX_DIR / 'faiss_index.bin'
METADATA_PATH = INDEX_DIR / 'metadata.pkl'


class VectorService:

    def __init__(self, prompt_service: PromptService):
        self.prompt_service = prompt_service
        self.model = None
        self.index = None
        self.metadata: List[Dict] = []
        self.initialized = False
        self.vector_enabled = faiss is not None and SentenceTransformer is not None

        if self.vector_enabled:
            self._init_model()
            if not self._load_index():
                self._build_index()
        else:
            print('Vector dependencies unavailable. Falling back to keyword search.')
            self._build_metadata_only()

    def _init_model(self):
        print('Loading SentenceTransformer model...')
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print('Model loaded.')

    def _load_index(self) -> bool:
        if not self.vector_enabled:
            return False
        if INDEX_PATH.exists() and METADATA_PATH.exists():
            try:
                print('Loading FAISS index from disk...')
                self.index = faiss.read_index(str(INDEX_PATH))
                with open(METADATA_PATH, 'rb') as f:
                    self.metadata = pickle.load(f)
                self.initialized = True
                print(f'Loaded index with {self.index.ntotal} clauses from disk.')
                return True
            except Exception as e:
                print(f'Error loading index: {e}. Will rebuild.')
        return False

    def _save_index(self):
        if not self.vector_enabled or self.index is None:
            return
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(INDEX_PATH))
        with open(METADATA_PATH, 'wb') as f:
            pickle.dump(self.metadata, f)
        print('FAISS index and metadata saved to disk.')

    def _build_index(self):
        if not self.vector_enabled or self.model is None or np is None:
            self._build_metadata_only()
            return

        print('Building Vector Index...')
        all_clauses = []
        self.metadata = []
        domains = self.prompt_service.get_domains()
        for domain in domains:
            docs = self.prompt_service.get_documents_by_domain(domain)
            for doc in docs:
                clauses = self.prompt_service.get_document_clauses(domain, doc)
                for clause in clauses:
                    text = clause.get('ClauseText', '')
                    title = clause.get('ClauseTitle', '')
                    all_clauses.append(f'{title}: {text}')
                    self.metadata.append(
                        {
                            'domain': domain,
                            'doc_type': doc,
                            'clause_id': clause.get('ClauseID'),
                            'title': title,
                            'text': text,
                            'is_mandatory': clause.get('IsMandatory'),
                        }
                    )

        if not all_clauses:
            print('No clauses found to index.')
            self.initialized = True
            return

        embeddings = self.model.encode(all_clauses)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings))
        self.initialized = True
        print(f'Index built with {self.index.ntotal} clauses.')
        self._save_index()

    def _build_metadata_only(self):
        self.metadata = []
        domains = self.prompt_service.get_domains()
        for domain in domains:
            docs = self.prompt_service.get_documents_by_domain(domain)
            for doc in docs:
                clauses = self.prompt_service.get_document_clauses(domain, doc)
                for clause in clauses:
                    self.metadata.append(
                        {
                            'domain': domain,
                            'doc_type': doc,
                            'clause_id': clause.get('ClauseID'),
                            'title': clause.get('ClauseTitle', ''),
                            'text': clause.get('ClauseText', ''),
                            'is_mandatory': clause.get('IsMandatory'),
                        }
                    )
        self.initialized = True
        print(f'Keyword-search metadata prepared with {len(self.metadata)} clauses.')

    def _keyword_search(self, query: str, k: int) -> List[Dict]:
        q_terms = set(re.findall(r'\w+', query.lower()))
        scored = []
        for item in self.metadata:
            hay = f"{item.get('title', '')} {item.get('text', '')}".lower()
            h_terms = set(re.findall(r'\w+', hay))
            if not h_terms:
                continue
            overlap = len(q_terms.intersection(h_terms))
            if overlap > 0:
                res = item.copy()
                res['score'] = float(overlap)
                scored.append(res)
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:k]

    def search_similar_clauses(self, query: str, k: int = 3) -> List[Dict]:
        if not self.initialized:
            return []
        if not self.vector_enabled or self.index is None or self.model is None or np is None:
            return self._keyword_search(query, k)

        query_vec = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_vec), k)
        results = []
        for i in range(k):
            idx = indices[0][i]
            if idx < len(self.metadata):
                res = self.metadata[idx].copy()
                res['score'] = float(distances[0][i])
                results.append(res)
        return results