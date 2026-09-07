"""
Scorer — weighted confidence combination from rule, pattern, and LLM engines.

Loads weights from weights.yaml (hot-reloadable) and validates they sum to 1.0.
When LLM is not invoked, its weight is redistributed proportionally.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from engines.llm_engine import LLMResult
from engines.pattern_engine import PatternMatch
from engines.rule_engine import RuleMatch

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS_PATH = Path(__file__).parent.parent / "config" / "weights.yaml"


@dataclass
class ScoredResult:
    """Combined scored classification result."""
    subtype: str
    category: str
    regulation: str
    confidence: float
    matched_by: List[str]  # which engines contributed: ["rule", "pattern", "llm"]
    description: str
    rule_confidence: float = 0.0
    pattern_confidence: float = 0.0
    llm_confidence: float = 0.0
    llm_justification: str = ""


class Scorer:
    """
    Weighted combination of engine scores.

    Weights are loaded from weights.yaml and must sum to 1.0.
    When the LLM engine is not invoked, its weight is redistributed
    proportionally to the rule and pattern engines.
    """

    def __init__(self, weights_path: Optional[str] = None):
        self._weights_path = Path(weights_path) if weights_path else DEFAULT_WEIGHTS_PATH
        self._last_mtime: float = 0
        self._weights: Dict[str, float] = {}
        self._config: Dict[str, Any] = {}
        self._load_weights()

    def _load_weights(self) -> None:
        """Load or reload weights.yaml if the file has changed."""
        try:
            current_mtime = os.path.getmtime(self._weights_path)
            if current_mtime != self._last_mtime:
                with open(self._weights_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                self._weights = data.get("engine_weights", {
                    "rule_engine": 0.35,
                    "pattern_engine": 0.45,
                    "llm_engine": 0.20,
                })
                self._config = data

                # Validate weights sum to ~1.0
                total = sum(self._weights.values())
                if abs(total - 1.0) > 0.01:
                    raise ValueError(
                        f"Engine weights must sum to 1.0, got {total:.4f}: {self._weights}"
                    )

                self._last_mtime = current_mtime
                logger.info(f"Loaded engine weights: {self._weights}")
        except Exception as e:
            logger.error(f"Failed to load weights: {e}")
            if not self._weights:
                # Use defaults if first load fails
                self._weights = {
                    "rule_engine": 0.35,
                    "pattern_engine": 0.45,
                    "llm_engine": 0.20,
                }

    def compute_score(
        self,
        rule_matches: List[RuleMatch],
        pattern_match: Optional[PatternMatch],
        llm_result: Optional[LLMResult],
    ) -> ScoredResult:
        """
        Compute the weighted combination of engine scores.

        When LLM is not invoked, its weight is redistributed proportionally.
        """
        self._load_weights()

        w_rule = self._weights.get("rule_engine", 0.35)
        w_pattern = self._weights.get("pattern_engine", 0.45)
        w_llm = self._weights.get("llm_engine", 0.20)

        # Get best rule match
        rule_conf = rule_matches[0].confidence if rule_matches else 0.0
        best_rule = rule_matches[0] if rule_matches else None

        # Pattern confidence
        pattern_conf = pattern_match.confidence if pattern_match else 0.0

        # LLM confidence
        llm_conf = llm_result.confidence if llm_result else 0.0

        matched_by = []
        if rule_conf > 0:
            matched_by.append("rule")
        if pattern_conf > 0:
            matched_by.append("pattern")
        if llm_result and llm_conf > 0:
            matched_by.append("llm")

        # Redistribute LLM weight if not used
        if llm_result is None:
            # Proportionally redistribute LLM weight
            total_non_llm = w_rule + w_pattern
            if total_non_llm > 0:
                w_rule = w_rule / total_non_llm
                w_pattern = w_pattern / total_non_llm
            w_llm = 0.0

        # Compute weighted score
        final_confidence = (
            w_rule * rule_conf
            + w_pattern * pattern_conf
            + w_llm * llm_conf
        )
        final_confidence = round(min(final_confidence, 1.0), 4)

        # Determine the best subtype from available sources
        subtype, category, regulation = self._determine_classification(
            best_rule, pattern_match, llm_result
        )

        # Generate description
        description = self._generate_description(
            subtype, category, matched_by, final_confidence
        )

        return ScoredResult(
            subtype=subtype,
            category=category,
            regulation=regulation,
            confidence=final_confidence,
            matched_by=matched_by,
            description=description,
            rule_confidence=round(rule_conf, 4),
            pattern_confidence=round(pattern_conf, 4),
            llm_confidence=round(llm_conf, 4),
            llm_justification=llm_result.justification if llm_result else "",
        )

    def _determine_classification(
        self,
        best_rule: Optional[RuleMatch],
        pattern_match: Optional[PatternMatch],
        llm_result: Optional[LLMResult],
    ) -> tuple:
        """
        Determine the best subtype/category/regulation from available engine results.
        Priority: pattern match (if high confidence) > LLM result > rule match.
        """
        # If pattern has very high confidence and rule agrees, prefer that
        if pattern_match and pattern_match.confidence > 0.5 and best_rule:
            return (best_rule.subtype, best_rule.category, best_rule.regulation)

        # If LLM gave a result, and is more confident than rule alone
        if llm_result and llm_result.confidence > 0.3:
            if best_rule and best_rule.confidence >= llm_result.confidence:
                return (best_rule.subtype, best_rule.category, best_rule.regulation)
            return (llm_result.subtype, llm_result.category, llm_result.regulation)

        # Default to best rule match
        if best_rule:
            return (best_rule.subtype, best_rule.category, best_rule.regulation)

        return ("Non-Sensitive", "Non-Sensitive", "None")

    def _generate_description(
        self,
        subtype: str,
        category: str,
        matched_by: List[str],
        confidence: float,
    ) -> str:
        """Generate a human-readable description (<20 words)."""
        if subtype == "Non-Sensitive":
            return "Field does not match any sensitive data pattern."

        engines = ", ".join(matched_by) if matched_by else "no engine"
        conf_label = "high" if confidence >= 0.75 else "medium" if confidence >= 0.5 else "low"

        return f"{conf_label.capitalize()} confidence {subtype} detected by {engines} engine(s)."

    def get_llm_threshold(self) -> float:
        """Get the LLM fallback threshold from config."""
        self._load_weights()
        return self._config.get("llm_fallback_threshold", 0.4)
