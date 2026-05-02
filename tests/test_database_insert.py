import sqlite3

from src.database import initialize_database, insert_email_record


def make_test_record(message_id="msg-1"):
    return {
        "message_id": message_id,
        "date": "2001-01-01T00:00:00+00:00",
        "from_address": "sender@example.com",
        "to_addresses": ["receiver@example.com"],
        "subject": "Test Email",
        "subject_normalized": "test email",
        "body": "This is a test email.",
        "body_normalized": "this is a test email.",
        "body_hash": "abc123",
        "source_file": "sample/1",
        "cc_addresses": [],
        "bcc_addresses": [],
        "x_from": None,
        "x_to": None,
        "x_cc": None,
        "x_bcc": None,
        "x_folder": None,
        "x_origin": None,
        "content_type": "text/plain",
        "has_attachment": False,
        "forwarded_content": None,
        "quoted_content": None,
        "headings": None,
    }


def test_email_insert_success(tmp_path):
    db_path = tmp_path / "test.db"

    initialize_database(db_path, reset=True)

    with sqlite3.connect(db_path) as connection:
        inserted = insert_email_record(connection, make_test_record())

    assert inserted is True


def test_duplicate_message_id_is_not_inserted_twice(tmp_path):
    db_path = tmp_path / "test.db"

    initialize_database(db_path, reset=True)

    with sqlite3.connect(db_path) as connection:
        first_insert = insert_email_record(connection, make_test_record("msg-1"))
        second_insert = insert_email_record(connection, make_test_record("msg-1"))

    assert first_insert is True
    assert second_insert is False