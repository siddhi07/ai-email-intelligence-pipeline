# Enron Email Intelligence Pipeline

AI-Assisted Email Extraction, SQLite Storage, Duplicate Detection, and Gmail MCP Notifications

This project demonstrates the full workflow from raw email ingestion to automated Gmail MCP notification validation.

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

## 2. Dataset Scope

Source: **Enron Email Dataset**

The full dataset contains approximately **500,000+ emails across 150 employee mailboxes**.

A representative subset was used for pipeline validation to keep execution practical while preserving realistic complexity.

### Selected Mailboxes

- kaminski-v
- lay-k
- skilling-j
- mann-k
- taylor-m

### Why These Mailboxes Were Chosen

These mailboxes were selected to provide:

- varied folder depth and nested structure
- realistic communication volume
- multiple senders and recipients
- forwarded / reply chains
- diverse metadata quality
- more than 10,000 emails total for robust testing

This allowed realistic end-to-end validation without requiring the full dataset.

---

## 3. Deliverables Included

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

## 4. Repository Structure

```text
ai-email-intelligence-pipeline/
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
│   └── send_log.csv
│
├── main.py
├── schema.sql
├── sample_queries.sql
├── requirements.txt
├── AI_USAGE.md
├── README.md
└── mcp_config.json.example
```

## 5. Database Output

The SQLite database is generated locally during pipeline execution.

It is intentionally not committed to GitHub because generated database files can be large and can always be recreated.

To generate locally:

```bash
python3 main.py --maildir /path/to/maildir_subset --reset-db
```

## 6. Installation

Create virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 7. Run Tests

```bash
python3 -m pytest
```

Current status:

```
10 tests passed (parser, database, duplicate detection, notifier)
```

## 8. How to Run

Before running main.py, place a local Enron subset in:

```
data/maildir_subset/
```

### Standard Full Pipeline

```bash
python3 main.py --maildir data/maildir_subset --reset-db
```

### Dry Run Mode

Generates duplicate notices without sending live emails.

```bash
python3 main.py --maildir data/maildir_subset --reset-db --send-live false
```

### Controlled Live Mode

Sends capped notifications through Gmail MCP.

```bash
python3 main.py --maildir data/maildir_subset --send-live --max-live-sends 3
```

## 9. Architecture Overview

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

## 10. Database Design

Main tables:

- **emails** — Stores parsed email metadata and duplicate flags
- **email_recipients** — Normalized to, cc, bcc recipients
- **pipeline_runs** — Tracks each pipeline execution
- **parse_failures** — Stores rejected email records and reasons

Required duplicate fields included:

```
is_duplicate
duplicate_of
notification_sent
notification_date
```

## 11. Duplicate Detection Strategy

This project avoids expensive all-vs-all fuzzy comparison.

Instead:

- Normalize subject lines (Re:, Fwd: removed)
- Group by sender + normalized subject
- Hash normalized body text
- Use exact matches first
- Use fuzzy similarity only inside small groups

### Fuzzy Matching Library

Used RapidFuzz with a 90% similarity threshold.

### Benefits

- Faster runtime
- Better scalability
- Cleaner duplicate linking

## 12. Gmail MCP Setup

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

This repository includes mcp_config.json.example as a reusable safe template with no credentials committed.

### Step 3: Authenticate

```bash
cd ~/.gmail-mcp
npx -y @gongrzhe/server-gmail-autoauth-mcp auth
```

## 13. Live Validation Completed

Three real duplicate notification emails were successfully sent through Gmail MCP to:

```
enron.pipeline.test@gmail.com
```

After delivery:

- SQLite records updated
- `notification_sent = 1`
- `notification_date` stored

## 14. Outputs Generated

```
duplicates_report.csv
error_log.txt
output/send_log.csv
output/replies/*.eml
extraction_stats.json
```

## 15. Sample SQL Queries

See:

```
sample_queries.sql
```

Includes examples such as:

- Top duplicate senders
- Unnotified duplicates
- Parse failure counts

## 16. AI Collaboration Notes

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
- Dedicated MCP integration workflow

## 17. Final Outcome

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
