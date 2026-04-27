import pandas as pd
import json
from pathlib import Path

# Data Structure: 
# Domain | DocumentType | ClauseID | ClauseTitle | ClauseText | IsMandatory | Variables (JSON) | CanRewrite

def create_clause(domain, doc_type, cid, title, text, vars=[], mandatory=True, rewrite=False):
    return {
        "Domain": domain,
        "DocumentType": doc_type,
        "ClauseID": cid,
        "ClauseTitle": title,
        "ClauseText": text.strip(),
        "IsMandatory": mandatory,
        "Variables": json.dumps(vars),
        "CanRewrite": rewrite
    }

# 1. FAMILY LAW
family_clauses = [
    create_clause("FamilyLaw", "Divorce Petition", 1.0, "Header", "IN THE FAMILY COURT OF {{ court_city }}\nPETITION NO. ______ OF {{ year }}"),
    create_clause("FamilyLaw", "Divorce Petition", 1.1, "Parties", "BETWEEN:\n{{ petitioner_name }}\n(Residing at {{ petitioner_address }}) ... Petitioner\n\nAND\n\n{{ respondent_name }}\n(Residing at {{ respondent_address }}) ... Respondent", ["petitioner_name", "petitioner_address", "respondent_name", "respondent_address"]),
    create_clause("FamilyLaw", "Divorce Petition", 1.2, "Subject", "SUBJECT: PETITION FOR DIVORCE UNDER SECTION 13 OF THE HINDU MARRIAGE ACT, 1955."),
    create_clause("FamilyLaw", "Divorce Petition", 2.1, "Marriage Details", "1. That the marriage between the Petitioner and the Respondent was solemnized on {{ marriage_date }} at {{ marriage_place }} according to Hindu rites and ceremonies.", ["marriage_date", "marriage_place"]),
    create_clause("FamilyLaw", "Divorce Petition", 2.2, "Cohabitation", "2. That the parties last resided together at {{ last_resided_address }}.", ["last_resided_address"]),
    create_clause("FamilyLaw", "Divorce Petition", 2.3, "Status of Children", "3. That there are {{ children_count }} children born out of the wedlock: {{ children_details }}.", ["children_count", "children_details"], mandatory=True, rewrite=True),
    create_clause("FamilyLaw", "Divorce Petition", 2.4, "Grounds - Cruelty", "4. That the Respondent has treated the Petitioner with cruelty as detailed below:\n{{ cruelty_details }}", ["cruelty_details"], mandatory=True, rewrite=True),
    create_clause("FamilyLaw", "Divorce Petition", 2.5, "Grounds - Desertion", "5. That the Respondent has deserted the Petitioner for a continuous period of not less than two years immediately preceding the presentation of the petition.", [], mandatory=False),
    create_clause("FamilyLaw", "Divorce Petition", 2.6, "No Collusion", "6. That there is no collusion between the Petitioner and the Respondent in filing this present petition."),
    create_clause("FamilyLaw", "Divorce Petition", 2.7, "Jurisdiction", "7. That the parties reside within the local limits of this Hon'ble Court, and hence this Hon'ble Court has jurisdiction to try and entertain this petition."),
    create_clause("FamilyLaw", "Divorce Petition", 3.0, "Prayer", "PRAYER:\nThe Petitioner therefore prays that:\na) A decree of divorce be granted dissolving the marriage;\nb) Custody of children be granted to Petitioner;\nc) Such other relief as this Hon'ble Court deems fit."),
    create_clause("FamilyLaw", "Divorce Petition", 4.0, "Verification", "VERIFICATION\nI, {{ petitioner_name }}, do hereby verify that the contents of paras 1 to 7 are true to my personal knowledge.", ["petitioner_name"])
]

