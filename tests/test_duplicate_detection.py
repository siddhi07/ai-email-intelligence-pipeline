from src.duplicate_detector import detect_duplicate_groups


def test_duplicate_threshold_accepts_identical_body_hash_group():
    candidate_groups = {
        ("a@example.com", "meeting"): [
            {
                "message_id": "msg-1",
                "date": "2001-01-01T00:00:00+00:00",
                "from_address": "a@example.com",
                "subject": "Meeting",
                "subject_normalized": "meeting",
                "body_normalized": "same body text",
                "body_hash": "hash-1",
            },
            {
                "message_id": "msg-2",
                "date": "2001-01-02T00:00:00+00:00",
                "from_address": "a@example.com",
                "subject": "Re: Meeting",
                "subject_normalized": "meeting",
                "body_normalized": "same body text",
                "body_hash": "hash-1",
            },
        ]
    }

    groups = detect_duplicate_groups(candidate_groups, threshold=90)

    assert len(groups) == 1
    assert groups[0]["original"]["message_id"] == "msg-1"
    assert groups[0]["duplicates"][0]["record"]["message_id"] == "msg-2"
    assert groups[0]["duplicates"][0]["similarity_score"] == 100.0


def test_duplicate_threshold_rejects_low_similarity():
    candidate_groups = {
        ("a@example.com", "meeting"): [
            {
                "message_id": "msg-1",
                "date": "2001-01-01T00:00:00+00:00",
                "from_address": "a@example.com",
                "subject": "Meeting",
                "subject_normalized": "meeting",
                "body_normalized": "project meeting tomorrow morning",
                "body_hash": "hash-1",
            },
            {
                "message_id": "msg-2",
                "date": "2001-01-02T00:00:00+00:00",
                "from_address": "a@example.com",
                "subject": "Meeting",
                "subject_normalized": "meeting",
                "body_normalized": "completely different legal contract terms",
                "body_hash": "hash-2",
            },
        ]
    }

    groups = detect_duplicate_groups(candidate_groups, threshold=90)

    assert len(groups) == 0