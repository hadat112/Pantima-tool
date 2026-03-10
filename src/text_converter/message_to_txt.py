"""Convert message records (SMS, chat, etc.) to .txt files."""

import csv
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime


def _slug(text: str) -> str:
    return re.sub(r"[^\w]+", "_", text).strip("_").lower()


TEMPLATE = """\
[{timestamp}] {sender}: {body}
"""


def format_message(sender: str, body: str, timestamp: str | None = None) -> str:
    ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return TEMPLATE.format(timestamp=ts, sender=sender, body=body)


def convert(
    messages: list[dict],
    output_path: Path,
    header: str | None = None,
) -> Path:
    """Write a list of messages to a single .txt file.

    Each message dict must have: sender, body.
    Optional keys: timestamp.

    Args:
        messages: List of message dicts
        output_path: Destination .txt file
        header: Optional header line at top of file

    Returns:
        Path to the written file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    if header:
        lines.append(header)
        lines.append("=" * len(header))
        lines.append("")

    for msg in messages:
        lines.append(format_message(
            sender=msg["sender"],
            body=msg["body"],
            timestamp=msg.get("timestamp"),
        ))

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def batch_from_csv(
    csv_path: Path,
    output_dir: Path,
    script_col: str = "Script",
    participant_col: str = "participant",
    data_type_col: str = "Data_type",
    data_type_filter: str | None = None,
    max_workers: int = 1,
    limit: int = 0,
) -> list[Path]:
    """Convert Script column rows from a CSV to individual .txt message files.

    Args:
        csv_path: Path to the CSV file
        output_dir: Directory to write .txt files
        script_col: Column containing the message body
        participant_col: Column containing the sender/participant name
        data_type_col: Column used for filtering by type
        data_type_filter: Only process rows where data_type_col equals this value.
            None = all rows.
        max_workers: Number of parallel workers for file writing.
        limit: Max number of rows to process (0 = all).

    Returns:
        List of written .txt file paths
    """
    csv_path = Path(csv_path)
    output_dir = Path(output_dir)

    # Phase 1: collect work items (serial CSV read)
    items: list[tuple[int, str, Path]] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if data_type_filter:
                if (row.get(data_type_col) or "").strip() != data_type_filter:
                    continue

            script = (row.get(script_col) or "").strip()
            if not script:
                continue

            participant = (row.get(participant_col) or f"row_{i+1}").strip()
            filename = f"{i+1:04d}_{_slug(participant)}.txt"
            items.append((i + 1, script, output_dir / filename))

    if limit:
        items = items[:limit]

    if not items:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)

    # Phase 2: write files (concurrent)
    def _write(args: tuple[int, str, Path]) -> Path:
        _, script, out_path = args
        out_path.write_text(script, encoding="utf-8")
        return out_path

    results = []
    errors = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [(item, executor.submit(_write, item)) for item in items]

    for item, future in futures:
        try:
            results.append(future.result())
        except Exception as exc:
            errors.append((item[0], exc))

    if errors:
        for row_num, exc in errors:
            print(f"[SKIP] row {row_num}: {exc}")

    return results


def batch_convert(conversations: list[dict], output_dir: Path) -> list[Path]:
    """Convert multiple conversations, each to its own .txt file.

    Each conversation dict must have: messages (list), filename or title.
    """
    output_dir = Path(output_dir)
    results = []
    for i, conv in enumerate(conversations):
        filename = conv.get("filename") or f"conversation_{i + 1:04d}.txt"
        out = convert(
            messages=conv["messages"],
            output_path=output_dir / filename,
            header=conv.get("title"),
        )
        results.append(out)
    return results
