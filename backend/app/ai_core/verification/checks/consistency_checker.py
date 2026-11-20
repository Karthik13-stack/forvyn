class ConsistencyChecker:

    def check(self, text):
        from .base import VerificationResult
        result = VerificationResult()
        if 'not liable' in text and 'liable' in text:
            result.warn('Contradictory liability statements')
        return result