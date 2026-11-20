"""
Judgement Summarizer Service
Provides structured summarization of court judgements with high accuracy.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re
import uuid
import logging

from app.ai_core.llm.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class SummaryType(str, Enum):
    """Types of judgment summaries."""
    BRIEF = "brief"          # Quick 1-2 paragraph summary
    STANDARD = "standard"    # Standard structured summary
    DETAILED = "detailed"    # Comprehensive analysis
    HEADNOTE = "headnote"    # Legal headnote format


class JurisdictionType(str, Enum):
    """Court jurisdiction types."""
    SUPREME_COURT = "supreme_court"
    HIGH_COURT = "high_court"
    DISTRICT_COURT = "district_court"
    TRIBUNAL = "tribunal"
    OTHER = "other"


@dataclass
class JudgementMetadata:
    """Extracted metadata from the judgement."""
    case_number: Optional[str] = None
    case_title: Optional[str] = None
    court: Optional[str] = None
    jurisdiction: Optional[JurisdictionType] = None
    judges: List[str] = field(default_factory=list)
    date_of_judgement: Optional[str] = None
    petitioner: Optional[str] = None
    respondent: Optional[str] = None
    subject_matter: Optional[str] = None
    acts_referred: List[str] = field(default_factory=list)
    sections_cited: List[str] = field(default_factory=list)
    cases_cited: List[str] = field(default_factory=list)


@dataclass
class JudgementSummary:
    """Complete judgement summary result."""
    id: str
    summary_type: SummaryType
    metadata: JudgementMetadata
    
    # Core summary components
    brief_summary: str                      # 2-3 line summary
    facts_of_case: str                      # Facts as stated
    issues_framed: List[str]                # Legal issues
    arguments_petitioner: List[str]         # Petitioner's arguments
    arguments_respondent: List[str]         # Respondent's arguments
    court_observations: List[str]           # Key observations
    ratio_decidendi: str                    # Core legal principle
    holding: str                            # Court's decision
    orders_passed: List[str]                # Specific orders
    
    # Optional detailed components
    obiter_dicta: Optional[List[str]] = None  # Non-binding remarks
    dissenting_opinion: Optional[str] = None   # If any dissent
    precedent_analysis: Optional[str] = None   # How precedents were applied
    
    # Analysis
    key_takeaways: List[str] = field(default_factory=list)
    practical_implications: Optional[str] = None
    confidence_score: float = 0.0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    original_length: int = 0
    summary_length: int = 0


class JudgementSummarizer:
    """
    Service for summarizing court judgements with legal accuracy.
    Uses advanced chain-of-thought reasoning for better extraction.
    """
    
    SUMMARY_PROMPTS = {
        SummaryType.BRIEF: """You are a senior legal expert at the Supreme Court of India specializing in legal research and case analysis.

<TASK>
Provide a precise BRIEF summary (2-3 paragraphs max) of the following court judgement.
</TASK>

<THINKING_PROCESS>
Before summarizing, mentally analyze:
1. Identify the court and its jurisdiction level
2. Extract party names (Petitioner vs Respondent)
3. Find the core legal question/issue
4. Locate the court's final decision (allow/dismiss/remand)
5. Identify the key legal principle applied
</THINKING_PROCESS>

<OUTPUT_FORMAT>
Your summary MUST include:
- Case identification (parties, court, type of case)
- Central legal issue in one sentence
- Court's decision with brief reasoning
- Key legal principle or precedent applied
</OUTPUT_FORMAT>

JUDGEMENT TEXT:
{judgement_text}

BRIEF SUMMARY:""",

        SummaryType.STANDARD: """You are a senior legal expert at the Supreme Court of India with 20 years of experience in legal research and case analysis.

<TASK>
Analyze and summarize the following court judgement with precision and legal accuracy.
</TASK>

<CHAIN_OF_THOUGHT_ANALYSIS>
Follow this systematic analysis process:

STEP 1 - IDENTIFY METADATA:
- Search for "Case No.", "Writ Petition", "Civil Appeal", "Criminal Appeal" patterns
- Look for "CORAM", "Before", "Hon'ble" to find judges
- Find "Petitioner/Appellant" vs "Respondent" names
- Locate date patterns (DD/MM/YYYY or Month DD, YYYY)

STEP 2 - EXTRACT LEGAL FRAMEWORK:
- Identify ALL Acts mentioned (Constitution, IPC/BNS, CPC, etc.)
- List ALL section numbers cited
- Note case laws referenced with citations (AIR, SCC, SCR)

STEP 3 - ANALYZE SUBSTANCE:
- Facts: What happened? What led to this litigation?
- Issues: What legal questions did the court frame?
- Arguments: What did each party argue?
- Court's Analysis: How did the court reason?
- Decision: What was the final order?

STEP 4 - EXTRACT LEGAL PRINCIPLES:
- Ratio Decidendi: The binding legal principle
- Obiter Dicta: Additional observations (not binding)
</CHAIN_OF_THOUGHT_ANALYSIS>

