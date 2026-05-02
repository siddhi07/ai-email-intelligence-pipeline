# AI Tool Usage Documentation

## 1. Tools Used

The following AI tools were used during the development of this assignment:

- **Claude Sonnet**  
  Used for architecture planning, code refactoring ideas, debugging support, and improving modular project structure.

- **Claude Haiku**  
  Used for quick iterations, smaller code corrections, syntax checks, and lightweight prompt-response tasks.

- **ChatGPT**  
  Used for notebook structuring, markdown polishing, documentation writing, test case design, pipeline review, and implementation refinement.

These tools were used as coding assistants, while all final integration, validation, and decision-making remained manual.

---

## 2. Prompting Strategy

I used a **task-by-task prompting strategy** rather than submitting the full assignment at once.

This worked better because the assignment had multiple independent components:

1. Email parsing pipeline
2. SQLite schema design
3. Duplicate detection logic
4. MCP Gmail integration
5. Reporting and exports
6. Testing and documentation

Breaking the work into smaller prompts allowed better control, easier debugging, and clearer outputs.

### Example Prompts Used

#### Prompt 1
> Design a normalized SQLite schema for storing Enron emails, recipients, and duplicate detection results.

**Why:** Used early to create a clean relational schema before coding the parser.

#### Prompt 2
> Improve duplicate detection scalability. Fuzzy comparison on every record pair will be too expensive. Suggest a hash + bucketing strategy.

**Why:** Used to redesign duplicate matching into a production-friendly approach.

#### Prompt 3
> Rewrite my notebook into professional markdown cells and clean code cells suitable for a graded submission.

**Why:** Used to improve notebook readability and presentation quality.

#### Prompt 4
> Create pytest test cases for parser.py, database.py, duplicate_detector.py and notifier.py.

**Why:** Used after the repo structure was completed.

#### Prompt 5
> Help configure Gmail MCP with Claude Desktop and Google OAuth credentials.

**Why:** Used during final live integration testing.

---

## 3. Iterations & Debugging

### Case 1: Gmail MCP Authentication Failed

**Problem**

The Gmail MCP server initially failed with:
```
OAuth keys file not found
redirect_uri_mismatch
access_denied
Gmail API not enabled
```

**Fix**

I manually:
- Created Google Cloud OAuth credentials
- Added correct redirect URIs
- Added test users
- Enabled Gmail API
- Re-ran authentication flow
- Restarted Claude Desktop

**Result**

Successfully connected Gmail MCP and sent controlled live duplicate notifications.

### Case 2: Duplicate Detection Was Too Expensive

**Problem**

The first approach compared many email bodies using fuzzy matching directly, which would scale poorly.

**Fix**

I redesigned the logic to:
- Normalize subject lines
- Bucket by sender + normalized subject
- Generate normalized body hashes
- Use exact hash matches first
- Only use fuzzy matching inside small candidate groups

**Result**

Much faster duplicate detection and cleaner logic.

### Case 3: Notification Status Not Updating

**Problem**

After live Gmail sends, the SQLite database still showed pending notifications.

**Fix**

I added a helper function `mark_notification_sent(...)` and updated the three sent records manually after validation.

**Result**

Database state now correctly reflects completed sends.

---

## 4. What I Wrote vs What AI Wrote

### Approximate contribution breakdown:

**AI Assisted (~40%)**
- Initial schema suggestions
- Refactoring ideas
- Unit test templates
- Markdown polishing
- Error debugging suggestions
- MCP configuration guidance

**Manual Engineering / Final Ownership (~60%)**
- Final notebook structure
- Parsing adjustments
- Business logic decisions
- Duplicate detection thresholds
- Google Cloud OAuth setup
- Gmail API enablement
- MCP live testing
- Code integration across modules
- Final repository organization
- Validation of all outputs

All final code was reviewed and adjusted manually before use.

---

## 5. Lessons Learned

### What Worked Well
- AI was very effective for speeding up repetitive coding tasks.
- Useful for generating test scaffolds quickly.
- Helpful for debugging configuration issues step-by-step.
- Good at improving documentation quality and readability.

### What Was Harder Than Expected
- External integrations still required manual setup.
- OAuth and API permissions needed human troubleshooting.
- AI suggestions needed validation before trusting them.
- Large assignments work better when broken into smaller prompts.

### Key Takeaway

AI accelerated implementation speed, but correctness still required testing, debugging, and engineering judgment.

---

## 6. Final Outcome

Using AI assistance plus manual engineering effort, I built:

- End-to-end Enron email extraction pipeline
- Normalized SQLite storage system
- Scalable duplicate detection workflow
- Reporting outputs
- Pytest tested modular repo
- Live Gmail MCP validation with three successful controlled notification sends to a test Gmail inbox

This assignment was completed using AI as a productivity tool, not as a substitute for implementation ownership.