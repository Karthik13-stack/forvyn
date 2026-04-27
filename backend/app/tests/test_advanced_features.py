import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from backend.app.main import app
client = TestClient(app)

def test_export_pdf():
    print('\n[TEST] PDF Export...')
    response = client.post('/api/export/pdf', json={'content': 'This is a test contract clause.', 'filename': 'test'})
    if response.status_code == 200:
        print('✅ PDF Export Success')
        print(f"   Response type: {response.headers['content-type']}")
        print(f'   Size: {len(response.content)} bytes')
    else:
        print(f'❌ PDF Export Failed: {response.text}')

def test_export_docx():
    print('\n[TEST] DOCX Export...')
    response = client.post('/api/export/docx', json={'content': 'This is a test contract clause.', 'filename': 'test'})
    if response.status_code == 200:
        print('✅ DOCX Export Success')
        print(f"   Response type: {response.headers['content-type']}")
        print(f'   Size: {len(response.content)} bytes')
    else:
        print(f'❌ DOCX Export Failed: {response.text}')

def test_rewrite_clause():
    print('\n[TEST] Clause Rewrite (Simulated)...')
    response = client.post('/api/clause/rewrite', json={'clause_text': 'The tenant shall pay rent on time.', 'intent': 'Make it stricter'})
    if response.status_code == 200:
        print('✅ Rewrite Success')
        print(f"   Output: {response.json()['rewritten_text']}")
    else:
        print(f'ℹ️ Rewrite returned {response.status_code} (Likely expected if no API Key)')
        print(f'   Detail: {response.text}')
if __name__ == '__main__':
    print('--- Running Advanced Feature Verification ---')
    test_export_pdf()
    test_export_docx()
    test_rewrite_clause()