<OUTPUT_JSON_FORMAT>
Your response MUST be in this exact JSON format:
{{
    "metadata": {{
        "case_number": "Full case number as mentioned",
        "case_title": "Petitioner vs Respondent",
        "court": "Full court name",
        "judges": ["Justice Name 1", "Justice Name 2"],
        "date_of_judgement": "Date as mentioned in judgement",
        "petitioner": "Petitioner/Appellant name",
        "respondent": "Respondent name",
        "subject_matter": "Primary area of law (e.g., Constitutional Law, Criminal Law)",
        "acts_referred": ["Full Act name with year"],
        "sections_cited": ["Section X of Act Y"],
        "cases_cited": ["Case Name - Citation"]
    }},
    "brief_summary": "A compelling 2-3 sentence executive summary capturing the essence",
    "facts_of_case": "Comprehensive chronological statement of facts (include all key events, dates, and parties' actions)",
    "issues_framed": [
        "Issue 1: [Full legal question as framed by court or inferred]",
        "Issue 2: [Second issue if applicable]"
    ],
    "arguments_petitioner": [
        "[Key argument 1 with legal basis]",
        "[Key argument 2 with case law cited if any]"
    ],
    "arguments_respondent": [
        "[Counter-argument 1 with legal basis]",
        "[Counter-argument 2 with case law cited if any]"
    ],
    "court_observations": [
        "[Critical observation 1 by the court]",
        "[Critical observation 2 - analysis of law/facts]"
    ],
    "ratio_decidendi": "The core legal principle/rule that formed the basis of decision (this is the precedent)",
    "holding": "The court's final decision with clear outcome (allowed/dismissed/modified with details)",
    "orders_passed": [
        "[Specific direction/order 1]",
        "[Specific direction/order 2]"
    ],
    "key_takeaways": [
        "[Practical takeaway 1 for legal practitioners]",
        "[Practical takeaway 2]",
        "[Practical takeaway 3]"
    ]
}}
</OUTPUT_JSON_FORMAT>

<ACCURACY_REQUIREMENTS>
- Do NOT invent or assume facts not present in the text
- Use "null" for fields where information is not available
- Quote exact statutory provisions and case citations
- Maintain legal precision in terminology
</ACCURACY_REQUIREMENTS>

JUDGEMENT TEXT:
{judgement_text}

JSON RESPONSE:""",

        SummaryType.DETAILED: """You are an eminent jurist and legal scholar at the Supreme Court of India with expertise in comprehensive legal analysis.

<TASK>
Provide an EXHAUSTIVE legal analysis of the following court judgement suitable for legal research and academic reference.
</TASK>

<COMPREHENSIVE_ANALYSIS_FRAMEWORK>

PHASE 1 - PROCEDURAL HISTORY:
- Original filing court and case type
- Appeals/revisions if any
- Current court and nature of proceedings

PHASE 2 - FACTUAL MATRIX:
- Background facts in chronological order
- Disputed facts vs admitted facts
- Documentary evidence referred

PHASE 3 - LEGAL FRAMEWORK:
- Constitutional provisions involved
- Statutory framework (Acts, Sections, Rules)
- Judicial precedents cited by parties
- Precedents cited by court

PHASE 4 - ISSUE ANALYSIS:
- Issues as framed by lower court (if applicable)
- Issues as framed by this court
- Sub-issues within each main issue

PHASE 5 - ARGUMENTATION:
- Detailed petitioner arguments with legal support
- Detailed respondent arguments with legal support
- Intervener arguments if any

PHASE 6 - COURT'S REASONING:
- Analysis of each issue
- Treatment of precedents (followed/distinguished/overruled)
- Statutory interpretation principles applied
- Constitutional interpretation if applicable

PHASE 7 - DECISION ANALYSIS:
- Ratio decidendi (binding principle)
- Obiter dicta (persuasive observations)
- Relief granted
- Directions issued
- Costs

PHASE 8 - DISSENT ANALYSIS (if applicable):
- Dissenting judge(s)
- Points of disagreement
- Alternative reasoning

</COMPREHENSIVE_ANALYSIS_FRAMEWORK>

