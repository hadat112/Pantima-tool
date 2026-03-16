"""Remove already-processed rows from a CSV."""

import csv
import re
from pathlib import Path


def _refs_from_log(ref_path: Path) -> set[str]:
    """Parse filenames like '0071_daniel.txt' → strip leading zeros → {'71', ...}."""
    done: set[str] = set()
    pattern = re.compile(r"^\s+(\d+)_")
    for line in ref_path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            val = m.group(1).lstrip("0") or "0"
            done.add(val)
    return done


def _refs_from_csv_col(ref_path: Path, ref_col: str) -> set[str]:
    """Read a CSV ref-file and return the set of values in ref_col, stripped of leading zeros."""
    done: set[str] = set()
    with open(ref_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            val = (row.get(ref_col) or "").strip()
            if val:
                normalized = val.lstrip("0") or "0"
                done.add(normalized)
    return done


_AUTO_ID_COLS = ("index", "id")


def _detect_ref_col(ref_path: Path) -> str | None:
    """Return the first column name matching a known ID column, or None."""
    if ref_path.suffix.lower() != ".csv":
        return None
    with open(ref_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return None
        for col in reader.fieldnames:
            if col.strip().lower() in _AUTO_ID_COLS:
                return col.strip()
    return None


def subtract(
    csv_path: Path,
    ref_path: Path,
    output_path: Path,
    ref_col: str | None = None,
    target_col: str | None = None,
) -> tuple[int, int]:
    """Write a new CSV with already-processed rows removed.

    Args:
        csv_path:    Original CSV file.
        ref_path:    Processed-rows file. Three modes:
                       - CSV with ref_col: reads that column's values as IDs.
                       - CSV with auto-detected 'index'/'id' column (no ref_col needed).
                       - Log/text with filenames (0071_name.txt): parses leading digits.
        output_path: Destination CSV (created/overwritten).
        ref_col:     Column in ref_path to read IDs from (CSV mode).
                     None = auto-detect 'index'/'id' column, then fall back to filename parsing.
        target_col:  Column in csv_path to match against.
                     None = use first column.

    Returns:
        (kept, removed)
    """
    csv_path = Path(csv_path)
    ref_path = Path(ref_path)
    output_path = Path(output_path)

    if not ref_col:
        ref_col = _detect_ref_col(ref_path)

    if ref_col:
        done = _refs_from_csv_col(ref_path, ref_col)
    else:
        done = _refs_from_log(ref_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    kept = removed = 0
    with (
        open(csv_path, encoding="utf-8-sig", newline="") as fin,
        open(output_path, "w", encoding="utf-8", newline="") as fout,
    ):
        reader = csv.DictReader(fin)
        fieldnames = list(reader.fieldnames or [])
        col = target_col if target_col and target_col in fieldnames else fieldnames[0]
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            val = (row.get(col) or "").strip().lstrip("0") or "0"
            if val in done:
                removed += 1
            else:
                writer.writerow(row)
                kept += 1

    return kept, removed
