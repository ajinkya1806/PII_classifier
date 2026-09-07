"""
SQLite-backed job and results persistence store.

Manages scan_jobs and scan_results tables for audit trail and history.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "pii_classifier.db"


class JobStore:
    """
    SQLite-backed persistence for scan jobs and results.

    Tables:
      - scan_jobs: job metadata, status, progress
      - scan_results: per-field classification results
    """

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a SQLite connection with row_factory set to Row."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        """Initialize database tables."""
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS scan_jobs (
                    id TEXT PRIMARY KEY,
                    connection_info TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    total_fields INTEGER DEFAULT 0,
                    scanned_fields INTEGER DEFAULT 0,
                    tables_filter TEXT,
                    error_message TEXT
                );

                CREATE TABLE IF NOT EXISTS scan_results (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    column_name TEXT NOT NULL,
                    subtype TEXT,
                    category TEXT,
                    regulation TEXT,
                    confidence REAL DEFAULT 0.0,
                    matched_by TEXT,
                    description TEXT,
                    rule_confidence REAL DEFAULT 0.0,
                    pattern_confidence REAL DEFAULT 0.0,
                    llm_confidence REAL DEFAULT 0.0,
                    llm_justification TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES scan_jobs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_results_job_id
                    ON scan_results(job_id);
            """)
            conn.commit()
            logger.info(f"Database initialized at {self._db_path}")
        finally:
            conn.close()

    def create_job(
        self,
        connection_info: Dict[str, Any],
        tables_filter: Optional[List[str]] = None,
    ) -> str:
        """
        Create a new scan job.

        Returns the job_id (UUID).
        Connection info is stored without the password for security.
        """
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Strip password from stored connection info
        safe_info = {k: v for k, v in connection_info.items() if k != "password"}

        conn = self._get_conn()
        try:
            conn.execute(
                """
                INSERT INTO scan_jobs
                    (id, connection_info, status, created_at, updated_at, tables_filter)
                VALUES (?, ?, 'pending', ?, ?, ?)
                """,
                (
                    job_id,
                    json.dumps(safe_info),
                    now,
                    now,
                    json.dumps(tables_filter) if tables_filter else None,
                ),
            )
            conn.commit()
            logger.info(f"Created scan job: {job_id}")
            return job_id
        finally:
            conn.close()

    def update_status(
        self,
        job_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Update job status (pending, running, completed, failed)."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        try:
            conn.execute(
                """
                UPDATE scan_jobs
                SET status = ?, updated_at = ?, error_message = ?
                WHERE id = ?
                """,
                (status, now, error_message, job_id),
            )
            conn.commit()
        finally:
            conn.close()

    def update_progress(
        self,
        job_id: str,
        total_fields: int,
        scanned_fields: int,
    ) -> None:
        """Update scan progress counters."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_conn()
        try:
            conn.execute(
                """
                UPDATE scan_jobs
                SET total_fields = ?, scanned_fields = ?, updated_at = ?
                WHERE id = ?
                """,
                (total_fields, scanned_fields, now, job_id),
            )
            conn.commit()
        finally:
            conn.close()

    def store_result(
        self,
        job_id: str,
        result: Dict[str, Any],
    ) -> str:
        """Store a single field classification result."""
        result_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        conn = self._get_conn()
        try:
            conn.execute(
                """
                INSERT INTO scan_results
                    (id, job_id, table_name, column_name, subtype, category,
                     regulation, confidence, matched_by, description,
                     rule_confidence, pattern_confidence, llm_confidence,
                     llm_justification, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    job_id,
                    result.get("table", ""),
                    result.get("column", ""),
                    result.get("subtype", ""),
                    result.get("category", ""),
                    result.get("regulation", ""),
                    result.get("confidence", 0.0),
                    json.dumps(result.get("matched_by", [])),
                    result.get("description", ""),
                    result.get("rule_confidence", 0.0),
                    result.get("pattern_confidence", 0.0),
                    result.get("llm_confidence", 0.0),
                    result.get("llm_justification", ""),
                    now,
                ),
            )
            conn.commit()
            return result_id
        finally:
            conn.close()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details by ID."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM scan_jobs WHERE id = ?", (job_id,)
            ).fetchone()

            if row is None:
                return None

            return {
                "id": row["id"],
                "connection_info": json.loads(row["connection_info"]),
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "total_fields": row["total_fields"],
                "scanned_fields": row["scanned_fields"],
                "tables_filter": (
                    json.loads(row["tables_filter"])
                    if row["tables_filter"]
                    else None
                ),
                "error_message": row["error_message"],
            }
        finally:
            conn.close()

    def get_results(self, job_id: str) -> List[Dict[str, Any]]:
        """Get all results for a job."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM scan_results WHERE job_id = ? ORDER BY table_name, column_name",
                (job_id,),
            ).fetchall()

            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "table": row["table_name"],
                    "column": row["column_name"],
                    "subtype": row["subtype"],
                    "category": row["category"],
                    "regulation": row["regulation"],
                    "confidence": row["confidence"],
                    "matched_by": json.loads(row["matched_by"]) if row["matched_by"] else [],
                    "description": row["description"],
                    "rule_confidence": row["rule_confidence"],
                    "pattern_confidence": row["pattern_confidence"],
                    "llm_confidence": row["llm_confidence"],
                    "llm_justification": row["llm_justification"],
                })
            return results
        finally:
            conn.close()

    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all scan jobs, ordered by most recent first."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM scan_jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()

            jobs = []
            for row in rows:
                jobs.append({
                    "id": row["id"],
                    "connection_info": json.loads(row["connection_info"]),
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "total_fields": row["total_fields"],
                    "scanned_fields": row["scanned_fields"],
                    "error_message": row["error_message"],
                })
            return jobs
        finally:
            conn.close()

    def export_results_csv(self, job_id: str) -> str:
        """Export results as CSV string."""
        results = self.get_results(job_id)
        if not results:
            return ""

        headers = [
            "table", "column", "subtype", "category", "regulation",
            "confidence", "matched_by", "description"
        ]
        lines = [",".join(headers)]

        for r in results:
            row = [
                self._csv_escape(r.get("table", "")),
                self._csv_escape(r.get("column", "")),
                self._csv_escape(r.get("subtype", "")),
                self._csv_escape(r.get("category", "")),
                self._csv_escape(r.get("regulation", "")),
                str(r.get("confidence", 0.0)),
                self._csv_escape("|".join(r.get("matched_by", []))),
                self._csv_escape(r.get("description", "")),
            ]
            lines.append(",".join(row))

        return "\n".join(lines)

    def _csv_escape(self, value: str) -> str:
        """Escape a value for CSV output."""
        if "," in value or '"' in value or "\n" in value:
            return f'"{value.replace(chr(34), chr(34)+chr(34))}"'
        return value