<OUTPUT_JSON_FORMAT>
{{
    "metadata": {{
        "case_number": "Complete case number",
        "case_title": "Full case title",
        "court": "Court name with bench composition",
        "jurisdiction": "supreme_court/high_court/district_court/tribunal/other",
        "judges": ["Full designation of each judge"],
        "date_of_judgement": "Full date",
        "petitioner": "Complete petitioner description",
        "respondent": "Complete respondent description",
        "subject_matter": "Primary and secondary areas of law",
        "acts_referred": ["All Acts with sections mentioned"],
        "sections_cited": ["Every section with Act name"],
        "cases_cited": ["All case laws with full citations"]
    }},
    "brief_summary": "Executive summary (3-4 sentences)",
    "procedural_history": "Complete procedural history from original filing",
    "facts_of_case": "Exhaustive chronological facts with all relevant details",
    "issues_framed": [
        "Detailed Issue 1 with legal context",
        "Detailed Issue 2 with legal context"
    ],
    "arguments_petitioner": [
        "Comprehensive argument 1 with case law support",
        "Comprehensive argument 2 with statutory basis"
    ],
    "arguments_respondent": [
        "Comprehensive counter-argument 1",
        "Comprehensive counter-argument 2"
    ],
    "court_observations": [
        "Detailed observation 1 with court's reasoning",
        "Detailed observation 2 with legal analysis",
        "Detailed observation 3"
    ],
    "ratio_decidendi": "The binding legal principle with full explanation of how it was derived",
    "holding": "Comprehensive final decision with all aspects of relief/dismissal",
    "orders_passed": [
        "Detailed order 1 with timeline if any",
        "Detailed order 2 with compliance requirements"
    ],
    "obiter_dicta": [
        "Non-binding observation 1",
        "Non-binding observation 2"
    ],
    "dissenting_opinion": "Complete summary of dissent with reasoning (null if unanimous)",
    "precedent_analysis": "How cited cases were applied - followed, distinguished, or overruled with reasoning",
    "key_takeaways": [
        "Major legal takeaway 1",
        "Major legal takeaway 2",
        "Procedural takeaway 1",
        "Practice pointer 1"
    ],
    "practical_implications": "Real-world applicability, impact on future cases, changes in legal landscape"
}}
</OUTPUT_JSON_FORMAT>

JUDGEMENT TEXT:
{judgement_text}

JSON RESPONSE:""",

        SummaryType.HEADNOTE: """You are a legal editor preparing HEADNOTES for publication in a Law Reporter (like SCC, AIR).

<TASK>
Create a professional HEADNOTE in standard legal publication format.
</TASK>

<HEADNOTE_STRUCTURE>
A proper headnote must contain:
1. CATCHWORDS - Key legal terms and concepts (alphabetical)
2. ACTS & SECTIONS - All legislation referenced
3. HELD - What the court decided (numbered points)
4. RATIO - The core legal principle in one statement
5. CASES REFERRED - All precedents with how they were treated
</HEADNOTE_STRUCTURE>

<OUTPUT_JSON_FORMAT>
{{
    "metadata": {{
        "case_number": "Complete citation",
        "case_title": "Reporter-style title",
        "court": "Court name",
        "date_of_judgement": "Date",
        "judges": ["Judges list"],
        "subject_matter": "Area of law"
    }},
    "headnote": {{
        "catchwords": ["KEYWORD1", "KEYWORD2", "KEYWORD3"],
        "acts_sections": ["Act Name, Year - Ss. X, Y, Z"],
        "held": "Numbered points of what was held:\n1. [First point]\n2. [Second point]\n3. [Third point]",
        "ratio": "Single statement of the ratio decidendi",
        "cases_referred": [
            "Case Name - Citation - [Followed/Distinguished/Overruled]"
        ]
    }},
    "brief_summary": "One paragraph reporter-style summary",
    "key_takeaways": ["Point 1", "Point 2", "Point 3"]
}}
</OUTPUT_JSON_FORMAT>

JUDGEMENT TEXT:
{judgement_text}

JSON RESPONSE:""",

        SummaryType.STANDARD: """You are an expert legal analyst specializing in Indian court judgements.

Analyze and summarize the following court judgement in a STRUCTURED FORMAT.

Your response MUST be in this exact JSON format:
{{
    "metadata": {{
        "case_number": "extracted case number or null",
        "case_title": "extracted case title or null",
        "court": "court name",
        "judges": ["list of judges"],
        "date_of_judgement": "date if found",
        "petitioner": "petitioner name",
        "respondent": "respondent name",
        "subject_matter": "primary legal area",
        "acts_referred": ["list of acts"],
        "sections_cited": ["list of sections"],
        "cases_cited": ["list of cited cases"]
    }},
    "brief_summary": "2-3 sentences capturing the essence of the judgement",
    "facts_of_case": "Clear statement of facts (2-3 paragraphs)",
    "issues_framed": ["Issue 1", "Issue 2"],
    "arguments_petitioner": ["Argument 1", "Argument 2"],
    "arguments_respondent": ["Argument 1", "Argument 2"],
    "court_observations": ["Key observation 1", "Key observation 2"],
    "ratio_decidendi": "The core legal principle/rule established",
    "holding": "The court's final decision",
    "orders_passed": ["Specific order 1", "Specific order 2"],
    "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"]
}}

Be thorough and accurate. Extract all relevant information.

JUDGEMENT TEXT:
{judgement_text}

JSON RESPONSE:""",

        SummaryType.DETAILED: """You are an expert legal analyst specializing in Indian court judgements.

Provide a COMPREHENSIVE legal analysis of the following court judgement.

