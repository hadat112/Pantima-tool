"""
Core logic for chat screenshot generation.
Called by `tc chat from-csv` CLI.
"""

from __future__ import annotations

import asyncio
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

# Templates bundled inside the package
TEMPLATES_DIR = Path(__file__).parent / "templates"

# ── Constants ────────────────────────────────────────────────────────────────

DEVICES = [
    {"name": "iPhone 15 Pro Max", "width": 430, "height": 932, "scale": 3,
     "os": "iOS 17",     "application": "iMessage",  "template": "ios_imessage.html"},
    {"name": "iPhone SE",         "width": 375, "height": 667, "scale": 2,
     "os": "iOS 15",     "application": "iMessage",  "template": "ios_imessage.html"},
    {"name": "Samsung Galaxy S23","width": 360, "height": 800, "scale": 3,
     "os": "Android 13", "application": "WhatsApp",  "template": "android_whatsapp.html"},
    {"name": "Google Pixel 7",    "width": 412, "height": 915, "scale": 3,
     "os": "Android 13", "application": "WhatsApp",  "template": "android_whatsapp.html"},
    {"name": "iPhone 15 Pro Max", "width": 430, "height": 932, "scale": 3,
     "os": "iOS 17",     "application": "WhatsApp",  "template": "ios_whatsapp.html"},
    {"name": "iPhone 14",         "width": 390, "height": 844, "scale": 3,
     "os": "iOS 16",     "application": "Messenger", "template": "messenger.html"},
    # {"name": "Samsung Galaxy S24","width": 360, "height": 780, "scale": 3,
    #  "os": "Android 14", "application": "Messenger", "template": "android_messenger.html"},
    {"name": "iPhone 13",         "width": 390, "height": 844, "scale": 3,
     "os": "iOS 15",     "application": "Telegram",  "template": "telegram.html"},
    {"name": "iPhone 15",         "width": 393, "height": 852, "scale": 3,
     "os": "iOS 17",     "application": "iMessage",  "template": "ios_imessage.html"},
]


def _find_device(application: str, os_name: str, device_name: str, seed: int) -> dict:
    """Look up a DEVICE entry matching the CSV columns. Fall back to random."""
    candidates = [
        d for d in DEVICES
        if d["application"] == application and d["os"] == os_name and d["name"] == device_name
    ]
    if candidates:
        return candidates[0]
    # Partial match: application + device name
    candidates = [
        d for d in DEVICES
        if d["application"] == application and d["name"] == device_name
    ]
    if candidates:
        return candidates[0]
    # Partial match: application only
    candidates = [d for d in DEVICES if d["application"] == application]
    if candidates:
        return random.Random(seed).choice(candidates)
    return random.Random(seed).choice(DEVICES)

BATTERY_LEVELS = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]

SPEAKER_COLORS = ["#E91E63", "#9C27B0", "#1976D2", "#00897B", "#E65100", "#5D4037"]

# Country → language code mapping
COUNTRY_LANG = {
    "us": "en", "uk": "en", "au": "en", "ca": "en", "nz": "en", "gb": "en",
    "fr": "fr", "be": "fr", "ch": "fr",
    "it": "it",
    "de": "de", "at": "de",
    "es": "es", "mx": "es", "ar": "es", "co": "es", "cl": "es", "pe": "es",
}

# Localised UI strings per language
LANG_STRINGS = {
    "en": {
        "today": "Today", "yesterday": "Yesterday", "am": "AM", "pm": "PM",
        "months": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
        "weekdays": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
    },
    "fr": {
        "today": "Aujourd'hui", "yesterday": "Hier", "am": "AM", "pm": "PM",
        "months": ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."],
        "weekdays": ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"],
    },
    "it": {
        "today": "Oggi", "yesterday": "Ieri", "am": "AM", "pm": "PM",
        "months": ["gen","feb","mar","apr","mag","giu","lug","ago","set","ott","nov","dic"],
        "weekdays": ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"],
    },
    "de": {
        "today": "Heute", "yesterday": "Gestern", "am": "AM", "pm": "PM",
        "months": ["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"],
        "weekdays": ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"],
    },
    "es": {
        "today": "Hoy", "yesterday": "Ayer", "am": "AM", "pm": "PM",
        "months": ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"],
        "weekdays": ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"],
    },
}


