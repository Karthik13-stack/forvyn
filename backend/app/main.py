import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.http.chat_routes import router as chat_router
from app.api.http.clause_routes import router as clause_router
from app.api.http.export_routes import router as export_router
from app.api.http.form_routes import router as form_router
from app.api.http.risk_routes import router as risk_router
from app.api.http.sources_routes import router as source_router
from app.api.http.legal_routes import router as legal_router
from app.api.http.chatbot_routes import router as chatbot_router
from app.api.http.drafting_routes import router as drafting_router
from app.api.http.payment_routes import router as payment_router

APP_DIR = Path(__file__).parent
FRONTEND_DIR = APP_DIR.parent.parent / 'frontend'

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Startup: Initializing AI Core Services...')
    from app.core.dependencies import init_services
    init_services()
    yield
    print('Shutdown: Cleanup complete')
app = FastAPI(lifespan=lifespan)
_allow_unsafe_eval = os.environ.get('ALLOW_UNSAFE_EVAL', 'false').lower() in ('1', 'true', 'yes')
if _allow_unsafe_eval:

    @app.middleware('http')
    async def _add_dev_csp_header(request, call_next):
        resp = await call_next(request)
        resp.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline';"
        return resp
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(chat_router, prefix='/api')
app.include_router(clause_router, prefix='/api')
app.include_router(export_router, prefix='/api')
app.include_router(form_router, prefix='/api')
app.include_router(risk_router, prefix='/api')
app.include_router(source_router, prefix='/api')
app.include_router(legal_router, prefix='/api')
app.include_router(chatbot_router, prefix='/api')
app.include_router(drafting_router, prefix='/api')
app.include_router(payment_router, prefix='/api')
app.mount('/static', StaticFiles(directory=FRONTEND_DIR), name='static')

@app.get('/')
def serve_index():
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / 'dashboard.html')

@app.get('/draft')
def serve_draft():
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / 'draft.html')

@app.get('/mapping')
def serve_mapping():
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / 'mapping.html')

@app.get('/summarize')
def serve_summarize():
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / 'summarize.html')

@app.get('/explain')
def serve_explain():
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / 'explain.html')

@app.get('/analyze-risks')
def serve_analyze_risks():
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / 'analyze-risks.html')

@app.get('/sources')
def serve_sources():
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / 'sources.html')

@app.get('/billing')
def serve_billing():
    from fastapi.responses import FileResponse
    return FileResponse(FRONTEND_DIR / 'payment.html')

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(content=b'', media_type='image/x-icon')
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')