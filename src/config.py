from pathlib import Path

DATASET_URL = "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz"

DEFAULT_SELECTED_MAILBOXES = [
    "lay-k",
    "skilling-j",
    "kaminski-v",
    "mann-k",
    "taylor-m",
]

MINIMUM_EMAIL_COUNT = 10000
DUPLICATE_SIMILARITY_THRESHOLD = 90

DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_DB_PATH = DEFAULT_OUTPUT_DIR / "enron_emails.db"
DEFAULT_REPLIES_DIR = DEFAULT_OUTPUT_DIR / "replies"

ERROR_LOG_FILE = "error_log.txt"
DUPLICATES_REPORT_FILE = "duplicates_report.csv"
SEND_LOG_FILE = "send_log.csv"
EXTRACTION_STATS_FILE = "extraction_stats.json"
SCHEMA_FILE = "schema.sql"
SAMPLE_QUERIES_FILE = "sample_queries.sql"
DEFAULT_TEST_RECIPIENT_EMAIL = "enron.pipeline.test@gmail.com"
DEFAULT_MAX_LIVE_SENDS = 3
USE_TEST_RECIPIENT_ONLY = True