import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services.export_service import ExportService

def test_export():
    service = ExportService()

    # Simulated output from AssemblyService (Legal Markdown)
    sample_content = """# NON-DISCLOSURE AGREEMENT

## 1. DEFINITIONS

**1.1** **Confidential Information**. "Confidential Information" means all non-public, confidential or proprietary information disclosed by one party to the other party, whether orally or in writing.

**1.1.1** **Exclusions**. Confidential Information shall not include information that: (a) is now or subsequently becomes generally available to the public; (b) the Receiving Party can demonstrate was rightfully in its possession prior to disclosure.

## 2. OBLIGATIONS

**2.1** **Non-Use and Non-Disclosure**. The Receiving Party shall not use the Confidential Information for any purpose other than evaluating a potential business relationship.

**2.2** **Standard of Care**. The Receiving Party shall protect the Confidential Information by using the same degree of care, but no less than a reasonable degree of care, to prevent the unauthorized use or disclosure specific information."""

    print("Generating PDF...")
    pdf_bytes = service.export_pdf(sample_content)
    with open("test_lexilaw_output.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"PDF Generated: {len(pdf_bytes)} bytes")

    print("Generating DOCX...")
    docx_bytes = service.export_docx(sample_content)
    with open("test_lexilaw_output.docx", "wb") as f:
        f.write(docx_bytes)
    print(f"DOCX Generated: {len(docx_bytes)} bytes")

    print("\nSUCCESS: Validation files created in project root.")
    print(" - test_lexilaw_output.pdf")
    print(" - test_lexilaw_output.docx")

if __name__ == "__main__":
    test_export()
