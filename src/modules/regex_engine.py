import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class RegexRule:
    """Defines a regex pattern to search for."""
    id: str
    pattern: str
    flags: int = re.IGNORECASE
    entity_type: Optional[str] = None
    confidence: float = 1.0

@dataclass
class RegexMatch:
    rule_id: str
    entity_type: str
    start: int
    end: int
    text: str
    confidence: float


class RegexEngine:
    """
    Dumb regex execution engine.

    It does NOT:
    - decide which regex to run
    - understand entities
    - know about signals, views, or intent

    It ONLY:
    - runs given regex rules on given text
    - returns matches with spans
    """

    def __init__(self, rules: List[RegexRule]):
        self.rules = [
            (rule, re.compile(rule.pattern, rule.flags))
            for rule in rules
        ]

    def run(self, text: str) -> List[RegexMatch]:
        results: List[RegexMatch] = []

        for rule, compiled in self.rules:
            for match in compiled.finditer(text):
                results.append(
                    RegexMatch(
                        rule_id=rule.id,
                        entity_type=rule.entity_type or "UNKNOWN",
                        start=match.start(),
                        end=match.end(),
                        text=match.group(),
                        confidence=rule.confidence,
                    )
                )

        return results
