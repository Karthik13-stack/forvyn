import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[3]))
from fastapi.testclient import TestClient
from backend.app.main import app
client = TestClient(app)

def test_get_domains():
    response = client.get('/api/meta/domains')
    assert response.status_code == 200
    domains = response.json()
    assert 'FamilyLaw' in domains
    assert 'ContractLaw' in domains

def test_get_documents():
    response = client.get('/api/meta/FamilyLaw/documents')
    assert response.status_code == 200
    docs = response.json()
    assert 'Divorce Petition' in docs

def test_get_schema():
    response = client.get('/api/meta/FamilyLaw/Divorce Petition/schema')
    assert response.status_code == 200
    schema = response.json()
    assert isinstance(schema, list)
    keys = [field['key'] for field in schema]
    assert 'petitioner_name' in keys
    assert 'marriage_date' in keys

def test_generate_document():
    payload = {'domain': 'FamilyLaw', 'doc_type': 'Divorce Petition', 'form_data': {'court_city': 'Mumbai', 'year': 2024, 'petitioner_name': 'Jane Doe', 'petitioner_address': '123 Lane', 'respondent_name': 'John Doe', 'respondent_address': '456 Street', 'marriage_date': '2010-01-01', 'marriage_place': 'Mumbai', 'last_resided_address': 'Mumbai', 'cruelty_details': 'N/A', 'current_date': '2024-05-01'}}
    response = client.post('/api/generate', json=payload)
    assert response.status_code == 200
    content = response.json()['content']
    assert 'IN THE FAMILY COURT OF Mumbai' in content
if __name__ == '__main__':
    try:
        test_get_domains()
        print('test_get_domains PASSED')
        test_get_documents()
        print('test_get_documents PASSED')
        test_get_schema()
        print('test_get_schema PASSED')
        test_generate_document()
        print('test_generate_document PASSED')
    except Exception as e:
        print(f'FAILED: {e}')
        import traceback
        traceback.print_exc()