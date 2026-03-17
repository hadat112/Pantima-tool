# Chat to PNG — Run Commands (PowerShell)

> Chạy từ thư mục gốc của project.

## Cài đặt (chạy 1 lần)

```powershell
poetry install --with chat
poetry run playwright install chromium
```

---

## Relationship (20 records)

```powershell
poetry run tc chat from-csv `
  "data/chat/Screenshot test - Relationship.csv" `
  output/chat `
  --script-col "Script" `
  --id-col "Number" `
  --qa-col "participant" `
  --participant-col "participant" `
  --workers 8 `
  --done-csv "data/done-data/chat.csv"
```

---

**Notes:**
- `` ` `` là ký tự line continuation của PowerShell
- `--script-col "Script"` — cột chứa nội dung hội thoại
- `--id-col "Number"` — cột ID dùng làm seed (deterministic device/theme)
- `--qa-col "participant"` — cột dùng trong tên file output (`{id}_{qa}.png`)
- `--participant-col "participant"` — cột participant dùng cho done-csv
- `--done-csv` — append danh sách index đã chạy vào file CSV (format: `index,participant,filename`)
- Log tự động ghi vào `logs/<filename>.log`
- Output vào subfolder theo timestamp: `output/chat/YYYY-MM-DD_HH-MM-SS/`
