# TODO

## [PENDING] Metadata updater — bulk update file timestamps & headers

### Bối cảnh
Sau khi convert xong hàng loạt file `.txt` / `.eml`, cần cập nhật metadata của chúng
(timestamp, email headers) để trông tự nhiên / đồng nhất hơn.

### Cần làm

Tạo module `src/text_converter/metadata.py` với 2 chức năng:

**1. Sửa filesystem timestamp** (áp dụng cho cả `.txt` lẫn `.eml`)
- Dùng `os.utime()` để set `mtime` và `atime`
- Input: `datetime` object

**2. Sửa email headers** (chỉ `.eml`)
- Dùng stdlib `email` — không cần cài thêm gì
- Các header cần sửa: `Date`, `X-Mailer`, `User-Agent`
- Input: string theo chuẩn RFC 2822, ví dụ `"Wed, 24 Jul 2024 04:39:44 +0000"`

### API mong muốn

```python
from text_converter.metadata import batch_update
from pathlib import Path
from datetime import datetime

batch_update(
    folder=Path("./output"),
    dt=datetime(2024, 7, 24, 4, 39, 44),   # filesystem timestamp
    eml_date="Wed, 24 Jul 2024 04:39:44 +0000",  # Date header trong .eml
    x_mailer="Apple Mail",
)
```

### CLI command (nếu muốn expose ra `tc`)

```
tc metadata update ./output --date "2024-07-24 04:39:44" --mailer "Apple Mail"
```

### Lưu ý kỹ thuật
- `ctime` / `birthtime` trên macOS **không sửa được bằng Python** — chỉ `mtime` và `atime`
- Không cần thư viện ngoài, stdlib đủ dùng (`os`, `email`, `pathlib`, `datetime`)
- `.txt` không có embedded metadata — chỉ sửa được filesystem timestamp

### File cần đụng tới
- Tạo mới: `src/text_converter/metadata.py`
- Sửa: `src/text_converter/cli.py` — thêm `metadata_app` nếu muốn CLI
