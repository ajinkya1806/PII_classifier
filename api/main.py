"""
FastAPI application — PII/Sensitive Data Classification API.

Endpoints:
  POST /connections/test          — validate MySQL connection
  GET  /connections/{id}/schema   — list tables/columns
  POST /scan                      — start async scan → {job_id}
  GET  /scan/{job_id}             — status + progress
  GET  /scan/{job_id}/results     — final results
  GET  /scan/{job_id}/export      — download as JSON or CSV
  GET  /scan/{job_id}/stream      — SSE live progress
  GET  /jobs                      — list past scan jobs
  GET  /health                    — health check
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from connectors.mysql_connector import MySQLConnector
from jobs.runner import ScanRunner
from jobs.store import JobStore

# ──────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# App creation
# ──────────────────────────────────────────────
app = FastAPI(
    title="PII/Sensitive Data Classifier",
    description=(
        "Enterprise data classification API for DPDP Act 2023 and "
        "RBI-DADP compliance. Scans MySQL databases and classifies "
        "columns against a multi-method detection ensemble."
    ),
    version="1.0.0",
)

# CORS for local SPA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
store = JobStore()
runner = ScanRunner(store)


# ──────────────────────────────────────────────
# Request / Response Models
# ──────────────────────────────────────────────
class ConnectionRequest(BaseModel):
    host: str = Field(default="localhost", description="MySQL host")
    port: int = Field(default=3306, description="MySQL port")
    user: str = Field(description="MySQL user")
    password: str = Field(description="MySQL password")
    database: str = Field(description="MySQL database name")


class ScanRequest(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=3306)
    user: str
    password: str
    database: str
    tables: Optional[List[str]] = Field(
        default=None,
        description="Optional list of table names to scan. If null, scans all tables.",
    )


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str


class SchemaColumn(BaseModel):
    name: str
    data_type: str
    nullable: bool


class SchemaTable(BaseModel):
    table_name: str
    columns: List[SchemaColumn]


class ScanStartResponse(BaseModel):
    job_id: str
    message: str


class JobStatusResponse(BaseModel):
    id: str
    status: str
    total_fields: int
    scanned_fields: int
    created_at: str
    updated_at: str
    error_message: Optional[str] = None


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "PII Classifier API", "version": "1.0.0"}


@app.post("/connections/test", response_model=ConnectionTestResponse)
async def test_connection(req: ConnectionRequest):
    """Validate MySQL connection details."""
    connector = MySQLConnector()
    try:
        connector.connect(
            host=req.host,
            port=req.port,
            user=req.user,
            password=req.password,
            database=req.database,
        )
        result = connector.test_connection()
        return ConnectionTestResponse(**result)
    except Exception as e:
        return ConnectionTestResponse(success=False, message=str(e))
    finally:
        connector.close()


@app.post("/connections/schema", response_model=List[SchemaTable])
async def get_schema(req: ConnectionRequest):
    """List tables and columns for a connection (no classification)."""
    connector = MySQLConnector()
    try:
        connector.connect(
            host=req.host,
            port=req.port,
            user=req.user,
            password=req.password,
            database=req.database,
        )
        tables = connector.list_tables()
        result = []
        for table_name in tables:
            schema = connector.fetch_schema(table_name)
            columns = [
                SchemaColumn(
                    name=f.name,
                    data_type=f.data_type,
                    nullable=f.nullable,
                )
                for f in schema.fields
            ]
            result.append(SchemaTable(table_name=table_name, columns=columns))
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        connector.close()


@app.post("/scan", response_model=ScanStartResponse)
async def start_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    """Start an async scan job. Returns job_id immediately."""
    connection_info = {
        "host": req.host,
        "port": req.port,
        "user": req.user,
        "password": req.password,
        "database": req.database,
    }

    # Create job
    job_id = store.create_job(connection_info, req.tables)

    # Run scan in background
    background_tasks.add_task(
        _run_scan_background,
        job_id,
        connection_info,
        req.tables,
    )

    return ScanStartResponse(
        job_id=job_id,
        message="Scan started. Poll /scan/{job_id} for progress.",
    )


async def _run_scan_background(
    job_id: str,
    connection_info: Dict[str, Any],
    tables_filter: Optional[List[str]],
):
    """Wrapper to run scan in background with proper async context."""
    await runner.run_scan(job_id, connection_info, tables_filter)


@app.get("/scan/{job_id}", response_model=JobStatusResponse)
async def get_scan_status(job_id: str):
    """Get scan job status and progress."""
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatusResponse(
        id=job["id"],
        status=job["status"],
        total_fields=job["total_fields"] or 0,
        scanned_fields=job["scanned_fields"] or 0,
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        error_message=job.get("error_message"),
    )


@app.get("/scan/{job_id}/results")
async def get_scan_results(job_id: str):
    """Get final classification results for a scan job."""
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    results = store.get_results(job_id)
    return {
        "job_id": job_id,
        "status": job["status"],
        "total_fields": job["total_fields"],
        "results": results,
    }


@app.get("/scan/{job_id}/export")
async def export_scan_results(
    job_id: str,
    format: str = Query(default="json", description="Export format: json or csv"),
):
    """Export scan results as JSON or CSV."""
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if format.lower() == "csv":
        csv_content = store.export_results_csv(job_id)
        return PlainTextResponse(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="scan_{job_id}.csv"'
            },
        )
    else:
        results = store.get_results(job_id)
        return {
            "job_id": job_id,
            "status": job["status"],
            "total_fields": job["total_fields"],
            "results": results,
        }


@app.get("/scan/{job_id}/stream")
async def stream_scan_progress(job_id: str):
    """SSE endpoint for live scan progress updates."""
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    async def event_generator():
        while True:
            job = store.get_job(job_id)
            if not job:
                break

            data = json.dumps({
                "status": job["status"],
                "total_fields": job["total_fields"] or 0,
                "scanned_fields": job["scanned_fields"] or 0,
            })
            yield f"data: {data}\n\n"

            if job["status"] in ("completed", "failed"):
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/jobs")
async def list_jobs(limit: int = Query(default=50, le=200)):
    """List all past scan jobs."""
    jobs = store.list_jobs(limit)
    return {"jobs": jobs}


# ──────────────────────────────────────────────
# Startup
# ──────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("PII Classifier API starting up...")
    logger.info(f"Database: {store._db_path}")
