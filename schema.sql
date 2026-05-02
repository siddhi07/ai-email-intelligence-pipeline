DROP TABLE IF EXISTS email_recipients;
DROP TABLE IF EXISTS parse_failures;
DROP TABLE IF EXISTS pipeline_runs;
DROP TABLE IF EXISTS emails;

CREATE TABLE pipeline_runs (
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

CREATE TABLE emails (
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

CREATE TABLE email_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL,
    recipient_address TEXT NOT NULL,
    recipient_type TEXT NOT NULL CHECK (recipient_type IN ('to', 'cc', 'bcc')),

    FOREIGN KEY (message_id) REFERENCES emails(message_id)
);

CREATE TABLE parse_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    failure_reason TEXT NOT NULL,
    failed_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_emails_date ON emails(date);
CREATE INDEX idx_emails_from_address ON emails(from_address);
CREATE INDEX idx_emails_subject ON emails(subject);
CREATE INDEX idx_emails_subject_normalized ON emails(subject_normalized);
CREATE INDEX idx_emails_body_hash ON emails(body_hash);
CREATE INDEX idx_emails_duplicate_status ON emails(is_duplicate);
CREATE INDEX idx_recipients_address ON email_recipients(recipient_address);
CREATE INDEX idx_recipients_type ON email_recipients(recipient_type);