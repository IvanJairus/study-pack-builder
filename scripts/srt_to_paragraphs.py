#!/usr/bin/env python3
"""Merge SRT segments into readable timestamped paragraphs.

Usage:
  python srt_to_paragraphs.py working/session.srt
  python srt_to_paragraphs.py working/session.srt --out working/session.paragraphs.txt
"""
import argparse
import re
from pathlib import Path


def parse_srt(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore").replace("\r\n", "\n")
    segments = []
    for block in re.split(r"\n\s*\n", text):
        lines = [line for line in block.split("\n") if line.strip()]
        if len(lines) < 3:
            continue
        match = re.search(
            r"(\d{2}:\d{2}:\d{2}),\d{3}\s*-->\s*(\d{2}:\d{2}:\d{2}),\d{3}",
            block,
        )
        if not match:
            continue
        body = re.sub(r"\s+", " ", " ".join(lines[2:])).strip()
        if body:
            segments.append((match.group(1), match.group(2), body))
    return segments


def seconds(value: str) -> int:
    hour, minute, second = map(int, value.split(":"))
    return hour * 3600 + minute * 60 + second


def paragraphs(segments, gap: float):
    result = []
    current = []
    start = None
    last_end = None
    for begin, end, text in segments:
        if start is None:
            start = begin
        if last_end and seconds(begin) - seconds(last_end) > gap and current:
            result.append((start, " ".join(current)))
            current = []
            start = begin
        current.append(text)
        last_end = end
    if current:
        result.append((start, " ".join(current)))
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("srt", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--gap", type=float, default=2.0, help="seconds of silence that starts a new paragraph")
    args = ap.parse_args()

    if not args.srt.exists():
        print(f"File not found: {args.srt}")
        return 2

    segments = parse_srt(args.srt)
    paras = paragraphs(segments, args.gap)
    out = args.out or args.srt.with_suffix(".paragraphs.txt")
    with out.open("w", encoding="utf-8") as handle:
        for timestamp, text in paras:
            handle.write(f"[{timestamp}] {text}\n\n")

    print(f"segments={len(segments)} paragraphs={len(paras)}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
