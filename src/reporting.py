import csv
import json
import sqlite3
from pathlib import Path
from typing import Dict


def write_extraction_stats(stats: Dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(stats, indent=2),
        encoding="utf-8",
    )


def write_sample_queries(output_path: Path) -> None:
    sample_queries_sql = """
-- Query 1: Count emails per sender
SELECT
    from_address,
    COUNT(*) AS email_count
FROM emails
GROUP BY from_address
ORDER BY email_count DESC
LIMIT 10;

-- Query 2: Find emails sent within a date range
SELECT
    message_id,
    date,
    from_address,
    subject
FROM emails
WHERE date BETWEEN '2001-01-01' AND '2001-12-31'
ORDER BY date
LIMIT 20;

-- Query 3: Find emails with CC recipients
SELECT
    e.message_id,
    e.date,
    e.from_address,
    e.subject,
    r.recipient_address AS cc_address
FROM emails e
JOIN email_recipients r
    ON e.message_id = r.message_id
WHERE r.recipient_type = 'cc'
LIMIT 20;
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sample_queries_sql.strip(), encoding="utf-8")


def generate_duplicates_report(db_path: Path, output_path: Path) -> int:
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                duplicate.message_id AS duplicate_message_id,
                original.message_id AS original_message_id,
                duplicate.subject AS subject,
                duplicate.from_address AS from_address,
                duplicate.date AS duplicate_date,
                original.date AS original_date,
                duplicate.similarity_score AS similarity_score
            FROM emails duplicate
            JOIN emails original
                ON duplicate.duplicate_of = original.message_id
            WHERE duplicate.is_duplicate = 1
            ORDER BY duplicate.from_address, duplicate.subject, duplicate.date
            """
        ).fetchall()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "duplicate_message_id",
                "original_message_id",
                "subject",
                "from_address",
                "duplicate_date",
                "original_date",
                "similarity_score",
            ]
        )

        for row in rows:
            writer.writerow(
                [
                    row["duplicate_message_id"],
                    row["original_message_id"],
                    row["subject"],
                    row["from_address"],
                    row["duplicate_date"],
                    row["original_date"],
                    row["similarity_score"],
                ]
            )

    return len(rows)


def get_final_summary(db_path: Path, output_paths: Dict) -> Dict:
    with sqlite3.connect(db_path) as connection:
        total_emails = connection.execute(
            "SELECT COUNT(*) FROM emails"
        ).fetchone()[0]

        total_recipients = connection.execute(
            "SELECT COUNT(*) FROM email_recipients"
        ).fetchone()[0]

        total_duplicates = connection.execute(
            "SELECT COUNT(*) FROM emails WHERE is_duplicate = 1"
        ).fetchone()[0]

        total_parse_failures = connection.execute(
            "SELECT COUNT(*) FROM parse_failures"
        ).fetchone()[0]

        total_pipeline_runs = connection.execute(
            "SELECT COUNT(*) FROM pipeline_runs"
        ).fetchone()[0]

    return {
        "total_emails_stored": total_emails,
        "total_recipient_records": total_recipients,
        "total_duplicates_flagged": total_duplicates,
        "total_parse_failures": total_parse_failures,
        "total_pipeline_runs": total_pipeline_runs,
        **output_paths,
    }