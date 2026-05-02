import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, List

from src.config import (
    DEFAULT_DB_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPLIES_DIR,
    DUPLICATE_SIMILARITY_THRESHOLD,
    DUPLICATES_REPORT_FILE,
    ERROR_LOG_FILE,
    EXTRACTION_STATS_FILE,
    SAMPLE_QUERIES_FILE,
    SCHEMA_FILE,
    SEND_LOG_FILE,
    DEFAULT_MAX_LIVE_SENDS,
    DEFAULT_TEST_RECIPIENT_EMAIL,
)
from src.database import (
    SCHEMA_SQL,
    finish_pipeline_run,
    initialize_database,
    insert_email_record,
    log_parse_failure_to_db,
    start_pipeline_run,
)
from src.duplicate_detector import (
    detect_duplicate_groups,
    fetch_duplicate_candidates,
    flag_duplicates_in_database,
)
from src.notifier import (
    create_notification_drafts,
    run_mcp_notification_sender,
    write_send_log,
)
from src.parser import parse_email_file
from src.reporting import (
    generate_duplicates_report,
    get_final_summary,
    write_extraction_stats,
    write_sample_queries,
)


def discover_email_files(maildir_path: Path, max_files: int | None = None) -> List[Path]:
    if not maildir_path.exists():
        raise FileNotFoundError(f"Maildir path does not exist: {maildir_path}")

    email_files = [
        path
        for path in maildir_path.rglob("*")
        if path.is_file() and not path.name.startswith(".")
    ]

    email_files = sorted(email_files)

    if max_files is not None:
        return email_files[:max_files]

    return email_files


def update_missing_field_counts(stats: Dict, failure_reason: str) -> None:
    error_lower = failure_reason.lower()

    if "message_id" in error_lower:
        stats["missing_message_id_count"] += 1
    elif "date" in error_lower:
        stats["missing_or_invalid_date_count"] += 1
    elif "from_address" in error_lower:
        stats["missing_from_count"] += 1
    elif "to_addresses" in error_lower:
        stats["missing_to_count"] += 1
    elif "subject" in error_lower:
        stats["missing_subject_count"] += 1
    elif "body" in error_lower:
        stats["missing_body_count"] += 1
    else:
        stats["malformed_email_count"] += 1


def run_extraction_pipeline(
    email_files: List[Path],
    root_path: Path,
    db_path: Path,
    error_log_path: Path,
    extraction_stats_path: Path,
) -> Dict:
    stats = {
        "total_files_found": len(email_files),
        "successfully_parsed": 0,
        "failed": 0,
        "duplicate_message_ids_skipped": 0,
        "missing_message_id_count": 0,
        "missing_or_invalid_date_count": 0,
        "missing_from_count": 0,
        "missing_to_count": 0,
        "missing_subject_count": 0,
        "missing_body_count": 0,
        "malformed_email_count": 0,
        "field_completeness": {},
    }

    fields_to_track = [
        "message_id",
        "date",
        "from_address",
        "subject",
        "body",
        "body_hash",
        "cc_addresses",
        "bcc_addresses",
        "x_from",
        "x_to",
        "x_folder",
        "x_origin",
        "content_type",
        "has_attachment",
        "forwarded_content",
        "quoted_content",
        "headings",
    ]

    field_counts = {field: 0 for field in fields_to_track}

    error_log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(error_log_path, "w", encoding="utf-8") as error_log:
        with sqlite3.connect(db_path) as connection:
            for index, file_path in enumerate(email_files, start=1):
                record, error = parse_email_file(file_path, root_path)

                if record is None:
                    stats["failed"] += 1

                    source_file = str(file_path.relative_to(root_path))
                    failure_reason = error or "Unknown parse error"

                    error_log.write(f"{source_file} | {failure_reason}\n")
                    log_parse_failure_to_db(connection, source_file, failure_reason)
                    update_missing_field_counts(stats, failure_reason)

                    continue

                inserted = insert_email_record(connection, record)

                if not inserted:
                    stats["duplicate_message_ids_skipped"] += 1

                    source_file = str(file_path.relative_to(root_path))
                    failure_reason = (
                        f"Duplicate message_id skipped: {record['message_id']}"
                    )

                    error_log.write(f"{source_file} | {failure_reason}\n")
                    log_parse_failure_to_db(connection, source_file, failure_reason)

                    continue

                stats["successfully_parsed"] += 1

                for field in fields_to_track:
                    value = record.get(field)

                    if isinstance(value, list):
                        if len(value) > 0:
                            field_counts[field] += 1
                    elif value not in [None, "", False]:
                        field_counts[field] += 1

                if index % 1000 == 0:
                    print(f"Processed {index} / {len(email_files)} files")

    parsed_count = max(stats["successfully_parsed"], 1)

    stats["field_completeness"] = {
        field: {
            "count": count,
            "percentage": round((count / parsed_count) * 100, 2),
        }
        for field, count in field_counts.items()
    }

    write_extraction_stats(stats, extraction_stats_path)

    return stats


