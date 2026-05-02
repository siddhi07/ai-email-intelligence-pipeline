import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def build_notification_email(row: sqlite3.Row) -> Tuple[str, str, str]:
    recipient = row["from_address"]
    subject = f"[Duplicate Notice] Re: {row['subject']}"

    current_timestamp = datetime.now(timezone.utc).isoformat()

    body = f"""This is an automated notification from the Email Deduplication System.

Your email has been identified as a potential duplicate:

  Your Email (Flagged):
    Message-ID:  {row['duplicate_message_id']}
    Date Sent:   {row['duplicate_date']}
    Subject:     {row['subject']}

  Original Email on Record:
    Message-ID:  {row['original_message_id']}
    Date Sent:   {row['original_date']}

  Similarity Score: {round(row['similarity_score'], 2)}%

If this was NOT a duplicate and you intended to send this email,
please reply with CONFIRM to restore it to active status.

No action is required if this is indeed a duplicate.
"""

    email_text = f"""To: {recipient}
Subject: {subject}
Date: {current_timestamp}
References: {row['duplicate_message_id']}
Content-Type: text/plain; charset=UTF-8

{body}
"""

    return recipient, subject, email_text


def fetch_pending_duplicate_notifications(
    db_path: Path,
    limit: Optional[int] = None,
) -> List[sqlite3.Row]:
    query = """
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
          AND duplicate.notification_sent = 0
        ORDER BY duplicate.date DESC
    """

    if limit is not None:
        query += " LIMIT ?"

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row

        if limit is not None:
            rows = connection.execute(query, (limit,)).fetchall()
        else:
            rows = connection.execute(query).fetchall()

    return rows


def create_notification_drafts(db_path: Path, replies_dir: Path) -> List[Dict]:
    replies_dir.mkdir(parents=True, exist_ok=True)

    rows = fetch_pending_duplicate_notifications(db_path)

    draft_logs = []

    for row in rows:
        recipient, subject, email_text = build_notification_email(row)

        safe_id = hashlib.md5(
            row["duplicate_message_id"].encode("utf-8")
        ).hexdigest()

        draft_path = replies_dir / f"duplicate_notice_{safe_id}.eml"
        draft_path.write_text(email_text, encoding="utf-8")

        draft_logs.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "recipient": recipient,
                "original_recipient": recipient,
                "subject": subject,
                "status": "draft_created",
                "error": "",
                "draft_path": str(draft_path),
                "references": row["duplicate_message_id"],
            }
        )

    return draft_logs


def load_mcp_config(config_path: Path) -> Dict:
    if not config_path.exists():
        raise FileNotFoundError(
            f"MCP config file not found at {config_path}. "
            "Create mcp_config.json locally using mcp_config.json.example as a template."
        )

    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)

    if "mcpServers" not in config or "gmail" not in config["mcpServers"]:
        raise ValueError("Invalid MCP config. Expected mcpServers.gmail section.")

    return config


def send_email_via_gmail_mcp(
    recipient: str,
    subject: str,
    body: str,
    references: str,
    send_live: bool = False,
    test_recipient_email: Optional[str] = None,
    use_test_recipient_only: bool = True,
) -> Dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    original_recipient = recipient

    if use_test_recipient_only and test_recipient_email:
        recipient = test_recipient_email

    if not send_live:
        return {
            "timestamp": timestamp,
            "recipient": recipient,
            "original_recipient": original_recipient,
            "subject": subject,
            "status": "dry_run_not_sent",
            "error": "",
            "references": references,
        }

    return {
        "timestamp": timestamp,
        "recipient": recipient,
        "original_recipient": original_recipient,
        "subject": subject,
        "status": "mcp_runtime_required",
        "error": (
            "Live Gmail delivery is executed through Claude Desktop with the "
            "Gmail MCP server configured. This Python wrapper prepares the "
            "payload and enforces the test-recipient safety rule."
        ),
        "references": references,
    }


def mark_notification_sent(
    db_path: Path,
    duplicate_message_id: str,
    notification_date: str,
) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            UPDATE emails
            SET
                notification_sent = 1,
                notification_date = ?
            WHERE message_id = ?
            """,
            (notification_date, duplicate_message_id),
        )


def run_mcp_notification_sender(
    db_path: Path,
    send_live: bool = False,
    max_live_sends: int = 3,
    test_recipient_email: Optional[str] = None,
    use_test_recipient_only: bool = True,
) -> List[Dict]:
    limit = max_live_sends if send_live else 5
    pending_rows = fetch_pending_duplicate_notifications(db_path, limit=limit)

    logs = []

    for row in pending_rows:
        recipient, subject, email_text = build_notification_email(row)

        result = send_email_via_gmail_mcp(
            recipient=recipient,
            subject=subject,
            body=email_text,
            references=row["duplicate_message_id"],
            send_live=send_live,
            test_recipient_email=test_recipient_email,
            use_test_recipient_only=use_test_recipient_only,
        )

        logs.append(result)

        if result["status"] == "sent":
            mark_notification_sent(
                db_path=db_path,
                duplicate_message_id=row["duplicate_message_id"],
                notification_date=result["timestamp"],
            )

    return logs


def prepare_live_test_payloads(
    db_path: Path,
    test_recipient_email: str,
    limit: int = 3,
) -> List[Dict]:
    rows = fetch_pending_duplicate_notifications(db_path, limit=limit)

    payloads = []

    for row in rows:
        original_recipient, subject, email_text = build_notification_email(row)

        payloads.append(
            {
                "duplicate_message_id": row["duplicate_message_id"],
                "to": test_recipient_email,
                "original_recipient": original_recipient,
                "subject": subject,
                "body": email_text,
            }
        )

    return payloads


def write_send_log(logs: List[Dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "timestamp",
        "recipient",
        "original_recipient",
        "subject",
        "status",
        "error",
        "draft_path",
        "references",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for log in logs:
            writer.writerow(
                {
                    "timestamp": log.get("timestamp", ""),
                    "recipient": log.get("recipient", ""),
                    "original_recipient": log.get("original_recipient", ""),
                    "subject": log.get("subject", ""),
                    "status": log.get("status", ""),
                    "error": log.get("error", ""),
                    "draft_path": log.get("draft_path", ""),
                    "references": log.get("references", ""),
                }
            )