from src.notifier import send_email_via_gmail_mcp


def test_mcp_wrapper_routes_to_test_recipient_in_dry_run():
    result = send_email_via_gmail_mcp(
        recipient="original@example.com",
        subject="Test Subject",
        body="Test Body",
        references="msg-1",
        send_live=False,
        test_recipient_email="dummy@gmail.com",
        use_test_recipient_only=True,
    )

    assert result["recipient"] == "dummy@gmail.com"
    assert result["original_recipient"] == "original@example.com"
    assert result["status"] == "dry_run_not_sent"