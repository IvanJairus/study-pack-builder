#!/usr/bin/env python3
"""Render a narrated slide video from a timed script, slides, and audio.

Usage:
  python render_video.py working/script-timed.json --slides working/slides --audio working/audio --out working/final/overview.mp4
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(command):
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def encode(slide: Path, audio: Path | None, duration: float, out: Path, hold: str | None = None):
    vf = "scale=1920:1080,format=yuv420p"
    if hold == "in":
        vf += ",fade=t=in:st=0:d=0.5"
    if hold == "out":
        vf += ",fade=t=out:st=0:d=0.5"
    command = ["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(slide)]
    if audio:
        command += ["-i", str(audio)]
    else:
        command += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    command += [
        "-t", f"{duration:.3f}",
        "-vf", vf,
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-ac", "2",
        "-shortest",
        str(out),
    ]
    run(command)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("script", type=Path)
    ap.add_argument("--slides", type=Path, required=True)
    ap.add_argument("--audio", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--intro-hold", type=float, default=0.5)
    ap.add_argument("--outro-hold", type=float, default=0.5)
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            print(f"{tool} is required", file=sys.stderr)
            return 2

    data = json.loads(args.script.read_text(encoding="utf-8"))
    sections = data.get("sections") if isinstance(data, dict) else data
    if not isinstance(sections, list) or not sections:
        print("Script must contain a non-empty sections list", file=sys.stderr)
        return 2

    work = args.out.parent / "segments"
    work.mkdir(parents=True, exist_ok=True)
    segments = []

    first = sections[0]
    first_slide = args.slides / f"{first.get('num', '01'):0>2}-{first['id']}.png"
    intro = work / "00-intro.mp4"
    encode(first_slide, None, args.intro_hold, intro, hold="in")
    segments.append(intro)

    for index, section in enumerate(sections, 1):
        slide = args.slides / f"{section.get('num', index):0>2}-{section['id']}.png"
        audio = Path(section.get("audio") or args.audio / f"{section['id']}.aiff")
        duration = float(section["duration"])
        if not slide.exists():
            print(f"Missing slide: {slide}", file=sys.stderr)
            return 2
        if not audio.exists():
            print(f"Missing audio: {audio}", file=sys.stderr)
            return 2
        out = work / f"{section.get('num', index):0>2}-{section['id']}.mp4"
        encode(slide, audio, duration, out)
        segments.append(out)
        print(f"segment {section['id']}: {duration:.2f}s")

    last = sections[-1]
    last_slide = args.slides / f"{last.get('num', len(sections)):0>2}-{last['id']}.png"
    outro = work / "99-outro.mp4"
    encode(last_slide, None, args.outro_hold, outro, hold="out")
    segments.append(outro)

    concat = work / "concat.txt"
    concat.write_text("\n".join(f"file '{segment}'" for segment in segments) + "\n", encoding="utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(args.out)])

    duration = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "default=nw=1", str(args.out)],
        text=True,
    ).strip()
    print(duration)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