# 2. CONTRACT LAW
contract_clauses = [
    create_clause("ContractLaw", "Non-Disclosure Agreement (NDA)", 1.0, "Title", "NON-DISCLOSURE AGREEMENT\n\nThis Agreement is entered into on {{ effective_date }}.", ["effective_date"]),
    create_clause("ContractLaw", "Non-Disclosure Agreement (NDA)", 1.1, "Parties", "BETWEEN:\n\n1. {{ disclosing_party }} (the \"Disclosing Party\")\nAND\n2. {{ receiving_party }} (the \"Receiving Party\").", ["disclosing_party", "receiving_party"]),
    create_clause("ContractLaw", "Non-Disclosure Agreement (NDA)", 1.2, "Recitals", "WHEREAS, the Disclosing Party possesses certain confidential information relating to {{ purpose }}; and\nWHEREAS, the Receiving Party desires to receive such information for the sole purpose of evaluating a potential business relationship.", ["purpose"]),
    create_clause("ContractLaw", "Non-Disclosure Agreement (NDA)", 2.1, "Definition", "1. DEFINITION OF CONFIDENTIAL INFORMATION\n\"Confidential Information\" shall mean any and all information disclosed by Disclosing Party, including but not limited to trade secrets, technical data, and customer lists."),
    create_clause("ContractLaw", "Non-Disclosure Agreement (NDA)", 2.2, "Exclusions", "2. EXCLUSIONS\nConfidential Information shall not include information that:\n(a) is already known to the Receiving Party;\n(b) becomes publicly known through no wrongful act of the Receiving Party.", [], mandatory=True),
    create_clause("ContractLaw", "Non-Disclosure Agreement (NDA)", 3.1, "Obligations", "3. OBLIGATIONS OF RECEIVING PARTY\nThe Receiving Party agrees to hold all Confidential Information in strict confidence and shall not disclose it to any third party without prior written consent.", [], mandatory=True, rewrite=True),
    create_clause("ContractLaw", "Non-Disclosure Agreement (NDA)", 4.1, "Term", "4. TERM\nThis Agreement shall remain in effect for a period of {{ term_years }} years from the Effective Date.", ["term_years"]),
    create_clause("ContractLaw", "Non-Disclosure Agreement (NDA)", 5.1, "Return of Materials", "5. RETURN OF MATERIALS\nUpon termination, the Receiving Party shall promptly return or destroy all copies of Confidential Information."),
    create_clause("ContractLaw", "Non-Disclosure Agreement (NDA)", 6.1, "Governing Law", "6. GOVERNING LAW\nThis Agreement shall be governed by the laws of {{ jurisdiction }}.", ["jurisdiction"]),
    create_clause("ContractLaw", "Non-Disclosure Agreement (NDA)", 7.1, "Signatures", "IN WITNESS WHEREOF, the parties have executed this Agreement.\n\n___________________________\nDisclosing Party\n\n___________________________\nReceiving Party")
]

# 3. IPR LAW
ipr_clauses = [
    create_clause("IPRLaw", "Trademark Assignment", 1.0, "Title", "TRADEMARK ASSIGNMENT DEED\n\nThis Deed of Assignment is made on {{ date }}.", ["date"]),
    create_clause("IPRLaw", "Trademark Assignment", 1.1, "Parties", "BETWEEN:\n{{ assignor_name }} (hereinafter \"Assignor\")\nAND\n{{ assignee_name }} (hereinafter \"Assignee\")", ["assignor_name", "assignee_name"]),
    create_clause("IPRLaw", "Trademark Assignment", 2.1, "Recitals", "WHEREAS the Assignor is the registered proprietor of the trademark \"{{ trademark_name }}\" bearing Registration No. {{ reg_no }}.", ["trademark_name", "reg_no"]),
    create_clause("IPRLaw", "Trademark Assignment", 3.1, "Assignment", "1. ASSIGNMENT\nThe Assignor hereby irrevocably assigns, transfers, and conveys to the Assignee all rights, title, and interest in the said Trademark, including the goodwill associated therewith."),
    create_clause("IPRLaw", "Trademark Assignment", 3.2, "Consideration", "2. CONSIDERATION\nIn consideration of the sum of {{ amount }}, receipt of which is hereby acknowledged, the Assignor affects this transfer.", ["amount"]),
    create_clause("IPRLaw", "Trademark Assignment", 4.1, "Warranties", "3. WARRANTIES\nThe Assignor warrants that they have full power and authority to assign the Trademark and that it is free from any encumbrances.", [], mandatory=True, rewrite=True),
    create_clause("IPRLaw", "Trademark Assignment", 5.1, "Jurisdiction", "4. JURISDICTION\nDisputes arising from this deed shall be subject to the exclusive jurisdiction of the courts in {{ court_city }}.", ["court_city"]),
    create_clause("IPRLaw", "Trademark Assignment", 6.0, "Signatures", "Signed and Delivered by the within named Assignor and Assignee.")
]

