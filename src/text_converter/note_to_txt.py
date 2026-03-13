"""Convert structured notes to .txt files."""

import csv
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime


def _slug(text: str) -> str:
    return re.sub(r"[^\w]+", "_", text).strip("_").lower()


def convert(
    title: str,
    body: str,
    output_path: Path,
    tags: list[str] | None = None,
    created_at: str | None = None,
) -> Path:
    """Write a single note to a .txt file.

    Args:
        title: Note title
        body: Note content
        output_path: Destination .txt file
        tags: Optional list of tags
        created_at: Optional creation date string

    Returns:
        Path to the written file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [title, "=" * len(title), ""]

    if created_at:
        lines.append(f"Date: {created_at}")
    else:
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if tags:
        lines.append(f"Tags: {', '.join(tags)}")

    lines.append("")
    lines.append(body)

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


_ACCEPTED_VALUES = {"accept", "accepted"}


def batch_from_csv(
    csv_path: Path,
    output_dir: Path,
    script_col: str = "Script",
    participant_col: str = "participant",
    date_col: str = "Date",
    occupation_col: str = "occupation",
    category_col: str = "primary category",
    data_type_col: str = "Data_type",
    data_type_filter: str | None = None,
    accepted_col: str | None = None,
    max_workers: int = 1,
    limit: int = 0,
    export_csv: Path | None = None,
) -> list[Path]:
    """Convert Script column rows from a CSV to individual .txt note files.

    Args:
        csv_path: Path to the CSV file
        output_dir: Directory to write .txt files
        script_col: Column containing the note body
        participant_col: Column containing the note author/name
        date_col: Column containing the date
        occupation_col: Column containing occupation (used as tag)
        category_col: Column containing category (used as tag)
        data_type_col: Column used for filtering by type
        data_type_filter: Only process rows where data_type_col equals this value.
            None = all rows.
        accepted_col: Column containing accept/reject status. When set, only rows
            where the value is "accept" or "accepted" (case-insensitive) are exported.
        max_workers: Number of parallel workers for file writing.
        limit: Max number of rows to process (0 = all).

    Returns:
        List of written .txt file paths
    """
    csv_path = Path(csv_path)
    output_dir = Path(output_dir)

    # Phase 1: collect work items (serial CSV read)
    items: list[tuple[int, str, Path]] = []
    exported_rows: list[dict] = []
    fieldnames: list[str] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        for i, row in enumerate(reader):
            if data_type_filter:
                row_type = (row.get(data_type_col) or "").strip()
                if row_type != data_type_filter:
                    continue

            if accepted_col:
                status = (row.get(accepted_col) or "").strip().lower()
                if status not in _ACCEPTED_VALUES:
                    continue

            script = (row.get(script_col) or "").strip()
            if not script:
                continue

            participant = (row.get(participant_col) or f"row_{i+1}").strip()
            filename = f"{i+1:04d}_{_slug(participant)}.txt"
            items.append((i + 1, script, output_dir / filename))
            exported_rows.append(dict(row))

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

    if export_csv and exported_rows:
        export_csv = Path(export_csv)
        export_csv.parent.mkdir(parents=True, exist_ok=True)
        with open(export_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(exported_rows)

    return results


def batch_convert(notes: list[dict], output_dir: Path) -> list[Path]:
    """Convert a list of notes, each to its own .txt file.

    Each note dict must have: title, body.
    Optional keys: tags, created_at, filename.
    """
    output_dir = Path(output_dir)
    results = []
    for i, note in enumerate(notes):
        filename = note.get("filename") or f"note_{i + 1:04d}.txt"
        out = convert(
            title=note["title"],
            body=note["body"],
            output_path=output_dir / filename,
            tags=note.get("tags"),
            created_at=note.get("created_at"),
        )
        results.append(out)
    return results