# ── Script parser ─────────────────────────────────────────────────────────────

def parse_script(script: str, seed: int) -> dict | None:
    """
    Parse script format:
        A: Xin chào
        B: Chào bạn
        C: Chào cả nhà   ← 3+ speakers = group chat

    Returns dict with keys: contact_name, is_group, messages
    Each message: {role, text, display_name, color}
    """
    rng = random.Random(seed)

    lines = [l.strip() for l in script.strip().splitlines() if l.strip()]

    parsed: list[tuple[str, str]] = []
    speakers_seen: list[str] = []
    for line in lines:
        if ":" not in line:
            continue
        speaker, _, text = line.partition(":")
        speaker = speaker.strip()
        text    = text.strip()
        if not speaker or not text:
            continue
        if speaker not in speakers_seen:
            speakers_seen.append(speaker)
        parsed.append((speaker, text))

    if not speakers_seen or not parsed:
        return None

    color_map = {spk: SPEAKER_COLORS[i % len(SPEAKER_COLORS)] for i, spk in enumerate(speakers_seen)}

    me       = speakers_seen[0]   # first speaker = "me" (sent side)
    is_group = len(speakers_seen) >= 3

    if is_group:
        others       = [s for s in speakers_seen if s != me]
        contact_name = ", ".join(n.split()[-1] for n in others[:3])
        if len(others) > 3:
            contact_name += f" +{len(others) - 3}"
    else:
        other        = next((s for s in speakers_seen if s != me), me)
        contact_name = other

    messages = [
        {
            "role":         "sent" if spk == me else "recv",
            "text":         text,
            "display_name": spk,
            "color":        color_map[spk],
        }
        for spk, text in parsed
    ]

    return {"contact_name": contact_name, "is_group": is_group, "messages": messages}


# ── Time helpers ─────────────────────────────────────────────────────────────

def _random_datetime(seed: int) -> datetime:
    rng = random.Random(seed + 9999)
    now = datetime.now()
    return now - timedelta(
        days=rng.randint(0, 730),
        hours=rng.randint(0, 23),
        minutes=rng.randint(0, 59),
    )

def _fmt_status(dt: datetime) -> str:
    s = dt.strftime("%I:%M").lstrip("0")
    return s or "12:00"

def _fmt_message(dt: datetime, lang: str = "en") -> str:
    hour    = _fmt_status(dt)
    strings = LANG_STRINGS.get(lang, LANG_STRINGS["en"])
    period  = strings["am"] if dt.hour < 12 else strings["pm"]
    time_str = f"{hour} {period}"

    today     = datetime.now().date()
    msg_date  = dt.date()
    delta     = (today - msg_date).days

    if delta < 7:
        label = strings["weekdays"][msg_date.weekday()]
    else:
        label = f"{strings['months'][msg_date.month - 1]} {msg_date.day}"

    return f"{label}, {time_str}"

def _get_lang(country: str) -> str:
    c = country.strip().lower()
    # Support locale format: fr_FR, en_US, de_DE, it_IT, es_ES
    if "_" in c:
        lang = c.split("_")[0]
        if lang in LANG_STRINGS:
            return lang
    return COUNTRY_LANG.get(c, "en")


# ── Async worker ──────────────────────────────────────────────────────────────

