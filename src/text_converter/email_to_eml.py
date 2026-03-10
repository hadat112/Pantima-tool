"""Convert plain text email input to .eml file format."""

import csv
import re
from concurrent.futures import ThreadPoolExecutor
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime

_HEADER_RE = re.compile(r"^(From|To|Cc|Bcc|Subject|Date|Reply-To)\s*:\s*(.+)$", re.IGNORECASE)


def parse(text: str) -> dict:
    """Parse a raw plain-text email into structured fields.

    Expected format:
        From:  sender@example.com
        To:    <recipient@example.com>
        Subject: Some subject
        <blank line or body starts directly>
        Body text...

    Raises ValueError if From or To headers are missing.
    """
    # Strip wrapping quotes if the entire text is quoted (e.g. from CSV export)
    text = text.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]

    lines = text.splitlines()
    result: dict = {}
    body_start = 0

    for i, line in enumerate(lines):
        m = _HEADER_RE.match(line)
        if m:
            key = m.group(1).lower().replace("-", "_")
            value = m.group(2).strip()
            value = re.sub(r"^<(.+)>$", r"\1", value).strip()
            if key == "from":
                result["sender"] = value
            elif key == "to":
                result["recipient"] = value
            else:
                result[key] = value
            body_start = i + 1
        elif i < body_start:
            if line.strip():
                body_start = i
                break
        else:
            break

    body_lines = lines[body_start:]
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

    result["body"] = "\n".join(body_lines)

    if "sender" not in result:
        raise ValueError("Missing 'From:' header")
    if "recipient" not in result:
        raise ValueError("Missing 'To:' header")
    if "subject" not in result:
        result["subject"] = "(no subject)"

    return result


def convert(
    sender: str,
    recipient: str,
    subject: str,
    body: str,
    output_path: Path,
    date: str | None = None,
    cc: str | None = None,
    reply_to: str | None = None,
    html_body: str | None = None,
) -> Path:
    """Convert structured email fields to a .eml file."""
    if html_body:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
    else:
        msg = MIMEText(body, "plain", "utf-8")

    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Date"] = date or datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    msg["MIME-Version"] = "1.0"

    if cc:
        msg["Cc"] = cc
    if reply_to:
        msg["Reply-To"] = reply_to

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(msg.as_string(), encoding="utf-8")
    return output_path


def from_text(text: str, output_path: Path) -> Path:
    """Parse a raw email text and write it as a .eml file.

    Raises ValueError if the script is missing From or To headers.
    """
    fields = parse(text)
    return convert(
        sender=fields["sender"],
        recipient=fields["recipient"],
        subject=fields["subject"],
        body=fields["body"],
        output_path=output_path,
        date=fields.get("date"),
        cc=fields.get("cc"),
        reply_to=fields.get("reply_to"),
    )


def _safe_filename(subject: str, index: int) -> str:
    safe = re.sub(r"[^\w\s-]", "", subject).strip()
    safe = re.sub(r"\s+", "_", safe)[:60]
    return f"{index:04d}_{safe}.eml" if safe else f"email_{index:04d}.eml"


def batch_convert(records: list[dict], output_dir: Path) -> list[Path]:
    """Convert a list of structured email records to .eml files.

    Each record must have: sender, recipient, subject, body.
    Optional keys: date, cc, reply_to, html_body, filename.
    """
    output_dir = Path(output_dir)
    results = []
    for i, record in enumerate(records):
        filename = record.get("filename") or _safe_filename(record.get("subject", ""), i + 1)
        out = convert(
            sender=record["sender"],
            recipient=record["recipient"],
            subject=record["subject"],
            body=record["body"],
            output_path=output_dir / filename,
            date=record.get("date"),
            cc=record.get("cc"),
            reply_to=record.get("reply_to"),
            html_body=record.get("html_body"),
        )
        results.append(out)
    return results


def batch_from_csv(
    csv_path: Path,
    output_dir: Path,
    scrip_col: str = "Scrip",
    category_col: str = "Data type/category",
    category_prefix: str | list[str] | None = None,
    max_workers: int = 1,
    limit: int = 0,
) -> list[tuple[str, Path]]:
    """Convert email Script rows from a CSV to .eml files.

    Only rows whose Script contains valid From/To/Subject headers are converted.
    Rows missing these headers are skipped and reported.

    Args:
        csv_path: Path to the CSV file
        output_dir: Directory to write .eml files
        scrip_col: Column containing the raw email script
        category_col: Column used for filtering/naming
        category_prefix: Filter rows by category prefix(es). None = all rows.
        max_workers: Number of parallel workers for file writing.
        limit: Max number of rows to process (0 = all).

    Returns:
        List of (category, output_path) tuples for converted files
    """
    csv_path = Path(csv_path)
    output_dir = Path(output_dir)
    skipped = []

    if isinstance(category_prefix, str):
        prefixes = [category_prefix] if category_prefix else []
    else:
        prefixes = [p for p in (category_prefix or []) if p]

    # Phase 1: parse all rows (serial CSV read)
    items: list[tuple[str, dict, Path]] = []  # (category, fields, output_path)
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            category = (row.get(category_col) or f"row_{i+1}").strip()

            if prefixes and not any(category.startswith(p) for p in prefixes):
                continue

            scrip = (row.get(scrip_col) or "").strip()
            if not scrip:
                continue

            try:
                fields = parse(scrip)
            except ValueError as exc:
                skipped.append((category, str(exc)))
                continue

            filename = f"{i+1:04d}_{category.lower().replace(' ', '_')}.eml"
            items.append((category, fields, output_dir / filename))

    if skipped:
        for cat, reason in skipped:
            print(f"[SKIP] {cat}: {reason}")

    if limit:
        items = items[:limit]

    if not items:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)

    # Phase 2: write .eml files (concurrent)
    def _convert_item(args: tuple[str, dict, Path]) -> tuple[str, Path]:
        category, fields, out_path = args
        out = convert(
            sender=fields["sender"],
            recipient=fields["recipient"],
            subject=fields["subject"],
            body=fields["body"],
            output_path=out_path,
            date=fields.get("date"),
            cc=fields.get("cc"),
        )
        return category, out

    results = []
    errors = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [(item, executor.submit(_convert_item, item)) for item in items]

    for item, future in futures:
        try:
            results.append(future.result())
        except Exception as exc:
            errors.append((item[0], exc))

    if errors:
        for cat, exc in errors:
            print(f"[SKIP] {cat}: {exc}")

    return results


def batch_from_dir(input_dir: Path, output_dir: Path, glob: str = "*.txt", max_workers: int = 1) -> list[Path]:
    """Convert all plain-text email files in a directory to .eml files.

    Each .txt file must follow the From/To/Subject + body format.
    Files missing required headers are skipped and reported.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    txt_files = sorted(input_dir.glob(glob))
    if not txt_files:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)

    def _process(txt_file: Path) -> Path:
        text = txt_file.read_text(encoding="utf-8")
        out = output_dir / txt_file.with_suffix(".eml").name
        return from_text(text, out)

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [(f, executor.submit(_process, f)) for f in txt_files]

    for txt_file, future in futures:
        try:
            results.append(future.result())
        except Exception as exc:
            print(f"[SKIP] {txt_file.name}: {exc}")

    return results
