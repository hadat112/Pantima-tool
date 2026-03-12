# TODO: Hệ thống Tự động hóa Chụp ảnh Chat (1000+ Conversions)

## 🎯 Mục tiêu
Chuyển đổi 1000 đoạn hội thoại (text) thành 1000 ảnh chụp màn hình giao diện di động (PNG) với tốc độ cao (< 2 phút cho toàn bộ).

---

## 🏗️ Kiến trúc đề xuất (High-Level)
1.  **Dữ liệu:** File CSV hoặc JSON chứa danh sách hội thoại.
2.  **Engine:** Python + `Playwright` (Headless Browser) + `Jinja2` (HTML Template).
3.  **Quy trình:** 
    - Đọc dữ liệu -> Render vào HTML -> Dùng trình duyệt ẩn mở HTML -> Chụp ảnh màn hình (Screenshot) -> Lưu file.

---

## 📝 Quy trình thực hiện (Dành cho Dev)

### 1. Chuẩn bị Môi trường
- Cài đặt thư viện: `pip install playwright jinja2 pandas`
- Cài đặt browser: `playwright install chromium`

### 2. Phát triển Template (HTML/CSS)
- Tạo file `chat_template.html` giả lập iMessage hoặc Messenger.
- Sử dụng CSS Flexbox để xử lý các bóng chat trái/phải.
- **Quan trọng:** Phải có phần "Status Bar" giả (Pin, Sóng, Giờ) ở trên cùng để ảnh trông giống thật 100%.

### 3. Script Tự động hóa (Python)
- Sử dụng `playwright.async_api` để tận dụng tốc độ của xử lý bất đồng bộ.
- Thiết lập Viewport chuẩn: `width=390, height=844` (iPhone 14) hoặc tùy chọn.
- Sử dụng `device_scale_factor=3` để ảnh đạt độ nét Retina (không bị mờ).

---

## 🎲 RANDOMIZATION: Đa dạng hóa bộ dữ liệu (1000 ảnh)

Để tránh việc 1000 ảnh trông giống hệt nhau, cần áp dụng logic ngẫu nhiên:

1.  **Random Thiết bị (Device List):**
    - [ ] `iPhone 15 Pro Max` (430x932, iOS 17)
    - [ ] `Samsung Galaxy S23` (360x800, Android 13)
    - [ ] `Google Pixel 7` (412x915, Android 13)
    - [ ] `iPhone SE` (375x667, iOS 15)
2.  **Random Giao diện (UI Themes):**
    - [ ] **iMessage:** Xanh dương/Xám.
    - [ ] **WhatsApp:** Xanh lá/Trắng + Hình nền Doodle.
    - [ ] **Dark Mode:** Ngẫu nhiên 30% ảnh sử dụng giao diện tối.
3.  **Random Thời gian (Dynamic Timestamps):**
    - [ ] Không dùng cố định "9:41 AM". Hãy lấy thời gian ngẫu nhiên trong khoảng 1-2 năm gần đây.
    - [ ] Đảm bảo Giờ trên Status Bar và Giờ trong tin nhắn phải khớp nhau.

---

## 🛡️ NÂNG CAO: Fake Metadata (EXIF) để tránh bị phát hiện

Để ảnh trông như chụp từ điện thoại thật (tránh AI Detection/Manual QA), cần thực hiện bước chèn Metadata:

1.  **Công cụ:** Sử dụng thư viện `piexif` hoặc `exiftool` trong Python.
2.  **Cấu trúc EXIF cần chèn:**
    - `Make`: "Apple" (cho iOS) hoặc "Samsung/Google" (cho Android).
    - `Model`: "iPhone 14 Pro" hoặc "Pixel 7".
    - `Software`: Phiên bản hệ điều hành (VD: "iOS 17.2").
    - `DateTimeOriginal`: **Bắt buộc** phải trùng khớp với thời gian hiển thị trong bong bóng chat.
3.  **Xử lý màu sắc (Color Profile):** Chèn Profile "Display P3" vào ảnh để màu sắc hiển thị rực rỡ đúng chuẩn màn hình điện thoại cao cấp.
4.  **Định dạng file:** Chuyển đổi từ PNG sang JPG (Chất lượng 100%) để việc lưu trữ EXIF được tự nhiên nhất.

---

## 💡 CÁC LƯU Ý QUAN TRỌNG (NOTES - MUST READ)

> **Dành cho Manager & Developer:**

1.  **Độ sắc nét (Resolution):** Tuyệt đối không chụp ảnh ở độ phân giải màn hình máy tính thông thường (scale = 1). Phải set `device_scale_factor: 3` trong code Playwright. Nếu không ảnh sẽ bị mờ và trông rất "giả".
2.  **Lỗi Font & Emoji:** Đây là lỗi phổ biến nhất. Máy tính chạy script (Server/Laptop) phải được cài font hỗ trợ Emoji (như `Apple Color Emoji` hoặc `Noto Color Emoji`). Nếu không, các icon trong chat sẽ biến thành ô vuông `[ ]`.
3.  **Xử lý Tin nhắn dài:** 1000 đoạn chat sẽ có những đoạn rất dài. 
    - *Giải pháp:* Nếu chat vượt quá chiều cao màn hình (844px), có thể chọn `full_page=True` (ảnh sẽ dài ra) hoặc dùng CSS `overflow: hidden` để cắt bớt (nếu chỉ cần lấy phần đầu).
4.  **Tốc độ (Parallelism):** Để đạt tốc độ 1000 ảnh / 1-2 phút, không được chạy vòng lặp `for` bình thường. Phải dùng `asyncio.gather` để mở khoảng 5-10 "tab" trình duyệt ảo cùng lúc.
5.  **Thời gian hệ thống:** Trong ảnh chat thường có giờ (9:41 AM). Hãy hard-code giờ này trong HTML hoặc lấy giờ ngẫu nhiên để trông tự nhiên, tránh việc 1000 bức ảnh đều có cùng một phút giây.
6.  **Tên File:** Nên đặt tên file theo ID hoặc tên người gửi để dễ quản lý (VD: `0001_NguyenVanA.png`).

---

## 🛠️ Cấu trúc thư mục triển khai (Mới)
Dự án được tổ chức tại thư mục `/mock_chat`:

```text
mock_chat/
├── main.py              # Script chạy chính (Playwright logic)
├── metadata_editor.py   # Script xử lý EXIF/Metadata sau khi chụp
├── templates/           # Chứa các mẫu giao diện (HTML/CSS)
│   ├── ios_imessage.html
│   └── android_whatsapp.html
├── data/                # Chứa file CSV đầu vào (1000 hội thoại)
└── output/              # Nơi xuất 1000 ảnh PNG/JPG kết quả
```
