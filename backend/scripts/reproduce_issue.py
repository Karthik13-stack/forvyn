
import requests
import json

url = "http://127.0.0.1:8000/api/generate"

payload = {
    "domain": "ContractLaw",
    "doc_type": "NDA",
    "form_data": {
        "Effective Date": "01-02-2006",
        "Disclosing Party": "huhud",
        "Receiving Party": "zljxnsl",
        "Purpose": "hkjk",
        "Term Years": "0",
        "Jurisdiction": "wmnm"
    }
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print("Response Content:")
    print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
