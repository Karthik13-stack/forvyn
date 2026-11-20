PROJECT:
* Name: Forvyn (LexiLaw v2)
* One-line purpose: AI-powered legal document generation and clause rewriting using a strict, hard-gated RAG pipeline.
* Tech stack: FastAPI (Python), Google Gemini LLM, FAISS (Vector DB), SentenceTransformers, Vanilla JS/HTML frontend.

FLOW:
* User Query / Clause → Clause Chunking → Embedding Generation → Vector Store (FAISS) Retriever → [HARD GATE: IF chunks == 0 THEN Block] → Prompt Builder → Gemini LLM → Formatted Response / File Export.

RUN:
* Setup steps:
  1. python -m venv .venv
  2. .venv\Scripts\activate  (Windows) or source .venv/bin/activate (Mac/Linux)
  3. pip install -r requirements.txt
* Commands to run the project:
  python run_server.py
  (Alternatively: cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000)
  (Docker: docker-compose up --build -d)
* Required environment variables:
  GEMINI_API_KEY="your-gemini-api-key"

STRUCTURE:
* /backend/app/ai_core → AI processing modules (chunking, embeddings, LLM client, orchestration, FAISS vector store).
* /backend/app/api → HTTP and WebSocket API route definitions.
* /backend/app/core → Core configuration and startup logic.
* /backend/app/schemas → Pydantic models for data validation and API payloads.
* /backend/app/services → Core business logic (Excel parsing, prompt handling, PDF/DOCX export).
* /frontend → Frontend vanilla HTML, CSS, and JS files served dynamically by FastAPI.
* /backend/app/storage → Output storage location for generated legal documents and vector DB.
* /backend/app/tests → Pytest unit test suites for API validation and strict RAG behavior.
* /backend/app/utils → Helper utility functions for generic tasks.

RULES:
* The Strict Retrieval Hard Gate must NEVER be bypassed; if FAISS returns 0 context, the LLM is explicitly not invoked.
* All AI requests must use retrieved legal context directly; the LLM must not access general knowledge or hallucinate.
* Exception: The drafting wizard question-generation endpoint (`/api/drafting/questions`) intentionally uses Gemini without RAG context, since it generates intake questions, not legal content.
* Maintain clause-level granularity when formatting templates; do not index monolithic documents into FAISS.
* Frontend must be served directly via FastAPI; no separate Node.js server should be required in local dev.
* The 4-step drafting wizard UI lives in `frontend/draft.html` + `frontend/draft-app.js`, with backend routes in `backend/app/api/http/drafting_routes.py`.

CONCEPTS:
* Hard Gate: An unconditional orchestration layer validation that blocks Gemini network requests if the retriever returns an empty match, preventing "invented" legal advice.
* Template Grounding: Excel spreadsheets in the prompts folder are the primary source of truth, loaded into the FAISS index at startup.
* Chunking Constraint: Splitting legal contracts into numbered clauses before embedding to ensure semantic closeness and minimize token windows.

TASKS:
* Add new API:
  1. Define Pydantic payload models in `backend/app/schemas/`
  2. Implement business logic inside a corresponding file in `backend/app/services/`
  3. Create route handlers in `backend/app/api/` mapping the request model to the service
  4. Include the router instance in `backend/app/main.py`
* Add new DB model:
  1. Add data structure or database schema definition (e.g., Pydantic model for metadata)
  2. Update data loader in `backend/app/services/prompt_service.py` if fetching from Excel
  3. Update `vector_service.py` to index new text components if making them searchable
* Modify existing feature:
  1. Locate route in `backend/app/api/`
  2. Traverse to `backend/app/ai_core/` (if it modifies generation) or `backend/app/services/`
  3. Keep modifications inside the Hard Gate constraints
  4. Run Pytest suite in `backend/app/tests/` to verify no hallucination regressions

WARNINGS:
* Removing the Hard Gate from `RAGGenerationFlow` or `ClauseRegenerationFlow` will break strict legal safety guarantees.
* Modifying Excel templates without restarting the server will cause state mismatches; the vector index builds at runtime.
* Embedding model mismatch between what generated the FAISS index and the current `all-MiniLM-L6-v2` will break search retrieval entirely.
