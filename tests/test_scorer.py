"""Tests for the Scorer — weighted confidence combination."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from classifier.scorer import Scorer, ScoredResult
from engines.llm_engine import LLMResult
from engines.pattern_engine import PatternMatch
from engines.rule_engine import RuleMatch


class TestScorer:
    """Test weighted combination of engine scores."""

    def setup_method(self):
        self.scorer = Scorer()

    def test_rule_only_scoring(self):
        """Score with only rule engine match, no pattern or LLM."""
        rule_matches = [
            RuleMatch(
                subtype="Email address",
                category="PII",
                regulation="DPDP",
                confidence=0.6,
                matched_keywords=["email"],
            )
        ]
        result = self.scorer.compute_score(rule_matches, None, None)
        assert result.subtype == "Email address"
        assert result.confidence > 0
        assert "rule" in result.matched_by
        assert "llm" not in result.matched_by

    def test_rule_and_pattern_scoring(self):
        """Combined rule + pattern should produce higher confidence."""
        rule_matches = [
            RuleMatch(
                subtype="PAN",
                category="PII",
                regulation="DPDP",
                confidence=0.65,
                matched_keywords=["pan"],
            )
        ]
        pattern_match = PatternMatch(
            subtype="PAN",
            pattern_ref="pan",
            confidence=0.9,
            matched_count=9,
            total_count=10,
            validator_name="validate_pan",
        )
        result = self.scorer.compute_score(rule_matches, pattern_match, None)
        assert result.confidence > 0.5
        assert "rule" in result.matched_by
        assert "pattern" in result.matched_by

    def test_llm_weight_redistribution(self):
        """When LLM is None, its weight should be redistributed."""
        rule_matches = [
            RuleMatch(
                subtype="IFSC code",
                category="Financial Sensitive (RBI-DADP)",
                regulation="RBI-DADP",
                confidence=0.5,
                matched_keywords=["ifsc"],
            )
        ]
        # Without LLM, rule weight = 0.35/(0.35+0.45) ≈ 0.4375
        # pattern weight = 0.45/(0.35+0.45) ≈ 0.5625
        result = self.scorer.compute_score(rule_matches, None, None)
        assert result.confidence > 0  # Should be > 0 since rule matched

    def test_all_three_engines(self):
        """All three engines contributing should combine properly."""
        rule_matches = [
            RuleMatch(
                subtype="Aadhaar number",
                category="PII",
                regulation="DPDP",
                confidence=0.7,
                matched_keywords=["aadhaar"],
            )
        ]
        pattern_match = PatternMatch(
            subtype="",
            pattern_ref="aadhaar",
            confidence=0.85,
            matched_count=85,
            total_count=100,
            validator_name="validate_aadhaar",
        )
        llm_result = LLMResult(
            subtype="Aadhaar number",
            category="PII",
            regulation="DPDP",
            confidence=0.9,
            justification="Column name and 12-digit pattern confirm Aadhaar",
        )
        result = self.scorer.compute_score(rule_matches, pattern_match, llm_result)
        # 0.35*0.7 + 0.45*0.85 + 0.20*0.9 = 0.245 + 0.3825 + 0.18 = 0.8075
        assert abs(result.confidence - 0.8075) < 0.01
        assert "rule" in result.matched_by
        assert "pattern" in result.matched_by
        assert "llm" in result.matched_by

    def test_non_sensitive_with_no_matches(self):
        """No engine matches should result in Non-Sensitive."""
        result = self.scorer.compute_score([], None, None)
        assert result.subtype == "Non-Sensitive"
        assert result.confidence == 0.0

    def test_description_generation(self):
        """Description should be < 20 words."""
        rule_matches = [
            RuleMatch(
                subtype="PAN",
                category="PII",
                regulation="DPDP",
                confidence=0.6,
                matched_keywords=["pan"],
            )
        ]
        result = self.scorer.compute_score(rule_matches, None, None)
        assert len(result.description.split()) <= 20
