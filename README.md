# 📝 Pantima Note Converter Tool

Công cụ chuyển đổi nội dung từ tệp CSV thành hình ảnh giao diện ứng dụng Ghi chú (Note) chuyên nghiệp trên iOS và Android.

---

## 🚀 Hướng dẫn cài đặt cho người mới

Công cụ này yêu cầu **Python 3.13** và **Poetry**. Chọn hướng dẫn phù hợp với hệ điều hành của bạn:

### 🔹 Trên Windows
1. Mở **PowerShell** trong thư mục dự án.
2. Chạy lệnh cài đặt tự động:
   ```powershell
   powershell -ExecutionPolicy Bypass -File setup.ps1
   ```
3. **Cập nhật PATH**: Nếu gõ `poetry` báo lỗi, hãy chạy lệnh sau:
   ```powershell
   $env:PATH = "$env:APPDATA\Python\Scripts;$env:PATH"
   ```

### 🔹 Trên macOS / Linux (Ubuntu/Debian)
1. Mở **Terminal** trong thư mục dự án.
2. Cấp quyền và chạy tệp cài đặt:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
3. **Cập nhật PATH**: Sau khi chạy xong, hãy khởi động lại Terminal hoặc chạy:
   ```bash
   source ~/.zshrc  # Nếu dùng Zsh (macOS mặc định)
   # hoặc
   source ~/.bashrc # Nếu dùng Bash
   ```

---

## 🛠 Cách sử dụng công cụ

### 1. Chuyển đổi Ghi chú sang ảnh PNG (To-PNG)
Sử dụng lệnh `tc note to-png` để biến các dòng trong CSV thành ảnh chụp màn hình điện thoại.

**Cú pháp cơ bản:**
```bash
# Windows
poetry run tc note to-png "đường-dẫn-tệp.csv" "thư-mục-đầu-ra" --template-col "Tên-Cột-Nội-Dung"

# macOS / Linux
poetry run tc note to-png "đường-dẫn-tệp.csv" "thư-mục-đầu-ra" --template-col "Tên-Cột-Nội-Dung"
```

**Ví dụ thực tế:**
```bash
poetry run tc note to-png "data\Note Design - Sheet1 (1).csv" "output\png" --template-col "Template" -n 5
```
*Tham số `-n 5` có nghĩa là chỉ chạy thử nghiệm 5 dòng đầu tiên.*

### 2. Các tùy chọn nâng cao
- `--template-col`: Tên cột chứa nội dung ghi chú (Mặc định: `Template`).
- `--device-col`: Cột chứa tên thiết bị (Ví dụ: `iPhone 13`, `iPhone SE`).
- `--os-col`: Cột chứa phiên bản hệ điều hành (Ghi `iOS 26` để dùng giao diện mới).
- `--spec-col`: Cột chứa độ phân giải màn hình (Ví dụ: `390x844`).

---

## ✨ Các tính năng nổi bật

1.  **Giao diện linh hoạt**: Tự động chuyển đổi giữa giao diện iOS truyền thống và giao diện **iOS 26** hiện đại.
2.  **Chế độ Tối (Dark Mode)**: Tự động áp dụng Dark Mode ngẫu nhiên hoặc theo dữ liệu.
3.  **Bàn phím ngẫu nhiên**: Tự động hiển thị bàn phím iOS giả lập một cách ngẫu nhiên (xác suất 50%) giúp ảnh chân thực hơn.
4.  **Tự động cuộn**: Vùng nội dung sẽ tự động hỗ trợ cuộn khi bàn phím hiện lên.

---

## 📂 Cấu trúc thư mục quan trọng

- `src/text_converter/templates/`: Chứa các file giao diện chính (`notes_ios.html`, `notes_ios26.html`, `keyboard_ios.html`).
- `data/`: Nơi chứa các tệp dữ liệu CSV mẫu.
- `output/png/`: Thư mục mặc định chứa các ảnh kết quả.

---

## ❓ Xử lý sự cố thường gặp

**Lỗi: `poetry : The term 'poetry' is not recognized...`**
- Hãy chạy lệnh cập nhật PATH theo hướng dẫn cài đặt ở trên, sau đó mở lại Terminal.

**Lỗi: `ValueError: Không tìm thấy cột '...' trong CSV`**
- Kiểm tra lại file CSV, đảm bảo tên cột truyền vào sau `--template-col` phải khớp hoàn toàn (Lưu ý: công cụ đã tự động xóa khoảng trắng ở đầu/cuối tên cột).

---
*Chúc bạn có những bức ảnh ghi chú thật đẹp!*
