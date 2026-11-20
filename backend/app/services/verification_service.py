from typing import List, Dict, Any
import re

class VerificationService:

    def verify_variables_filled(self, text: str) -> List[str]:
        matches = re.findall('\\{\\{\\s*(.*?)\\s*\\}\\}', text)
        return list(set(matches))

    def verify_structure(self, text: str) -> bool:
        if not text or len(text) < 10:
            return False
        return True