Your response MUST be in this exact JSON format:
{{
    "metadata": {{
        "case_number": "extracted case number or null",
        "case_title": "extracted case title or null",
        "court": "court name",
        "jurisdiction": "supreme_court/high_court/district_court/tribunal/other",
        "judges": ["list of judges"],
        "date_of_judgement": "date if found",
        "petitioner": "petitioner name",
        "respondent": "respondent name",
        "subject_matter": "primary legal area",
        "acts_referred": ["list of acts with sections"],
        "sections_cited": ["list of specific sections"],
        "cases_cited": ["list of cited cases with citations"]
    }},
    "brief_summary": "Executive summary (3-4 sentences)",
    "facts_of_case": "Detailed statement of facts (comprehensive)",
    "issues_framed": ["Issue 1 with detail", "Issue 2 with detail"],
    "arguments_petitioner": ["Detailed argument 1", "Detailed argument 2"],
    "arguments_respondent": ["Detailed argument 1", "Detailed argument 2"],
    "court_observations": ["Detailed observation 1", "Detailed observation 2"],
    "ratio_decidendi": "The core legal principle/ratio with explanation",
    "holding": "Detailed final decision with reasoning",
    "orders_passed": ["Detailed order 1", "Detailed order 2"],
    "obiter_dicta": ["Non-binding remark 1", "Non-binding remark 2"],
    "dissenting_opinion": "Summary of dissent if any, else null",
    "precedent_analysis": "How cited cases were distinguished/followed",
    "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3", "Takeaway 4"],
    "practical_implications": "Real-world impact and applicability"
}}

Be extremely thorough and legally precise. This is for professional legal reference.

JUDGEMENT TEXT:
{judgement_text}

JSON RESPONSE:""",

        SummaryType.HEADNOTE: """You are an expert legal analyst creating HEADNOTES for court judgements.

Create a professional HEADNOTE for the following judgement in standard legal format.

Your response MUST be in this exact JSON format:
{{
    "metadata": {{
        "case_number": "case number",
        "case_title": "case title",
        "court": "court name",
        "date_of_judgement": "date",
        "judges": ["list of judges"],
        "subject_matter": "legal area"
    }},
    "headnote": {{
        "catchwords": ["keyword1", "keyword2", "keyword3"],
        "acts_sections": ["Act Name - Section X, Y, Z"],
        "held": "What was held by the court in 2-3 clear points",
        "ratio": "The ratio decidendi in one clear statement",
        "cases_referred": ["Case 1 - citation", "Case 2 - citation"]
    }},
    "brief_summary": "One paragraph summary",
    "key_takeaways": ["Key point 1", "Key point 2", "Key point 3"]
}}

Format this as it would appear in a law reporter.

JUDGEMENT TEXT:
{judgement_text}

