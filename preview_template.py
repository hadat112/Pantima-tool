"""
Quick preview server for chat templates.

Usage:
    python preview_template.py [template_name]

Examples:
    python preview_template.py ios_imessage
    python preview_template.py android_whatsapp
    python preview_template.py telegram
    python preview_template.py messenger
    python preview_template.py luminati
    python preview_template.py ios_whatsapp

Opens browser at http://localhost:8899 with live-reload (just refresh after editing).
"""

import http.server
import sys
import webbrowser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "src" / "text_converter" / "templates"

# Sample data matching the real template variables
SAMPLE_DATA = {
    "contact_name": "Sarah Johnson",
    "is_group": True,
    "status_time": "10:30",
    "message_time": "Today, 10:28 AM",
    "dark_mode": False,
    "messages": [
        {"role": "recv", "text": "Hey everyone! Are we still meeting for lunch today?", "display_name": "Sarah Johnson", "color": "#E91E63"},
        {"role": "recv", "text": "Yes! I was thinking we could try that new Thai place on 5th street 🍜", "display_name": "Mike Chen", "color": "#9C27B0"},
        {"role": "sent", "text": "Sounds great! What time works for you guys?", "display_name": "You", "color": "#1976D2"},
        {"role": "recv", "text": "How about 12:30? I have a meeting until noon", "display_name": "Sarah Johnson", "color": "#E91E63"},
        {"role": "sent", "text": "Perfect, 12:30 works for me 👍", "display_name": "You", "color": "#1976D2"},
        {"role": "recv", "text": "Same here. Should I make a reservation?", "display_name": "Mike Chen", "color": "#9C27B0"},
        {"role": "recv", "text": "That would be great! Book for 4 people just in case", "display_name": "Sarah Johnson", "color": "#E91E63"},
        {"role": "sent", "text": "See you all there! 🎉", "display_name": "You", "color": "#1976D2"},
    ],
}

SAMPLE_DATA_DARK = {**SAMPLE_DATA, "dark_mode": True}

SAMPLE_DATA_1ON1 = {
    "contact_name": "Alex",
    "is_group": False,
    "status_time": "14:05",
    "message_time": "Today, 2:03 PM",
    "dark_mode": False,
    "messages": [
        {"role": "recv", "text": "Did you finish the report?", "display_name": "Alex", "color": "#E91E63"},
        {"role": "sent", "text": "Almost done, just reviewing the numbers", "display_name": "You", "color": "#1976D2"},
        {"role": "recv", "text": "Great, send it over when you're ready", "display_name": "Alex", "color": "#E91E63"},
        {"role": "sent", "text": "Will do! Should be about 30 minutes", "display_name": "You", "color": "#1976D2"},
    ],
}


def render_template(template_name: str, data: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    template = env.get_template(f"{template_name}.html")
    return template.render(**data)


def build_preview_page(template_name: str) -> str:
    """Build a page showing group, 1-on-1, and dark mode variants."""
    group_html = render_template(template_name, SAMPLE_DATA)
    dark_html = render_template(template_name, SAMPLE_DATA_DARK)
    solo_html = render_template(template_name, SAMPLE_DATA_1ON1)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Preview: {template_name}</title>
<style>
  body {{ background: #e0e0e0; font-family: -apple-system, sans-serif; margin: 0; padding: 20px; }}
  h1 {{ text-align: center; color: #333; }}
  .variants {{ display: flex; gap: 24px; justify-content: center; flex-wrap: wrap; padding: 20px; }}
  .variant {{ text-align: center; }}
  .variant h3 {{ margin-bottom: 8px; color: #555; }}
  .frame {{ border: 2px solid #999; border-radius: 12px; overflow: hidden; background: #fff; }}
  iframe {{ border: none; }}
</style>
</head>
<body>
<h1>{template_name}.html</h1>
<p style="text-align:center;color:#666">Edit the template, then refresh this page to see changes</p>
<div class="variants">
  <div class="variant">
    <h3>Group Chat (Light)</h3>
    <div class="frame">
      <iframe srcdoc='{_escape_srcdoc(group_html)}' width="430" height="932"></iframe>
    </div>
  </div>
  <div class="variant">
    <h3>1-on-1 Chat (Light)</h3>
    <div class="frame">
      <iframe srcdoc='{_escape_srcdoc(solo_html)}' width="430" height="932"></iframe>
    </div>
  </div>
  <div class="variant">
    <h3>Group Chat (Dark)</h3>
    <div class="frame">
      <iframe srcdoc='{_escape_srcdoc(dark_html)}' width="430" height="932"></iframe>
    </div>
  </div>
</div>
</body>
</html>"""


def _escape_srcdoc(html: str) -> str:
    return html.replace("&", "&amp;").replace("'", "&#39;").replace('"', "&quot;")


def main():
    template_name = sys.argv[1] if len(sys.argv) > 1 else "ios_imessage"

    # Verify template exists
    template_file = TEMPLATES_DIR / f"{template_name}.html"
    if not template_file.exists():
        available = [f.stem for f in TEMPLATES_DIR.glob("*.html")]
        print(f"Template '{template_name}' not found. Available: {', '.join(available)}")
        sys.exit(1)

    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8899

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            # Re-render on every request so edits are picked up
            html = build_preview_page(template_name)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(html.encode())

        def log_message(self, format, *args):
            pass  # quiet

    print(f"Serving preview of '{template_name}' at http://localhost:{port}")
    print("Edit the template file, then refresh browser to see changes.")
    print("Press Ctrl+C to stop.\n")

    webbrowser.open(f"http://localhost:{port}")
    server = http.server.HTTPServer(("localhost", port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
