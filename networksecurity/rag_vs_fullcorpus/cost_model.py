"""
cost_model.py
-------------
Token estimation and $ cost model.

Token counting: uses a simple whitespace-tokenization heuristic scaled by an
empirical words-to-tokens ratio (~1.3 tokens/word for English technical text
with tiktoken-style BPE). This is a well-known approximation, NOT an exact
count from the real tokenizer -- if you have `tiktoken` or the Anthropic
token-counting endpoint available, swap `estimate_tokens()` for a call to
that instead. The approximation is consistent across both strategies, so the
*relative* comparison (full-corpus vs. RAG) it produces is meaningful even
if the absolute numbers are off by a constant factor.

Pricing: set INPUT_PRICE_PER_MTOK to your model's current published input
price (Anthropic pricing page) before treating $ figures as final -- pricing
changes over time and by model tier. The value below is a placeholder to be
confirmed at submission time.
"""

WORDS_TO_TOKENS_RATIO = 1.3

# Placeholder -- confirm current Claude Sonnet input pricing at
# https://www.anthropic.com/pricing before citing this number in the paper.
INPUT_PRICE_PER_MTOK_USD = 3.00


def estimate_tokens(text: str) -> int:
    n_words = len(text.split())
    return int(round(n_words * WORDS_TO_TOKENS_RATIO))


def estimate_cost_usd(n_tokens: int, price_per_mtok: float = INPUT_PRICE_PER_MTOK_USD) -> float:
    return n_tokens / 1_000_000 * price_per_mtok
