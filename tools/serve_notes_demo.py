#!/usr/bin/env python3
from __future__ import annotations

import re
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import pandas as pd
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "src" / "text_converter" / "templates"
TEMPLATE_VARIANTS_DIR = TEMPLATES_DIR / "note_variants"
CSV_PATH = ROOT / "data" / "Note Design - Sheet1 (1).csv"
HOST = "127.0.0.1"
PORT = 8765

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)


DEVICE_PRESETS = {
    "iphone 13": (390, 844),
    "iphone xs": (375, 812),
    "iphone 15 promax": (430, 932),
    "iphone 15 pro max": (430, 932),
    "samsung galaxy s25": (412, 915),
    "samsung galaxy s25+": (450, 1000),
    "samsung galaxy s25 ultra": (480, 1067),
    "samsung galaxy a56 5g": (412, 892),
    "samsung galaxy a36 5g": (412, 914),
    "google pixel 9": (412, 915),
    "google pixel 9a": (412, 915),
    "google pixel 9 pro": (412, 915),
    "google pixel 9 pro xl": (450, 1000),
    "oneplus 13": (450, 1000),
    "xiaomi 15 ultra": (420, 920),
    "oppo find x8 pro": (450, 1000),
    "oppo reno13 pro 5g": (420, 930),
    "vivo x200 pro": (420, 933),
    "vivo v50": (412, 915),
    "iphone se": (375, 667),
}


def _parse_resolution(text: str) -> tuple[int, int] | None:
    raw = (text or "").strip().lower()
    if not raw:
        return None
    m = re.search(r"(\d{3,5})\s*[x×*]\s*(\d{3,5})", raw)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)))


def _resolve_viewport(device: str, os_name: str) -> tuple[int, int]:
    os_res = _parse_resolution(os_name)
    if os_res:
        return os_res
    return DEVICE_PRESETS.get(device.strip().lower(), (430, 932))


def load_device_os_rows() -> list[tuple[str, str]]:
    if not CSV_PATH.exists():
        return []
    df = pd.read_csv(CSV_PATH)
    df.columns = [c.strip() for c in df.columns]
    if "Device" not in df.columns or "OS" not in df.columns:
        return []
    sub = df[["Device", "OS"]].fillna("").astype(str)
    sub = sub[(sub["Device"].str.strip() != "") | (sub["OS"].str.strip() != "")]
    rows = []
    seen = set()
    for _, r in sub.iterrows():
        d = r["Device"].strip()
        o = r["OS"].strip()
        key = (d, o)
        if key in seen:
            continue
        seen.add(key)
        rows.append(key)
    se_key = ("iPhone SE", "iOS 17")
    if se_key not in seen:
        rows.append(se_key)
    return rows


DEVICE_OS_ROWS = load_device_os_rows()


def detect_platform(device_name: str, os_name: str) -> str:
    device_l = (device_name or "").strip().lower()
    os_l = (os_name or "").strip().lower()
    ios_hints = ("ios", "iphone", "ipad")
    android_hints = ("android", "samsung", "pixel", "oneplus", "xiaomi", "oppo", "vivo")
    if any(h in os_l for h in ios_hints) or any(h in device_l for h in ios_hints):
        return "ios"
    if any(h in os_l for h in android_hints) or any(h in device_l for h in android_hints):
        return "android"
    return "ios"


def is_ios26(os_name: str) -> bool:
    return bool(re.search(r"\bios\s*26(?:\D|$)", (os_name or "").strip().lower()))


