"""SQLite repository for generation jobs shared by the API and AI worker."""

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / "ai_image_studio.sqlite3"
DATABASE_PATH = Path(os.getenv("AI_IMAGE_DATABASE", str(DEFAULT_DATABASE_PATH)))
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
_UPDATABLE_FIELDS = {
    "status",
    "progress",
    "message",
    "images",
    "model_path",
    "engine",
}


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with _connection() as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(schema)


def create_job(job: dict[str, Any]) -> None:
    with _connection() as connection:
        connection.execute(
            """INSERT INTO generation_jobs (
                   job_id, prompt, model, model_file, ratio, count, cfg_scale,
                   base_url, status, progress, message
               ) VALUES (
                   :job_id, :prompt, :model, :model_file, :ratio, :count,
                   :cfg_scale, :base_url, :status, :progress, :message
               )""",
            job,
        )


def claim_next_job() -> dict[str, Any] | None:
    with _connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """SELECT * FROM generation_jobs
               WHERE status = 'queued'
               ORDER BY created_at, job_id
               LIMIT 1"""
        ).fetchone()
        if row is None:
            return None

        connection.execute(
            """UPDATE generation_jobs
               SET status = 'processing', message = 'กำลังเริ่มงาน',
                   updated_at = CURRENT_TIMESTAMP
               WHERE job_id = ? AND status = 'queued'""",
            (row["job_id"],),
        )
        claimed = connection.execute(
            "SELECT * FROM generation_jobs WHERE job_id = ?",
            (row["job_id"],),
        ).fetchone()
        return _decode_job(claimed)


def update_job(job_id: str, **values: Any) -> None:
    unknown_fields = values.keys() - _UPDATABLE_FIELDS
    if unknown_fields:
        raise ValueError(f"Unsupported job fields: {', '.join(sorted(unknown_fields))}")
    if not values:
        return

    assignments = []
    parameters = []
    for field, value in values.items():
        assignments.append(f"{field} = ?")
        parameters.append(json.dumps(value) if field == "images" else value)
    assignments.append("updated_at = CURRENT_TIMESTAMP")
    parameters.append(job_id)

    with _connection() as connection:
        cursor = connection.execute(
            f"UPDATE generation_jobs SET {', '.join(assignments)} WHERE job_id = ?",
            parameters,
        )
        if cursor.rowcount == 0:
            raise KeyError(f"Generation job not found: {job_id}")


def get_job(job_id: str) -> dict[str, Any] | None:
    with _connection() as connection:
        row = connection.execute(
            "SELECT * FROM generation_jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()
    return _decode_job(row) if row is not None else None


def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    safe_limit = min(max(limit, 1), 100)
    with _connection() as connection:
        rows = connection.execute(
            """SELECT * FROM generation_jobs
               ORDER BY created_at DESC, job_id DESC
               LIMIT ?""",
            (safe_limit,),
        ).fetchall()
    return [_decode_job(row) for row in rows]


def _decode_job(row: sqlite3.Row) -> dict[str, Any]:
    job = dict(row)
    job["images"] = json.loads(job["images"])
    return job