"""
METADATA & EXIF SPOOFING
-------------------------
Nhiệm vụ: Nhúng thông tin thiết bị vào ảnh đã chụp.
Công cụ: pip install piexif Pillow
"""

import piexif
from PIL import Image
import os

def update_metadata(image_path, device_name, os_version, creation_time):
    """
    Hàm fake EXIF cho ảnh chụp màn hình.
    :param image_path: Đường dẫn ảnh
    :param device_name: VD: 'iPhone 15 Pro Max'
    :param os_version: VD: 'iOS 17.2'
    :param creation_time: Thời gian chụp (YYYY:MM:DD HH:MM:SS)
    """
    print(f"Bơm metadata {device_name} vào {image_path}...")
    # 1. Load ảnh bằng Pillow
    # 2. Xây dựng dict EXIF (piexif)
    # 3. Ghi dữ liệu: Make, Model, Software, DateTimeOriginal
    # 4. Save ảnh với EXIF mới
    pass

# Ví dụ chạy:
# update_metadata("output/chat_0001.jpg", "iPhone 15 Pro Max", "iOS 17.2", "2024:03:12 09:41:00")
