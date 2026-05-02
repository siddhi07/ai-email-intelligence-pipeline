import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

from rapidfuzz import fuzz


def fetch_duplicate_candidates(db_path: Path) -> Dict[Tuple[str, str], List[Dict]]:
    groups = {}

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                message_id,
                date,
                from_address,
                subject,
                subject_normalized,
                body_normalized,
                body_hash
            FROM emails
            WHERE body_normalized IS NOT NULL
              AND body_normalized != ''
            ORDER BY from_address, subject_normalized, body_hash, date
            """
        ).fetchall()

    for row in rows:
        record = dict(row)

        key = (
            record["from_address"],
            record["subject_normalized"],
        )

        if key not in groups:
            groups[key] = []

        groups[key].append(record)

    return {
        key: value
        for key, value in groups.items()
        if len(value) > 1
    }


def detect_duplicate_groups(
    candidate_groups: Dict[Tuple[str, str], List[Dict]],
    threshold: int,
) -> List[Dict]:
    duplicate_groups = []

    for _, records in candidate_groups.items():
        records = sorted(records, key=lambda item: item["date"])

        hash_groups = {}

        for record in records:
            hash_groups.setdefault(record["body_hash"], []).append(record)

        used_message_ids = set()

        for _, hash_records in hash_groups.items():
            if len(hash_records) > 1:
                original = hash_records[0]
                duplicates = []

                for duplicate in hash_records[1:]:
                    duplicates.append(
                        {
                            "record": duplicate,
                            "similarity_score": 100.0,
                        }
                    )
                    used_message_ids.add(duplicate["message_id"])

                duplicate_groups.append(
                    {
                        "original": original,
                        "duplicates": duplicates,
                    }
                )

        remaining_records = [
            record
            for record in records
            if record["message_id"] not in used_message_ids
        ]

        for i, original in enumerate(remaining_records):
            if original["message_id"] in used_message_ids:
                continue

            group_duplicates = []

            for candidate in remaining_records[i + 1:]:
                if candidate["message_id"] in used_message_ids:
                    continue

                similarity = fuzz.ratio(
                    original["body_normalized"],
                    candidate["body_normalized"],
                )

                if similarity >= threshold:
                    group_duplicates.append(
                        {
                            "record": candidate,
                            "similarity_score": similarity,
                        }
                    )
                    used_message_ids.add(candidate["message_id"])

            if group_duplicates:
                duplicate_groups.append(
                    {
                        "original": original,
                        "duplicates": group_duplicates,
                    }
                )

    return duplicate_groups


def flag_duplicates_in_database(db_path: Path, duplicate_groups: List[Dict]) -> Dict:
    total_flagged = 0
    group_sizes = []

    with sqlite3.connect(db_path) as connection:
        for group in duplicate_groups:
            original = group["original"]
            duplicates = group["duplicates"]

            group_sizes.append(1 + len(duplicates))

            for duplicate_entry in duplicates:
                duplicate = duplicate_entry["record"]
                similarity_score = duplicate_entry["similarity_score"]

                connection.execute(
                    """
                    UPDATE emails
                    SET
                        is_duplicate = 1,
                        duplicate_of = ?,
                        similarity_score = ?
                    WHERE message_id = ?
                    """,
                    (
                        original["message_id"],
                        similarity_score,
                        duplicate["message_id"],
                    ),
                )

                total_flagged += 1

    average_group_size = (
        round(sum(group_sizes) / len(group_sizes), 2)
        if group_sizes
        else 0
    )

    return {
        "total_duplicate_groups_found": len(duplicate_groups),
        "total_emails_flagged": total_flagged,
        "average_group_size": average_group_size,
    }