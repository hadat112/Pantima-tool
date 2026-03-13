"""Transcribe voicemail / audio notes to .txt files using faster-whisper.

For CSV-based transcripts (pre-transcribed text), use batch_from_csv().
For actual audio files, use transcribe() or batch_transcribe().
"""

import csv
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal


def _slug(text: str) -> str:
    return re.sub(r"[^\w]+", "_", text).strip("_").lower()

SUPPORTED_FORMATS = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".flac", ".webm"}


def transcribe(
    audio_path: Path,
    output_path: Path,
    model_size: Literal["tiny", "base", "small", "medium", "large"] = "base",
    language: str | None = None,
    device: str = "cpu",
) -> Path:
    """Transcribe an audio file to a .txt file.

    Args:
        audio_path: Path to the audio file
        output_path: Destination .txt file
        model_size: Whisper model size (tiny/base/small/medium/large)
        language: Language code (e.g. "vi", "en"). None = auto-detect.
        device: "cpu" or "cuda"

    Returns:
        Path to the written transcript file
    """
    from faster_whisper import WhisperModel

    audio_path = Path(audio_path)
    if audio_path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {audio_path.suffix}. Supported: {SUPPORTED_FORMATS}")

    model = WhisperModel(model_size, device=device, compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), language=language)
    transcript = " ".join(seg.text.strip() for seg in segments)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(transcript, encoding="utf-8")
    return output_path


_ACCEPTED_VALUES = {"accept", "accepted"}


def batch_from_csv(
    csv_path: Path,
    output_dir: Path,
    script_col: str = "Script",
    participant_col: str = "participant",
    data_type_col: str = "Data_type",
    data_type_filter: str | None = None,
    accepted_col: str | None = None,
    max_workers: int = 1,
    limit: int = 0,
    export_csv: Path | None = None,
) -> list[Path]:
    """Convert pre-transcribed voicemail/audio note rows from a CSV to .txt files.

    Use this when the CSV already contains transcript text (not audio files).
    For actual audio files, use transcribe() or batch_transcribe() instead.

    Args:
        csv_path: Path to the CSV file
        output_dir: Directory to write .txt files
        script_col: Column containing the transcript text
        participant_col: Column containing the participant/speaker name
        data_type_col: Column used for filtering by type
        data_type_filter: Only process rows where data_type_col equals this value.
            None = all rows.
        accepted_col: Column containing accept/reject status. When set, only rows
            where the value is "accept" or "accepted" (case-insensitive) are exported.
        max_workers: Number of parallel workers for file writing.
        limit: Max number of rows to process (0 = all).
        export_csv: If set, write a CSV of only the exported rows (all columns preserved).

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
                if (row.get(data_type_col) or "").strip() != data_type_filter:
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


def batch_transcribe(
    audio_dir: Path,
    output_dir: Path,
    model_size: Literal["tiny", "base", "small", "medium", "large"] = "base",
    language: str | None = None,
    device: str = "cpu",
    glob: str = "**/*",
) -> list[Path]:
    """Transcribe all audio files in a directory.

    Args:
        audio_dir: Directory containing audio files
        output_dir: Directory to write .txt transcripts
        model_size: Whisper model size
        language: Language code or None for auto-detect
        device: "cpu" or "cuda"
        glob: Glob pattern to filter files

    Returns:
        List of written transcript paths
    """
    from faster_whisper import WhisperModel

    audio_dir = Path(audio_dir)
    output_dir = Path(output_dir)

    audio_files = [
        f for f in audio_dir.glob(glob)
        if f.suffix.lower() in SUPPORTED_FORMATS
    ]

    if not audio_files:
        return []

    # Load model once for all files
    model = WhisperModel(model_size, device=device, compute_type="int8")
    results = []

    for audio_path in audio_files:
        segments, _ = model.transcribe(str(audio_path), language=language)
        transcript = " ".join(seg.text.strip() for seg in segments)

        out = output_dir / audio_path.with_suffix(".txt").name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(transcript, encoding="utf-8")
        results.append(out)

    return results
