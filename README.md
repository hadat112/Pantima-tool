# text-converter

A CLI tool for bulk conversion of plain-text scripts into structured files (`.eml`, `.txt`).
Supports emails, notes, messages, and voicemail/audio transcripts — sourced from individual files or CSV exports.

---

## Requirements

- Python 3.13+
- [Poetry](https://python-poetry.org/)

## Installation

```bash
git clone <repo-url>
cd text-converter
poetry install
```

---

## Usage

All commands are prefixed with `poetry run tc`. Run them from inside the `text-converter/` directory.

```
tc
├── email
│   ├── convert       # Single .txt file → .eml
│   ├── batch         # Folder of .txt files → .eml
│   └── from-csv      # CSV rows → .eml
├── note
│   └── from-csv      # CSV rows → .txt
├── message
│   └── from-csv      # CSV rows → .txt
└── audio
    └── from-csv      # CSV rows → .txt
```

---

## Email → `.eml`

### Script format

Each email script **must** contain `From:`, `To:`, and `Subject:` headers at the top.
Rows missing these headers are automatically skipped.

```
From:  michael.johnson.dev@gmail.com
To:    <amanda.reynolds@sunridge-realty.com>
Subject: Reaching out about the project contact

Hi Amanda,

I got your info from Kevin at the meetup last week and figured I'd send a quick email.
If you need to reach me directly about the backend integration work,
feel free to call or text.

Michael Johnson
Software Engineer
Phone: +1 (415) 732-8841
```

### Commands

**Convert a single file:**
```bash
poetry run tc email convert input.txt output.eml
```

**Convert all `.txt` files in a folder:**
```bash
poetry run tc email batch ./input_emails/ ./output/eml/
```

**Convert from CSV — all rows:**
```bash
poetry run tc email from-csv data.csv output/eml/
```

**Convert from CSV — filter by category prefix:**
```bash
poetry run tc email from-csv data.csv output/eml/ --prefix Mail_Contact
```

**Convert from CSV — multiple prefixes:**
```bash
poetry run tc email from-csv data.csv output/eml/ \
  --prefix Mail_Contact \
  --prefix Message_contact
```

**Custom column names:**
```bash
poetry run tc email from-csv data.csv output/eml/ \
  --scrip-col "Scrip" \
  --cat-col "Data type/category"
```

### Options

| Option | Default | Description |
|---|---|---|
| `--scrip-col` | `Scrip` | Column containing the email script |
| `--cat-col` | `Data type/category` | Column used for category filtering |
| `--prefix` / `-p` | _(all rows)_ | Filter rows by category prefix. Repeatable. |

---

## Note → `.txt`

Each row's script is written as-is into its own `.txt` file, named `{index}_{participant}.txt`.

### Commands

**Convert all rows:**
```bash
poetry run tc note from-csv data.csv output/notes/
```

**Filter by data type:**
```bash
poetry run tc note from-csv data.csv output/notes/ --type Note
```

**Custom column names:**
```bash
poetry run tc note from-csv data.csv output/notes/ \
  --script-col "Script" \
  --participant-col "participant" \
  --type-col "Data_type"
```

### Options

| Option | Default | Description |
|---|---|---|
| `--script-col` | `Script` | Column containing the note content |
| `--participant-col` | `participant` | Column used for output filename |
| `--date-col` | `Date` | Date column |
| `--occupation-col` | `occupation` | Occupation column |
| `--category-col` | `primary category` | Category column |
| `--type-col` | `Data_type` | Column used for `--type` filtering |
| `--type` / `-t` | _(all rows)_ | Only process rows matching this value |

---

## Message → `.txt`

Same behavior as Note — script content written directly into individual `.txt` files.

### Commands

**Convert all rows:**
```bash
poetry run tc message from-csv data.csv output/messages/
```

**Filter by data type:**
```bash
poetry run tc message from-csv data.csv output/messages/ --type Message
```

**Custom column names:**
```bash
poetry run tc message from-csv data.csv output/messages/ \
  --script-col "Script" \
  --participant-col "participant"
```

### Options

| Option | Default | Description |
|---|---|---|
| `--script-col` | `Script` | Column containing the message content |
| `--participant-col` | `participant` | Column used for output filename |
| `--type-col` | `Data_type` | Column used for `--type` filtering |
| `--type` / `-t` | _(all rows)_ | Only process rows matching this value |

---

## Voicemail / Audio Transcript → `.txt`

Handles **pre-transcribed** text from CSV — not actual audio files.
Script content is written directly into individual `.txt` files.

> For transcribing real audio files, use `audio.transcribe()` or `audio.batch_transcribe()` directly in Python (requires `poetry install --with audio`).

### Commands

**Convert all rows:**
```bash
poetry run tc audio from-csv data.csv output/audio/
```

**Filter by data type:**
```bash
poetry run tc audio from-csv data.csv output/audio/ --type Voicemail
```

**Custom column names:**
```bash
poetry run tc audio from-csv data.csv output/audio/ \
  --script-col "Script" \
  --participant-col "participant"
```

### Options

| Option | Default | Description |
|---|---|---|
| `--script-col` | `Script` | Column containing the transcript content |
| `--participant-col` | `participant` | Column used for output filename |
| `--type-col` | `Data_type` | Column used for `--type` filtering |
| `--type` / `-t` | _(all rows)_ | Only process rows matching this value |

---

## CSV Format Reference

### Email CSV (`email from-csv`)

| Column | Required | Notes |
|---|---|---|
| `Scrip` | Yes | Must contain `From:`, `To:`, `Subject:` headers. Rows without them are skipped. |
| `Data type/category` | No | Used for `--prefix` filtering |

### Note / Message / Audio CSV (`note`, `message`, `audio from-csv`)

| Column | Required | Notes |
|---|---|---|
| `Script` | Yes | Raw script content. Empty rows are skipped. |
| `participant` | No | Used for output filename |
| `Date` | No | Included in note metadata |
| `Data_type` | No | Used for `--type` filtering |

---

## Output Naming

| Module | Filename pattern | Example |
|---|---|---|
| `email from-csv` | `{index}_{category}.eml` | `0001_mail_contact_1.eml` |
| `email batch` | `{original_name}.eml` | `email1.eml` |
| `note from-csv` | `{index}_{participant}.txt` | `0001_liam.txt` |
| `message from-csv` | `{index}_{participant}.txt` | `0007_emily_carter.txt` |
| `audio from-csv` | `{index}_{participant}.txt` | `0003_claire_dubois.txt` |
