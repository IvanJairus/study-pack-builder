#!/usr/bin/env python3
"""Build a range-level coverage manifest from the study map and quiz data.

Use this for legacy or slide-range packs. For unit-level coverage, create a
manifest from normalized JSONL and set level to unit.

Usage:
  python build_coverage.py --out sumber/coverage.json \
    --map assets/map-data.js --quiz assets/quiz-data.js \
    --source "deck.pptx" --question-source "question bank"
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from quiz_schema import load_questions_file

RANGE = re.compile(r"(?i)\b(slide|line|page|row)s?\s*(\d+)\s*[-\u2013]\s*(\d+)")
KIND = {"slide": "slide_range", "line": "line_range", "page": "page_range", "row": "row_range"}


def parse_map(path):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.STUDY_MAP\s*=\s*(\{.*\})\s*;", text, re.S)
    if not match:
        raise ValueError("window.STUDY_MAP not found")
    return json.loads(match.group(1))


def parse_range(value):
    match = RANGE.search(str(value or ""))
    if not match:
        return None
    return KIND[match.group(1).lower()], int(match.group(2)), int(match.group(3))


def load_raw_ids(path):
    if not path:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError("raw questions must be a list or an object with questions")
    ids = []
    for index, item in enumerate(items, 1):
        if isinstance(item, str):
            ids.append(item)
            continue
        if not isinstance(item, dict):
            continue
        value = item.get("id") or item.get("source_id")
        if not value:
            number = item.get("no", index)
            prefix = item.get("set", "Q")
            value = f"{prefix}-{int(number):02d}"
        ids.append(str(value))
    return ids


def build(args):
    map_data = parse_map(args.map)
    questions = load_questions_file(args.quiz)
    units = []
    for topic in map_data.get("topics", []):
        parsed = parse_range(topic.get("source"))
        if not parsed:
            continue
        kind, start, end = parsed
        units.append({
            "source": args.source,
            "ref": topic["source"],
            "kind": kind,
            "from": start,
            "to": end,
            "page": topic.get("page"),
            "status": "covered",
            "label": topic.get("title"),
        })
    if args.question_source:
        units.append({
            "source": args.question_source,
            "ref": "question set",
            "kind": "question_set",
            "page": args.quiz_page,
            "status": "covered",
        })
    for audio in args.audio:
        units.append({
            "source": audio,
            "ref": f"session:{Path(audio).stem}",
            "kind": "audio",
            "page": args.interview_page,
            "status": "covered",
        })
    if args.derived:
        units.append({
            "source": args.source,
            "ref": "derived:reference",
            "kind": "derived",
            "page": args.reference_page,
            "status": "covered",
        })
    mapped = [str(source) for question in questions for source in question.get("sources", [])]
    raw = load_raw_ids(args.raw_questions)
    if raw is None:
        raw = sorted(set(mapped))
    missing = sorted(set(raw) - set(mapped))
    duplicate = sorted({item for item in mapped if mapped.count(item) > 1})
    totals = {}
    for unit in units:
        if unit.get("kind") in KIND.values():
            key = (unit["source"], unit["kind"])
            totals[key] = max(totals.get(key, 0), unit["to"])
    coverage = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "level": "range",
        "source_inventory": args.source_inventory,
        "range_totals": [
            {"source": source, "kind": kind, "total": total}
            for (source, kind), total in sorted(totals.items())
        ],
        "units": units,
        "questions": {
            "raw_total": len(raw),
            "unique_total": len(questions),
            "raw_ids": sorted(raw),
            "mapped_ids": mapped,
            "missing_ids": missing,
            "duplicate_ids": duplicate,
        },
        "summary": {
            "total": len(units),
            "covered": sum(1 for unit in units if unit["status"] == "covered"),
            "non_content": sum(1 for unit in units if unit["status"] == "non-content"),
            "unresolved": sum(1 for unit in units if unit["status"] == "unresolved"),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"units={len(units)} ranges={sum(1 for unit in units if unit['kind'] in KIND.values())}")
    print(f"questions raw={len(raw)} unique={len(questions)} missing={len(missing)} duplicate={len(duplicate)}")
    print(f"wrote {args.out}")
    return 1 if missing or duplicate else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--map", type=Path, default=Path("assets/map-data.js"))
    parser.add_argument("--quiz", type=Path, default=Path("assets/quiz-data.js"))
    parser.add_argument("--source", default="source deck")
    parser.add_argument("--question-source", default="question bank")
    parser.add_argument("--audio", action="append", default=[], help="Audio session source; repeatable")
    parser.add_argument("--derived", action="store_true", help="Add a derived reference page unit")
    parser.add_argument("--source-inventory", default="sumber/source-inventory.json")
    parser.add_argument("--quiz-page", default="bank-soal.html")
    parser.add_argument("--interview-page", default="interview.html")
    parser.add_argument("--reference-page", default="reference.html")
    parser.add_argument("--raw-questions", type=Path, default=None)
    args = parser.parse_args()
    try:
        return build(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Cannot build coverage: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
