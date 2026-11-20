class VerificationResult:

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.score = 1.0

    def fail(self, msg):
        self.errors.append(msg)
        self.score -= 0.4

    def warn(self, msg):
        self.warnings.append(msg)
        self.score -= 0.1