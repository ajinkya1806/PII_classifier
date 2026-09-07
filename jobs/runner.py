"""
Scan Runner — async background job execution with progress tracking.

Orchestrates the full classification pipeline:
  connect → fetch schema → sample → rule engine → pattern engine →
  (optional) LLM fallback → score → categorize → persist results
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from classifier.categorizer import Categorizer
from classifier.scorer import Scorer
from connectors.base import mask_value
from connectors.mysql_connector import MySQLConnector
from engines.llm_engine import LLMEngine
from engines.pattern_engine import PatternEngine
from engines.rule_engine import RuleEngine
from jobs.store import JobStore

logger = logging.getLogger(__name__)


class ScanRunner:
    """
    Async background scan runner.

    Runs the full classification pipeline for each field in the target
    database, tracks progress, and stores results to the JobStore.
    """

    def __init__(self, store: JobStore):
        self.store = store
        self.rule_engine = RuleEngine()
        self.pattern_engine = PatternEngine()
        self.llm_engine = LLMEngine()
        self.scorer = Scorer()
        self.categorizer = Categorizer()

    async def run_scan(
        self,
        job_id: str,
        connection_info: Dict[str, Any],
        tables_filter: Optional[List[str]] = None,
    ) -> None:
        """
        Execute a full scan as a background task.

        Args:
            job_id: The scan job ID from the store.
            connection_info: MySQL connection parameters.
            tables_filter: Optional list of table names to limit the scan.
        """
        connector = MySQLConnector()
        try:
            # Mark as running
            self.store.update_status(job_id, "running")
            logger.info(f"[Job {job_id}] Starting scan...")

            # Connect to MySQL
            await asyncio.to_thread(connector.connect, **connection_info)

            # Get tables
            tables = await asyncio.to_thread(connector.list_tables)
            if tables_filter:
                tables = [t for t in tables if t in tables_filter]

            logger.info(f"[Job {job_id}] Scanning {len(tables)} tables")

            # Count total fields
            total_fields = 0
            table_schemas = {}
            for table in tables:
                schema = await asyncio.to_thread(connector.fetch_schema, table)
                table_schemas[table] = schema
                total_fields += len(schema.fields)

            self.store.update_progress(job_id, total_fields, 0)

            # Get taxonomy for LLM prompts
            taxonomy = self.rule_engine.get_taxonomy()
            llm_threshold = self.scorer.get_llm_threshold()

            # Process each field
            scanned = 0
            for table, schema in table_schemas.items():
                for field_meta in schema.fields:
                    try:
                        result = await self._classify_field(
                            connector,
                            table,
                            field_meta.name,
                            field_meta.data_type,
                            taxonomy,
                            llm_threshold,
                        )
                        self.store.store_result(job_id, result)
                    except Exception as e:
                        logger.error(
                            f"[Job {job_id}] Error classifying "
                            f"{table}.{field_meta.name}: {e}"
                        )
                        # Store error result
                        self.store.store_result(job_id, {
                            "table": table,
                            "column": field_meta.name,
                            "subtype": "Error",
                            "category": "Non-Sensitive",
                            "regulation": "None",
                            "confidence": 0.0,
                            "matched_by": [],
                            "description": f"Classification error: {str(e)[:100]}",
                        })

                    scanned += 1
                    self.store.update_progress(job_id, total_fields, scanned)

            # Mark as completed
            self.store.update_status(job_id, "completed")
            logger.info(
                f"[Job {job_id}] Scan completed: {scanned}/{total_fields} fields"
            )

        except Exception as e:
            logger.error(f"[Job {job_id}] Scan failed: {e}")
            self.store.update_status(job_id, "failed", str(e))
        finally:
            await asyncio.to_thread(connector.close)

    async def _classify_field(
        self,
        connector: MySQLConnector,
        table: str,
        column: str,
        data_type: str,
        taxonomy: List[Dict[str, Any]],
        llm_threshold: float,
    ) -> Dict[str, Any]:
        """
        Run the full classification pipeline for a single field.

        Returns a result dict ready for storage.
        """
        start_time = time.time()

        # Step 1: Rule engine (uses column + table name)
        rule_matches = self.rule_engine.classify(column, table)

        # Step 2: Sample raw data for pattern engine
        raw_samples = await asyncio.to_thread(
            connector.sample_data_raw, table, column, 100
        )

        # Step 3: Pattern engine
        pattern_match = None

        # If rule engine found a match with a pattern_ref, try that first
        if rule_matches:
            best_rule = rule_matches[0]
            # Find the taxonomy entry for the best rule match to get pattern_ref
            pattern_ref = self._get_pattern_ref(best_rule.subtype, taxonomy)
            if pattern_ref:
                pattern_match = self.pattern_engine.classify(
                    pattern_ref, raw_samples
                )

        # If no pattern match from rule suggestion, try all validators
        if pattern_match is None or pattern_match.confidence == 0:
            all_pattern_matches = self.pattern_engine.classify_all(raw_samples)
            if all_pattern_matches:
                pattern_match = all_pattern_matches[0]

        # Step 4: Check if LLM fallback is needed
        rule_conf = rule_matches[0].confidence if rule_matches else 0.0
        pattern_conf = pattern_match.confidence if pattern_match else 0.0
        combined_pre_llm = max(rule_conf, pattern_conf)

        llm_result = None
        if combined_pre_llm < llm_threshold:
            # Get masked samples for LLM
            masked_samples = await asyncio.to_thread(
                connector.sample_data, table, column, 10
            )
            llm_result = await asyncio.to_thread(
                self.llm_engine.classify,
                column, table, masked_samples, taxonomy
            )

        # Step 5: Score
        scored = self.scorer.compute_score(
            rule_matches, pattern_match, llm_result
        )

        # Step 6: Categorize
        classified = self.categorizer.categorize(scored, table, column)

        elapsed = time.time() - start_time
        logger.info(
            f"  {table}.{column} → {classified.subtype} "
            f"({classified.category}) [{classified.confidence:.2f}] "
            f"by {classified.matched_by} ({elapsed:.2f}s)"
        )

        return classified.to_dict()

    def _get_pattern_ref(
        self, subtype: str, taxonomy: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Look up pattern_ref for a subtype from the taxonomy."""
        for entry in taxonomy:
            if entry["name"] == subtype:
                return entry.get("pattern_ref")
        return None
