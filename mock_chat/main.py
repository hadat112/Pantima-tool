"""
MOCK CHAT SCREENSHOT GENERATOR
------------------------------
Hướng dẫn sử dụng:
1. Cài đặt: pip install playwright jinja2 pandas
2. Chạy: python main.py
"""

import asyncio
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
import os

# --- CẤU HÌNH THIẾT BỊ (RANDOM LIST) ---
DEVICES = [
    {"name": "iPhone 15 Pro Max", "width": 430, "height": 932, "scale": 3, "os": "iOS 17"},
    {"name": "Samsung Galaxy S23", "width": 360, "height": 800, "scale": 3, "os": "Android 13"},
    {"name": "Google Pixel 7", "width": 412, "height": 915, "scale": 2.6, "os": "Android 13"},
]

# --- HÀM CHÍNH ---
async def generate_chat_screenshots():
    # 1. Đọc dữ liệu (1000 đoạn hội thoại)
    # 2. Khởi tạo Playwright
    # 3. Chạy vòng lặp song song (Parallelism)
    # 4. Render HTML -> Screenshot -> Lưu file
    print("Mời Dev hoàn thiện logic tại đây...")

if __name__ == "__main__":
    # Đảm bảo thư mục output tồn tại
    os.makedirs("output", exist_ok=True)
    asyncio.run(generate_chat_screenshots())
