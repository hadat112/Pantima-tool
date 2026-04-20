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

- Template HTML mới đặt theo cấu trúc:
  - `src/text_converter/templates/note_variants/ios/0001/template.html`
  - `src/text_converter/templates/note_variants/android/0001/template.html`
- Mỗi bản ghi sẽ lấy template theo thứ tự folder số (`0001`, `0002`, ...) và xoay vòng theo từng platform.
- Template cũ (`notes_ios.html`, `notes_ios26.html`, `notes_android.html`) vẫn được giữ nguyên để fallback.
