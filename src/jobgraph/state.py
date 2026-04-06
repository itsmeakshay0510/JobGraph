from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import JobPosting


class StateStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS processed_jobs (
                job_key TEXT PRIMARY KEY,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                apply_url TEXT NOT NULL,
                description_hash TEXT NOT NULL,
                processed_at TEXT NOT NULL,
                markdown_path TEXT,
                docx_path TEXT
            );
            """
        )
        self.connection.commit()

    def has_processed(self, job: JobPosting, description_hash: str) -> bool:
        row = self.connection.execute(
            "SELECT description_hash FROM processed_jobs WHERE job_key = ?",
            (job.key,),
        ).fetchone()
        return bool(row and row["description_hash"] == description_hash)

    def mark_processed(
        self,
        job: JobPosting,
        description_hash: str,
        markdown_path: str,
        docx_path: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            """
            INSERT INTO processed_jobs (
                job_key, company, title, apply_url, description_hash, processed_at, markdown_path, docx_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_key) DO UPDATE SET
                description_hash = excluded.description_hash,
                processed_at = excluded.processed_at,
                markdown_path = excluded.markdown_path,
                docx_path = excluded.docx_path
            """,
            (
                job.key,
                job.company,
                job.title,
                job.apply_url,
                description_hash,
                now,
                markdown_path,
                docx_path,
            ),
        )
        self.connection.commit()

    def fetch_processed_jobs(self) -> list[dict[str, str]]:
        rows = self.connection.execute(
            """
            SELECT company, title, apply_url, processed_at, markdown_path, docx_path
            FROM processed_jobs
            ORDER BY processed_at DESC, company ASC, title ASC
            """
        ).fetchall()
        return [
            {
                "company": str(row["company"] or ""),
                "title": str(row["title"] or ""),
                "apply_url": str(row["apply_url"] or ""),
                "processed_at": str(row["processed_at"] or ""),
                "markdown_path": str(row["markdown_path"] or ""),
                "docx_path": str(row["docx_path"] or ""),
            }
            for row in rows
        ]

    def close(self) -> None:
        self.connection.close()
