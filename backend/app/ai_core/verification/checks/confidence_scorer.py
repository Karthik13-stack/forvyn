class ConfidenceScorer:

    def score(self, results):
        score = 1.0
        for r in results:
            score = min(score, r.score)
        return max(score, 0.0)