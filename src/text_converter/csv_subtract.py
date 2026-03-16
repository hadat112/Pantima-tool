"""Remove already-processed rows from a CSV using a run log."""

import csv
import re
from pathlib import Path


def _parse_done_indices(log_path: Path) -> set[int]:
    """Return the set of 1-based row indices recorded in a run log.

    Each data line in the log looks like:
        0071_daniel.txt
    The four leading digits are the row index used when the file was created.
    """
    done: set[int] = set()
    pattern = re.compile(r"^\s+(\d+)_")
    for line in log_path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            done.add(int(m.group(1)))
    return done


def subtract(
    csv_path: Path,
    log_path: Path,
    output_path: Path,
) -> tuple[int, int]:
    """Write a new CSV with already-processed rows removed.

    Args:
        csv_path:    Original CSV file.
        log_path:    File listing already-processed rows (.log, .csv, .txt, or any text file).
        output_path: Destination CSV (will be created / overwritten).

    Returns:
        (kept, removed) — number of data rows kept and removed.
    """
    csv_path = Path(csv_path)
    log_path = Path(log_path)
    output_path = Path(output_path)

    done = _parse_done_indices(log_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    kept = 0
    removed = 0
    with (
        open(csv_path, encoding="utf-8", newline="") as fin,
        open(output_path, "w", encoding="utf-8", newline="") as fout,
    ):
        reader = csv.DictReader(fin)
        fieldnames = list(reader.fieldnames or [])
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for i, row in enumerate(reader, start=1):
            if i in done:
                removed += 1
            else:
                writer.writerow(row)
                kept += 1

    return kept, removed