async def _worker(
    worker_id: int,
    queue: asyncio.Queue,
    browser,
    jinja_env: Environment,
    output_dir: Path,
    results: list,
) -> None:
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break

        row, device = item
        context = None
        try:
            row_id  = int(row["_id"])
            qa      = str(row.get("_qa", "unknown")).strip().lower()
            script  = str(row.get("_script", ""))
            country = str(row.get("_country", "US")).strip()
            lang    = _get_lang(country)

            parsed = parse_script(script, seed=row_id)
            if not parsed:
                raise ValueError("Script rỗng hoặc không đúng định dạng")

            dt        = _random_datetime(seed=row_id)
            dark_mode = random.Random(row_id + 42).random() < 0.3
            battery   = random.Random(row_id + 1337).choice(BATTERY_LEVELS)

            context = await browser.new_context(
                viewport={"width": device["width"], "height": device["height"]},
                device_scale_factor=device["scale"],
            )
            page = await context.new_page()

            html = jinja_env.get_template(device["template"]).render(
                contact_name=parsed["contact_name"],
                is_group=parsed["is_group"],
                messages=parsed["messages"],
                status_time=_fmt_status(dt),
                message_time=_fmt_message(dt, lang=lang),
                dark_mode=dark_mode,
                lang=lang,
                battery=battery,
                os=device["os"],
            )

            await page.set_content(html, wait_until="domcontentloaded")

            custom_fn = str(row.get("_filename", "")).strip()
            if custom_fn and custom_fn.lower() != "nan":
                filename = custom_fn if custom_fn.lower().endswith(".png") else custom_fn + ".png"
            else:
                filename = f"{str(row_id).zfill(4)}_{qa}.png"
            filepath = output_dir / filename
            await page.screenshot(path=str(filepath), full_page=False)

            results.append({
                **row,
                "_output_file":  str(filepath),
                "_status":       "ok",
                "_application":  device["application"],
                "_os":           device["os"],
                "_device":       device["name"],
                "_battery":      battery,
            })

            group_tag = " 👥" if parsed["is_group"] else ""
            dark_tag  = " 🌙" if dark_mode else ""
            print(f"[W{worker_id:02d}] ✓  {filename}  ({device['name']}{group_tag}{dark_tag})")

        except Exception as exc:
            results.append({**row, "_output_file": None, "_status": f"error: {exc}"})
            print(f"[W{worker_id:02d}] ✗  id={row.get('_id', '?')}: {exc}")
        finally:
            if context:
                await context.close()
            queue.task_done()


# ── Async runner ──────────────────────────────────────────────────────────────

async def _run(
    rows: list[dict],
    output_dir: Path,
    templates_dir: Path,
    num_workers: int,
) -> list[dict]:
    from playwright.async_api import async_playwright

    output_dir.mkdir(parents=True, exist_ok=True)
    jinja_env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=False)

    queue: asyncio.Queue = asyncio.Queue()
    for row in rows:
        row_id = int(row["_id"])
        app    = str(row.get("_application_csv", "")).strip()
        os_csv = str(row.get("_os_csv", "")).strip()
        dev    = str(row.get("_device_csv", "")).strip()
        if app and app.lower() != "nan":
            device = _find_device(app, os_csv, dev, seed=row_id)
        else:
            device = random.Random(row_id).choice(DEVICES)
        queue.put_nowait((row, device))
    for _ in range(num_workers):
        queue.put_nowait(None)

    results: list = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        await asyncio.gather(*[
            asyncio.create_task(_worker(i + 1, queue, browser, jinja_env, output_dir, results))
            for i in range(num_workers)
        ])
        await browser.close()
    return results


# ── Public API ────────────────────────────────────────────────────────────────

