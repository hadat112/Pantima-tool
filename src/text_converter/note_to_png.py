"""
Core logic for note screenshot generation.
Called by `tc note to-png` CLI.
"""

from __future__ import annotations

import asyncio
import random
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"

BATTERY_LEVELS = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
US_CARRIERS = ["Verizon", "AT&T", "T-Mobile"]
ANDROID_NETWORK_TYPES = ["4G", "5G", "LTE"]

DEVICE_PRESETS = {
    "iphone 13": {"width": 390, "height": 844},
    "iphone xs": {"width": 375, "height": 812},
    "iphone 15 promax": {"width": 430, "height": 932},
    "iphone 15 pro max": {"width": 430, "height": 932},
    "samsung galaxy s25": {"width": 412, "height": 915},
    "samsung galaxy s25+": {"width": 450, "height": 1000},
    "samsung galaxy s25 ultra": {"width": 480, "height": 1067},
    "samsung galaxy a56 5g": {"width": 412, "height": 892},
    "samsung galaxy a36 5g": {"width": 412, "height": 914},
    "google pixel 9": {"width": 412, "height": 915},
    "google pixel 9a": {"width": 412, "height": 915},
    "google pixel 9 pro": {"width": 412, "height": 915},
    "google pixel 9 pro xl": {"width": 450, "height": 1000},
    "oneplus 13": {"width": 450, "height": 1000},
    "xiaomi 15 ultra": {"width": 420, "height": 920},
    "oppo find x8 pro": {"width": 450, "height": 1000},
    "oppo reno13 pro 5g": {"width": 420, "height": 930},
    "vivo x200 pro": {"width": 420, "height": 933},
    "vivo v50": {"width": 412, "height": 915},
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Some sheets contain trailing spaces in headers (e.g. "Template ").
    rename_map = {col: col.strip() for col in df.columns}
    return df.rename(columns=rename_map)


def _parse_resolution(text: str) -> tuple[int, int] | None:
    raw = (text or "").strip().lower()
    if not raw:
        return None
    # Supports "1170x2532", "1080 × 2340", "1080*2340".
    m = re.search(r"(\d{3,5})\s*[x×*]\s*(\d{3,5})", raw)
    if not m:
        return None
    w = int(m.group(1))
    h = int(m.group(2))
    if w <= 0 or h <= 0:
        return None
    return (w, h)


def _resolve_viewport(spec: str, os_name: str, device_name: str) -> dict:
    spec_res = _parse_resolution(spec)
    if spec_res:
        return {"width": spec_res[0], "height": spec_res[1]}

    os_res = _parse_resolution(os_name)
    if os_res:
        return {"width": os_res[0], "height": os_res[1]}

    preset = DEVICE_PRESETS.get((device_name or "").strip().lower())
    if preset:
        return preset

    return {"width": 390, "height": 844}


def _detect_platform(device_name: str, os_name: str) -> str:
    device_l = (device_name or "").strip().lower()
    os_l = (os_name or "").strip().lower()

    ios_hints = ("ios", "iphone", "ipad")
    android_hints = ("android", "samsung", "pixel", "oneplus", "xiaomi", "oppo", "vivo")

    if any(h in os_l for h in ios_hints) or any(h in device_l for h in ios_hints):
        return "ios"
    if any(h in os_l for h in android_hints) or any(h in device_l for h in android_hints):
        return "android"

    # Default to iOS look for unknown rows.
    return "ios"


def _fmt_status_time(seed: int, platform: str) -> str:
    rng = random.Random(seed + 7777)
    dt = datetime.now().replace(
        hour=rng.randint(0, 23),
        minute=rng.randint(0, 59),
        second=0,
        microsecond=0,
    )
    if platform == "android":
        return dt.strftime("%H:%M")
    s = dt.strftime("%I:%M").lstrip("0")
    return s or "12:00"


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

        row = item
        context = None
        try:
            row_id = int(row["_id"])
            note_text = str(row.get("_note", "")).strip()
            if not note_text:
                raise ValueError("Template rỗng")

            viewport = _resolve_viewport(
                spec=str(row.get("_spec", "")),
                os_name=str(row.get("_os", "")),
                device_name=str(row.get("_device", "")),
            )
            platform = _detect_platform(
                device_name=str(row.get("_device", "")),
                os_name=str(row.get("_os", "")),
            )
            template_name = "notes_ios.html" if platform == "ios" else "notes_android.html"
            dark_mode = random.Random(row_id + 42).random() < 0.3
            battery = random.Random(row_id + 1337).choice(BATTERY_LEVELS)
            status_time = _fmt_status_time(seed=row_id, platform=platform)
            signal_level = random.Random(row_id + 888).randint(1, 4)
            wifi_level = random.Random(row_id + 999).randint(1, 3)
            carrier = random.Random(row_id + 555).choice(US_CARRIERS)
            network_type = random.Random(row_id + 666).choice(ANDROID_NETWORK_TYPES)

            context = await browser.new_context(
                viewport={"width": viewport["width"], "height": viewport["height"]},
                device_scale_factor=1,
            )
            page = await context.new_page()

            html = jinja_env.get_template(template_name).render(
                note_text=note_text,
                dark_mode=dark_mode,
                battery=battery,
                status_time=status_time,
                device_name=str(row.get("_device", "")),
                os_name=str(row.get("_os", "")),
                carrier=carrier,
                signal_level=signal_level,
                wifi_level=wifi_level,
                wifi_signal=signal_level,
                network_type=network_type,
            )
            await page.set_content(html, wait_until="domcontentloaded")

            custom_fn = str(row.get("_filename", "")).strip()
            if custom_fn and custom_fn.lower() != "nan":
                filename = custom_fn if custom_fn.lower().endswith(".png") else custom_fn + ".png"
            else:
                filename = f"{str(row_id).zfill(4)}_note.png"

            filepath = output_dir / filename
            await page.screenshot(path=str(filepath), full_page=False)

            results.append({
                **row,
                "_output_file": str(filepath),
                "_status": "ok",
                "_width": viewport["width"],
                "_height": viewport["height"],
                "_battery": battery,
                "_dark_mode": dark_mode,
                "_status_time": status_time,
                "_platform": platform,
                "_template": template_name,
            })

            dark_tag = " 🌙" if dark_mode else ""
            print(
                f"[W{worker_id:02d}] ✓  {filename}  "
                f"({platform} {viewport['width']}x{viewport['height']}{dark_tag})"
            )
        except Exception as exc:
            results.append({**row, "_output_file": None, "_status": f"error: {exc}"})
            print(f"[W{worker_id:02d}] ✗  id={row.get('_id', '?')}: {exc}")
        finally:
            if context:
                await context.close()
            queue.task_done()


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
        queue.put_nowait(row)
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


def batch_from_csv(
    csv_path: Path,
    output_dir: Path,
    templates_dir: Path | None = None,
    template_col: str = "Template",
    device_col: str = "Device",
    os_col: str = "OS",
    spec_col: str = "spec",
    filename_col: str | None = None,
    num_workers: int = 8,
    limit: int = 0,
    export_csv: Path | None = None,
    done_csv: Path | None = None,
) -> list[Path]:
    """
    Read CSV, generate note screenshots, return list of output Paths.

    The note body is read from `template_col`.
    Viewport priority: spec column -> OS if resolution-like -> device preset -> fallback.
    """
    df = _normalize_columns(pd.read_csv(csv_path))

    if template_col not in df.columns:
        raise ValueError(f"Không tìm thấy cột '{template_col}' trong CSV.")

    df = df[df[template_col].notna() & (df[template_col].astype(str).str.strip() != "")].reset_index(drop=True)

    if limit > 0:
        df = df.head(limit)

    if df.empty:
        return []

    rows = []
    for i, r in df.iterrows():
        row = r.to_dict()
        row["_id"] = i + 1
        row["_note"] = str(r.get(template_col, ""))
        row["_device"] = str(r.get(device_col, "")).strip() if device_col in df.columns else ""
        row["_os"] = str(r.get(os_col, "")).strip() if os_col in df.columns else ""
        row["_spec"] = str(r.get(spec_col, "")).strip() if spec_col in df.columns else ""
        if filename_col and filename_col in df.columns:
            row["_filename"] = str(r.get(filename_col, "")).strip()
        rows.append(row)

    run_dir = output_dir / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    results = asyncio.run(_run(rows, run_dir, templates_dir or TEMPLATES_DIR, num_workers))
    elapsed = time.perf_counter() - t0

    ok_results = [r for r in results if r["_status"] == "ok"]
    ok_paths = [Path(r["_output_file"]) for r in ok_results]
    failed_count = len(results) - len(ok_results)

    if ok_results:
        import csv as csv_mod
        meta_path = run_dir / "metadata.csv"
        with open(meta_path, "w", encoding="utf-8", newline="") as f:
            writer = csv_mod.writer(f)
            writer.writerow([
                "index", "filename", "device", "os", "spec", "platform", "template",
                "width", "height", "battery", "dark_mode", "status_time",
            ])
            for r in sorted(ok_results, key=lambda x: int(x["_id"])):
                writer.writerow([
                    str(int(r["_id"])).zfill(4),
                    Path(r["_output_file"]).name,
                    r.get("_device", ""),
                    r.get("_os", ""),
                    r.get("_spec", ""),
                    r.get("_platform", ""),
                    r.get("_template", ""),
                    r.get("_width", ""),
                    r.get("_height", ""),
                    r.get("_battery", ""),
                    r.get("_dark_mode", ""),
                    r.get("_status_time", ""),
                ])

    print(f"\n{'─' * 50}")
    print(f"✅  Thành công : {len(ok_paths)}/{len(rows)}")
    if failed_count:
        print(f"❌  Thất bại   : {failed_count}/{len(rows)}")
    print(f"⏱️   Thời gian  : {elapsed:.1f}s  |  🚀 {len(ok_paths)/elapsed:.1f} ảnh/giây")
    if ok_results:
        print(f"📊  Metadata   : {meta_path}")

    if export_csv and ok_results:
        id_to_file = {r["_id"]: r["_output_file"] for r in ok_results}
        ok_ids = set(id_to_file.keys())
        export_df = df[df.index.map(lambda idx: (idx + 1) in ok_ids)].copy()
        export_df["output_file"] = export_df.index.map(lambda idx: id_to_file.get(idx + 1))
        export_csv = Path(export_csv)
        export_csv.parent.mkdir(parents=True, exist_ok=True)
        export_df.to_csv(export_csv, index=False)

    if done_csv and ok_results:
        done_csv = Path(done_csv)
        done_csv.parent.mkdir(parents=True, exist_ok=True)
        file_exists = done_csv.exists() and done_csv.stat().st_size > 0
        with open(done_csv, "a", encoding="utf-8", newline="") as f:
            import csv as csv_mod
            writer = csv_mod.writer(f)
            if not file_exists:
                writer.writerow(["index", "filename"])
            for r in sorted(ok_results, key=lambda x: int(x["_id"])):
                writer.writerow([str(int(r["_id"])).zfill(4), Path(r["_output_file"]).name])
        print(f"📋  Done-data cập nhật → {done_csv}  (+{len(ok_results)} dòng)")

    return ok_paths
