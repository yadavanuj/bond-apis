import re
import unicodedata
import base64
import urllib.parse
from typing import Tuple, List, Dict, Any
from collections import Counter
import math
from .base64_helpers import find_base64_like_spans, shannon_entropy

class Normalizer:
    """
    Text Normalizer for Security Scanning (DLP / Agent Guarding).

    In AI and cybersecurity, Data Loss Prevention (DLP) systems protect sensitive data from being leaked,
    while Agent Guarding monitors AI agents to prevent them from generating harmful or unauthorized content.
    Attackers often try to hide malicious content by encoding, obfuscating, or transforming text to evade detection.

    This class performs ONLY reversible, deterministic transformations to "unmask" hidden content:
    - Reversible: We can always trace back to the original text for auditing.
    - Deterministic: Same input always produces the same output, ensuring consistent scanning.
    - No ML/Heuristics: Pure rule-based processing for reliability and explainability.

    Why normalize? Attackers use tricks like:
    - Unicode homoglyphs (e.g., 'а' looks like 'a' but is different character)
    - URL encoding (%40 for '@')
    - Base64 encoding (hiding secrets in binary-like text)
    - Extra whitespace or mixed case to confuse scanners

    Recommended Strategy (Dual-Scan):
    Normalization is destructive (e.g., "file_name.txt" -> "file name.txt").
    For best security coverage, use a "Dual-Scan" approach:
    1. Scan Original Text: Catch exact matches, filenames, and structured identifiers.
    2. Scan Normalized Text: Catch obfuscated keywords (e.g., "h_i_d_d_e_n").
    Combine results from both passes.

    Output:
      - normalized_text: The cleaned, standardized text ready for scanning
      - normalization_steps: List of transformations applied (for audit/debugging)

    Parameter Relationships & Dependencies:

    1. enable_separator_normalization & collapse_whitespace (Interaction):
       - enable_separator_normalization generates whitespace by replacing _, -, # with spaces
       - collapse_whitespace cleans up irregular spacing
       - Example: "hidden___payload" -> separator norm -> "hidden   payload" -> collapse -> "hidden payload"
       - Recommendation: Enable both together for canonical output

    2. enable_base64 & enable_substring_base64 (Dependency):
       - enable_base64 acts as master switch
       - enable_substring_base64 is ignored if enable_base64 is False
       - Code explicitly checks: if self.enable_base64 and self.enable_substring_base64

    3. lowercase & enable_base64 (Order Dependency):
       - Base64 is case-sensitive and must be decoded before lowercasing
       - Lowercasing before decoding would corrupt Base64 payloads
       - Normalizer correctly orders: decoding steps (2 & 3) before lowercasing (Step 5)
    """

    def __init__(
        self,
        max_decode_depth: int = 2,
        enable_base64: bool = True,
        enable_url_decode: bool = True,
        enable_unicode_norm: bool = True,
        collapse_whitespace: bool = True,
        lowercase: bool = False,
        enable_substring_base64: bool = True,
        min_base64_substring_len: int = 8,
        base64_entropy_threshold: float = 2.5,
        max_base64_substrings: int = 10,
        enable_separator_normalization: bool = False,
    ):
        self.max_decode_depth = max_decode_depth
        self.enable_base64 = enable_base64
        self.enable_url_decode = enable_url_decode
        self.enable_unicode_norm = enable_unicode_norm
        self.collapse_whitespace = collapse_whitespace
        self.lowercase = lowercase
        self.enable_substring_base64 = enable_substring_base64
        self.min_base64_substring_len = min_base64_substring_len
        self.base64_entropy_threshold = base64_entropy_threshold
        self.max_base64_substrings = max_base64_substrings
        self.enable_separator_normalization = enable_separator_normalization

    def normalize(self, text: str) -> Tuple[str, List[str]]:
        """
        Main normalization pipeline for security scanning.

        This method applies a series of transformations to "unmask" potential threats hidden in text.
        Each step is designed to counter common attacker techniques while remaining reversible for auditing.

        Returns:
            normalized_text: str - The cleaned text ready for security scanning
            steps: List[str] - List of transformations applied (for audit/debugging)
        """
        steps = []  # Track what transformations were applied
        out = text  # Start with the original text

        # ---------------------------------------------
        # Step 1: Unicode normalization (homoglyph handling)
        # ---------------------------------------------
        # Why? Attackers use Unicode homoglyphs (visually identical characters) to hide malicious content.
        # Example: Cyrillic 'а' (U+0430) looks like Latin 'a' but is different, fooling scanners.
        # What it does: Converts to canonical forms using NFKC (Normalization Form KC - Compatibility Composition).
        # This handles full-width characters, accented variants, and other visual tricks.
        # Security impact: Prevents evasion of keyword detection (e.g., "pаssword" becomes "password").
        if self.enable_unicode_norm:
            new_out = unicodedata.normalize("NFKC", out)
            if new_out != out:
                steps.append("unicode_nfkc")
                out = new_out

        # ---------------------------------------------
        # Step 2: URL decoding
        # ---------------------------------------------
        # Why? Attackers encode malicious URLs or data using percent-encoding to hide them.
        # Example: "http%3A%2F%2Fevil.com" becomes "http://evil.com" after decoding.
        # What it does: Decodes %XX sequences back to their original characters (%40 -> '@', %2E -> '.').
        # Security impact: Reveals hidden URLs, email addresses, or commands in encoded text.
        if self.enable_url_decode:
            decoded = urllib.parse.unquote(out)
            if decoded != out:
                steps.append("url_decode")
                out = decoded

        # ---------------------------------------------
        # Step 3A: Substring Base64 decoding (entropy-gated)
        # ---------------------------------------------
        # Dependency: Requires self.enable_base64 to be True.
        # Why? Attackers often hide encoded data inside otherwise normal strings:
        #   ZXZpbF9wYXlsb2Fk%40hidden.com
        # This step selectively decodes ONLY high-entropy Base64-like substrings.
        if self.enable_base64 and self.enable_substring_base64:
            out, sub_steps = self._decode_base64_substrings(out)
            steps.extend(sub_steps)
        
        # ---------------------------------------------
        # Step 3: Recursive Base64 decoding (bounded)
        # ---------------------------------------------
        # Why? Attackers hide secrets, malware, or commands by encoding them in Base64.
        # They often encode multiple times: Base64(Base64(secret)) to make it harder to detect.
        # What it does: Attempts to decode Base64 recursively, but safely and bounded.
        # Security impact: Unmasks hidden data like API keys, scripts, or encrypted payloads.
        # Conservative approach: Only decodes if result is printable text, not binary garbage.
        if self.enable_base64:
            out, b64_steps = self._recursive_base64_decode(out)
            steps.extend(b64_steps)

        # ---------------------------------------------
        # Step 4: Separator normalization
        # ---------------------------------------------
        # Why? Attackers use characters like _, -, # to break up keywords or obfuscate content.
        # Example: "p_a_s_s_w_o_r_d" or "malicious-payload" or "cmd#exe".
        # What it does: Replaces sequences of _, -, # with a single space.
        # Interaction: This introduces spaces. 'collapse_whitespace' should be enabled
        # to clean up the resulting text (e.g., "A___B" -> "A   B" -> "A B").
        if self.enable_separator_normalization:
            new_out = re.sub(r"[_\-#]+", " ", out)
            if new_out != out:
                steps.append("normalize_separators")
                out = new_out

        # ---------------------------------------------
        # Step 4: Whitespace normalization
        # ---------------------------------------------
        # Why? Attackers use extra whitespace, tabs, or newlines to break up keywords or confuse parsers.
        # Example: "s e c r e t" or "secret\nkey" might evade simple string matching.
        # What it does: Collapses all whitespace (spaces, tabs, newlines) into single spaces and trims edges.
        # Security impact: Ensures consistent text for pattern matching and keyword detection.
        if self.collapse_whitespace:
            new_out = re.sub(r"\s+", " ", out).strip()
            if new_out != out:
                steps.append("collapse_whitespace")
                out = new_out

        # ---------------------------------------------
        # Step 5: Optional lowercasing
        # ---------------------------------------------
        # Why? Some security scanners are case-insensitive, but attackers mix cases to evade detection.
        # Example: "Secret" vs "secret" - scanner might miss mixed case.
        # What it does: Converts all text to lowercase for uniform processing.
        # Security impact: Enables case-insensitive matching, but WARNING: Only use if case doesn't matter!
        # Do NOT enable if you're scanning for proper nouns, passwords, or case-sensitive data.
        if self.lowercase:
            new_out = out.lower()
            if new_out != out:
                steps.append("lowercase")
                out = new_out

        return out, steps

    # -------------------------------------------------
    # Internal helpers
    # -------------------------------------------------

    def _recursive_base64_decode(self, text: str) -> Tuple[str, List[str]]:
        """
        Attempts to base64-decode the entire text recursively, up to max_decode_depth times.

        Why recursive? Attackers often layer encodings: Base64(Base64("secret")) to hide data deeper.
        This method peels back layers safely to reveal hidden content.

        Security considerations:
        - Conservative approach: Only continues if decoding produces valid, printable text
        - Bounded recursion: Limited by max_decode_depth to prevent infinite loops or DoS
        - Printable check: Ensures we don't decode to binary garbage that could crash scanners

        Returns:
            Tuple of (final_decoded_text, list_of_steps_taken)
        """
        steps = []  # Track each successful decode step
        out = text  # Current text being processed

        # Try decoding up to max_decode_depth times
        for depth in range(self.max_decode_depth):
            # Attempt a single decode
            candidate = self._safe_base64_decode(out)
            if candidate is None:
                # Decode failed - probably not valid Base64, stop trying
                break

            # Only accept the decode if result is mostly printable text
            # This prevents us from decoding binary files, images, or corrupted data
            if self._is_mostly_printable(candidate):
                out = candidate  # Accept this decode
                steps.append(f"base64_decode_depth_{depth+1}")  # Record the step
            else:
                # Result looks like binary junk, stop decoding
                break

        return out, steps

    def _decode_base64_substrings(self, text: str) -> Tuple[str, List[str]]:
        """
        Selectively decodes Base64-like substrings inside text.

        SAFETY GUARANTEES:
        - Only Base64-character substrings
        - Minimum length enforced
        - Entropy-gated (avoids false positives)
        - Printable output only
        - Bounded replacements (performance safe)

        This defends against mixed-encoding exfiltration techniques.
        """
        steps = []
        out = text

        spans = find_base64_like_spans(out, self.min_base64_substring_len)
        if not spans:
            return out, steps

        # Hard cap to prevent pathological inputs
        spans = spans[: self.max_base64_substrings]

        new_text = []
        last = 0
        modified = False

        for start, end in spans:
            candidate = out[start:end]

            # Entropy gate: skip natural language
            if shannon_entropy(candidate) < self.base64_entropy_threshold:
                continue

            decoded = self._safe_base64_decode(candidate)
            if not decoded:
                continue

            if not self._is_mostly_printable(decoded):
                continue

            # Replace encoded substring
            new_text.append(out[last:start])
            new_text.append(decoded)
            last = end
            modified = True
            steps.append("base64_substring_decode")

        if not modified:
            return out, steps

        new_text.append(out[last:])
        return "".join(new_text), steps


    def _safe_base64_decode(self, text: str):
        """
        Attempts to decode the given text as Base64, safely handling errors.

        Base64 is a common encoding for binary data as text. Attackers use it to hide:
        - API keys and passwords
        - Malware payloads
        - Encrypted commands

        This method is "safe" because:
        - It catches all exceptions (invalid Base64, decode errors)
        - It removes whitespace (attackers often format Base64 nicely)
        - It validates Base64 format (length must be multiple of 4)
        - It uses strict validation to reject malformed Base64

        Returns:
            Decoded string if successful, None if invalid Base64
        """
        try:
            # Remove all whitespace - attackers might format Base64 with spaces/newlines
            compact = re.sub(r"\s+", "", text)

            # Base64 requirement: length must be multiple of 4
            if len(compact) % 4 != 0:
                return None  # Invalid Base64 format

            # Decode with strict validation (rejects invalid characters/padding)
            decoded_bytes = base64.b64decode(compact, validate=True)

            # Convert bytes back to string, ignoring any invalid UTF-8 sequences
            return decoded_bytes.decode("utf-8", errors="ignore")

        except Exception:
            # Any error (invalid Base64, decode failure, etc.) - return None
            return None

    def _is_mostly_printable(self, text: str, threshold: float = 0.9) -> bool:
        """
        Checks if text is mostly printable characters (not binary data).

        Why needed? Base64 can encode anything - images, executables, compressed files.
        We only want to decode text that becomes readable text, not binary blobs.

        Security impact:
        - Prevents decoding to unreadable binary that could crash text processors
        - Ensures decoded content is actually human-readable/scannable text
        - Threshold (90% by default) allows some special characters but rejects mostly-binary

        Returns:
            True if >= threshold percentage of characters are printable
        """
        if not text:
            return False  # Empty text is not printable

        # Count printable characters (letters, numbers, punctuation, spaces, etc.)
        printable_count = sum(1 for c in text if c.isprintable())

        # Calculate percentage of printable characters
        printable_ratio = printable_count / len(text)

        # Return True if above threshold (default 90%)
        return printable_ratio >= threshold