JSON RESPONSE:"""
    }
    
    def __init__(self, llm_service: Optional[GeminiClient] = None):
        """Initialize with optional LLM service."""
        self.llm_service = llm_service
    
    def preprocess_judgement(self, text: str) -> str:
        """
        Clean and preprocess the judgement text for better analysis.
        
        Args:
            text: Raw judgement text
            
        Returns:
            Cleaned text optimized for extraction
        """
        # Remove excessive whitespace while preserving paragraph breaks
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove page numbers and headers
        text = re.sub(r'\[Page\s*\d+\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Page\s*\d+\s*of\s*\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'-\s*\d+\s*-', '', text)  # Page markers like - 5 -
        
        # Remove URL artifacts and headers
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'www\.\S+', '', text)
        
        # Clean common OCR artifacts
        text = re.sub(r'[_]{3,}', '', text)
        text = re.sub(r'[\.]{4,}', '...', text)
        text = re.sub(r'[-]{3,}', '--', text)
        
        # Normalize quotes and special characters
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('—', '-').replace('–', '-')
        
        # Clean legal document specific artifacts
        text = re.sub(r'\bpara\s*\.?\s*(\d+)', r'paragraph \1', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def extract_basic_metadata(self, text: str) -> JudgementMetadata:
        """
        Extract comprehensive metadata using advanced regex patterns.
        Enhanced for Indian court judgement formats.
        
        Args:
            text: Judgement text
            
        Returns:
            Extracted metadata with high accuracy
        """
        metadata = JudgementMetadata()
        
        # ========== CASE NUMBER EXTRACTION ==========
        case_patterns = [
            # Supreme Court patterns
            r'(?:Civil|Criminal)\s*Appeal\s*(?:No\.?|Number)\.?\s*(\d+(?:\s*[-/]\s*\d+)?(?:\s+of\s+\d{4})?)',
            r'SLP\s*\(?(?:C|Crl|Civil|Criminal)?\)?\s*(?:No\.?)?\.?\s*(\d+(?:\s*[-/]\s*\d+)?(?:\s+of\s+\d{4})?)',
            r'Writ\s*Petition\s*\(?(?:C|Crl|Civil|Criminal)?\)?\s*(?:No\.?)?\s*(\d+(?:\s+of\s+\d{4})?)',
            r'Transfer\s*Petition\s*\(?(?:C|Crl)?\)?\s*(?:No\.?)?\s*(\d+(?:\s+of\s+\d{4})?)',
            # High Court patterns
            r'CWP\s*(?:No\.?)?\s*(\d+(?:\s+of\s+\d{4})?)',
            r'CRA\s*(?:No\.?)?\s*(\d+(?:\s+of\s+\d{4})?)',
            r'RFA\s*(?:No\.?)?\s*(\d+(?:\s+of\s+\d{4})?)',
            # General patterns
            r'Case\s*(?:No\.?|Number)\s*[:.]?\s*([A-Z0-9/-]+\s*(?:of\s*\d{4})?)',
            r'Petition\s*(?:No\.?)\s*(\d+(?:\s+of\s+\d{4})?)',
            # Citation patterns
            r'\((\d{4})\)\s*(\d+)\s*(SCC|SCR|AIR)\s*(\d+)',
        ]
        for pattern in case_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata.case_number = match.group(0).strip()
                break
        
        # ========== PARTY EXTRACTION ==========
        party_patterns = [
            # Standard vs/versus patterns
            r'([A-Z][A-Za-z\s\.\,\(\)]+?)\s+(?:Vs?\.?|versus|v/s)\s+([A-Z][A-Za-z\s\.\,\(\)]+?)(?=\n|$|CORAM|Before)',
            # Appellant/Respondent patterns
            r'([A-Z][A-Za-z\s\.]+)\s*[\.\-\s]*\.+\s*(?:Appellant|Petitioner)',
            r'([A-Z][A-Za-z\s\.]+)\s*[\.\-\s]*\.+\s*(?:Respondent)',
        ]
        versus_match = re.search(party_patterns[0], text, re.IGNORECASE)
        if versus_match:
            metadata.petitioner = versus_match.group(1).strip()[:150]
            metadata.respondent = versus_match.group(2).strip()[:150]
            # Clean up party names
            metadata.petitioner = re.sub(r'\s+', ' ', metadata.petitioner).strip()
            metadata.respondent = re.sub(r'\s+', ' ', metadata.respondent).strip()
            metadata.case_title = f"{metadata.petitioner} v. {metadata.respondent}"
        
        # ========== COURT EXTRACTION ==========
        court_patterns = [
            r'(?:IN\s+THE\s+)?(SUPREME\s+COURT\s+OF\s+INDIA)',
            r'(?:IN\s+THE\s+)?(HIGH\s+COURT\s+OF\s+[A-Z][A-Za-z\s]+?)(?:\s+AT|\s+BENCH|,)',
            r'(?:IN\s+THE\s+)?(HIGH\s+COURT\s+(?:OF|FOR)\s+[A-Z][A-Za-z\s]+)',
            r'(?:IN\s+THE\s+)?(DISTRICT\s+(?:AND\s+SESSIONS\s+)?COURT[A-Za-z\s,]+)',
            r'(?:IN\s+THE\s+)?([A-Z][A-Za-z\s]+TRIBUNAL)',
            r'(NATIONAL\s+(?:GREEN|COMPANY|CONSUMER)\s+TRIBUNAL)',
            r'((?:ITAT|NCLT|NCLAT|NGT|CAT|SAT)\b)',
        ]
        for pattern in court_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata.court = match.group(1).strip().title()
                break
        
        # ========== JURISDICTION DETERMINATION ==========
        if metadata.court:
            court_lower = metadata.court.lower()
            if 'supreme' in court_lower:
                metadata.jurisdiction = JurisdictionType.SUPREME_COURT
            elif 'high' in court_lower:
                metadata.jurisdiction = JurisdictionType.HIGH_COURT
            elif 'district' in court_lower or 'sessions' in court_lower:
                metadata.jurisdiction = JurisdictionType.DISTRICT_COURT
            elif any(t in court_lower for t in ['tribunal', 'itat', 'nclt', 'nclat', 'ngt', 'cat', 'sat']):
                metadata.jurisdiction = JurisdictionType.TRIBUNAL
            else:
                metadata.jurisdiction = JurisdictionType.OTHER
        
        # ========== JUDGES EXTRACTION ==========
        judge_patterns = [
            r'CORAM[\s:]+(.+?)(?=\n\n|\nJ\s*U\s*D\s*G|\nORDER|\nJUDGMENT)',
            r'(?:Before|BEFORE)[\s:]+(.+?)(?=\n\n|\nJ\s*U\s*D\s*G|\nORDER)',
            r"Hon['\.]?ble\s+((?:Mr\.?|Mrs\.?|Ms\.?|Justice|Dr\.?|Chief\s+Justice)?\s*[A-Z][a-zA-Z\.\s]+?),?\s*(?:J\b|JJ\b|C\.?J\.?)",
            r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+),?\s*(?:J\b|,\s*J(?:\s|$))',
        ]
        judges = []
        for pattern in judge_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                for match in matches:
                    # Clean up judge names
                    judge_text = match.strip() if isinstance(match, str) else match[0].strip()
                    # Split if multiple judges in one match
                    judge_list = re.split(r'\s+AND\s+|\s*,\s*(?=[A-Z])', judge_text, flags=re.IGNORECASE)
                    for j in judge_list:
                        j = re.sub(r'\s+', ' ', j).strip()
                        if j and len(j) > 3 and j not in judges:
                            judges.append(j)
                if judges:
                    break
        metadata.judges = judges[:5]
        
        # ========== DATE EXTRACTION ==========
        date_patterns = [
            r'(?:Date\s*(?:of\s+)?(?:Decision|Judgment|Order)|Dated|Decided\s+on|Pronounced\s+on)[\s:]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:Date\s*(?:of\s+)?(?:Decision|Judgment|Order)|Dated|Decided\s+on|Pronounced\s+on)[\s:]+(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})',
            r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata.date_of_judgement = match.group(1).strip()
                break
        
        # ========== ACTS EXTRACTION (Enhanced) ==========
        act_patterns = [
            r'(?:the\s+)?([A-Z][A-Za-z\s,]+(?:Act|Code|Rules|Regulations)[,\s]*(?:19|20)\d{2})',
            r'(?:under|u/s|section\s+\d+\s+of|provisions\s+of|Article\s+\d+\s+of)\s+(?:the\s+)?([A-Z][A-Za-z\s,]+(?:Act|Code|Constitution)[,\s]*(?:19|20)?\d{2,4})?',
            r'(Constitution\s+of\s+India)',
            r'(Indian\s+Penal\s+Code|IPC|Bharatiya\s+Nyaya\s+Sanhita|BNS)',
            r'(Code\s+of\s+Criminal\s+Procedure|CrPC|Bharatiya\s+Nagarik\s+Suraksha\s+Sanhita|BNSS)',
            r'(Code\s+of\s+Civil\s+Procedure|CPC)',
            r'(Indian\s+Evidence\s+Act|Bharatiya\s+Sakshya\s+Adhiniyam|BSA)',
        ]
        acts = set()
        for pattern in act_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and len(match) > 3:
                    acts.add(match.strip())
        metadata.acts_referred = list(acts)[:15]
        
        # ========== SECTIONS EXTRACTION (Enhanced) ==========
        section_patterns = [
            r'[Ss]ection\s*(\d+[A-Za-z]?(?:\s*[-,/]\s*\d+[A-Za-z]?)*)',
            r'[Ss]s?\.\s*(\d+[A-Za-z]?(?:\s*[-,/]\s*\d+[A-Za-z]?)*)',
            r'[Ss]ec\.\s*(\d+[A-Za-z]?)',
            r'u/s\.?\s*(\d+[A-Za-z]?(?:\s*[-,/r/w]\s*\d+[A-Za-z]?)*)',
            r'[Aa]rticle\s*(\d+[A-Za-z]?(?:\s*[-,]\s*\d+[A-Za-z]?)*)',
            r'[Oo]rder\s+([IVXLC]+)\s+[Rr]ule\s+(\d+)',
        ]
        sections = set()
        for pattern in section_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    sections.add(f"Order {match[0]} Rule {match[1]}")
                elif match:
                    sections.add(f"Section {match}")
        metadata.sections_cited = list(sections)[:20]
        
        # ========== CASES CITED EXTRACTION ==========
        case_citation_patterns = [
            r'([A-Z][A-Za-z\s\.]+\s+v[s]?\.?\s+[A-Z][A-Za-z\s\.]+)\s*[\(\[]?\s*(?:\d{4})?\s*[\)\]]?\s*(\d+)?\s*(SCC|SCR|AIR|All(?:ahabad)?|Bom(?:bay)?|Mad(?:ras)?|Cal(?:cutta)?)',
            r'(\d{4})\s*\(\d+\)\s*(SCC|SCR)\s*\d+',
            r'AIR\s*(\d{4})\s*(SC|[A-Za-z]+)\s*\d+',
        ]
        cases = set()
        for pattern in case_citation_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    cases.add(' '.join(str(m) for m in match if m))
                elif match:
                    cases.add(match)
        metadata.cases_cited = list(cases)[:15]
        
        # ========== SUBJECT MATTER DETECTION ==========
        subject_keywords = {
            'Constitutional Law': ['article', 'constitution', 'fundamental right', 'writ', 'habeas corpus', 'mandamus', 'certiorari'],
            'Criminal Law': ['ipc', 'bns', 'murder', 'theft', 'cheating', 'forgery', 'crpc', 'fir', 'bail', 'conviction', 'acquittal'],
            'Civil Law': ['contract', 'specific relief', 'injunction', 'decree', 'suit', 'civil procedure'],
            'Family Law': ['divorce', 'maintenance', 'custody', 'marriage', 'hindu marriage', 'muslim law', 'adoption'],
            'Property Law': ['property', 'land', 'registration', 'transfer', 'land acquisition', 'tenancy'],
            'Labour Law': ['industrial dispute', 'workman', 'employer', 'wages', 'termination', 'reinstatement'],
            'Tax Law': ['income tax', 'gst', 'excise', 'customs', 'assessment', 'penalty', 'tax tribunal'],
            'Company Law': ['company', 'director', 'shareholder', 'winding up', 'nclt', 'corporate'],
            'Intellectual Property': ['trademark', 'copyright', 'patent', 'infringement', 'passing off'],
            'Service Law': ['government servant', 'disciplinary', 'promotion', 'pension', 'cat'],
        }
        text_lower = text.lower()
        subject_scores = {}
        for subject, keywords in subject_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                subject_scores[subject] = score
        if subject_scores:
            metadata.subject_matter = max(subject_scores.items(), key=lambda x: x[1])[0]
        
        return metadata
    
    async def summarize(
        self,
        judgement_text: str,
        summary_type: SummaryType = SummaryType.STANDARD
    ) -> JudgementSummary:
        """
        Summarize a court judgement.
        
        Args:
            judgement_text: The full text of the judgement
            summary_type: Type of summary to generate
            
        Returns:
            JudgementSummary with all extracted information
        """
        if not self.llm_service:
            raise ValueError("LLM service required for summarization")
        
        # Preprocess
        original_length = len(judgement_text)
        cleaned_text = self.preprocess_judgement(judgement_text)
        
        # Extract basic metadata first
        basic_metadata = self.extract_basic_metadata(cleaned_text)
        
        # Prepare prompt
        prompt = self.SUMMARY_PROMPTS[summary_type].format(
            judgement_text=cleaned_text[:50000]  # Limit text length
        )
        
        try:
            # Generate summary using LLM
            if summary_type == SummaryType.BRIEF:
                response = self.llm_service.model.generate_content(prompt)
                response_text = response.text.strip()
                
                # For brief type, return simple summary
                summary = JudgementSummary(
                    id=str(uuid.uuid4()),
                    summary_type=summary_type,
                    metadata=basic_metadata,
                    brief_summary=response_text,
                    facts_of_case="",
                    issues_framed=[],
                    arguments_petitioner=[],
                    arguments_respondent=[],
                    court_observations=[],
                    ratio_decidendi="",
                    holding="",
                    orders_passed=[],
                    key_takeaways=[],
                    confidence_score=0.85,
                    original_length=original_length,
                    summary_length=len(response_text)
                )
            else:
                # For structured types, parse JSON response
                response = self.llm_service.model.generate_content(prompt)
                response_text = response.text.strip()
                summary = self._parse_structured_response(
                    response_text, 
                    summary_type, 
                    basic_metadata,
                    original_length
                )
            
            logger.info(f"Successfully summarized judgement: {summary.id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing judgement: {e}")
            raise
    
    def _parse_structured_response(
        self,
        response: str,
        summary_type: SummaryType,
        fallback_metadata: JudgementMetadata,
        original_length: int
    ) -> JudgementSummary:
        """
        Parse LLM response into structured summary.
        
        Args:
            response: Raw LLM response
            summary_type: Type of summary
            fallback_metadata: Metadata extracted via regex
            original_length: Original text length
            
        Returns:
            Parsed JudgementSummary
        """
        import json
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            # If no JSON, create basic summary from text
            return JudgementSummary(
                id=str(uuid.uuid4()),
                summary_type=summary_type,
                metadata=fallback_metadata,
                brief_summary=response[:500],
                facts_of_case=response,
                issues_framed=[],
                arguments_petitioner=[],
                arguments_respondent=[],
                court_observations=[],
                ratio_decidendi="",
                holding="",
                orders_passed=[],
                key_takeaways=[],
                confidence_score=0.5,
                original_length=original_length,
                summary_length=len(response)
            )
        
        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            # Try to clean and parse
            cleaned_json = json_match.group().replace('\n', '\\n')
            try:
                data = json.loads(cleaned_json)
            except:
                data = {}
        
        # Extract metadata from response or use fallback
        meta_data = data.get('metadata', {})
        metadata = JudgementMetadata(
            case_number=meta_data.get('case_number') or fallback_metadata.case_number,
            case_title=meta_data.get('case_title') or fallback_metadata.case_title,
            court=meta_data.get('court') or fallback_metadata.court,
            jurisdiction=self._parse_jurisdiction(meta_data.get('jurisdiction')) or fallback_metadata.jurisdiction,
            judges=meta_data.get('judges', []) or fallback_metadata.judges,
            date_of_judgement=meta_data.get('date_of_judgement') or fallback_metadata.date_of_judgement,
            petitioner=meta_data.get('petitioner') or fallback_metadata.petitioner,
            respondent=meta_data.get('respondent') or fallback_metadata.respondent,
            subject_matter=meta_data.get('subject_matter') or fallback_metadata.subject_matter,
            acts_referred=meta_data.get('acts_referred', []) or fallback_metadata.acts_referred,
            sections_cited=meta_data.get('sections_cited', []) or fallback_metadata.sections_cited,
            cases_cited=meta_data.get('cases_cited', []) or fallback_metadata.cases_cited
        )
        
        # Handle headnote format
        if summary_type == SummaryType.HEADNOTE:
            headnote = data.get('headnote', {})
            return JudgementSummary(
                id=str(uuid.uuid4()),
                summary_type=summary_type,
                metadata=metadata,
                brief_summary=data.get('brief_summary', ''),
                facts_of_case="",
                issues_framed=[],
                arguments_petitioner=[],
                arguments_respondent=[],
                court_observations=[],
                ratio_decidendi=headnote.get('ratio', ''),
                holding=headnote.get('held', ''),
                orders_passed=[],
                key_takeaways=data.get('key_takeaways', []),
                confidence_score=0.8,
                original_length=original_length,
                summary_length=len(response)
            )
        
        # Build full summary
        summary = JudgementSummary(
            id=str(uuid.uuid4()),
            summary_type=summary_type,
            metadata=metadata,
            brief_summary=data.get('brief_summary', ''),
            facts_of_case=data.get('facts_of_case', ''),
            issues_framed=data.get('issues_framed', []),
            arguments_petitioner=data.get('arguments_petitioner', []),
            arguments_respondent=data.get('arguments_respondent', []),
            court_observations=data.get('court_observations', []),
            ratio_decidendi=data.get('ratio_decidendi', ''),
            holding=data.get('holding', ''),
            orders_passed=data.get('orders_passed', []),
            obiter_dicta=data.get('obiter_dicta'),
            dissenting_opinion=data.get('dissenting_opinion'),
            precedent_analysis=data.get('precedent_analysis'),
            key_takeaways=data.get('key_takeaways', []),
            practical_implications=data.get('practical_implications'),
            confidence_score=0.85 if summary_type == SummaryType.STANDARD else 0.9,
            original_length=original_length,
            summary_length=len(response)
        )
        
        return summary
    
    def _parse_jurisdiction(self, value: Optional[str]) -> Optional[JurisdictionType]:
        """Parse jurisdiction string to enum."""
        if not value:
            return None
        try:
            return JurisdictionType(value.lower().replace(' ', '_'))
        except ValueError:
            return JurisdictionType.OTHER
    
    def format_summary_for_display(self, summary: JudgementSummary) -> Dict[str, Any]:
        """
        Format summary for frontend display.
        
        Args:
            summary: The judgement summary
            
        Returns:
            Formatted dictionary for display
        """
        return {
            "id": summary.id,
            "type": summary.summary_type.value,
            
            # Metadata section
            "metadata": {
                "case_number": summary.metadata.case_number,
                "case_title": summary.metadata.case_title,
                "court": summary.metadata.court,
                "jurisdiction": summary.metadata.jurisdiction.value if summary.metadata.jurisdiction else None,
                "judges": summary.metadata.judges,
                "date": summary.metadata.date_of_judgement,
                "parties": {
                    "petitioner": summary.metadata.petitioner,
                    "respondent": summary.metadata.respondent
                },
                "subject": summary.metadata.subject_matter,
                "legal_references": {
                    "acts": summary.metadata.acts_referred,
                    "sections": summary.metadata.sections_cited,
                    "cases_cited": summary.metadata.cases_cited
                }
            },
            
            # Summary sections
            "summary": {
                "brief": summary.brief_summary,
                "facts": summary.facts_of_case,
                "issues": summary.issues_framed,
                "arguments": {
                    "petitioner": summary.arguments_petitioner,
                    "respondent": summary.arguments_respondent
                },
                "observations": summary.court_observations,
                "ratio": summary.ratio_decidendi,
                "holding": summary.holding,
                "orders": summary.orders_passed
            },
            
            # Additional analysis
            "analysis": {
                "obiter_dicta": summary.obiter_dicta,
                "dissent": summary.dissenting_opinion,
                "precedent_analysis": summary.precedent_analysis,
                "key_takeaways": summary.key_takeaways,
                "implications": summary.practical_implications
            },
            
            # Meta info
            "statistics": {
                "original_length": summary.original_length,
                "summary_length": summary.summary_length,
                "compression_ratio": round(summary.summary_length / max(summary.original_length, 1) * 100, 1),
                "confidence": summary.confidence_score
            },
            
            "created_at": summary.created_at.isoformat()
        }


# Singleton-style accessor
_summarizer_instance: Optional[JudgementSummarizer] = None


def get_judgement_summarizer(llm_service: Optional[GeminiClient] = None) -> JudgementSummarizer:
    """Get or create the judgement summarizer instance."""
    global _summarizer_instance
    if llm_service:
        return JudgementSummarizer(llm_service)
    if _summarizer_instance is None:
        _summarizer_instance = JudgementSummarizer()
    return _summarizer_instance
