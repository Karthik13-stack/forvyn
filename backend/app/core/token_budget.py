class TokenBudgetExceeded(Exception):
    pass

class TokenBudget:

    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens
        self.used_tokens = 0

    def consume(self, tokens: int):
        if self.used_tokens + tokens > self.max_tokens:
            raise TokenBudgetExceeded(f'Token limit exceeded: {self.used_tokens + tokens}/{self.max_tokens}')
        self.used_tokens += tokens