# Developer Notes

## Repo
`git@github.com:hadat112/Pantima-tool.git`

## Setup on New Machine
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"  # add to ~/.zshrc

# Install dependencies
cd text-converter
poetry install
```

## Run Commands

```bash
# Email → .eml
poetry run tc email convert data/ex-mail.txt output/ex-mail.eml
poetry run tc email batch ./input_dir/ ./output/eml/
poetry run tc email from-csv data.csv output/eml/
poetry run tc email from-csv data.csv output/eml/ --prefix Mail_Contact

# Note → .txt
poetry run tc note from-csv data.csv output/notes/
poetry run tc note from-csv data.csv output/notes/ --type Note

# Message → .txt
poetry run tc message from-csv data.csv output/messages/
poetry run tc message from-csv data.csv output/messages/ --type Message

# Audio/Voicemail transcript → .txt
poetry run tc audio from-csv data.csv output/audio/
poetry run tc audio from-csv data.csv output/audio/ --type Voicemail
```

## CSV Column Defaults
| Option | Default |
|---|---|
| `--scrip-col` | `Scrip` |
| `--script-col` | `Script` |
| `--participant-col` | `participant` |
| `--type-col` | `Data_type` |
| `--cat-col` | `Data type/category` |

## Key Rules
- **Email**: Script must have `From:`, `To:`, `Subject:` headers — rows missing them are skipped
- **Note / Message / Audio**: Script content written as-is, no metadata added
- Wrapping quotes `"..."` in script files are auto-stripped
- `faster-whisper` (real audio files) is optional: `poetry install --with audio`
