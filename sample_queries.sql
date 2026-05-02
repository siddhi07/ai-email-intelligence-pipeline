-- Query 1: Count emails per sender
SELECT
    from_address,
    COUNT(*) AS email_count
FROM emails
GROUP BY from_address
ORDER BY email_count DESC
LIMIT 10;

-- Query 2: Find emails sent within a date range
SELECT
    message_id,
    date,
    from_address,
    subject
FROM emails
WHERE date BETWEEN '2001-01-01' AND '2001-12-31'
ORDER BY date
LIMIT 20;

-- Query 3: Find emails with CC recipients
SELECT
    e.message_id,
    e.date,
    e.from_address,
    e.subject,
    r.recipient_address AS cc_address
FROM emails e
JOIN email_recipients r
    ON e.message_id = r.message_id
WHERE r.recipient_type = 'cc'
LIMIT 20;