def run_pipeline(args: argparse.Namespace) -> Dict:
    maildir_path = Path(args.maildir)
    output_dir = Path(args.output_dir)
    db_path = Path(args.db_path)

    replies_dir = output_dir / "replies"
    error_log_path = output_dir / ERROR_LOG_FILE
    duplicates_report_path = output_dir / DUPLICATES_REPORT_FILE
    send_log_path = output_dir / SEND_LOG_FILE
    extraction_stats_path = output_dir / EXTRACTION_STATS_FILE
    schema_path = output_dir / SCHEMA_FILE
    sample_queries_path = output_dir / SAMPLE_QUERIES_FILE

    output_dir.mkdir(parents=True, exist_ok=True)
    replies_dir.mkdir(parents=True, exist_ok=True)

    initialize_database(db_path, reset=args.reset_db)
    schema_path.write_text(SCHEMA_SQL.strip(), encoding="utf-8")

    run_id = start_pipeline_run(db_path)

    try:
        email_files = discover_email_files(maildir_path, max_files=args.max_files)

        stats = run_extraction_pipeline(
            email_files=email_files,
            root_path=maildir_path,
            db_path=db_path,
            error_log_path=error_log_path,
            extraction_stats_path=extraction_stats_path,
        )

        candidate_groups = fetch_duplicate_candidates(db_path)

        duplicate_groups = detect_duplicate_groups(
            candidate_groups,
            threshold=args.duplicate_threshold,
        )

        duplicate_stats = flag_duplicates_in_database(db_path, duplicate_groups)
        stats.update(duplicate_stats)

        duplicate_report_count = generate_duplicates_report(
            db_path,
            duplicates_report_path,
        )

        stats["duplicates_flagged"] = duplicate_report_count

        draft_logs = create_notification_drafts(db_path, replies_dir)

        mcp_logs = run_mcp_notification_sender(
            db_path=db_path,
            send_live=args.send_live,
            max_live_sends=args.max_live_sends,
            test_recipient_email=args.test_recipient_email,
            use_test_recipient_only=True,
        )

        combined_logs = draft_logs + mcp_logs
        write_send_log(combined_logs, send_log_path)

        write_sample_queries(sample_queries_path)
        write_extraction_stats(stats, extraction_stats_path)

        finish_pipeline_run(
            db_path=db_path,
            run_id=run_id,
            stats=stats,
            status="success",
            notes="Pipeline completed successfully",
        )

        summary = get_final_summary(
            db_path,
            {
                "database_path": str(db_path),
                "error_log_path": str(error_log_path),
                "duplicates_report_path": str(duplicates_report_path),
                "send_log_path": str(send_log_path),
                "schema_path": str(schema_path),
                "sample_queries_path": str(sample_queries_path),
            },
        )

        summary_path = output_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        return summary

    except Exception as error:
        finish_pipeline_run(
            db_path=db_path,
            run_id=run_id,
            stats={},
            status="failed",
            notes=str(error),
        )

        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enron Email Extraction and Deduplication Pipeline"
    )

    parser.add_argument(
        "--maildir",
        required=True,
        help="Path to Enron maildir or selected mailbox subset",
    )

    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where reports, logs, and drafts will be written",
    )

    parser.add_argument(
        "--db-path",
        default=str(DEFAULT_DB_PATH),
        help="SQLite database path",
    )

    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Optional limit for testing on a smaller subset",
    )

    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Reset SQLite database before running",
    )

    parser.add_argument(
        "--duplicate-threshold",
        type=int,
        default=DUPLICATE_SIMILARITY_THRESHOLD,
        help="Fuzzy body similarity threshold for duplicate detection",
    )

    parser.add_argument(
        "--send-live",
        action="store_true",
        help="Enable live MCP sending mode. Default is dry-run only.",
    )

    parser.add_argument(
        "--max-live-sends",
        type=int,
        default=DEFAULT_MAX_LIVE_SENDS,
    )

    parser.add_argument(
        "--test-recipient-email",
        default=DEFAULT_TEST_RECIPIENT_EMAIL,
    )

    return parser.parse_args()


if __name__ == "__main__":
    final_summary = run_pipeline(parse_args())

    print("\nPipeline completed.")
    print(json.dumps(final_summary, indent=2))