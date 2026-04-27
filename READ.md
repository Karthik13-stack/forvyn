<<<<<<< HEAD
# LexiLaw v2

## AI-Powered Legal Document Generator

LexiLaw v2 is an advanced AI-driven platform for generating, assembling, and managing legal documents. Built with FastAPI and integrated with Google's Gemini LLM, it leverages Retrieval-Augmented Generation (RAG) to create accurate, professional legal content.

## Core Features

###  AI-Powered Generation
- **Clause Rewriting**: Rewrite legal clauses based on user intent using Gemini 2.5 Flash
- **Document Assembly**: Automatically assemble full legal documents from modular clauses
- **RAG Integration**: Retrieve relevant legal knowledge from vector database for context-aware generation
- **Real-time Generation**: WebSocket-powered live document updates during AI processing

###  Document Management
- **Multi-format Export**: Generate professional PDFs and DOCX files with legal formatting (Times New Roman, justified text, hanging indents)
- **Document Versioning**: Track and manage multiple versions of generated documents
- **Prompt Management**: Load and organize legal clauses from Excel spreadsheets by domain and document type
- **Dynamic Forms**: Interactive frontend for configuring document parameters

###  Verification & Quality Assurance
- **Factual Checking**: Verify accuracy against legal context and citations
- **Consistency Validation**: Ensure document coherence and legal rule compliance
- **Confidence Scoring**: Rate AI-generated content reliability
- **Legal Rule Checking**: Validate against established legal frameworks

###  Technical Architecture
- **Vector Database**: FAISS-powered semantic search for legal knowledge retrieval
- **Embeddings**: Advanced text embeddings for similarity matching
- **Chunking**: Intelligent text segmentation for processing large legal documents
- **Model Routing**: Dynamic selection of AI models based on task complexity
- **Workflow Orchestration**: Modular AI pipelines for different legal tasks

###  API & Integration
- **RESTful API**: Comprehensive HTTP endpoints for document operations
- **WebSocket Support**: Real-time communication for live generation updates
- **Static Frontend**: User-friendly web interface for document creation
- **Extensible Services**: Modular service architecture for easy feature addition

###  Testing & Validation
- **Unit Tests**: Comprehensive test suite covering all major components
- **Mock Services**: Development mode with simulated AI responses
- **Validation Tools**: Automated checks for document structure and content

## Architecture Overview

```
LexiLaw v2/
├── backend/
│   ├── app/
│   │   ├── ai_core/          # AI processing modules
│   │   │   ├── chunking/     # Text chunking utilities
│   │   │   ├── embeddings/   # Embedding generation
│   │   │   ├── llm/          # Gemini AI client
│   │   │   ├── orchestrator/ # Model routing
│   │   │   ├── rag/          # Retrieval system
│   │   │   ├── reasoning/    # Prompt building
│   │   │   ├── vector/       # FAISS vector store
│   │   │   ├── verification/ # Quality checks
│   │   │   └── workflows/    # AI pipelines
│   │   ├── api/              # HTTP/WebSocket APIs
│   │   ├── services/         # Business logic
│   │   ├── static/           # Frontend assets
│   │   └── tests/            # Test suites
├── prompts/                  # Legal clause templates
└── generated_documents/      # Output storage
```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/lexilaw-v2.git
   cd lexilaw-v2
   ```

2. **Set up Python environment**
   ```bash
   python -m venv .venv
   .venv/scripts/activate  
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```

4. **Run the application**
   ```bash
   uvicorn backend.app.main:app --reload
   ```

## Usage

### Web Interface
1. Open `http://localhost:8000` in your browser
2. Select legal domain and document type
3. Fill in required parameters
4. Click "Generate Document" for AI-powered creation

### API Usage
```python
# Generate a document
response = requests.post("/api/document/generate", json={
    "domain": "corporate",
    "type": "nda",
    "parameters": {...}
})

# Rewrite a clause
response = requests.post("/api/clause/rewrite", json={
    "clause_text": "Original clause...",
    "intent": "Make more restrictive"
})
```

## API Endpoints

- `POST /api/clause/rewrite` - Rewrite legal clauses
- `POST /api/document/generate` - Generate full documents
- `POST /api/export/pdf` - Export to PDF format
- `POST /api/export/docx` - Export to DOCX format
- `WebSocket /ws/generate` - Real-time document generation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request



LexiLaw V2 - Codebase Reference
This document provides a detailed, file-by-file explanation of the entire project. It is designed to help you understand every single line of code.

📁 backend/app/main.py
Status: Core Entry Point

What it does: This is the "brain" initialization. It creates the FastAPI server (app = FastAPI(...)).
Key Features:
Loads environment variables (
.env
).
Connects all "Routes" (URL paths) so the frontend can talk to the backend.
lifespan
: A special function that runs once when the server starts to build the Vector Index (memory).
app.mount: Serves the frontend (HTML/JS) files so you can see them in the browser.
📁 backend/app/api/http/form_routes.py
Status: Form & Document API

