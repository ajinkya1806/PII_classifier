"""Tests for the Rule Engine."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.rule_engine import RuleEngine


class TestRuleEngine:
    """Test keyword/name matching against taxonomy subtypes."""

    def setup_method(self):
        self.engine = RuleEngine()

    def test_aadhaar_field_detection(self):
        """Column named 'aadhaar_number' should match Aadhaar subtype."""
        matches = self.engine.classify("aadhaar_number", "users")
        assert len(matches) > 0
        assert matches[0].subtype == "Aadhaar number"
        assert matches[0].category == "PII"
        assert matches[0].regulation == "DPDP"
        assert matches[0].confidence > 0.4

    def test_pan_field_detection(self):
        """Column named 'pan_card' should match PAN subtype."""
        matches = self.engine.classify("pan_card", "kyc_details")
        assert len(matches) > 0
        top = matches[0]
        assert top.subtype == "PAN"
        assert top.confidence > 0.4

    def test_email_field_detection(self):
        """Column named 'email_address' should match Email."""
        matches = self.engine.classify("email_address", "contacts")
        assert len(matches) > 0
        assert matches[0].subtype == "Email address"

    def test_bank_account_detection(self):
        """Column named 'bank_account_no' should match Financial category."""
        matches = self.engine.classify("bank_account_no", "payments")
        assert len(matches) > 0
        assert matches[0].category == "Financial Sensitive (RBI-DADP)"

    def test_sensitive_demographic(self):
        """Column named 'religion' should match Sensitive Personal Data."""
        matches = self.engine.classify("religion", "demographics")
        assert len(matches) > 0
        assert matches[0].category == "Sensitive Personal Data (DPDP)"

    def test_no_match_for_generic_column(self):
        """Column named 'created_at' should return empty or very low confidence."""
        matches = self.engine.classify("created_at", "logs")
        # Either no matches or all below a reasonable threshold
        if matches:
            assert matches[0].confidence < 0.3

    def test_multiple_matches_sorted(self):
        """Results should be sorted by confidence descending."""
        matches = self.engine.classify("phone_number", "users")
        if len(matches) > 1:
            for i in range(len(matches) - 1):
                assert matches[i].confidence >= matches[i + 1].confidence

    def test_table_name_context(self):
        """Table name should provide additional matching context."""
        # 'salary' field in 'employee' table
        matches = self.engine.classify("salary", "employee_payroll")
        assert len(matches) > 0
