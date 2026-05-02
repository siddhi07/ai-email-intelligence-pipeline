import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT,
    total_files_found INTEGER DEFAULT 0,
    successfully_parsed INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    duplicate_message_ids_skipped INTEGER DEFAULT 0,
    duplicates_flagged INTEGER DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS emails (
    message_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    from_address TEXT NOT NULL,
    subject TEXT NOT NULL,
    subject_normalized TEXT NOT NULL,
    body TEXT NOT NULL,
    body_normalized TEXT NOT NULL,
    body_hash TEXT NOT NULL,
    source_file TEXT NOT NULL,

    x_from TEXT,
    x_to TEXT,
    x_cc TEXT,
    x_bcc TEXT,
    x_folder TEXT,
    x_origin TEXT,
    content_type TEXT,
    has_attachment INTEGER DEFAULT 0,
    forwarded_content TEXT,
    quoted_content TEXT,
    headings TEXT,

    is_duplicate INTEGER DEFAULT 0,
    duplicate_of TEXT,
    similarity_score REAL,
    notification_sent INTEGER DEFAULT 0,
    notification_date TEXT,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (duplicate_of) REFERENCES emails(message_id)
);

CREATE TABLE IF NOT EXISTS email_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    recipient_address TEXT NOT NULL,
    recipient_type TEXT NOT NULL CHECK (recipient_type IN ('to', 'cc', 'bcc')),

    FOREIGN KEY (message_id) REFERENCES emails(message_id)
);

CREATE TABLE IF NOT EXISTS parse_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    failure_reason TEXT NOT NULL,
    failed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date);
CREATE INDEX IF NOT EXISTS idx_emails_from_address ON emails(from_address);
CREATE INDEX IF NOT EXISTS idx_emails_subject ON emails(subject);
CREATE INDEX IF NOT EXISTS idx_emails_subject_normalized ON emails(subject_normalized);
CREATE INDEX IF NOT EXISTS idx_emails_body_hash ON emails(body_hash);
CREATE INDEX IF NOT EXISTS idx_emails_duplicate_status ON emails(is_duplicate);
CREATE INDEX IF NOT EXISTS idx_recipients_address ON email_recipients(recipient_address);
CREATE INDEX IF NOT EXISTS idx_recipients_type ON email_recipients(recipient_type);
"""


def initialize_database(db_path: Path, reset: bool = False) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if reset and db_path.exists():
        db_path.unlink()

    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL)


def start_pipeline_run(db_path: Path) -> int:
    started_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO pipeline_runs (
                started_at,
                status
            )
            VALUES (?, ?)
            """,
            (started_at, "running"),
        )

        return int(cursor.lastrowid)


def finish_pipeline_run(
    db_path: Path,
    run_id: int,
    stats: Dict,
    status: str = "success",
    notes: str = "",
) -> None:
    finished_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            UPDATE pipeline_runs
            SET
                finished_at = ?,
                status = ?,
                total_files_found = ?,
                successfully_parsed = ?,
                failed = ?,
                duplicate_message_ids_skipped = ?,
                duplicates_flagged = ?,
                notes = ?
            WHERE run_id = ?
            """,
            (
                finished_at,
                status,
                stats.get("total_files_found", 0),
                stats.get("successfully_parsed", 0),
                stats.get("failed", 0),
                stats.get("duplicate_message_ids_skipped", 0),
                stats.get("duplicates_flagged", 0),
                notes,
                run_id,
            ),
        )


def log_parse_failure_to_db(
    connection: sqlite3.Connection,
    source_file: str,
    failure_reason: str,
) -> None:
    connection.execute(
        """
        INSERT INTO parse_failures (
            source_file,
            failure_reason
        )
        VALUES (?, ?)
        """,
        (source_file, failure_reason),
    )


def insert_email_record(connection: sqlite3.Connection, record: Dict) -> bool:
    try:
        connection.execute(
            """
            INSERT INTO emails (
                message_id,
                date,
                from_address,
                subject,
                subject_normalized,
                body,
                body_normalized,
                body_hash,
                source_file,
                x_from,
                x_to,
                x_cc,
                x_bcc,
                x_folder,
                x_origin,
                content_type,
                has_attachment,
                forwarded_content,
                quoted_content,
                headings
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["message_id"],
                record["date"],
                record["from_address"],
                record["subject"],
                record["subject_normalized"],
                record["body"],
                record["body_normalized"],
                record["body_hash"],
                record["source_file"],
                record["x_from"],
                record["x_to"],
                record["x_cc"],
                record["x_bcc"],
                record["x_folder"],
                record["x_origin"],
                record["content_type"],
                int(record["has_attachment"]),
                record["forwarded_content"],
                record["quoted_content"],
                record["headings"],
            ),
        )

        recipient_rows = []

        for address in record["to_addresses"]:
            recipient_rows.append((record["message_id"], address, "to"))

        for address in record["cc_addresses"]:
            recipient_rows.append((record["message_id"], address, "cc"))

        for address in record["bcc_addresses"]:
            recipient_rows.append((record["message_id"], address, "bcc"))

        connection.executemany(
            """
            INSERT INTO email_recipients (
                message_id,
                recipient_address,
                recipient_type
            )
            VALUES (?, ?, ?)
            """,
            recipient_rows,
        )

        return True

    except sqlite3.IntegrityError:
        return False