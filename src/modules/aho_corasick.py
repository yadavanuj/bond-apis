from collections import deque
from typing import List, Dict, Set, Any, Optional
from dataclasses import dataclass
from enum import Enum

MATCH_SUBSTRING = 0b0001
MATCH_PREFIX    = 0b0010
MATCH_SUFFIX    = 0b0100
MATCH_FULL_WORD = 0b1000
MATCH_FILTERED_WORD = 0b10000

WORD_TYPE_ANY   = 0
WORD_TYPE_ALPHA = 0b001
WORD_TYPE_DIGIT = 0b010
WORD_TYPE_ALNUM = 0b100

MATCH_WEIGHTS = {
    MATCH_FULL_WORD: 1.0,
    MATCH_PREFIX: 0.6,
    MATCH_SUFFIX: 0.6,
    MATCH_SUBSTRING: 0.2,
    MATCH_FILTERED_WORD: 0.7
}

class CharType(str, Enum):
    ANY = "any"
    ALPHA = "alpha"
    DIGIT = "digit"
    ALPHANUMERIC = "alphanumeric"

@dataclass
class WordFilter:
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    exact_length: Optional[int] = None
    word_type: CharType = CharType.ANY
    label: Optional[str] = None
    must_contain: Optional[List[str]] = None
    min_occurrences: Optional[Dict[str, int]] = None
    max_occurrences: Optional[Dict[str, int]] = None

