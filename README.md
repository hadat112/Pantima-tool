# text-converter

A CLI tool for bulk conversion of plain-text scripts into structured files (`.eml`, `.txt`).
Supports emails, notes, messages, and voicemail/audio transcripts — sourced from individual files or CSV exports.

---

## Requirements

- Python 3.13+
- [Poetry](https://python-poetry.org/)

## Installation

### macOS / Ubuntu

Run the setup script — detects your OS automatically and handles everything from scratch:

```bash
bash setup.sh
```

**macOS** — what it does:

1. Installs [Homebrew](https://brew.sh/) (if not present)
2. Installs Python 3.13 via Homebrew
  > ⚠️ The system Python (3.9) bundled with Xcode cannot create virtual environments — use Homebrew's Python instead.
3. Installs Poetry using Python 3.13
4. Adds Poetry to `$PATH` and persists it to `~/.zshrc` or `~/.bashrc`
5. Runs `poetry install`
6. Verifies with `poetry run tc --help`

**Ubuntu/Debian** — what it does:

1. Installs Python 3.13 via the [deadsnakes PPA](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa)
2. Installs Poetry
3. Adds Poetry to `$PATH` and persists it to `~/.zshrc` or `~/.bashrc`
4. Runs `poetry install`
5. Verifies with `poetry run tc --help`

---

### Windows

Open **PowerShell as Administrator**, then run:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

What it does:

1. Installs Python 3.13 via `winget` (if not present)
2. Installs Poetry
3. Adds Poetry to the user `PATH` permanently
4. Runs `poetry install`
5. Verifies with `poetry run tc --help`

> **Requires:** [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/) (pre-installed on Windows 10 1709+ / Windows 11)

---

### Manual setup (any OS)

```bash
# 1. Install Python 3.13 from https://python.org/downloads

# 2. Install Poetry
curl -sSL https://install.python-poetry.org | python3.13 -

# 3. Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# 4. Install dependencies
poetry install

# 5. Verify
poetry run tc --help
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

**Convert with parallel workers:**

```bash
poetry run tc email batch ./input_emails/ ./output/eml/ --workers 4
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

**Convert with parallel workers:**

```bash
poetry run tc email from-csv data.csv output/eml/ --workers 4
```

**Limit rows per run:**

```bash
poetry run tc email from-csv data.csv output/eml/ --limit 100
```

### Options


| Option             | Default              | Description                                  |
| ------------------ | -------------------- | -------------------------------------------- |
| `--scrip-col`      | `Scrip`              | Column containing the email script           |
| `--cat-col`        | `Data type/category` | Column used for category filtering           |
| `--prefix` / `-p`  | *(all rows)*         | Filter rows by category prefix. Repeatable.  |
| `--workers` / `-w` | `1`                  | Number of parallel workers for file writing. |
| `--limit` / `-n`   | `0` *(all)*          | Max number of rows to process per run.       |


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

**Convert with parallel workers:**

```bash
poetry run tc note from-csv data.csv output/notes/ --workers 4
```

**Export only accepted rows (filter by status column):**

```bash
poetry run tc note from-csv data.csv output/notes/ --accepted-col "QA Status"
```

**Combine accepted filter with type filter:**

```bash
poetry run tc note from-csv data.csv output/notes/ \
  --type Note \
  --accepted-col "Anno Status"
```

**Limit rows per run:**

```bash
poetry run tc note from-csv data.csv output/notes/ --limit 100
```

### Options


| Option                  | Default            | Description                                                                                       |
| ----------------------- | ------------------ | ------------------------------------------------------------------------------------------------- |
| `--script-col`          | `Script`           | Column containing the note content                                                                |
| `--participant-col`     | `participant`      | Column used for output filename                                                                   |
| `--date-col`            | `Date`             | Date column                                                                                       |
| `--occupation-col`      | `occupation`       | Occupation column                                                                                 |
| `--category-col`        | `primary category` | Category column                                                                                   |
| `--type-col`            | `Data_type`        | Column used for `--type` filtering                                                                |
| `--type` / `-t`         | *(all rows)*       | Only process rows matching this value                                                             |
| `--accepted-col` / `-a` | *(disabled)*       | Column containing accept/reject status. Only rows with value `accept` or `accepted` are exported. |
| `--workers` / `-w`      | `1`                | Number of parallel workers for file writing.                                                      |
| `--limit` / `-n`        | `0` *(all)*        | Max number of rows to process per run.                                                            |


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

**Convert with parallel workers:**

```bash
poetry run tc message from-csv data.csv output/messages/ --workers 4
```

**Limit rows per run:**

```bash
poetry run tc message from-csv data.csv output/messages/ --limit 100
```

### Options


| Option              | Default       | Description                                  |
| ------------------- | ------------- | -------------------------------------------- |
| `--script-col`      | `Script`      | Column containing the message content        |
| `--participant-col` | `participant` | Column used for output filename              |
| `--type-col`        | `Data_type`   | Column used for `--type` filtering           |
| `--type` / `-t`     | *(all rows)*  | Only process rows matching this value        |
| `--workers` / `-w`  | `1`           | Number of parallel workers for file writing. |
| `--limit` / `-n`    | `0` *(all)*   | Max number of rows to process per run.       |


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

**Convert with parallel workers:**

```bash
poetry run tc audio from-csv data.csv output/audio/ --workers 4
```

**Limit rows per run:**

```bash
poetry run tc audio from-csv data.csv output/audio/ --limit 100
```

### Options


| Option              | Default       | Description                                  |
| ------------------- | ------------- | -------------------------------------------- |
| `--script-col`      | `Script`      | Column containing the transcript content     |
| `--participant-col` | `participant` | Column used for output filename              |
| `--type-col`        | `Data_type`   | Column used for `--type` filtering           |
| `--type` / `-t`     | *(all rows)*  | Only process rows matching this value        |
| `--workers` / `-w`  | `1`           | Number of parallel workers for file writing. |
| `--limit` / `-n`    | `0` *(all)*   | Max number of rows to process per run.       |


---

## CSV Format Reference

### Email CSV (`email from-csv`)


| Column               | Required | Notes                                                                           |
| -------------------- | -------- | ------------------------------------------------------------------------------- |
| `Scrip`              | Yes      | Must contain `From:`, `To:`, `Subject:` headers. Rows without them are skipped. |
| `Data type/category` | No       | Used for `--prefix` filtering                                                   |


### Note / Message / Audio CSV (`note`, `message`, `audio from-csv`)


| Column             | Required | Notes                                                                                                       |
| ------------------ | -------- | ----------------------------------------------------------------------------------------------------------- |
| `Script`           | Yes      | Raw script content. Empty rows are skipped.                                                                 |
| `participant`      | No       | Used for output filename                                                                                    |
| `Date`             | No       | Included in note metadata                                                                                   |
| `Data_type`        | No       | Used for `--type` filtering                                                                                 |
| *(any status col)* | No       | Used for `--accepted-col` filtering. Accepted values: `accept`, `accepted`. e.g. `Anno Status`, `QA Status` |


---

## Output Naming


| Module             | Filename pattern            | Example                   |
| ------------------ | --------------------------- | ------------------------- |
| `email from-csv`   | `{index}_{category}.eml`    | `0001_mail_contact_1.eml` |
| `email batch`      | `{original_name}.eml`       | `email1.eml`              |
| `note from-csv`    | `{index}_{participant}.txt` | `0001_liam.txt`           |
| `message from-csv` | `{index}_{participant}.txt` | `0007_emily_carter.txt`   |
| `audio from-csv`   | `{index}_{participant}.txt` | `0003_claire_dubois.txt`  |


