# Chat to PNG — Run Commands (PowerShell)

> Chạy từ thư mục gốc của project.

## Cài đặt (chạy 1 lần)

```powershell
poetry install --with chat
poetry run playwright install chromium
```

---

## HungLD Screenshot

```powershell
poetry run tc chat from-csv `
  "data/Meta Data HungLD - Screenshot.csv" `
  output/chat `
  --script-col "Script" `
  --id-col "Unnamed: 0" `
  --qa-col "participant" `
  --participant-col "participant" `
  --filename-col "File" `
  --country-col "country" `
  --application-col "application used" `
  --os-col "OS" `
  --device-col "device info" `
  --creation-col "Creation Date (YYYY.MM.DD)" `
  --workers 8 `
  --done-csv "data/done-data/chat.csv"
```

---

## Screenshot

```powershell
poetry run tc chat from-csv `
  "data/Screenshot.csv" `
  output/chat `
  --script-col "Script" `
  --id-col "#" `
  --qa-col "ID QA" `
  --participant-col "participant" `
  --filename-col "File" `
  --country-col "country" `
  --application-col "application used" `
  --os-col "OS" `
  --device-col "device info" `
  --creation-col "Creation Date (YYYY.MM.DD)" `
  --workers 8 `
  --done-csv "data/done-data/chat.csv"
```

---

**Notes:**
- `` ` `` là ký tự line continuation của PowerShell
- `--script-col "Script"` — cột chứa nội dung hội thoại
- `--id-col "Unnamed: 0"` — cột ID dùng làm seed (deterministic device/theme)
- `--filename-col "File"` — cột chứa tên file output (thay vì auto `{id}_{qa}.png`)
- `--country-col "country"` — cột country cho localisation (EN/FR/IT/DE/ES)
- `--application-col "application used"` — cột app (iMessage/WhatsApp/Messenger/Telegram)
- `--os-col "OS"` — cột OS (iOS 17/Android 13/...)
- `--device-col "device info"` — cột device (iPhone 15 Pro Max/Samsung Galaxy S23/...)
- `--creation-col "Creation Date (YYYY.MM.DD)"` — cột ngày tạo, dùng làm ngày hiển thị timestamp chat; giờ/phút vẫn random theo ID
- `--participant-col "participant"` — cột participant dùng cho done-csv
- `--done-csv` — append danh sách index đã chạy vào file CSV (format: `index,participant,filename`)
- Log tự động ghi vào `logs/<filename>.log`
- Output vào subfolder theo timestamp: `output/chat/YYYY-MM-DD_HH-MM-SS/`
