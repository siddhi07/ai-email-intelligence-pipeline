import hashlib
import re
from datetime import timezone
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dateutil import parser as date_parser


def read_email_bytes(file_path: Path) -> bytes:
    with open(file_path, "rb") as file:
        return file.read()


def parse_message(raw_bytes: bytes):
    return BytesParser(policy=policy.default).parsebytes(raw_bytes)


def clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    value = str(value).replace("\x00", "").strip()
    return value if value else None


def normalize_date_to_utc(date_value: Optional[str]) -> Optional[str]:
    if not date_value:
        return None

    try:
        parsed_date = date_parser.parse(str(date_value), fuzzy=True)

        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)

        return parsed_date.astimezone(timezone.utc).isoformat()

    except Exception:
        return None


def extract_addresses(header_value: Optional[str]) -> List[str]:
    if not header_value:
        return []

    extracted = []

    for _, address in getaddresses([str(header_value)]):
        address = address.strip().lower()

        if "@" in address and "." in address.split("@")[-1]:
            extracted.append(address)

    return sorted(set(extracted))


def normalize_subject(subject: Optional[str]) -> str:
    if not subject:
        return ""

    normalized = subject.strip()

    while True:
        updated = re.sub(
            r"^\s*(re|fw|fwd|forward)\s*:\s*",
            "",
            normalized,
            flags=re.IGNORECASE,
        )

        if updated == normalized:
            break

        normalized = updated

    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    return normalized


def normalize_body_for_matching(body: Optional[str]) -> str:
    if not body:
        return ""

    body = body.lower()
    body = re.sub(r"\s+", " ", body)
    body = re.sub(r"[-_=]{3,}", " ", body)

    return body.strip()


def create_body_hash(body_normalized: str) -> str:
    return hashlib.md5(body_normalized.encode("utf-8")).hexdigest()


def extract_body_parts(message) -> Tuple[str, str, str]:
    body_parts = []

    if message.is_multipart():
        for part in message.walk():
            content_disposition = part.get_content_disposition()
            content_type = part.get_content_type()

            if content_disposition == "attachment":
                continue

            if content_type == "text/plain":
                try:
                    content = part.get_content()
                    if content:
                        body_parts.append(str(content))
                except Exception:
                    continue
    else:
        try:
            content = message.get_content()
            if content:
                body_parts.append(str(content))
        except Exception:
            payload = message.get_payload(decode=True)
            if payload:
                body_parts.append(payload.decode("utf-8", errors="replace"))

    full_body = "\n".join(body_parts).strip()

    forwarded_content = ""
    quoted_content = ""

    forwarded_patterns = [
        r"[-]+\s*Forwarded by.*",
        r"[-]+\s*Original Message\s*[-]+",
        r"Begin forwarded message:",
        r"Forwarded message",
    ]

    for pattern in forwarded_patterns:
        match = re.search(pattern, full_body, flags=re.IGNORECASE | re.DOTALL)

        if match:
            forwarded_content = full_body[match.start():].strip()
            full_body = full_body[:match.start()].strip()
            break

    primary_lines = []
    quoted_lines = []

    for line in full_body.splitlines():
        if line.strip().startswith(">"):
            quoted_lines.append(line)
        else:
            primary_lines.append(line)

    if quoted_lines:
        quoted_content = "\n".join(quoted_lines).strip()
        full_body = "\n".join(primary_lines).strip()

    return full_body, forwarded_content, quoted_content


def infer_has_attachment(message, body: Optional[str]) -> bool:
    for part in message.walk():
        if part.get_content_disposition() == "attachment":
            return True

        if part.get_filename():
            return True

    body = body or ""

    attachment_terms = [
        "attached",
        "attachment",
        ".doc",
        ".xls",
        ".pdf",
        ".ppt",
        ".zip",
    ]

    return any(term in body.lower() for term in attachment_terms)


def extract_headings(body: Optional[str]) -> Optional[str]:
    if not body:
        return None

    headings = []

    for line in body.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if re.match(r"^[A-Z][A-Za-z\s]{2,40}:$", stripped):
            headings.append(stripped)

        elif re.match(
            r"^(from|to|subject|date|cc|bcc):",
            stripped,
            flags=re.IGNORECASE,
        ):
            headings.append(stripped)

    return "\n".join(headings) if headings else None


def parse_email_file(
    file_path: Path,
    root_path: Path,
) -> Tuple[Optional[Dict], Optional[str]]:
    try:
        raw_bytes = read_email_bytes(file_path)
        message = parse_message(raw_bytes)

        message_id = clean_text(message.get("Message-ID"))
        date = normalize_date_to_utc(message.get("Date"))
        from_addresses = extract_addresses(message.get("From"))
        to_addresses = extract_addresses(message.get("To"))
        subject = clean_text(message.get("Subject"))

        body, forwarded_content, quoted_content = extract_body_parts(message)

        if not message_id:
            return None, "Missing mandatory field: message_id"

        if not date:
            return None, "Missing or invalid mandatory field: date"

        if not from_addresses:
            return None, "Missing mandatory field: from_address"

        if not to_addresses:
            return None, "Missing mandatory field: to_addresses"

        if not subject:
            return None, "Missing mandatory field: subject"

        if not body:
            return None, "Missing mandatory field: body"

        body_normalized = normalize_body_for_matching(body)

        email_record = {
            "message_id": message_id,
            "date": date,
            "from_address": from_addresses[0],
            "to_addresses": to_addresses,
            "subject": subject,
            "subject_normalized": normalize_subject(subject),
            "body": body,
            "body_normalized": body_normalized,
            "body_hash": create_body_hash(body_normalized),
            "source_file": str(file_path.relative_to(root_path)),
            "cc_addresses": extract_addresses(message.get("Cc")),
            "bcc_addresses": extract_addresses(message.get("Bcc")),
            "x_from": clean_text(message.get("X-From")),
            "x_to": clean_text(message.get("X-To")),
            "x_cc": clean_text(message.get("X-cc")),
            "x_bcc": clean_text(message.get("X-bcc")),
            "x_folder": clean_text(message.get("X-Folder")),
            "x_origin": clean_text(message.get("X-Origin")),
            "content_type": clean_text(message.get_content_type()),
            "has_attachment": infer_has_attachment(message, body),
            "forwarded_content": clean_text(forwarded_content),
            "quoted_content": clean_text(quoted_content),
            "headings": extract_headings(body),
        }

        return email_record, None

    except Exception as error:
        return None, f"Unhandled parse error: {error}"