"""
Categorizer — maps scored results to final DPDP/RBI-DADP classifications
with threshold bands and human-readable labels.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from classifier.scorer import ScoredResult

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS_PATH = Path(__file__).parent.parent / "config" / "weights.yaml"


@dataclass
class ClassificationResult:
    """Final classification output for a single field."""
    table: str
    column: str
    subtype: str
    category: str
    regulation: str
    confidence: float
    matched_by: list
    description: str
    rule_confidence: float = 0.0
    pattern_confidence: float = 0.0
    llm_confidence: float = 0.0
    llm_justification: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API-friendly dictionary."""
        return {
            "table": self.table,
            "column": self.column,
            "subtype": self.subtype,
            "category": self.category,
            "regulation": self.regulation,
            "confidence": self.confidence,
            "matched_by": self.matched_by,
            "description": self.description,
            "rule_confidence": self.rule_confidence,
            "pattern_confidence": self.pattern_confidence,
            "llm_confidence": self.llm_confidence,
            "llm_justification": self.llm_justification,
        }


class Categorizer:
    """
    Maps scored results through confidence threshold bands to produce
    final classification with appropriate category and regulation labels.
    """

    # Valid categories per the spec
    VALID_CATEGORIES = [
        "Non-Sensitive",
        "PII",
        "Sensitive Personal Data (DPDP)",
        "Financial Sensitive (RBI-DADP)",
    ]

    def __init__(self, weights_path: Optional[str] = None):
        self._weights_path = Path(weights_path) if weights_path else DEFAULT_WEIGHTS_PATH
        self._last_mtime: float = 0
        self._bands: Dict[str, float] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load confidence bands from weights.yaml (hot-reloadable)."""
        try:
            current_mtime = os.path.getmtime(self._weights_path)
            if current_mtime != self._last_mtime:
                with open(self._weights_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                self._bands = data.get("confidence_bands", {
                    "high": 0.75,
                    "medium": 0.50,
                    "low": 0.25,
                })
                self._last_mtime = current_mtime
                logger.info(f"Loaded confidence bands: {self._bands}")
        except Exception as e:
            logger.error(f"Failed to load confidence bands: {e}")
            if not self._bands:
                self._bands = {"high": 0.75, "medium": 0.50, "low": 0.25}

    def categorize(
        self,
        scored_result: ScoredResult,
        table_name: str,
        column_name: str,
    ) -> ClassificationResult:
        """
        Apply threshold bands and produce final classification.

        If confidence < low threshold, the field is classified as Non-Sensitive.
        """
        self._load_config()

        low_threshold = self._bands.get("low", 0.25)

        # Below the low threshold → Non-Sensitive
        if scored_result.confidence < low_threshold:
            return ClassificationResult(
                table=table_name,
                column=column_name,
                subtype="Non-Sensitive",
                category="Non-Sensitive",
                regulation="None",
                confidence=scored_result.confidence,
                matched_by=scored_result.matched_by,
                description="Field does not match any sensitive data pattern.",
                rule_confidence=scored_result.rule_confidence,
                pattern_confidence=scored_result.pattern_confidence,
                llm_confidence=scored_result.llm_confidence,
                llm_justification=scored_result.llm_justification,
            )

        # Validate category
        category = scored_result.category
        if category not in self.VALID_CATEGORIES:
            logger.warning(
                f"Unexpected category '{category}' for {table_name}.{column_name}, "
                f"defaulting to 'PII'"
            )
            category = "PII"

        # Determine confidence band label for description
        high_threshold = self._bands.get("high", 0.75)
        medium_threshold = self._bands.get("medium", 0.50)

        if scored_result.confidence >= high_threshold:
            band = "high"
        elif scored_result.confidence >= medium_threshold:
            band = "medium"
        else:
            band = "low"

        # Refine description with band info
        description = scored_result.description
        if band == "low" and scored_result.subtype != "Non-Sensitive":
            description = (
                f"Low confidence {scored_result.subtype} — "
                f"may need manual review."
            )

        return ClassificationResult(
            table=table_name,
            column=column_name,
            subtype=scored_result.subtype,
            category=category,
            regulation=scored_result.regulation,
            confidence=scored_result.confidence,
            matched_by=scored_result.matched_by,
            description=description,
            rule_confidence=scored_result.rule_confidence,
            pattern_confidence=scored_result.pattern_confidence,
            llm_confidence=scored_result.llm_confidence,
            llm_justification=scored_result.llm_justification,
        )
