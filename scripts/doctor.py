#!/usr/bin/env python3
"""Check local tools before a study pack build.

The script reports what is present and prints the exact install command for
what is missing. It never installs packages on its own.

Usage:
  python doctor.py
  python doctor.py --need pdf,pptx
  python doctor.py --need pdf,video,ocr --json
"""
import argparse
import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path

MAC = platform.system() == "Darwin"
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]
CHECK_GROUPS = {
    "pdf": ["module:pymupdf"],
    "pptx": ["module:pptx"],
    "image": ["module:PIL"],
    "video": ["bin:ffmpeg", "bin:ffprobe"],
    "ocr": ["any:textutil,tesseract"],
    "transcribe": ["any:mlx_whisper,whisper-cpp,whisper"],
    "doc": ["any:textutil,soffice,libreoffice"],
    "tts": ["any:say,piper"],
    "browser": ["chrome"],
}
INSTALL_HINTS = {
    "module:pymupdf": "python3 -m pip install pymupdf",
    "module:pptx": "python3 -m pip install python-pptx",
    "module:PIL": "python3 -m pip install Pillow",
    "bin:ffmpeg": "brew install ffmpeg" if MAC else "sudo apt install ffmpeg",
    "bin:ffprobe": "brew install ffmpeg" if MAC else "sudo apt install ffmpeg",
    "any:textutil,tesseract": "macOS has textutil; elsewhere install tesseract",
    "any:mlx_whisper,whisper-cpp,whisper": "python3 -m pip install mlx-whisper (Apple Silicon) or install whisper.cpp",
    "any:textutil,soffice,libreoffice": "install LibreOffice, or convert DOC files to DOCX",
    "any:say,piper": "macOS has say; elsewhere install Piper",
    "chrome": "install Google Chrome or Chromium, or set CHROME_BIN",
}


def chrome_path():
    override = shutil.which("google-chrome") or shutil.which("chromium")
    if override:
        return override
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def check_item(item):
    if item.startswith("module:"):
        name = item.split(":", 1)[1]
        return importlib.util.find_spec(name) is not None, name
    if item.startswith("bin:"):
        name = item.split(":", 1)[1]
        path = shutil.which(name)
        return bool(path), path or name
    if item.startswith("any:"):
        names = item.split(":", 1)[1].split(",")
        for name in names:
            if name == "mlx_whisper":
                if importlib.util.find_spec(name) is not None:
                    return True, name
                continue
            path = shutil.which(name)
            if path:
                return True, path
        return False, ", ".join(names)
    if item == "chrome":
        path = chrome_path()
        return bool(path), path or "chrome"
    return False, item


def need_list(value):
    if not value:
        return []
    groups = []
    for item in value.split(","):
        item = item.strip().lower()
        if item:
            groups.append(item)
    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--need", default=None, help="Comma-separated groups: pdf, pptx, image, video, ocr, transcribe, doc, tts, browser")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    args = parser.parse_args()

    groups = need_list(args.need)
    unknown = [group for group in groups if group not in CHECK_GROUPS]
    if unknown:
        print(f"Unknown need group: {', '.join(unknown)}", file=sys.stderr)
        print(f"Known groups: {', '.join(CHECK_GROUPS)}", file=sys.stderr)
        return 2

    selected = groups or list(CHECK_GROUPS)
    report = {"python": sys.version.split()[0], "platform": platform.system(), "need": groups, "groups": []}
    missing_required = 0

    lines = [f"Python {report['python']} on {report['platform']}"]
    for group in selected:
        items = []
        for item in CHECK_GROUPS[group]:
            ok, detail = check_item(item)
            items.append({"check": item, "ok": ok, "detail": detail, "hint": INSTALL_HINTS.get(item, "")})
            if not ok:
                lines.append(f"[missing] {group:11} {detail:30} -> {INSTALL_HINTS.get(item, 'install this tool')}")
            else:
                lines.append(f"[ok]      {group:11} {detail}")
        if group in groups and not all(item["ok"] for item in items):
            missing_required += 1
        report["groups"].append({"group": group, "required": group in groups, "items": items})

    report["ready"] = missing_required == 0
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("\n".join(lines))
        print(f"Required groups: {', '.join(groups) if groups else 'none'}")
        if missing_required:
            print(f"BLOCKED: {missing_required} required group(s) missing")
        else:
            print("READY" if groups else "REPORT ONLY")
    return 1 if missing_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