# 4. REAL ESTATE LAW
real_estate_clauses = [
    create_clause("RealEstateLaw", "Lease Deed", 1.0, "Title", "LEASE DEED FOR RESIDENTIAL PROPERTY"),
    create_clause("RealEstateLaw", "Lease Deed", 1.1, "Date", "This Lease Deed is made on {{ date }} at {{ city }}.", ["date", "city"]),
    create_clause("RealEstateLaw", "Lease Deed", 1.2, "Parties", "BETWEEN:\n{{ landlord_name }} (\"Lessor\")\nAND\n{{ tenant_name }} (\"Lessee\")", ["landlord_name", "tenant_name"]),
    create_clause("RealEstateLaw", "Lease Deed", 2.1, "Demised Premises", "1. DEMISED PREMISES\nThe Lessor hereby lets to the Lessee the property located at: {{ property_address }}.", ["property_address"]),
    create_clause("RealEstateLaw", "Lease Deed", 3.1, "Term", "2. TERM\nThe lease shall be for a period of {{ lease_months }} months, commencing from {{ start_date }}.", ["lease_months", "start_date"]),
    create_clause("RealEstateLaw", "Lease Deed", 4.1, "Rent", "3. RENT\nThe Lessee shall pay a monthly rent of {{ rent_amount }} on or before the 5th of every month.", ["rent_amount"]),
    create_clause("RealEstateLaw", "Lease Deed", 4.2, "Security Deposit", "4. SECURITY DEPOSIT\nThe Lessee has paid an interest-free refundable security deposit of {{ deposit_amount }}.", ["deposit_amount"]),
    create_clause("RealEstateLaw", "Lease Deed", 5.1, "Termination", "5. TERMINATION\nEither party may terminate this lease by giving {{ notice_period }} months' notice in writing.", ["notice_period"], mandatory=True, rewrite=True),
    create_clause("RealEstateLaw", "Lease Deed", 6.1, "Signatures", "IN WITNESS WHEREOF, the parties have signed this Deed.")
]

# 5. CRIMINAL LAW
criminal_clauses = [
    create_clause("CriminalLaw", "Bail Application", 1.0, "Header", "IN THE COURT OF {{ court_name }}, {{ city }}\nBAIL APPLICATION NO. ______ OF {{ year }}", ["court_name", "city", "year"]),
    create_clause("CriminalLaw", "Bail Application", 1.1, "Cause Title", "STATE VS {{ accused_name }}\nFIR NO: {{ fir_no }}\nU/S: {{ sections }}\nP.S.: {{ police_station }}", ["accused_name", "fir_no", "sections", "police_station"]),
    create_clause("CriminalLaw", "Bail Application", 2.1, "Body", "APPLICATION UNDER SECTION 437/439 OF THE CODE OF CRIMINAL PROCEDURE, 1973 FOR GRANT OF REGULAR BAIL"),
    create_clause("CriminalLaw", "Bail Application", 3.1, "Grounds - Innocence", "1. That the Applicant/Accused is a peace-loving citizen and has been falsely implicated in the present case due to animosity.", [], mandatory=True, rewrite=True),
    create_clause("CriminalLaw", "Bail Application", 3.2, "Grounds - Custody", "2. That the Applicant was arrested on {{ arrest_date }} and has been in judicial custody since then.", ["arrest_date"]),
    create_clause("CriminalLaw", "Bail Application", 3.3, "Grounds - Investigation", "3. That the investigation is complete and the charge-sheet has been filed. No useful purpose will be served by keeping the Applicant behind bars."),
    create_clause("CriminalLaw", "Bail Application", 3.4, "Roots in Society", "4. That the Applicant has deep roots in society and there is no flight risk."),
    create_clause("CriminalLaw", "Bail Application", 4.1, "Prayer", "PRAYER:\nIdeally, the Applicant prays that he be released on bail on such terms and conditions as this Hon'ble Court deems fit and proper.\n\nDate: {{ current_date }}\nPlace: {{ city }}", ["current_date", "city"]),
    create_clause("CriminalLaw", "Bail Application", 5.0, "Affidavit", "AFFIDAVIT SUPPORTING APPLICATION...")
]

# Output
output_dir = Path(__file__).parent / "prompts"
output_dir.mkdir(parents=True, exist_ok=True)

# Generate
pd.DataFrame(family_clauses).to_excel(output_dir / "FamilyLaw.xlsx", index=False)
pd.DataFrame(contract_clauses).to_excel(output_dir / "ContractLaw.xlsx", index=False)
pd.DataFrame(ipr_clauses).to_excel(output_dir / "IPRLaw.xlsx", index=False)
pd.DataFrame(real_estate_clauses).to_excel(output_dir / "RealEstateLaw.xlsx", index=False)
pd.DataFrame(criminal_clauses).to_excel(output_dir / "CriminalLaw.xlsx", index=False)

print("Comprehensive Clause-Based Excel files created for all 5 domains.")
