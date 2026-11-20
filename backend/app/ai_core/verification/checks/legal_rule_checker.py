class LegalRuleChecker:

    def check(self, text):
        from .base import VerificationResult
        result = VerificationResult()
        required = ['confidential', 'term', 'obligation', 'disclosure']
        for r in required:
            if r not in text.lower():
                result.fail(f'Missing required NDA concept: {r}')
        return result