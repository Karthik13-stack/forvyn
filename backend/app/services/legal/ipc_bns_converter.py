"""
IPC to BNS Section Converter
Converts Indian Penal Code (IPC) sections to Bharatiya Nyaya Sanhita (BNS) sections.

The Bharatiya Nyaya Sanhita, 2023 (BNS) replaced the Indian Penal Code, 1860 (IPC)
effective from July 1, 2024.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)

class ConversionStatus(str, Enum):
    """Status of conversion."""
    DIRECT_MAPPING = "direct_mapping"
    PARTIAL_MAPPING = "partial_mapping"
    REPEALED = "repealed"
    NEW_IN_BNS = "new_in_bns"
    NOT_FOUND = "not_found"


@dataclass
class ConversionResult:
    """Result of section conversion."""
    ipc_section: str
    bns_section: Optional[str]
    status: ConversionStatus
    ipc_title: str
    bns_title: Optional[str]
    notes: str
    changes_summary: Optional[str] = None


class IPCToBNSConverter:
    """
    Converts IPC sections to BNS sections.
    
    The BNS reorganizes and modernizes the criminal law with:
    - Updated definitions and terminology
    - New offenses for modern crimes
    - Revised penalties
    - Gender-neutral language where applicable
    """
    
    # Comprehensive IPC to BNS mapping with details
    # Format: IPC Section -> (BNS Section, IPC Title, BNS Title, Notes, Changes)
    IPC_TO_BNS_MAPPING: Dict[str, Tuple[str, str, str, str, str]] = {
        # Chapter I - Introduction (IPC) -> Chapter I - Preliminary (BNS)
        "1": ("1", "Title and extent of operation", "Short title, commencement and application", 
              "Direct mapping", "Restructured with updated territorial application"),
        "2": ("2", "Punishment of offences committed within India", "Punishment of offences committed within India",
              "Direct mapping", "Essentially unchanged"),
        "3": ("3", "Punishment of offences committed beyond India", "Punishment of offences committed beyond India",
              "Direct mapping", "Extended extraterritorial jurisdiction"),
        "4": ("4", "Extension of Code to extra-territorial offences", "Extension of Code to extra-territorial offences",
              "Direct mapping", "Updated scope"),
        "5": ("5", "Certain laws not to be affected", "Certain laws not to be affected",
              "Direct mapping", "Unchanged"),
              
        # Chapter II - General Explanations (IPC) -> Chapter II - General Explanations (BNS)
        "6": ("6", "Definitions in the Code to be understood", "Definitions in the Code",
              "Direct mapping", "Updated definitions"),
        "7": ("7", "Sense of expression once explained", "Sense of expression once explained",
              "Direct mapping", "Unchanged"),
        "8": ("8", "Gender", "Gender", "Direct mapping", "Gender-neutral provisions added"),
        "9": ("9", "Number", "Number", "Direct mapping", "Unchanged"),
        "10": ("10", "Man, Woman", "Man, Woman", "Direct mapping", "Unchanged"),
        "11": ("11", "Person", "Person", "Direct mapping", "Unchanged"),
        "12": ("12", "Public", "Public", "Direct mapping", "Unchanged"),
        "17": ("15", "Government", "Government", "Direct mapping", "Updated definition"),
        "19": ("17", "Judge", "Judge", "Direct mapping", "Unchanged"),
        "21": ("18", "Public servant", "Public servant", "Direct mapping", "Expanded definition"),
        "22": ("19", "Moveable property", "Moveable property", "Direct mapping", "Unchanged"),
        "23": ("20", "Wrongful gain and wrongful loss", "Wrongful gain and wrongful loss", 
               "Direct mapping", "Unchanged"),
        "24": ("21", "Dishonestly", "Dishonestly", "Direct mapping", "Unchanged"),
        "25": ("22", "Fraudulently", "Fraudulently", "Direct mapping", "Unchanged"),
        "26": ("23", "Reason to believe", "Reason to believe", "Direct mapping", "Unchanged"),
        "29": ("26", "Document", "Document", "Direct mapping", "Includes electronic documents explicitly"),
        "29A": ("27", "Electronic record", "Electronic record", "Direct mapping", "Enhanced provisions"),
        
        # Offences Affecting Human Body - Murder, Culpable Homicide
        "299": ("100", "Culpable homicide", "Culpable homicide", 
                "Direct mapping", "Definition unchanged"),
        "300": ("101", "Murder", "Murder", "Direct mapping", "Definition clarified"),
        "301": ("102", "Culpable homicide by causing death of person other than intended",
                "Culpable homicide by causing death of person other than intended",
                "Direct mapping", "Unchanged"),
        "302": ("103", "Punishment for murder", "Punishment for murder",
                "Direct mapping", "Death penalty/life imprisonment retained"),
        "303": (None, "Murder by life-convict", "REPEALED", 
                "Repealed", "Section struck down by Supreme Court earlier"),
        "304": ("105", "Punishment for culpable homicide not amounting to murder",
                "Punishment for culpable homicide not amounting to murder",
                "Direct mapping", "Punishment structure retained"),
        "304A": ("106", "Causing death by negligence", "Causing death by negligence",
                 "Direct mapping", "Enhanced penalties for hit-and-run"),
        "304B": ("80", "Dowry death", "Dowry death",
                 "Direct mapping", "Moved to crimes against women chapter"),
        
        # Hurt and Grievous Hurt
        "319": ("114", "Hurt", "Hurt", "Direct mapping", "Definition unchanged"),
        "320": ("115", "Grievous hurt", "Grievous hurt", "Direct mapping", "Unchanged"),
        "321": ("116", "Voluntarily causing hurt", "Voluntarily causing hurt", 
                "Direct mapping", "Unchanged"),
        "322": ("117", "Voluntarily causing grievous hurt", "Voluntarily causing grievous hurt",
                "Direct mapping", "Unchanged"),
        "323": ("115", "Punishment for voluntarily causing hurt", "Punishment for hurt",
                "Direct mapping", "Penalties updated"),
        "324": ("118", "Voluntarily causing hurt by dangerous weapons",
                "Voluntarily causing hurt by dangerous weapons",
                "Direct mapping", "Unchanged"),
        "325": ("117", "Punishment for grievous hurt", "Punishment for grievous hurt",
                "Direct mapping", "Unchanged"),
        "326": ("118", "Voluntarily causing grievous hurt by dangerous weapons",
                "Voluntarily causing grievous hurt by dangerous weapons",
                "Direct mapping", "Unchanged"),
        "326A": ("124", "Voluntarily causing grievous hurt by acid attack",
                 "Voluntarily causing grievous hurt by acid attack",
                 "Direct mapping", "Enhanced penalties"),
        "326B": ("125", "Throwing acid", "Throwing acid",
                 "Direct mapping", "Enhanced penalties"),
        
        # Sexual Offences
        "354": ("74", "Assault or criminal force to woman with intent to outrage modesty",
                "Assault or criminal force to woman with intent to outrage modesty",
                "Direct mapping", "Penalties enhanced"),
        "354A": ("75", "Sexual harassment", "Sexual harassment",
                 "Direct mapping", "Expanded definition"),
        "354B": ("76", "Assault or use of criminal force to woman with intent to disrobe",
                 "Assault or criminal force to woman with intent to disrobe",
                 "Direct mapping", "Unchanged"),
        "354C": ("77", "Voyeurism", "Voyeurism", "Direct mapping", "Unchanged"),
        "354D": ("78", "Stalking", "Stalking", "Direct mapping", "Includes cyber stalking"),
        "375": ("63", "Rape", "Rape", "Direct mapping", "Definition expanded"),
        "376": ("64", "Punishment for rape", "Punishment for rape",
                "Direct mapping", "Minimum punishment increased"),
        "376A": ("66", "Punishment for causing death or persistent vegetative state",
                 "Punishment for causing death or persistent vegetative state",
                 "Direct mapping", "Unchanged"),
        "376AB": ("65", "Punishment for rape on woman under twelve years",
                  "Punishment for rape on woman under twelve years",
                  "Direct mapping", "Death penalty provision"),
        "376B": ("67", "Sexual intercourse by husband upon wife during separation",
                 "Sexual intercourse by husband upon wife during separation",
                 "Direct mapping", "Unchanged"),
        "376C": ("68", "Sexual intercourse by person in authority",
                 "Sexual intercourse by person in authority",
                 "Direct mapping", "Unchanged"),
        "376D": ("70", "Gang rape", "Gang rape", "Direct mapping", "Enhanced penalties"),
        "376DA": ("70(2)", "Punishment for gang rape on woman under sixteen years",
                  "Punishment for gang rape on woman under sixteen years",
                  "Direct mapping", "Death penalty provision"),
        "376DB": ("70(2)", "Punishment for gang rape on woman under twelve years",
                  "Punishment for gang rape on woman under twelve years",
                  "Direct mapping", "Death penalty provision"),
        "376E": ("71", "Punishment for repeat offenders", "Punishment for repeat offenders",
                 "Direct mapping", "Unchanged"),
        
        # Kidnapping and Abduction
        "359": ("137", "Kidnapping", "Kidnapping", "Direct mapping", "Definition unchanged"),
        "360": ("138", "Kidnapping from India", "Kidnapping from India", 
                "Direct mapping", "Unchanged"),
        "361": ("137", "Kidnapping from lawful guardianship", "Kidnapping from lawful guardianship",
                "Direct mapping", "Unchanged"),
        "362": ("139", "Abduction", "Abduction", "Direct mapping", "Unchanged"),
        "363": ("137", "Punishment for kidnapping", "Punishment for kidnapping",
                "Direct mapping", "Penalties updated"),
        "363A": ("140", "Kidnapping or obtaining custody of minor for begging",
                 "Kidnapping or obtaining custody of minor for begging",
                 "Direct mapping", "Unchanged"),
        "364": ("140", "Kidnapping for murder", "Kidnapping for murder",
                "Direct mapping", "Unchanged"),
        "364A": ("140", "Kidnapping for ransom", "Kidnapping for ransom",
                 "Direct mapping", "Enhanced penalties"),
        "365": ("141", "Kidnapping with intent to secretly confine",
                "Kidnapping with intent to secretly confine",
                "Direct mapping", "Unchanged"),
        "366": ("141", "Kidnapping woman to compel marriage",
                "Kidnapping woman to compel marriage",
                "Direct mapping", "Unchanged"),
        "366A": ("141", "Procuration of minor girl", "Procuration of minor girl",
                 "Direct mapping", "Unchanged"),
        "366B": ("141", "Importation of girl from foreign country",
                 "Importation of girl from foreign country",
                 "Direct mapping", "Unchanged"),
        "367": ("142", "Kidnapping for slavery", "Kidnapping for slavery",
                "Direct mapping", "Unchanged"),
        "368": ("143", "Wrongfully concealing kidnapped person",
                "Wrongfully concealing kidnapped person",
                "Direct mapping", "Unchanged"),
        "369": ("144", "Kidnapping child under ten", "Kidnapping child under ten",
                "Direct mapping", "Unchanged"),
        
        # Theft, Extortion, Robbery, Dacoity
        "378": ("303", "Theft", "Theft", "Direct mapping", "Unchanged"),
        "379": ("303", "Punishment for theft", "Punishment for theft",
                "Direct mapping", "Penalties updated"),
        "380": ("305", "Theft in dwelling house", "Theft in dwelling house",
                "Direct mapping", "Unchanged"),
        "381": ("306", "Theft by clerk or servant", "Theft by clerk or servant",
                "Direct mapping", "Unchanged"),
        "382": ("304", "Theft after preparation for causing death or hurt",
                "Theft after preparation for causing death or hurt",
                "Direct mapping", "Unchanged"),
        "383": ("308", "Extortion", "Extortion", "Direct mapping", "Unchanged"),
        "384": ("308", "Punishment for extortion", "Punishment for extortion",
                "Direct mapping", "Unchanged"),
        "385": ("309", "Putting person in fear of injury to commit extortion",
                "Putting person in fear of injury to commit extortion",
                "Direct mapping", "Unchanged"),
        "386": ("310", "Extortion by putting person in fear of death or grievous hurt",
                "Extortion by putting person in fear of death or grievous hurt",
                "Direct mapping", "Unchanged"),
        "390": ("309", "Robbery", "Robbery", "Direct mapping", "Unchanged"),
        "391": ("310", "Dacoity", "Dacoity", "Direct mapping", "Unchanged"),
        "392": ("309", "Punishment for robbery", "Punishment for robbery",
                "Direct mapping", "Unchanged"),
        "393": ("310", "Attempt to commit robbery", "Attempt to commit robbery",
                "Direct mapping", "Unchanged"),
        "394": ("311", "Voluntarily causing hurt in committing robbery",
                "Voluntarily causing hurt in committing robbery",
                "Direct mapping", "Unchanged"),
        "395": ("310", "Punishment for dacoity", "Punishment for dacoity",
                "Direct mapping", "Unchanged"),
        "396": ("312", "Dacoity with murder", "Dacoity with murder",
                "Direct mapping", "Death penalty retained"),
        "397": ("313", "Robbery or dacoity with attempt to cause death or grievous hurt",
                "Robbery or dacoity with attempt to cause death or grievous hurt",
                "Direct mapping", "Unchanged"),
        "398": ("314", "Attempt to commit robbery or dacoity when armed with deadly weapon",
                "Attempt to commit robbery or dacoity when armed with deadly weapon",
                "Direct mapping", "Unchanged"),
        "399": ("315", "Making preparation to commit dacoity",
                "Making preparation to commit dacoity",
                "Direct mapping", "Unchanged"),
        "400": ("316", "Belonging to gang of dacoits", "Belonging to gang of dacoits",
                "Direct mapping", "Unchanged"),
        "401": ("317", "Belonging to gang of thieves", "Belonging to gang of thieves",
                "Direct mapping", "Unchanged"),
        "402": ("318", "Assembling for purpose of committing dacoity",
                "Assembling for purpose of committing dacoity",
                "Direct mapping", "Unchanged"),
        
        # Criminal Breach of Trust and Cheating
        "403": ("316", "Dishonest misappropriation of property",
                "Dishonest misappropriation of property",
                "Direct mapping", "Unchanged"),
        "404": ("317", "Dishonest misappropriation of property possessed by deceased",
                "Dishonest misappropriation of property possessed by deceased",
                "Direct mapping", "Unchanged"),
        "405": ("316", "Criminal breach of trust", "Criminal breach of trust",
                "Direct mapping", "Unchanged"),
        "406": ("316", "Punishment for criminal breach of trust",
                "Punishment for criminal breach of trust",
                "Direct mapping", "Unchanged"),
        "407": ("317", "Criminal breach of trust by carrier",
                "Criminal breach of trust by carrier",
                "Direct mapping", "Unchanged"),
        "408": ("318", "Criminal breach of trust by public servant or banker",
                "Criminal breach of trust by public servant or banker",
                "Direct mapping", "Unchanged"),
        "409": ("319", "Criminal breach of trust by public servant or banker",
                "Criminal breach of trust by public servant, banker, merchant or agent",
                "Direct mapping", "Unchanged"),
        "415": ("318", "Cheating", "Cheating", "Direct mapping", "Unchanged"),
        "416": ("319", "Cheating by personation", "Cheating by personation",
                "Direct mapping", "Unchanged"),
        "417": ("318", "Punishment for cheating", "Punishment for cheating",
                "Direct mapping", "Unchanged"),
        "418": ("319", "Cheating with knowledge", "Cheating with knowledge",
                "Direct mapping", "Unchanged"),
        "419": ("319", "Punishment for cheating by personation",
                "Punishment for cheating by personation",
                "Direct mapping", "Unchanged"),
        "420": ("318", "Cheating and dishonestly inducing delivery of property",
                "Cheating and dishonestly inducing delivery of property",
                "Direct mapping", "Enhanced penalties"),
        
        # Forgery and Related Offences
        "463": ("336", "Forgery", "Forgery", "Direct mapping", "Includes digital forgery"),
        "464": ("337", "Making a false document", "Making a false document",
                "Direct mapping", "Includes electronic records"),
        "465": ("336", "Punishment for forgery", "Punishment for forgery",
                "Direct mapping", "Unchanged"),
        "466": ("338", "Forgery of record of Court", "Forgery of record of Court",
                "Direct mapping", "Unchanged"),
        "467": ("338", "Forgery of valuable security", "Forgery of valuable security",
                "Direct mapping", "Unchanged"),
        "468": ("339", "Forgery for purpose of cheating",
                "Forgery for purpose of cheating",
                "Direct mapping", "Unchanged"),
        "469": ("340", "Forgery for purpose of harming reputation",
                "Forgery for purpose of harming reputation",
                "Direct mapping", "Unchanged"),
        "470": ("341", "Forged document", "Forged document",
                "Direct mapping", "Includes electronic records"),
        "471": ("341", "Using as genuine a forged document",
                "Using as genuine a forged document",
                "Direct mapping", "Unchanged"),
        
        # Offences Against State
        "121": ("147", "Waging war against Government of India",
                "Waging war against Government of India",
                "Direct mapping", "Enhanced scope"),
        "121A": ("148", "Conspiracy to wage war", "Conspiracy to wage war",
                 "Direct mapping", "Unchanged"),
        "122": ("149", "Collecting arms to wage war", "Collecting arms to wage war",
                "Direct mapping", "Unchanged"),
        "123": ("150", "Concealing with intent to facilitate waging of war",
                "Concealing with intent to facilitate waging of war",
                "Direct mapping", "Unchanged"),
        "124": ("151", "Assaulting President, Governor with intent to compel",
                "Assaulting President, Governor with intent to compel",
                "Direct mapping", "Unchanged"),
        "124A": ("152", "Sedition", "Acts endangering sovereignty, unity and integrity of India",
                 "Partial mapping", "Significantly revised - sedition replaced with broader provision"),
        
        # Offences Relating to Public Tranquility
        "141": ("189", "Unlawful assembly", "Unlawful assembly", 
                "Direct mapping", "Definition unchanged"),
        "142": ("189", "Being member of unlawful assembly",
                "Being member of unlawful assembly",
                "Direct mapping", "Unchanged"),
        "143": ("189", "Punishment for unlawful assembly",
                "Punishment for unlawful assembly",
                "Direct mapping", "Unchanged"),
        "144": ("190", "Joining unlawful assembly armed with deadly weapon",
                "Joining unlawful assembly armed with deadly weapon",
                "Direct mapping", "Unchanged"),
        "145": ("191", "Joining or continuing in unlawful assembly knowing declared unlawful",
                "Joining or continuing in unlawful assembly knowing declared unlawful",
                "Direct mapping", "Unchanged"),
        "146": ("191", "Rioting", "Rioting", "Direct mapping", "Unchanged"),
        "147": ("191", "Punishment for rioting", "Punishment for rioting",
                "Direct mapping", "Unchanged"),
        "148": ("192", "Rioting armed with deadly weapon",
                "Rioting armed with deadly weapon",
                "Direct mapping", "Unchanged"),
        "149": ("190", "Every member of unlawful assembly guilty of offence committed",
                "Every member of unlawful assembly guilty of offence committed",
                "Direct mapping", "Unchanged"),
        "153": ("196", "Wantonly giving provocation with intent to cause riot",
                "Wantonly giving provocation with intent to cause riot",
                "Direct mapping", "Unchanged"),
        "153A": ("196", "Promoting enmity between different groups",
                 "Promoting enmity between different groups",
                 "Direct mapping", "Enhanced scope - includes digital medium"),
        "153B": ("197", "Imputations, assertions prejudicial to national integration",
                 "Imputations, assertions prejudicial to national integration",
                 "Direct mapping", "Unchanged"),
        
        # Defamation
        "499": ("356", "Defamation", "Defamation", "Direct mapping", "Unchanged"),
        "500": ("356", "Punishment for defamation", "Punishment for defamation",
                "Direct mapping", "Unchanged"),
        "501": ("357", "Printing defamatory matter", "Printing defamatory matter",
                "Direct mapping", "Includes digital publishing"),
        "502": ("358", "Sale of printed defamatory matter",
                "Sale of printed defamatory matter",
                "Direct mapping", "Unchanged"),
        
        # Criminal Intimidation
        "503": ("351", "Criminal intimidation", "Criminal intimidation",
                "Direct mapping", "Unchanged"),
        "504": ("352", "Intentional insult with intent to provoke breach of peace",
                "Intentional insult with intent to provoke breach of peace",
                "Direct mapping", "Unchanged"),
        "505": ("353", "Statements conducing to public mischief",
                "Statements conducing to public mischief",
                "Direct mapping", "Enhanced scope for digital media"),
        "506": ("351", "Punishment for criminal intimidation",
                "Punishment for criminal intimidation",
                "Direct mapping", "Unchanged"),
        "507": ("351", "Criminal intimidation by anonymous communication",
                "Criminal intimidation by anonymous communication",
                "Direct mapping", "Includes digital communication"),
        "509": ("79", "Word, gesture or act intended to insult modesty of woman",
                "Word, gesture or act intended to insult modesty of woman",
                "Direct mapping", "Includes digital communications"),
        
        # Cruelty and Domestic Violence
        "498": (None, "Enticing or taking away or detaining married woman",
                "REPEALED", "Repealed", "Removed as discriminatory"),
        "498A": ("85", "Husband or relative of husband subjecting woman to cruelty",
                 "Husband or relative of husband subjecting woman to cruelty",
                 "Direct mapping", "Procedural safeguards added"),
                 
        # NEW in BNS - Organized Crime
        "NEW": ("111", "New provision", "Organized crime",
                "New in BNS", "New provision for organized crime syndicates"),
        "NEW_MOB": ("103(2)", "New provision", "Mob lynching",
                    "New in BNS", "New provision for mob lynching - death penalty"),
        "NEW_SNATCH": ("304", "New provision", "Snatching",
                       "New in BNS", "New specific provision for snatching"),
        "NEW_PETTY": ("110", "New provision", "Petty organized crime",
                      "New in BNS", "New provision for petty organized crime"),
        "NEW_TERROR": ("113", "New provision", "Terrorist act",
                       "New in BNS", "Incorporated from UAPA"),
    }
    
    def __init__(self):
        """Initialize the converter."""
        self._build_reverse_mapping()
    
    def _build_reverse_mapping(self):
        """Build BNS to IPC reverse mapping."""
        self.bns_to_ipc: Dict[str, str] = {}
        for ipc, (bns, _, _, _, _) in self.IPC_TO_BNS_MAPPING.items():
            if bns and not ipc.startswith("NEW"):
                self.bns_to_ipc[bns] = ipc
    
    def convert_ipc_to_bns(self, ipc_section: str) -> ConversionResult:
        """
        Convert an IPC section to its BNS equivalent.
        
        Args:
            ipc_section: IPC section number (e.g., "302", "420", "376")
        
        Returns:
            ConversionResult with BNS equivalent and details
        """
        # Clean the section number
        section = ipc_section.strip().upper().replace("SECTION", "").strip()
        
        if section in self.IPC_TO_BNS_MAPPING:
            bns_section, ipc_title, bns_title, notes, changes = self.IPC_TO_BNS_MAPPING[section]
            
            if bns_section is None:
                return ConversionResult(
                    ipc_section=section,
                    bns_section=None,
                    status=ConversionStatus.REPEALED,
                    ipc_title=ipc_title,
                    bns_title=None,
                    notes=notes,
                    changes_summary=changes
                )
            
            status = (ConversionStatus.DIRECT_MAPPING if notes == "Direct mapping" 
                      else ConversionStatus.PARTIAL_MAPPING)
            
            return ConversionResult(
                ipc_section=section,
                bns_section=bns_section,
                status=status,
                ipc_title=ipc_title,
                bns_title=bns_title,
                notes=notes,
                changes_summary=changes
            )
        
        return ConversionResult(
            ipc_section=section,
            bns_section=None,
            status=ConversionStatus.NOT_FOUND,
            ipc_title="Unknown",
            bns_title=None,
            notes="Section not found in mapping database",
            changes_summary=None
        )
    
    def convert_bns_to_ipc(self, bns_section: str) -> ConversionResult:
        """
        Convert a BNS section to its IPC equivalent.
        
        Args:
            bns_section: BNS section number
        
        Returns:
            ConversionResult with IPC equivalent and details
        """
        section = bns_section.strip()
        
        if section in self.bns_to_ipc:
            ipc_section = self.bns_to_ipc[section]
            return self.convert_ipc_to_bns(ipc_section)
        
        # Check if it's a new BNS provision
        for ipc, (bns, ipc_title, bns_title, notes, changes) in self.IPC_TO_BNS_MAPPING.items():
            if bns == section and ipc.startswith("NEW"):
                return ConversionResult(
                    ipc_section=None,
                    bns_section=section,
                    status=ConversionStatus.NEW_IN_BNS,
                    ipc_title=None,
                    bns_title=bns_title,
                    notes=notes,
                    changes_summary=changes
                )
        
        return ConversionResult(
            ipc_section=None,
            bns_section=section,
            status=ConversionStatus.NOT_FOUND,
            ipc_title=None,
            bns_title="Unknown",
            notes="Section not found in mapping database"
        )
    
    def convert_text(self, text: str, convert_to: str = "bns") -> str:
        """
        Convert all IPC/BNS references in a text.
        
        Args:
            text: Text containing legal references
            convert_to: Target format - "bns" or "ipc"
        
        Returns:
            Text with converted references
        """
        if convert_to.lower() == "bns":
            # Convert IPC to BNS
            pattern = r'(?:Section\s+|Sec\.\s*|S\.\s*)?(\d+[A-Z]?)\s*(?:of\s+)?(?:the\s+)?(?:IPC|Indian\s+Penal\s+Code)'
            
            def replace_ipc(match):
                section = match.group(1)
                result = self.convert_ipc_to_bns(section)
                if result.bns_section:
                    return f"Section {result.bns_section} of BNS (formerly Section {section} IPC)"
                return match.group(0)
            
            return re.sub(pattern, replace_ipc, text, flags=re.IGNORECASE)
        else:
            # Convert BNS to IPC
            pattern = r'(?:Section\s+|Sec\.\s*|S\.\s*)?(\d+)\s*(?:of\s+)?(?:the\s+)?(?:BNS|Bharatiya\s+Nyaya\s+Sanhita)'
            
            def replace_bns(match):
                section = match.group(1)
                result = self.convert_bns_to_ipc(section)
                if result.ipc_section:
                    return f"Section {result.ipc_section} of IPC (now Section {section} BNS)"
                return match.group(0)
            
            return re.sub(pattern, replace_bns, text, flags=re.IGNORECASE)
    
    def get_section_comparison(self, ipc_section: str) -> Dict[str, Any]:
        """
        Get detailed comparison between IPC and BNS sections.
        
        Args:
            ipc_section: IPC section number
        
        Returns:
            Dictionary with detailed comparison
        """
        result = self.convert_ipc_to_bns(ipc_section)
        
        return {
            "ipc": {
                "section": result.ipc_section,
                "title": result.ipc_title,
                "code": "Indian Penal Code, 1860"
            },
            "bns": {
                "section": result.bns_section,
                "title": result.bns_title,
                "code": "Bharatiya Nyaya Sanhita, 2023"
            },
            "status": result.status.value,
            "notes": result.notes,
            "changes": result.changes_summary
        }
    
    def get_all_repealed_sections(self) -> List[str]:
        """Get list of IPC sections that were repealed in BNS."""
        repealed = []
        for ipc, (bns, ipc_title, _, notes, _) in self.IPC_TO_BNS_MAPPING.items():
            if bns is None and not ipc.startswith("NEW"):
                repealed.append(f"Section {ipc}: {ipc_title}")
        return repealed
    
    def get_new_bns_provisions(self) -> List[Dict[str, str]]:
        """Get list of new provisions introduced in BNS."""
        new_provisions = []
        for ipc, (bns, _, bns_title, _, changes) in self.IPC_TO_BNS_MAPPING.items():
            if ipc.startswith("NEW"):
                new_provisions.append({
                    "section": bns,
                    "title": bns_title,
                    "description": changes
                })
        return new_provisions



# Singleton instance
_converter_instance = None


def get_ipc_bns_converter() -> IPCToBNSConverter:
    """Get singleton instance of converter."""
    global _converter_instance
    if _converter_instance is None:
        _converter_instance = IPCToBNSConverter()
    return _converter_instance
