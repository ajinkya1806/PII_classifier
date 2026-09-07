"""
Rule Engine — keyword/name matching driven entirely by taxonomy.yaml.

Adding a new subtype requires zero code changes — just add an entry to taxonomy.yaml.
The engine hot-reloads taxonomy.yaml when the file changes (mtime check).
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Default path to taxonomy config
DEFAULT_TAXONOMY_PATH = Path(__file__).parent.parent / "config" / "taxonomy.yaml"


@dataclass
class RuleMatch:
    """A single rule-engine match for a field."""
    subtype: str
    category: str
    regulation: str
    confidence: float
    matched_keywords: List[str]


class RuleEngine:
    """
    Keyword/name matching engine driven by taxonomy.yaml.

    Normalizes field names (lowercase, strip special chars) and checks
    against each subtype's keyword list. Supports substring and fuzzy matching.
    """

    def __init__(self, taxonomy_path: Optional[str] = None):
        self._taxonomy_path = Path(taxonomy_path) if taxonomy_path else DEFAULT_TAXONOMY_PATH
        self._taxonomy: List[Dict[str, Any]] = []
        self._last_mtime: float = 0
        self._load_taxonomy()

    def _load_taxonomy(self) -> None:
        """Load or reload taxonomy.yaml if the file has changed."""
        try:
            current_mtime = os.path.getmtime(self._taxonomy_path)
            if current_mtime != self._last_mtime:
                with open(self._taxonomy_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                self._taxonomy = data.get("subtypes", [])
                self._last_mtime = current_mtime
                logger.info(
                    f"Loaded taxonomy with {len(self._taxonomy)} subtypes "
                    f"from {self._taxonomy_path}"
                )
        except Exception as e:
            logger.error(f"Failed to load taxonomy: {e}")
            if not self._taxonomy:
                raise

    def _normalize(self, text: str) -> str:
        """Normalize a field/table name for matching."""
        # Lowercase, replace common delimiters with underscores, strip extra
        text = text.lower().strip()
        text = re.sub(r'[\s\-\.]+', '_', text)
        text = re.sub(r'[^a-z0-9_]', '', text)
        return text

    def classify(
        self,
        field_name: str,
        table_name: str = "",
        additional_context: str = "",
    ) -> List[RuleMatch]:
        """
        Classify a field by matching its name (and optionally the table name)
        against taxonomy keywords.

        Returns a list of RuleMatch sorted by confidence descending.
        """
        # Hot-reload check
        self._load_taxonomy()

        normalized_field = self._normalize(field_name)
        normalized_table = self._normalize(table_name) if table_name else ""
        combined = f"{normalized_table}_{normalized_field}" if normalized_table else normalized_field

        matches: List[RuleMatch] = []

        for subtype in self._taxonomy:
            keywords = subtype.get("keywords", [])
            base_confidence = subtype.get("base_keyword_confidence", 0.5)
            matched_kws: List[str] = []
            best_score = 0.0

            for kw in keywords:
                norm_kw = self._normalize(kw)
                score = self._compute_keyword_score(
                    norm_kw, normalized_field, combined
                )
                if score > 0:
                    matched_kws.append(kw)
                    best_score = max(best_score, score)

            if matched_kws:
                # Final confidence = base * best_match_score
                final_confidence = min(base_confidence * best_score, 1.0)

                matches.append(
                    RuleMatch(
                        subtype=subtype["name"],
                        category=subtype["category"],
                        regulation=subtype["regulation"],
                        confidence=round(final_confidence, 4),
                        matched_keywords=matched_kws,
                    )
                )

        # Sort by confidence descending
        matches.sort(key=lambda m: m.confidence, reverse=True)

        if matches:
            logger.debug(
                f"Rule engine: {field_name} → top match: "
                f"{matches[0].subtype} ({matches[0].confidence:.2f})"
            )

        return matches

    def _compute_keyword_score(
        self, keyword: str, field_name: str, combined: str
    ) -> float:
        """
        Compute a match score between a keyword and a field name.

        Scoring:
          - Exact match → 1.0
          - Field name contains keyword or vice versa → 0.85
          - Combined (table_field) contains keyword → 0.70
          - Partial token overlap → 0.50
        """
        if keyword == field_name:
            return 1.0

        if keyword in field_name or field_name in keyword:
            return 0.85

        if keyword in combined:
            return 0.70

        # Token-level overlap
        kw_tokens = set(keyword.split("_"))
        field_tokens = set(field_name.split("_"))
        overlap = kw_tokens & field_tokens
        if overlap and len(overlap) >= 1:
            # Score based on fraction of keyword tokens matched
            token_score = len(overlap) / len(kw_tokens)
            if token_score >= 0.5:
                return 0.50 * token_score

        return 0.0

    def get_taxonomy(self) -> List[Dict[str, Any]]:
        """Return the current taxonomy data (for LLM prompts, etc.)."""
        self._load_taxonomy()
        return self._taxonomy
