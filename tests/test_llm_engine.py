"""Tests for the LLM Engine — mock Ollama responses and graceful failure."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.llm_engine import LLMEngine, LLMResult


class TestLLMEngine:
    """Test LLM fallback engine behavior."""

    def test_parse_valid_response(self):
        """Valid JSON response should be parsed correctly."""
        engine = LLMEngine()
        response_text = json.dumps({
            "subtype": "PAN",
            "category": "PII",
            "regulation": "DPDP",
            "confidence": 0.85,
            "justification": "Column name suggests PAN card data",
        })
        result = engine._parse_response(response_text)
        assert result is not None
        assert result.subtype == "PAN"
        assert result.confidence == 0.85
        assert result.category == "PII"

    def test_parse_invalid_response(self):
        """Invalid JSON should return None gracefully."""
        engine = LLMEngine()
        result = engine._parse_response("This is not JSON at all")
        assert result is None

    @patch("engines.llm_engine.LLMEngine._get_client")
    def test_ollama_unreachable_graceful(self, mock_get_client):
        """When Ollama is unreachable, classify should return None."""
        mock_get_client.return_value = None

        engine = LLMEngine()
        engine._available = False
        engine._client = None

        result = engine.classify(
            field_name="pan_no",
            table_name="users",
            masked_samples=["*****####*"],
            taxonomy_subtypes=[{"name": "PAN", "category": "PII", "regulation": "DPDP"}],
        )
        assert result is None

    def test_confidence_clamped_to_range(self):
        """Confidence values should be clamped between 0 and 1."""
        engine = LLMEngine()
        # Confidence > 1.0
        response = json.dumps({
            "subtype": "Email address",
            "category": "PII",
            "regulation": "DPDP",
            "confidence": 1.5,
            "justification": "Test",
        })
        result = engine._parse_response(response)
        assert result is not None
        assert result.confidence == 1.0

        # Confidence < 0.0
        response = json.dumps({
            "subtype": "Email address",
            "category": "PII",
            "regulation": "DPDP",
            "confidence": -0.5,
            "justification": "Test",
        })
        result = engine._parse_response(response)
        assert result is not None
        assert result.confidence == 0.0

    @patch("engines.llm_engine.LLMEngine._get_client")
    def test_classify_with_mocked_ollama(self, mock_get_client):
        """Test classification with a mocked Ollama response."""
        mock_client = MagicMock()
        mock_client.chat.return_value = {
            "message": {
                "content": json.dumps({
                    "subtype": "Aadhaar number",
                    "category": "PII",
                    "regulation": "DPDP",
                    "confidence": 0.78,
                    "justification": "Column name and pattern suggest Aadhaar",
                })
            }
        }
        mock_get_client.return_value = mock_client

        engine = LLMEngine()
        engine._available = True
        engine._client = mock_client

        result = engine.classify(
            field_name="uid_number",
            table_name="customers",
            masked_samples=["####-####-####"],
            taxonomy_subtypes=[
                {"name": "Aadhaar number", "category": "PII", "regulation": "DPDP"}
            ],
        )

        assert result is not None
        assert result.subtype == "Aadhaar number"
        assert result.confidence == 0.78