class AhoCorasick:
    """
    A reusable Aho-Corasick algorithm implementation for efficient 
    multi-pattern string matching.

    Features:
    - Efficient multi-pattern searching (O(n) scan time).
    - Support for overlapping matches and normalization.
    - Word boundary detection (start/end of word).
    - Signal weighting based on match type for intent confidence.
    - Capability to filter and extract words from text based on criteria.

    Signal Weighting:
    - MATCH_FULL_WORD (8) : 1.0
    - MATCH_PREFIX (2)    : 0.6
    - MATCH_SUFFIX (4)    : 0.6
    - MATCH_SUBSTRING (1) : 0.2
    - MATCH_FILTERED_WORD (16): 0.7
    """

    def __init__(self):
        self.transitions: List[Dict[str, int]] = [{}]
        self.outputs: List[Set[str]] = [set()]
        self.fail: List[int] = [0]
        self.is_built = False

    def add_pattern(self, pattern: str) -> None:
        """Adds a pattern to the trie."""
        if self.is_built:
            raise RuntimeError("Cannot add patterns after building the automaton.")
        
        state = 0
        for char in pattern:
            if char not in self.transitions[state]:
                self.transitions[state][char] = len(self.transitions)
                self.transitions.append({})
                self.outputs.append(set())
                self.fail.append(0)
            state = self.transitions[state][char]
        self.outputs[state].add(pattern)

    def build(self) -> None:
        """Builds the failure links and output sets."""
        queue = deque()
        
        # Initialize depth 1
        for char, next_state in self.transitions[0].items():
            queue.append(next_state)
            self.fail[next_state] = 0
        
        while queue:
            current_state = queue.popleft()
            
            for char, next_state in self.transitions[current_state].items():
                queue.append(next_state)
                
                fail_state = self.fail[current_state]
                while fail_state > 0 and char not in self.transitions[fail_state]:
                    fail_state = self.fail[fail_state]
                
                self.fail[next_state] = self.transitions[fail_state].get(char, 0)
                self.outputs[next_state].update(self.outputs[self.fail[next_state]])
        
        self.is_built = True

    def search(self, text: str, word_filters: Optional[List[WordFilter]] = None) -> List[Dict[str, Any]]:
        """
        Scans the text for all added patterns.
        Returns a list of dictionaries with match details.

        If word_filters are provided, it also extracts words from the text that match
        the specified criteria.

        Algorithm Steps:
        1. Build the automaton if not already built.
        2. Initialize state, results list, and word extraction variables.
        3. Pre-calculate allowed special characters from filters.
        4. For each character in text:
           a. Perform Aho-Corasick traversal to find pattern matches.
           b. For each matched pattern, determine match type and add to results.
           c. Handle word extraction: track word boundaries and validate words against filters.
        5. Handle any trailing word at the end of text.
        6. Return all matches.
        """
        # Step 1: Ensure the automaton is built
        if not self.is_built:
            self.build()

        # Step 2: Initialize variables
        state = 0  # Current state in the automaton
        results = []  # List to store all match results
        current_word_start = -1  # Start index of the current word being extracted

        # Step 3: Pre-calculate allowed special characters for word extraction
        # This allows treating special characters (like '@' in emails) as part of a word
        # during scanning if any filter requires them.
        allowed_special_chars = set()
        if word_filters:
            for wf in word_filters:
                if wf.must_contain:
                    for s in wf.must_contain:
                        for c in s:
                            if not c.isalnum():
                                allowed_special_chars.add(c)

        # Step 4: Scan through each character in the text
        for i, char in enumerate(text):
            # Step 4a: Aho-Corasick Traversal
            # Follow failure links until we find a valid transition or reach root
            while state > 0 and char not in self.transitions[state]:
                state = self.fail[state]
            # Move to the next state based on the current character
            state = self.transitions[state].get(char, 0)

            # Check for pattern matches at the current state
            for pattern in self.outputs[state]:
                # Calculate match boundaries
                start = i - len(pattern) + 1
                end = i + 1
                # Determine if this is a word boundary match
                is_word_start = (start == 0) or (not text[start - 1].isalnum())
                is_word_end = (end == len(text)) or (not text[end].isalnum())

                # Classify match type based on boundaries
                if is_word_start and is_word_end:
                    match_type = MATCH_FULL_WORD
                elif is_word_start:
                    match_type = MATCH_PREFIX
                elif is_word_end:
                    match_type = MATCH_SUFFIX
                else:
                    match_type = MATCH_SUBSTRING

                # Determine word type of the pattern
                word_type = WORD_TYPE_ANY
                if pattern.isalpha():
                    word_type = WORD_TYPE_ALPHA
                elif pattern.isdigit():
                    word_type = WORD_TYPE_DIGIT
                elif pattern.isalnum():
                    word_type = WORD_TYPE_ALNUM

                # Get weight for this match type
                weight = MATCH_WEIGHTS[match_type]

                # Add match to results
                results.append({
                    "keyword": pattern,
                    "start": start,
                    "end": end,
                    "length": len(pattern),
                    "is_word_start": is_word_start,
                    "is_word_end": is_word_end,
                    "match_type": match_type,
                    "word_type": word_type,
                    "weight": weight,
                })

            # Step 4c: Word Extraction Logic
            if word_filters:
                # Determine if current character is valid for word extraction
                # Valid if alphanumeric or explicitly allowed by filters
                is_valid_char = char.isalnum()
                if not is_valid_char:
                    if char in allowed_special_chars:
                        is_valid_char = True

                if is_valid_char:
                    # Start or continue a word
                    if current_word_start == -1:
                        current_word_start = i
                else:
                    # End of word detected, process the word
                    if current_word_start != -1:
                        self._process_word_filters(text, current_word_start, i, word_filters, results)
                        current_word_start = -1

        # Step 5: Handle any word that extends to the end of the text
        if word_filters and current_word_start != -1:
            self._process_word_filters(text, current_word_start, len(text), word_filters, results)

        # Step 6: Return all matches
        return results

    def _process_word_filters(self, text: str, start: int, end: int, word_filters: List[WordFilter], results: List[Dict[str, Any]]) -> None:
        """
        Validates a candidate word against a list of filters.

        This method is called whenever a word boundary is detected during text scanning.
        It checks the extracted word against each provided filter using AND logic within filters
        and OR logic between filters. Only words that pass at least one filter are added to results.

        Logic:
        - Iterates through each filter in word_filters.
        - Applies AND logic within a single filter: All constraints (length, type, must_contain, etc.) must pass.
        - Applies OR logic between filters: If the word matches Filter A OR Filter B, it is accepted.
        - Collects labels from all matching filters.
        - Filtering happens at word boundaries (end of word), not over-doing it by checking every character.
        """
        word = text[start:end]
        length = len(word)
        matching_labels = []
        
        # Performance Optimization:
        # Pre-calculate character type properties for the word.
        # Instead of iterating over the word for every filter to check isalpha/isdigit/isalnum,
        # we compute these once using Python's optimized string methods (which are implemented in C).
        # This reduces the complexity from O(F * L) to O(L) where F is number of filters and L is word length.
        is_alpha = word.isalpha()
        is_digit = word.isdigit()
        is_alnum = word.isalnum()

        for word_filter in word_filters:
            # Length Checks: Ensure word meets length criteria
            if word_filter.exact_length is not None and length != word_filter.exact_length:
                continue
            if word_filter.min_length is not None and length < word_filter.min_length:
                continue
            if word_filter.max_length is not None and length > word_filter.max_length:
                continue

            # Character Type Validation: Check if word matches the required character type
            valid_char_type = True
            if word_filter.word_type == CharType.ALPHA:
                # All characters must be alphabetic
                if not is_alpha:
                    valid_char_type = False
            elif word_filter.word_type == CharType.DIGIT:
                # All characters must be digits
                if not is_digit:
                    valid_char_type = False
            elif word_filter.word_type == CharType.ALPHANUMERIC:
                # All characters must be alphanumeric (letters or digits)
                if not is_alnum:
                    valid_char_type = False
            # For CharType.ANY, no type validation needed
            if not valid_char_type:
                continue

            # Constraints Validation: Additional substring and occurrence checks
            # AND logic: All constraints within this filter must be satisfied.
            if word_filter.must_contain:
                # Word must contain all specified substrings
                if any(sub not in word for sub in word_filter.must_contain):
                    continue

            if word_filter.min_occurrences:
                # Word must have at least the specified number of occurrences for each substring
                if any(word.count(sub) < min_count for sub, min_count in word_filter.min_occurrences.items()):
                    continue

            if word_filter.max_occurrences:
                # Word must not exceed the specified number of occurrences for each substring
                if any(word.count(sub) > max_count for sub, max_count in word_filter.max_occurrences.items()):
                    continue

            # If all checks pass, add the filter's label to matching labels
            if word_filter.label:
                matching_labels.append(word_filter.label)

        # If the word matched at least one filter, add it to results
        if matching_labels:
            # Determine the word_type based on the word's content
            word_type = WORD_TYPE_ANY
            if is_alpha:
                word_type = WORD_TYPE_ALPHA
            elif is_digit:
                word_type = WORD_TYPE_DIGIT
            elif is_alnum:
                word_type = WORD_TYPE_ALNUM

            results.append({
                "keyword": word,
                "start": start,
                "end": end,
                "length": length,
                "is_word_start": True,
                "is_word_end": True,
                "match_type": MATCH_FILTERED_WORD,
                "word_type": word_type,
                "weight": MATCH_WEIGHTS[MATCH_FILTERED_WORD],
                "filter_labels": matching_labels
            })

    def search_normalized(self, text: str, word_filters: Optional[List[WordFilter]] = None) -> List[Dict[str, Any]]:
        """
        Scans the text for all added patterns and returns non-overlapping matches.
        Matches are prioritized by start position (earliest first), then length (longest first).
        """
        matches = self.search(text, word_filters=word_filters)
        matches.sort(key=lambda x: (x['start'], -x['length']))
        
        normalized_matches = []
        last_end_index = -1
        
        for match in matches:
            if match['start'] >= last_end_index:
                normalized_matches.append(match)
                last_end_index = match['end']
                
        return normalized_matches