def batch_from_csv(
    csv_path: Path,
    output_dir: Path,
    templates_dir: Path | None = None,
    script_col: str  = "script",
    id_col: str      = "id",
    qa_col: str      = "QA",
    accepted_col: str | None = None,
    num_workers: int = 8,
    limit: int       = 0,
    export_csv: Path | None = None,
    done_csv: Path | None = None,
    participant_col: str = "participant",
    filename_col: str | None = None,
    country_col: str = "country",
    application_col: str = "application used",
    os_col: str = "OS",
    device_col: str = "device info",
) -> list[Path]:
    """
    Read CSV, generate PNG screenshots, return list of output Paths.

    Filters:
      - accepted_col: if set, only rows where that column == 'accept'/'accepted'
      - limit: max rows to process (0 = all)

    Export:
      - export_csv: if set, writes a CSV of successfully processed rows
    """
    df = pd.read_csv(csv_path)

    # Filter by accepted status
    if accepted_col and accepted_col in df.columns:
        mask = df[accepted_col].astype(str).str.strip().str.lower().isin({"accept", "accepted"})
        df   = df[mask].reset_index(drop=True)

    # Drop rows with empty script
    df = df[df[script_col].notna() & (df[script_col].astype(str).str.strip() != "")].reset_index(drop=True)

    # Apply limit
    if limit > 0:
        df = df.head(limit)

    if df.empty:
        return []

    # Normalise into internal row dicts
    rows = []
    for _, r in df.iterrows():
        row = r.to_dict()
        row["_id"]      = r.get(id_col, _)
        row["_qa"]      = r.get(qa_col, "unknown")
        row["_script"]  = str(r[script_col])
        row["_country"] = str(r.get(country_col, "US")) if country_col in df.columns else "US"
        if filename_col and filename_col in df.columns:
            row["_filename"] = str(r.get(filename_col, "")).strip()
        if application_col in df.columns:
            row["_application_csv"] = str(r.get(application_col, "")).strip()
        if os_col in df.columns:
            row["_os_csv"] = str(r.get(os_col, "")).strip()
        if device_col in df.columns:
            row["_device_csv"] = str(r.get(device_col, "")).strip()
        rows.append(row)

    # Each run gets its own timestamped subfolder: output/chat/2026-03-13_21-58-00/
    run_dir = output_dir / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    t0      = time.perf_counter()
    results = asyncio.run(_run(rows, run_dir, templates_dir or TEMPLATES_DIR, num_workers))
    elapsed = time.perf_counter() - t0

    ok_results   = [r for r in results if r["_status"] == "ok"]
    ok_paths     = [Path(r["_output_file"]) for r in ok_results]
    failed_count = len(results) - len(ok_results)

    # Always write metadata.csv in run_dir
    if ok_results:
        import csv as csv_mod
        meta_path = run_dir / "metadata.csv"
        with open(meta_path, "w", encoding="utf-8", newline="") as f:
            writer = csv_mod.writer(f)
            writer.writerow(["id", "filename", "application", "os", "device"])
            for r in sorted(ok_results, key=lambda x: int(x["_id"])):
                writer.writerow([
                    str(int(r["_id"])).zfill(4),
                    Path(r["_output_file"]).name,
                    r.get("_application", ""),
                    r.get("_os", ""),
                    r.get("_device", ""),
                ])

    print(f"\n{'─' * 50}")
    print(f"✅  Thành công : {len(ok_paths)}/{len(rows)}")
    if failed_count:
        print(f"❌  Thất bại   : {failed_count}/{len(rows)}")
    print(f"⏱️   Thời gian  : {elapsed:.1f}s  |  🚀 {len(ok_paths)/elapsed:.1f} ảnh/giây")
    if ok_results:
        print(f"📊  Metadata   : {meta_path}")

    # Export processed rows CSV
    if export_csv and ok_results:
        # Build id→output_file map (worker order is non-deterministic)
        id_to_file = {r["_id"]: r["_output_file"] for r in ok_results}
        ok_ids     = set(id_to_file.keys())
        id_vals    = df[id_col] if id_col in df.columns else df.index
        export_df  = df[id_vals.isin(ok_ids)].copy()
        export_df["output_file"] = export_df[id_col].map(id_to_file)
        export_csv = Path(export_csv)
        export_csv.parent.mkdir(parents=True, exist_ok=True)
        export_df.to_csv(export_csv, index=False)

    # Append to done-data CSV
    if done_csv and ok_results:
        done_csv = Path(done_csv)
        done_csv.parent.mkdir(parents=True, exist_ok=True)
        file_exists = done_csv.exists() and done_csv.stat().st_size > 0
        with open(done_csv, "a", encoding="utf-8", newline="") as f:
            import csv as csv_mod
            writer = csv_mod.writer(f)
            if not file_exists:
                writer.writerow(["index", "participant", "filename"])
            for r in sorted(ok_results, key=lambda x: int(x["_id"])):
                row_id   = str(int(r["_id"])).zfill(4)
                part     = str(r.get(participant_col, "")).strip().lower()
                filename = Path(r["_output_file"]).name
                writer.writerow([row_id, part, filename])
        print(f"📋  Done-data cập nhật → {done_csv}  (+{len(ok_results)} dòng)")

    return ok_paths
