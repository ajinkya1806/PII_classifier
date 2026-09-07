"""
LLM Fallback Engine — Llama 3.1 via Ollama.

Invoked only when rule+pattern confidence is below a configurable threshold.
Never sends raw sensitive values — only column name, table name, and masked samples.
Handles Ollama being unreachable gracefully.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS_PATH = Path(__file__).parent.parent / "config" / "weights.yaml"


@dataclass
class LLMResult:
    """Result from the LLM fallback engine."""
    subtype: str
    category: str
    regulation: str
    confidence: float
    justification: str


class LLMEngine:
    """
    LLM-based classification fallback using Llama 3.1 via Ollama.

    Usage:
        engine = LLMEngine()
        result = engine.classify(
            field_name="customer_pan",
            table_name="users",
            masked_samples=["*****####*", "*****####*"],
            taxonomy_subtypes=[...]
        )
    """

    def __init__(self, weights_path: Optional[str] = None):
        self._weights_path = Path(weights_path) if weights_path else DEFAULT_WEIGHTS_PATH
        self._config = self._load_config()
        self._client = None
        self._available = None  # None = not checked yet

    def _load_config(self) -> Dict[str, Any]:
        """Load Ollama config from weights.yaml."""
        try:
            with open(self._weights_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data.get("ollama", {
                "model": "llama3.1",
                "base_url": "http://localhost:11434",
                "timeout_seconds": 30,
            })
        except Exception as e:
            logger.warning(f"Could not load LLM config: {e}")
            return {
                "model": "llama3.1",
                "base_url": "http://localhost:11434",
                "timeout_seconds": 30,
            }

    def _get_client(self):
        """Get or create Ollama client. Returns None if unavailable."""
        if self._client is not None:
            return self._client

        try:
            from ollama import Client
            self._client = Client(host=self._config.get("base_url", "http://localhost:11434"))
            # Quick health check
            self._client.list()
            self._available = True
            logger.info("Ollama client connected successfully")
            return self._client
        except ImportError:
            logger.warning("ollama package not installed. LLM engine disabled.")
            self._available = False
            return None
        except Exception as e:
            logger.warning(f"Ollama not reachable: {e}. LLM engine disabled.")
            self._available = False
            return None

    def is_available(self) -> bool:
        """Check if the LLM engine is available."""
        if self._available is None:
            self._get_client()
        return self._available or False

    def classify(
        self,
        field_name: str,
        table_name: str,
        masked_samples: List[str],
        taxonomy_subtypes: List[Dict[str, Any]],
    ) -> Optional[LLMResult]:
        """
        Classify a field using Llama 3.1 via Ollama.

        Args:
            field_name: Column/field name
            table_name: Table/asset name
            masked_samples: Masked/generalized sample values (never raw data)
            taxonomy_subtypes: List of subtype dicts from taxonomy.yaml

        Returns:
            LLMResult or None if Ollama is unreachable or errors out.
        """
        client = self._get_client()
        if client is None:
            logger.info("LLM engine skipped (Ollama unavailable)")
            return None

        # Build taxonomy summary for prompt
        taxonomy_summary = self._build_taxonomy_summary(taxonomy_subtypes)

        # Build the prompt — no raw values, only masked patterns
        prompt = self._build_prompt(
            field_name, table_name, masked_samples[:10], taxonomy_summary
        )

        try:
            response = client.chat(
                model=self._config.get("model", "llama3.1"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a data classification expert specializing in "
                            "Indian data protection regulations (DPDP Act 2023 and "
                            "RBI-DADP norms). You classify database columns into "
                            "specific subtypes. Always respond with valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                format="json",
            )

            result_text = response.get("message", {}).get("content", "")
            return self._parse_response(result_text)

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            self._available = False  # Mark as unavailable to avoid repeated failures
            return None

    def _build_taxonomy_summary(
        self, taxonomy_subtypes: List[Dict[str, Any]]
    ) -> str:
        """Build a concise taxonomy listing for the LLM prompt."""
        lines = []
        for st in taxonomy_subtypes:
            lines.append(
                f"- {st['name']} | Category: {st['category']} | "
                f"Regulation: {st['regulation']}"
            )
        return "\n".join(lines)

    def _build_prompt(
        self,
        field_name: str,
        table_name: str,
        masked_samples: List[str],
        taxonomy_summary: str,
    ) -> str:
        """Build the classification prompt."""
        samples_str = ", ".join(f'"{s}"' for s in masked_samples) if masked_samples else "N/A"

        return f"""Classify the following database column against the taxonomy below.

Column name: {field_name}
Table name: {table_name}
Sample value patterns (masked, no raw data): [{samples_str}]

TAXONOMY (classify into one of these subtypes):
{taxonomy_summary}

If the column does not match any subtype, use:
- subtype: "Non-Sensitive"
- category: "Non-Sensitive"
- regulation: "None"

Respond with a single JSON object:
{{
  "subtype": "<exact subtype name from taxonomy>",
  "category": "<exact category from taxonomy>",
  "regulation": "<DPDP | RBI-DADP | Both | None>",
  "confidence": <float 0.0 to 1.0>,
  "justification": "<one-line explanation, max 20 words>"
}}"""

    def _parse_response(self, text: str) -> Optional[LLMResult]:
        """Parse the LLM JSON response into an LLMResult."""
        try:
            # Try to extract JSON from the response
            data = json.loads(text)

            return LLMResult(
                subtype=data.get("subtype", "Non-Sensitive"),
                category=data.get("category", "Non-Sensitive"),
                regulation=data.get("regulation", "None"),
                confidence=min(max(float(data.get("confidence", 0.0)), 0.0), 1.0),
                justification=data.get("justification", "LLM classification"),
            )
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {text[:500]}")
            return None
