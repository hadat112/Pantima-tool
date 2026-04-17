# text-converter

CLI tool for note workflows:
- CSV notes -> `.txt`
- CSV notes -> mobile Notes screenshots (`.png`, iOS/Android)
- Live browser preview for note templates

## Install

```bash
poetry install
poetry run playwright install chromium
```

## CLI

Entrypoint:

```bash
poetry run tc --help
```

### Note CSV -> `.txt`

```bash
poetry run tc note from-csv data.csv output/notes/
```

Common options:

```bash
poetry run tc note from-csv data.csv output/notes/ \
  --script-col "Script" \
  --participant-col "participant" \
  --type-col "Data_type" \
  --type "Note" \
  --accepted-col "QA Status" \
  --workers 4 \
  --limit 100 \
  --export-csv output/exported_notes.csv
```

### Note CSV -> `.png`

```bash
poetry run tc note to-png "data/Note Design - Sheet1 (1).csv" output/note-png/
```

Common options:

```bash
poetry run tc note to-png data.csv output/note-png/ \
  --template-col "Template" \
  --device-col "Device" \
  --os-col "OS" \
  --spec-col "spec" \
  --filename-col "filename" \
  --workers 8 \
  --limit 100
```

Viewport resolution priority:
1. `spec`
2. `OS` (if resolution-like, e.g. `1080 × 2340`)
3. device preset fallback (`Device`)
4. default fallback (`390x844`)

Platform template selection:
- iOS hints (`ios`, `iphone`, `ipad`) -> `notes_ios.html`
- Android hints (`android`, `samsung`, `pixel`, `oneplus`, `xiaomi`, `oppo`, `vivo`) -> `notes_android.html`

Each run writes a timestamped output folder and `metadata.csv`.

## Live Preview

Run:

```bash
python3 tools/serve_notes_demo.py
```

Open:

```text
http://127.0.0.1:8765/
```

Routes:
- `/` list Device/OS pairs from CSV + iPhone SE
- `/preview?...` render one screen dynamically (no cache)
- Legacy links:
  - `/ios-light-15promax.html`
  - `/ios-dark-15promax.html`
  - `/ios-dark-se.html`

## Project Structure

- `src/text_converter/cli.py` - CLI entrypoint (`tc`)
- `src/text_converter/note_to_txt.py` - Note text export
- `src/text_converter/note_to_png.py` - Note screenshot pipeline
- `src/text_converter/templates/notes_ios.html` - iOS template
- `src/text_converter/templates/notes_android.html` - Android template
- `src/text_converter/templates/assets/notes_ios/` - iOS icon assets
- `tools/serve_notes_demo.py` - live preview server