What it does: Handles the "Get Metadata" and "Generate Document" requests.
API Endpoints:
GET /api/meta/domains: Returns list of legal domains (e.g., "Contract Law").
GET /api/meta/{domain}/documents: Returns document types for a domain.
GET /api/meta/{domain}/{type}/schema: RETURNS the form fields needed (e.g., "Rent Amount", "Landlord Name").
POST /api/generate: The Big Button. Takes your form answers -> Runs AI -> Returns the full document text.
📁 backend/app/api/http/clause_routes.py
Status: Editing API

What it does: Handles the "Rewrite Clause" feature.
API Endpoints:
POST /api/clause/rewrite: Receives { text: "...", intent: "strict" }. Returns { rewritten_text: "..." }.
Detail: It initializes 
ClauseRewriter
 lazily (only when needed).
📁 backend/app/api/http/export_routes.py
Status: Export API

What it does: Converts text to PDF or DOCX.
API Endpoints:
POST /api/export/pdf: Returns a downloadable PDF blob.
POST /api/export/docx: Returns a downloadable Word doc blob.
📁 backend/app/services/prompt_service.py
Status: Excel Loader (The Librarian)

What it does: Reads ALL 
.xlsx
 files in backend/prompts/.
Detail:
_load_all(): Loops through every Excel file.
get_aggregated_schema(): Smartly figures out what inputs are needed (like "Rent Amount") based on variables in the Excel columns.
📁 backend/app/services/export_service.py
Status: File Converter

What it does: The actual code that draws PDFs and writes Word docs.
Detail:
Uses fpdf for PDF generation.
Uses python-docx for Word generation.
📁 backend/app/ai_core/llm/gemini_client.py
Status: AI Connector

What it does: Connects to Google Gemini.
Detail:
Finds the API Key (we fixed the path here!).
rewrite_clause(): Sends a specific prompt to Gemini to rewrite text.
generate_content(): The raw function to get text from Google.
📁 backend/app/ai_core/rag/vector_service.py
Status: The Semantic Brain (Memory)

What it does: Turns text into numbers (vectors) to find similar legal clauses.
Detail:
_build_index(): Reads every clause from Excel -> Calculates Vector -> Saves to FAISS.
search_similar_clauses(): Finds the best matching legal clauses for the AI to use as reference.
📁 backend/app/ai_core/workflows/document_generation.py
Status: Generation Logic

What it does: The "Recipe" for making a document.
Workflow:
Get standard clauses from Excel.
Find similar clauses using Vector Search (RAG).
Combine them into a mega-prompt for the AI.
Ask AI to write the final doc.
📁 backend/app/static/app.js
Status: The Frontend Logic

What it does: Controls the webpage behavior.
Key Functions:
loadDomains(): Fills the dropdowns.
generateBtn.addEventListener: Sends the form data to the backend.
btnConfirmRewrite: Sends the selected text to the Rewrite API.
Refreshes the UI (Spinners, error messages).
📁 backend/app/static/index.html
Status: The Webpage

What it does: The actual HTML structure you see.
Detail: Contains the sidebar, the form container, and the big text editor (<textarea id="editor">).



Project Status & Roadmap
✅ Completed (What Works Now)
The "Core Engine" is fully functional.

RAG Architecture: The system successfully reads Excel files, indexes them, and retrieves relevant clauses using Vector Search.
AI Document Generation: You can select a domain (Contract, Family, etc.), fill a dynamic form, and generate a full legal document.
Live Clause Rewriting: You can highlight text, specify an intent (e.g., "make strict"), and the AI instantly rewrites it.
Export: PDF and Word (DOCX) export is working.
Dynamic Forms: The system automatically builds forms based on the variables found in your Excel templates.
🚀 To-Do (Your Roadmap)
These are the features you mentioned adding next:

1. User System (Sign Up / Login)
Goal: Secure access and save user history.
Needs: Database (SQLite/PostgreSQL) to store users + Authentication API (JWT).
2. Legal Chatbot (The "Concierge")
Goal: A chat window where users describe their problem ("I need to evict a tenant"), and the bot redirects them to the correct form.
Needs: New API endpoint /api/chat + Vector Search on "Document Descriptions" to find the right template.
3. Lawyer-Grade Accuracy (RAG Upgrade)
Goal: Ensure 100% precision for real lawyers.
Needs: Hybrid Search (BM25) + Reranking (Cross-Encoder) as discussed.
4. Advanced Frontend
Goal: A "Real Website" look.
Needs: React/Next.js (optional but recommended for complex apps) or enhanced HTML/CSS.


saivinay2408@gmail.com 

features to be added-
1-ipc to bns section conversion is to be changed(research)**
2-accuracy check--if clause not needed,give a red flag since format changes so highlight that in the doc generated
3-change rewrite clauses to indian languages which are popular
4-suggest alternatives (accuracy checks)
5-chatbot assistant 
=======
# lexi_law_dhruvi
old folder (not merged)
>>>>>>> 4fbfbd196eae34ecc7bb25caa8852d8f8082c68e
