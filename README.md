# Enron Email Intelligence Pipeline

AI-Assisted Email Extraction, SQLite Storage, Duplicate Detection, and Gmail MCP Notifications

---

## 1. Project Summary

This project processes raw emails from the **Enron Email Dataset** and builds a production-style local pipeline that:

- Recursively scans mailbox folders
- Parses raw `.eml` style email files
- Handles malformed or incomplete records
- Stores normalized data in SQLite
- Detects exact and near-duplicate emails
- Generates duplicate notification emails
- Supports live Gmail MCP notifications
- Produces reporting outputs and logs

This submission includes both:

- A **Jupyter Notebook** for walkthrough and demonstration
- A **modular Python repository** for maintainable execution

---

## 2. Deliverables Included

| Item | Description |
|------|-------------|
| Source Code | Extraction, parsing, database, duplicate detection, notifier, reporting modules |
| README.md | Setup, architecture, run instructions |
| AI_USAGE.md | AI collaboration process and debugging history |
| schema.sql | SQLite schema definition |
| sample_queries.sql | Example SQL queries |
| mcp_config.json.example | Gmail MCP config template |
| output/replies/ | Dry-run generated duplicate notice emails |
| output/send_log.csv | Live send log |
| duplicates_report.csv | Duplicate summary report |
| error_log.txt | Parse failures log |
| requirements.txt | Python dependencies |

---

## 3. Repository Structure

```
enron-email-pipeline/
│
├── notebook/
│   └── Enron_Email_Pipeline.ipynb
│
├── src/
│   ├── config.py
│   ├── parser.py
│   ├── database.py
│   ├── duplicate_detector.py
│   ├── notifier.py
│   ├── reporting.py
│   └── __init__.py
│
├── tests/
│   ├── test_parser.py
│   ├── test_database_insert.py
│   ├── test_duplicate_detection.py
│   └── test_notifier.py
│
├── output/
│   ├── replies/
│   ├── send_log.csv
│   └── pipeline.db
│
├── schema.sql
├── sample_queries.sql
├── main.py
├── requirements.txt
├── AI_USAGE.md
├── README.md
└── mcp_config.json.example
```

## 4. Installation

Create virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 5. Run Tests

```bash
python3 -m pytest
```

Current status:

```
10 tests passed
```

## 6. How to Run

### Standard Full Pipeline

```bash
python3 main.py
```

### Dry Run Mode

Generates duplicate notices without sending live emails.

```bash
python3 main.py --send-live false
```

### Controlled Live Mode

Sends capped notifications through Gmail MCP.

```bash
python3 main.py --send-live --max-live-sends 3
```

## 7. Architecture Overview

```
Raw Enron Files
    ↓
Recursive Discovery
    ↓
Email Parsing
    ↓
SQLite Storage
    ↓
Duplicate Detection
    ↓
Dry Run Drafts / Gmail MCP Live Sends
    ↓
Reports + Logs
```

## 8. Database Design

Main tables:

- **emails** — Stores parsed email metadata and duplicate flags.
- **email_recipients** — Normalized `to`, `cc`, `bcc` recipients.
- **pipeline_runs** — Tracks each pipeline execution.
- **parse_failures** — Stores rejected email records and reasons.

Required duplicate fields included:

```
is_duplicate
duplicate_of
notification_sent
notification_date
```

## 9. Duplicate Detection Strategy

This project avoids expensive all-vs-all fuzzy comparison.

Instead:

1. Normalize subject lines (`Re:`, `Fwd:` removed)
2. Group by sender + normalized subject
3. Hash normalized body text
4. Use exact matches first
5. Use fuzzy similarity only inside small groups

Benefits:

- Faster runtime
- Better scalability
- Cleaner duplicate linking

## 10. Gmail MCP Setup

### Step 1: Google Cloud

Create OAuth Desktop Client.

Enable:

```
Gmail API
```

Add redirect URI:

```
http://localhost:3000/oauth2callback
```

### Step 2: MCP Config

Use:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "npx",
      "args": [
        "-y",
        "@gongrzhe/server-gmail-autoauth-mcp"
      ]
    }
  }
}
```

### Step 3: Authenticate

```bash
cd ~/.gmail-mcp
npx -y @gongrzhe/server-gmail-autoauth-mcp auth
```

## 11. Live Validation Completed

Three real duplicate notification emails were successfully sent through Gmail MCP to:

```
enron.pipeline.test@gmail.com
```

After delivery:

- SQLite records updated
- `notification_sent = 1`
- `notification_date` stored

## 12. Outputs Generated

Files:

```
duplicates_report.csv
error_log.txt
output/send_log.csv
output/replies/*.eml
extraction_stats.json
```

## 13. Sample SQL Queries

See:

```
sample_queries.sql
```

Includes examples such as:

- Top duplicate senders
- Unnotified duplicates
- Parse failure counts

## 14. AI Collaboration Notes

See:

```
AI_USAGE.md
```

Documents:

- Claude Sonnet
- Claude Haiku
- ChatGPT
- Prompting strategy
- Debugging iterations
- Ownership split

## 15. Final Outcome

This project demonstrates:

- Data engineering
- Email parsing robustness
- Relational modeling
- Duplicate intelligence workflows
- External API integration
- Testing discipline
- Production-style structure

---

**Author**

Siddhi Nirmale