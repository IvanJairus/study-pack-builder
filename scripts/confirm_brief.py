#!/usr/bin/env python3
"""Validate a project brief and record explicit user confirmation.

Run this only after the user has seen the MAKE SURE summary and replied yes.

Usage:
  python confirm_brief.py sumber/project-brief.json --by "user" --note "confirmed in chat"
  python confirm_brief.py sumber/project-brief.json --check
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def validate(brief):
    errors = []
    for field in ("goal", "sources", "output", "language"):
        value = brief.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"empty {field}")
    exam = brief.get("exam")
    if not isinstance(exam, dict):
        errors.append("missing exam")
    elif not isinstance(exam.get("questions"), int) or exam.get("questions") < 1:
        errors.append("exam.questions must be a positive integer")
    outputs = brief.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        errors.append("missing outputs")
    theme = brief.get("theme")
    if not isinstance(theme, dict) or theme.get("mode") not in {"light", "dark", "system"}:
        errors.append("theme.mode must be light, dark, or system")
    ssot = brief.get("ssot")
    if ssot is not None and (not isinstance(ssot, list) or not ssot):
        errors.append("ssot must be a non-empty list when present")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("brief", type=Path)
    parser.add_argument("--by", default="user", help="Who confirmed the brief")
    parser.add_argument("--note", default="", help="Confirmation note")
    parser.add_argument("--force", action="store_true", help="Replace an existing confirmation")
    parser.add_argument("--check", action="store_true", help="Validate and show confirmation state only")
    args = parser.parse_args()

    try:
        brief = json.loads(args.brief.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read brief: {exc}", file=sys.stderr)
        return 2

    errors = validate(brief)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    confirmed_at = brief.get("confirmed_at")
    if args.check:
        print(f"confirmed_at={confirmed_at or 'missing'}")
        print(f"confirmed_by={brief.get('confirmed_by') or 'missing'}")
        return 0 if confirmed_at and brief.get("confirmed_by") else 1
    if confirmed_at and not args.force:
        print(f"Already confirmed at {confirmed_at}; use --force to replace.", file=sys.stderr)
        return 2

    brief["confirmed_at"] = datetime.now(timezone.utc).isoformat()
    brief["confirmed_by"] = args.by.strip() or "user"
    if args.note.strip():
        brief["confirmation_note"] = args.note.strip()
    args.brief.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"confirmed {args.brief} at {brief['confirmed_at']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
