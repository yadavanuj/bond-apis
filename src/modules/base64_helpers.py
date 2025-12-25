from typing import Tuple, List
from collections import Counter
import math


BASE64_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")

# ---------------------------------------------
# Base64 substring detection helpers
# ---------------------------------------------

def shannon_entropy(s: str) -> float:
    """
    Shannon entropy used to detect high-information (likely encoded) substrings.
    """
    if not s:
        return 0.0
    freq = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


def find_base64_like_spans(text: str, min_len: int = 8) -> List[Tuple[int, int]]:
    """
    Finds spans of text that consist only of Base64 characters.
    This is a FAST lexical scan (O(n)), not decoding.
    """
    spans = []
    start = None

    for i, ch in enumerate(text):
        if ch in BASE64_CHARS:
            if start is None:
                start = i
        else:
            if start is not None and (i - start) >= min_len:
                spans.append((start, i))
            start = None

    if start is not None and (len(text) - start) >= min_len:
        spans.append((start, len(text)))

    return spans
