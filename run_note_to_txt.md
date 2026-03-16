# Note to TXT — Run Commands (PowerShell)

> Chạy từ thư mục gốc của project. Yêu cầu: `poetry install` đã được chạy trước.

---

## Contact (232 records)

```powershell
poetry run tc note from-csv `
  "data/Team management - Pantima - Notes_Contact_Cleaned.csv" `
  output/notes_contact `
  --accepted-col "QA Status" `
  --script-col "Script" `
  --workers 6 `
  --limit 232 `
  --export-csv output/notes_contact_accepted.csv
```

---

## Event (399 records)

```powershell
poetry run tc note from-csv `
  "data/Team management - Pantima - Notes_Event_Cleaned.csv" `
  output/notes_event `
  --accepted-col "QA Status" `
  --script-col "Script" `
  --workers 6 `
  --limit 399 `
  --export-csv output/notes_event_accepted.csv
```

---

## People & Relationships (1,050 records)

```powershell
poetry run tc note from-csv `
  "data/Team management - Pantima - Notes_People.csv" `
  output/notes_people `
  --accepted-col "QA Status" `
  --script-col "Script" `
  --workers 6 `
  --limit 1050 `
  --export-csv output/notes_people_accepted.csv
```

---

## Topics of Interest (1,050 records)

```powershell
poetry run tc note from-csv `
  "data/Team management - Pantima - Notes_Topic.csv" `
  output/notes_topic `
  --accepted-col "QA Status" `
  --script-col "Script" `
  --workers 6 `
  --limit 1050 `
  --export-csv output/notes_topic_accepted.csv
```

---

**Notes:**
- `` ` `` là ký tự line continuation của PowerShell
- `--accepted-col "QA Status"` — chỉ lấy rows có status `accepted`
- `--limit N` — giới hạn số file xuất ra (đếm trên rows đã accepted)
- `--export-csv` — xuất CSV chứa đúng N rows đã accepted
- Log tự động ghi vào `logs/<filename>.log`
