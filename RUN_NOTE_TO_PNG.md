# Run `note to-png` (macOS / Windows)

## 1. macOS / Linux (zsh/bash)

```bash
# Từ root project
poetry run tc note to-png "data/Note Design - Sheet1 (1).csv" output/note-png/
```

```bash
# Có options
poetry run tc note to-png "data/Note Design - Sheet1 (1).csv" output/note-png/ \
  --template-col "Template" \
  --device-col "Device" \
  --os-col "OS" \
  --spec-col "spec" \
  --filename-col "filename" \
  --workers 8 \
  --limit 100
```

## 2. Windows PowerShell

```powershell
# Từ root project
poetry run tc note to-png "data/Note Design - Sheet1 (1).csv" "output/note-png/"
```

```powershell
# Có options
poetry run tc note to-png "data/Note Design - Sheet1 (1).csv" "output/note-png/" `
  --template-col "Template" `
  --device-col "Device" `
  --os-col "OS" `
  --spec-col "spec" `
  --filename-col "filename" `
  --workers 8 `
  --limit 100
```

## 3. Windows CMD

```cmd
:: Từ root project
poetry run tc note to-png "data/Note Design - Sheet1 (1).csv" "output/note-png/"
```

```cmd
:: Có options
poetry run tc note to-png "data/Note Design - Sheet1 (1).csv" "output/note-png/" ^
  --template-col "Template" ^
  --device-col "Device" ^
  --os-col "OS" ^
  --spec-col "spec" ^
  --filename-col "filename" ^
  --workers 8 ^
  --limit 100
```

## 4. Ghi chú nhanh

- Cần chạy tại thư mục root của project.
- Nếu chưa cài browser cho Playwright:

```bash
poetry run playwright install chromium
```
