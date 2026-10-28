#!/usr/bin/env python3
"""Validate source-to-page coverage and raw-question coverage.

A coverage manifest proves that every source unit is either mapped to an
output page, explicitly marked as non-content, or reported as unresolved.
It also proves that every raw question ID appears exactly once in the quiz.

Usage:
  python check_coverage.py --coverage sumber/coverage.json --root . --quiz assets/quiz-data.js
  python check_coverage.py --coverage sumber/coverage.json --root . --normalized working/normalized.jsonl
"""
import argparse
import json
import re
import sys
from pathlib import Path

from quiz_schema import load_questions_file

STATUSES = {"covered", "non-content", "unresolved"}
RANGE_KINDS = {"slide_range", "line_range", "page_range", "row_range"}


def load_manifest(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("coverage manifest must be an object")
    return data


def normalize_source(value):
    return Path(str(value)).name


def page_exists(root, page):
    return bool(page) and (root / page).exists()


def validate_units(units, root):
    errors = []
    warnings = []
    seen = set()
    counts = {"covered": 0, "non-content": 0, "unresolved": 0}
    ranges = {}
    for index, unit in enumerate(units, 1):
        label = f"unit #{index}"
        if not isinstance(unit, dict):
            errors.append(f"{label}: not an object")
            continue
        source = str(unit.get("source") or "").strip()
        ref = str(unit.get("ref") or "").strip()
        status = unit.get("status")
        if not source:
            errors.append(f"{label}: empty source")
        if not ref:
            errors.append(f"{label}: empty ref")
        key = (source, ref)
        if key in seen:
            errors.append(f"{label}: duplicate source/ref {source} {ref}")
        seen.add(key)
        if status not in STATUSES:
            errors.append(f"{label}: invalid status {status!r}")
            continue
        counts[status] += 1
        if status == "covered":
            page = str(unit.get("page") or "").strip()
            if not page:
                errors.append(f"{label}: covered unit has no page")
            elif not page_exists(root, page):
                errors.append(f"{label}: page does not exist: {page}")
        elif status == "non-content":
            if not str(unit.get("reason") or "").strip():
                errors.append(f"{label}: non-content unit has no reason")
        else:
            errors.append(f"{label}: unresolved source unit")
        kind = unit.get("kind")
        if kind in RANGE_KINDS:
            start = unit.get("from")
            end = unit.get("to")
            if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
                errors.append(f"{label}: invalid range {start!r}-{end!r}")
            else:
                ranges.setdefault((source, kind), []).append((start, end, label))
    for (source, kind), items in ranges.items():
        items.sort()
        if items and items[0][0] > 1:
            warnings.append(f"{source} {kind} starts at {items[0][0]}, not 1")
        for previous, current in zip(items, items[1:]):
            if current[0] <= previous[1]:
                errors.append(f"{source} {kind} overlaps: {previous[2]} and {current[2]}")
            elif current[0] != previous[1] + 1:
                errors.append(f"{source} {kind} has a gap between {previous[1]} and {current[0]}")
    return errors, warnings, counts, ranges


def validate_questions(section, questions):
    errors = []
    warnings = []
    if not isinstance(section, dict):
        return ["coverage questions section is missing or invalid"], warnings
    raw_ids = section.get("raw_ids")
    mapped_ids = section.get("mapped_ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        return ["coverage questions.raw_ids is missing"], warnings
    if not all(isinstance(item, str) and item.strip() for item in raw_ids):
        errors.append("coverage questions.raw_ids must contain non-empty strings")
    raw_ids = [str(item) for item in raw_ids]
    if len(raw_ids) != len(set(raw_ids)):
        errors.append("coverage raw_ids contain duplicates")
    if not isinstance(mapped_ids, list):
        errors.append("coverage questions.mapped_ids is missing")
        mapped_ids = []
    raw_set = set(raw_ids)
    mapped_set = set(str(item) for item in mapped_ids)
    missing = sorted(raw_set - mapped_set)
    unknown = sorted(mapped_set - raw_set)
    duplicates = sorted({item for item in mapped_ids if mapped_ids.count(item) > 1})
    if missing:
        errors.append(f"raw question IDs not mapped: {missing[:10]}")
    if unknown:
        errors.append(f"mapped IDs not in raw set: {unknown[:10]}")
    if duplicates:
        errors.append(f"raw question IDs mapped more than once: {duplicates[:10]}")
    if section.get("missing_ids") not in (None, [], missing):
        errors.append("coverage questions.missing_ids is out of date")
    if section.get("duplicate_ids") not in (None, [], duplicates):
        errors.append("coverage questions.duplicate_ids is out of date")
    if section.get("raw_total") not in (None, len(raw_ids)):
        errors.append("coverage questions.raw_total is out of date")
    if section.get("unique_total") is not None and questions is not None and section.get("unique_total") != len(questions):
        errors.append(f"coverage unique_total {section.get('unique_total')} does not match quiz {len(questions)}")
    if questions is not None:
        actual_mapped = [str(source) for question in questions for source in question.get("sources", [])]
        actual_set = set(actual_mapped)
        if actual_set != mapped_set:
            errors.append("coverage mapped_ids do not match quiz sources")
        actual_missing = sorted(raw_set - actual_set)
        if actual_missing:
            errors.append(f"quiz is missing raw IDs: {actual_missing[:10]}")
        actual_duplicates = sorted({item for item in actual_mapped if actual_mapped.count(item) > 1})
        if actual_duplicates:
            errors.append(f"quiz maps raw IDs more than once: {actual_duplicates[:10]}")
        if len(actual_mapped) != len(raw_ids):
            warnings.append(f"quiz has {len(actual_mapped)} source tokens for {len(raw_ids)} raw IDs")
    return errors, warnings


def validate_normalized(path, units, level):
    errors = []
    warnings = []
    if not path:
        return errors, warnings
    try:
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, json.JSONDecodeError) as exc:
        return [f"normalized file is unreadable: {exc}"], warnings
    expected = {(normalize_source(item.get("source", "")), item.get("ref", "")) for item in records}
    if level != "unit":
        warnings.append("coverage level is range; unit-level normalized comparison skipped")
        return errors, warnings
    normalized_kinds = {"page", "slide", "line", "paragraph", "row", "block", "heading", "list_item", "code", "note", "cell"}
    actual = {
        (normalize_source(item.get("source", "")), item.get("ref", ""))
        for item in units
        if item.get("kind") in normalized_kinds
    }
    status_by_key = {
        (normalize_source(item.get("source", "")), item.get("ref", "")): item.get("status")
        for item in units
    }
    missing = sorted(expected - actual)
    extra = sorted(key for key in actual - expected if status_by_key.get(key) != "non-content")
    if missing:
        errors.append(f"normalized records not in coverage: {missing[:10]}")
    if extra:
        errors.append(f"coverage units not in normalized records: {extra[:10]}")
    return errors, warnings


def validate_coverage(path, root, questions=None, normalized=None):
    errors = []
    warnings = []
    try:
        data = load_manifest(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"coverage manifest is unreadable: {exc}"], warnings, {}
    inventory = str(data.get("source_inventory") or "").strip()
    if not inventory or not (root / inventory).exists():
        errors.append(f"coverage source_inventory is missing: {inventory or '(empty)'}")
    units = data.get("units")
    if not isinstance(units, list) or not units:
        return ["coverage manifest has no units"], warnings, {}
    level = data.get("level", "range")
    if level not in {"unit", "range"}:
        errors.append(f"coverage level must be unit or range, got {level!r}")
    unit_errors, unit_warnings, counts, ranges = validate_units(units, root)
    errors.extend(unit_errors)
    warnings.extend(unit_warnings)
    range_totals = data.get("range_totals")
    has_range_units = any(unit.get("kind") in RANGE_KINDS for unit in units if isinstance(unit, dict))
    if has_range_units and (not isinstance(range_totals, list) or not range_totals):
        warnings.append("coverage range_totals is missing; end of source ranges is not proven")
    elif isinstance(range_totals, list) and range_totals:
        for entry in range_totals:
            if not isinstance(entry, dict):
                errors.append("range_totals entry is not an object")
                continue
            source = str(entry.get("source") or "").strip()
            kind = entry.get("kind")
            total = entry.get("total")
            key = (source, kind)
            items = ranges.get(key, [])
            if not items:
                errors.append(f"range_totals has no ranges for {source} {kind}")
            elif not isinstance(total, int) or total < 1:
                errors.append(f"range_totals total is invalid for {source} {kind}")
            else:
                if items[0][0] != 1:
                    errors.append(f"{source} {kind} starts at {items[0][0]}, expected 1")
                if items[-1][1] != total:
                    errors.append(f"{source} {kind} ends at {items[-1][1]}, expected {total}")
    source_totals = data.get("source_totals")
    if isinstance(source_totals, list):
        for entry in source_totals:
            if not isinstance(entry, dict):
                errors.append("source_totals entry is not an object")
                continue
            source = str(entry.get("source") or "").strip()
            total = entry.get("total")
            if not isinstance(total, int) or total < 1:
                errors.append(f"source_totals total is invalid for {source}")
                continue
            numbers = set()
            for unit in units:
                if not isinstance(unit, dict):
                    continue
                if normalize_source(unit.get("source", "")) != normalize_source(source):
                    continue
                match = re.search(r"(\d+)", str(unit.get("ref") or ""))
                if match:
                    numbers.add(int(match.group(1)))
            missing = sorted(set(range(1, total + 1)) - numbers)
            extra = sorted(number for number in numbers if number > total)
            if missing:
                errors.append(f"source_totals {source} missing units: {missing[:10]}")
            if extra:
                errors.append(f"source_totals {source} has units beyond total: {extra[:10]}")
    summary = data.get("summary")
    if not isinstance(summary, dict):
        warnings.append("coverage summary is missing")
    else:
        expected = {
            "total": len(units),
            "covered": counts["covered"],
            "non_content": counts["non-content"],
            "unresolved": counts["unresolved"],
        }
        for key, value in expected.items():
            if summary.get(key) != value:
                errors.append(f"coverage summary.{key} is {summary.get(key)}, expected {value}")
    question_errors, question_warnings = validate_questions(data.get("questions"), questions)
    errors.extend(question_errors)
    warnings.extend(question_warnings)
    normalized_errors, normalized_warnings = validate_normalized(normalized, units, level)
    errors.extend(normalized_errors)
    warnings.extend(normalized_warnings)
    stats = {"level": level, "total": len(units), **counts}
    if isinstance(data.get("questions"), dict):
        stats["raw_questions"] = data["questions"].get("raw_total")
        stats["unique_questions"] = data["questions"].get("unique_total")
    return errors, warnings, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--quiz", type=Path, default=None)
    parser.add_argument("--normalized", type=Path, default=None)
    args = parser.parse_args()
    questions = None
    if args.quiz:
        try:
            questions = load_questions_file(args.quiz)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"Cannot read quiz: {exc}", file=sys.stderr)
            return 2
    errors, warnings, stats = validate_coverage(args.coverage, args.root, questions, args.normalized)
    print(f"coverage: {stats.get('total', 0)} units, {stats.get('covered', 0)} covered, {stats.get('non-content', 0)} non-content, {stats.get('unresolved', 0)} unresolved")
    if "raw_questions" in stats:
        print(f"questions: {stats['raw_questions']} raw, {stats['unique_questions']} unique")
    for error in errors[:30]:
        print(f"  error: {error}")
    for warning in warnings[:30]:
        print(f"  warning: {warning}")
    print("PASS" if not errors else "FAIL")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
