"""Tests for the Categorizer — threshold band mapping."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from classifier.categorizer import Categorizer, ClassificationResult
from classifier.scorer import ScoredResult


class TestCategorizer:
    """Test threshold band mapping and final classification."""

    def setup_method(self):
        self.categorizer = Categorizer()

    def test_high_confidence_classification(self):
        """Confidence >= 0.75 should give a clean classification."""
        scored = ScoredResult(
            subtype="Aadhaar number",
            category="PII",
            regulation="DPDP",
            confidence=0.85,
            matched_by=["rule", "pattern"],
            description="High confidence Aadhaar number detected by rule, pattern engine(s).",
            rule_confidence=0.7,
            pattern_confidence=0.9,
        )
        result = self.categorizer.categorize(scored, "users", "aadhaar_no")
        assert result.subtype == "Aadhaar number"
        assert result.category == "PII"
        assert result.confidence == 0.85

    def test_below_low_threshold_becomes_non_sensitive(self):
        """Confidence < 0.25 (low threshold) should classify as Non-Sensitive."""
        scored = ScoredResult(
            subtype="Email address",
            category="PII",
            regulation="DPDP",
            confidence=0.15,
            matched_by=["rule"],
            description="Low confidence",
        )
        result = self.categorizer.categorize(scored, "logs", "misc_field")
        assert result.subtype == "Non-Sensitive"
        assert result.category == "Non-Sensitive"

    def test_medium_confidence_classification(self):
        """Medium confidence should preserve classification with note."""
        scored = ScoredResult(
            subtype="Bank account number",
            category="Financial Sensitive (RBI-DADP)",
            regulation="RBI-DADP",
            confidence=0.55,
            matched_by=["rule"],
            description="Medium confidence Bank account number detected by rule engine(s).",
        )
        result = self.categorizer.categorize(scored, "payments", "acct_no")
        assert result.subtype == "Bank account number"
        assert result.category == "Financial Sensitive (RBI-DADP)"

    def test_to_dict_output(self):
        """ClassificationResult.to_dict() should produce API-ready dict."""
        scored = ScoredResult(
            subtype="PAN",
            category="PII",
            regulation="DPDP",
            confidence=0.75,
            matched_by=["rule", "pattern"],
            description="High confidence PAN detected.",
        )
        result = self.categorizer.categorize(scored, "kyc", "pan_number")
        d = result.to_dict()
        assert "table" in d
        assert "column" in d
        assert "subtype" in d
        assert "category" in d
        assert "regulation" in d
        assert "confidence" in d
        assert "matched_by" in d
        assert "description" in d
        assert d["table"] == "kyc"
        assert d["column"] == "pan_number"