def list_variant_templates() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    if not TEMPLATE_VARIANTS_DIR.exists():
        return items

    for platform_dir in sorted([p for p in TEMPLATE_VARIANTS_DIR.iterdir() if p.is_dir()], key=lambda p: p.name):
        platform = platform_dir.name
        for slot_dir in sorted([p for p in platform_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
            if not re.fullmatch(r"\d+", slot_dir.name):
                continue
            preferred = slot_dir / "template.html"
            chosen: Path | None = preferred if preferred.exists() else None
            if chosen is None:
                candidates = sorted(slot_dir.glob("*.html"))
                if candidates:
                    chosen = candidates[0]
            if chosen is None:
                continue
            rel = str(chosen.relative_to(TEMPLATES_DIR)).replace("\\", "/")
            items.append({
                "platform": platform,
                "slot": slot_dir.name,
                "template": rel,
            })
    return items


def _default_preview_target(platform: str) -> tuple[str, str]:
    if platform == "android":
        return ("Samsung Galaxy S25", "Android 15")
    return ("iPhone 15 Pro Max", "iOS 26")


def render_screen(theme: str, device: str, os_name: str, template_name: str | None = None) -> str:
    dark_mode = theme == "dark"
    device_name = device
    platform = detect_platform(device_name=device_name, os_name=os_name)
    if not template_name:
        if platform == "ios" and is_ios26(os_name):
            template_name = "notes_ios26.html"
        else:
            template_name = "notes_ios.html" if platform == "ios" else "notes_android.html"
    status_time = "7:05" if "se" in device.lower() else "9:41"
    note_text = (
        "SE screen check\n- Status bar layout\n- Header spacing\n- Footer alignment"
        if "se" in device.lower()
        else "Meeting Notes\n- Finalize Q2 roadmap\n- Review design handoff\n- Send follow-up by 5 PM"
    )

    html = env.get_template(template_name).render(
        note_text=note_text,
        dark_mode=dark_mode,
        battery=47 if dark_mode else 83,
        status_time=status_time,
        created_datetime_display="22 November 2025 at 11:16",
        has_ios26_undo_icon=(TEMPLATES_DIR / "assets" / "notes_ios" / "nav_undo_light.svg").exists()
        and (TEMPLATES_DIR / "assets" / "notes_ios" / "nav_undo_dark.svg").exists(),
        has_ios26_share_icon=(TEMPLATES_DIR / "assets" / "notes_ios" / "nav_share_light.svg").exists()
        and (TEMPLATES_DIR / "assets" / "notes_ios" / "nav_share_dark.svg").exists(),
        device_name=device_name,
        os_name=os_name,
        carrier="T-Mobile" if "se" in device.lower() else "Verizon",
        signal_level=4,
        wifi_level=3,
        wifi_signal=4,
        network_type="5G",
    )

    width, height = _resolve_viewport(device=device, os_name=os_name)
    title = f"{platform.upper()} {'Dark' if dark_mode else 'Light'} · {device_name}"
    escaped = (
        html.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <style>
      body {{
        margin: 0;
        background: #111;
        color: #fff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }}
      .shell {{
        padding: 24px;
      }}
      .title {{
        margin: 0 0 16px;
        font-size: 14px;
        opacity: 0.85;
      }}
      iframe {{
        border: 0;
        border-radius: 24px;
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.45);
        background: #000;
      }}
    </style>
  </head>
  <body>
    <div class="shell">
      <p class="title">{title} ({width}x{height})</p>
      <iframe srcdoc="{escaped}" width="{width}" height="{height}"></iframe>
    </div>
  </body>
</html>
"""


def render_index() -> str:
    cards: list[str] = []
    for device, os_name in DEVICE_OS_ROWS:
        query = urlencode({"theme": "dark", "device": device, "os": os_name})
        cards.append(
            f'<a class="card" href="/preview?{query}"><h3>{escape(device)}'
            f'</h3><p>{escape(os_name or "(empty OS)")}</p></a>'
        )
    card_html = "".join(cards)

    template_cards: list[str] = []
    for item in list_variant_templates():
        device, os_name = _default_preview_target(item["platform"])
        q_light = urlencode({
            "theme": "light",
            "device": device,
            "os": os_name,
            "template": item["template"],
        })
        q_dark = urlencode({
            "theme": "dark",
            "device": device,
            "os": os_name,
            "template": item["template"],
        })
        template_cards.append(
            f'<div class="card template-card">'
            f'<h3>{escape(item["platform"].upper())} · #{escape(item["slot"])}</h3>'
            f'<p>{escape(item["template"])}</p>'
            f'<p><a href="/preview?{q_light}">Light</a> · <a href="/preview?{q_dark}">Dark</a></p>'
            f"</div>"
        )
    template_card_html = "".join(template_cards)

    html = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Notes Demo (Live)</title>
    <style>
      body {
        margin: 0;
        padding: 24px;
        background: #0d0f14;
        color: #eef2ff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      h1 {
        margin: 0 0 8px;
        font-size: 22px;
      }
      h2 {
        margin: 20px 0 10px;
        font-size: 16px;
        opacity: 0.95;
      }
      p {
        margin: 0 0 16px;
        opacity: 0.8;
        font-size: 14px;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 12px;
        max-width: 960px;
      }
      .card {
        display: block;
        padding: 14px 16px;
        border: 1px solid #2a3042;
        border-radius: 14px;
        background: #151b2a;
        color: inherit;
        text-decoration: none;
      }
      .card:hover {
        border-color: #5b6b95;
        background: #192238;
      }
      .card h3 {
        margin: 0 0 8px;
        font-size: 15px;
      }
      .card p {
        margin: 0;
        opacity: 0.8;
        font-size: 13px;
      }
      .template-card p + p {
        margin-top: 10px;
      }
      .template-card a {
        color: #9ec1ff;
        text-decoration: none;
      }
      .template-card a:hover {
        text-decoration: underline;
      }
    </style>
  </head>
  <body>
    <h1>Notes Demo (Live Reload)</h1>
    <p>Preview theo từng template trong note_variants và preview theo Device/OS từ CSV.</p>
    <h2>By Template</h2>
    <div class="grid">
      __TEMPLATE_CARDS__
    </div>
    <h2>By Device/OS</h2>
    <div class="grid">
      __CARDS__
    </div>
  </body>
</html>
"""
    return html.replace("__CARDS__", card_html).replace("__TEMPLATE_CARDS__", template_card_html)


class Handler(BaseHTTPRequestHandler):
    def _send_html(self, content: str, code: int = 200) -> None:
        body = content.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        legacy_routes = {
            "/ios-light-15promax.html": ("light", "iPhone 15 Pro Max", "iOS 26"),
            "/ios-dark-15promax.html": ("dark", "iPhone 15 Pro Max", "iOS 26"),
            "/ios-dark-se.html": ("dark", "iPhone SE", "iOS 17"),
            "/ios26-light-15promax.html": ("light", "iPhone 15 Pro Max", "iOS 26"),
            "/ios26-dark-15promax.html": ("dark", "iPhone 15 Pro Max", "iOS 26"),
        }
        if parsed.path == "/":
            self._send_html(render_index())
            return
        if parsed.path in legacy_routes:
            theme, device, os_name = legacy_routes[parsed.path]
            self._send_html(render_screen(theme=theme, device=device, os_name=os_name))
            return
        if parsed.path == "/preview":
            q = parse_qs(parsed.query)
            theme = q.get("theme", ["light"])[0]
            device = q.get("device", ["iPhone 15 Pro Max"])[0]
            os_name = q.get("os", ["iOS 26"])[0]
            template_name = q.get("template", [""])[0].strip()
            if theme not in {"light", "dark"}:
                theme = "light"
            if template_name:
                candidate = (TEMPLATES_DIR / template_name).resolve()
                # Only allow templates inside configured templates root.
                if TEMPLATES_DIR.resolve() not in candidate.parents or not candidate.exists():
                    self._send_html("<h1>Invalid template path</h1>", code=400)
                    return
            self._send_html(
                render_screen(
                    theme=theme,
                    device=device,
                    os_name=os_name,
                    template_name=template_name or None,
                )
            )
            return
        self._send_html("<h1>404</h1>", code=404)


if __name__ == "__main__":
    httpd = HTTPServer((HOST, PORT), Handler)
    print(f"Serving live Notes demo on http://{HOST}:{PORT}")
    httpd.serve_forever()
