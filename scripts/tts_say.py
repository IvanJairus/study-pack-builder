#!/usr/bin/env python3
"""Generate per-section narration with macOS `say` and record durations.

Script JSON accepts a list or an object with a "sections" list.
Each section needs an id and text. The script adds audio and duration.

Usage:
  python tts_say.py working/script.json --voice Damayanti --rate 170 --out-dir working/audio
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def load_sections(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    sections = data.get("sections") if isinstance(data, dict) else data
    if not isinstance(sections, list) or not sections:
        raise ValueError("Expected a non-empty list or an object with a sections list")
    for index, section in enumerate(sections, 1):
        section.setdefault("id", f"section-{index:02d}")
        if not section.get("text"):
            raise ValueError(f"Section {section['id']} has no text")
    return data, sections


def duration(path: Path) -> float:
    output = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        text=True,
    ).strip()
    return round(float(output), 3)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("script", type=Path)
    ap.add_argument("--voice", default="Samantha")
    ap.add_argument("--rate", type=int, default=170)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--out-script", type=Path, default=None)
    args = ap.parse_args()

    if not shutil.which("say"):
        print("macOS `say` is required, or use another TTS and provide audio files.", file=sys.stderr)
        return 2
    if not shutil.which("ffprobe"):
        print("ffprobe is required to measure audio duration.", file=sys.stderr)
        return 2

    try:
        data, sections = load_sections(args.script)
    except Exception as exc:
        print(f"Invalid script: {exc}", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    total = 0.0
    for section in sections:
        out = args.out_dir / f"{section['id']}.aiff"
        subprocess.run(
            ["say", "-v", args.voice, "-r", str(args.rate), "-o", str(out), section["text"]],
            check=True,
        )
        section["audio"] = str(out)
        section["duration"] = duration(out)
        total += section["duration"]
        print(f"{section['id']}: {section['duration']:.2f}s")

    out_script = args.out_script or args.script.with_name(args.script.stem + "-timed.json")
    out_script.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"total={total:.2f}s")
    print(f"wrote {out_script}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
