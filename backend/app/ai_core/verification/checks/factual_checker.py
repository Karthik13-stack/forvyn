class FactualChecker:

    def check(self, text, context_chunks):
        from .base import VerificationResult
        result = VerificationResult()
        for c in context_chunks:
            if 'Source:' not in c.text and len(c.text) > 200:
                result.warn('Some context chunks have no citation')
        if 'Act' in text or 'Section' in text:
            result.warn('Potential legal citation detected – verify')
        return result