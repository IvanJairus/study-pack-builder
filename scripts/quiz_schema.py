#!/usr/bin/env python3
"""Validate question data for single choice, multiple choice, true or false,
and short answer questions.

A question may use two or more options. Choice question keys must be single
uppercase letters. Omitted type defaults to single_choice for older banks.

Usage:
  python quiz_schema.py assets/quiz-data.js
  python quiz_schema.py working/questions.json --strict
  python quiz_schema.py questions.json --json
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

CHOICE_TYPES = {"single_choice", "multiple_choice"}
VALID_TYPES = {"single_choice", "multiple_choice", "true_false", "short_answer"}
TYPE_ALIASES = {
    "single": "single_choice",
    "single choice": "single_choice",
    "single_choice": "single_choice",
    "mcq": "single_choice",
    "multiple": "multiple_choice",
    "multiple choice": "multiple_choice",
    "multiple_choice": "multiple_choice",
    "multi": "multiple_choice",
    "multiple select": "multiple_choice",
    "multiple_select": "multiple_choice",
    "select all": "multiple_choice",
    "true false": "true_false",
    "true_false": "true_false",
    "true/false": "true_false",
    "boolean": "true_false",
    "tf": "true_false",
    "short": "short_answer",
    "short answer": "short_answer",
    "short_answer": "short_answer",
    "text": "short_answer",
    "fill blank": "short_answer",
    "fill_blank": "short_answer",
}
TYPE_LABELS = {
    "single_choice": "single choice",
    "multiple_choice": "multiple choice",
    "true_false": "true or false",
    "short_answer": "short answer",
}


def normalize_type(value):
    if value is None:
        return "single_choice"
    key = re.sub(r"[\s_-]+", " ", str(value).strip().lower())
    return TYPE_ALIASES.get(key)


def normalize_answer_text(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = text.casefold()
    text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def options_for(question):
    question_type = normalize_type(question.get("type"))
    if question_type == "true_false":
        return {"A": "True", "B": "False"}
    if question_type == "short_answer":
        return {}
    options = question.get("options")
    return options if isinstance(options, dict) else {}


def order_for(question):
    options = options_for(question)
    order = question.get("order")
    if isinstance(order, list) and len(order) == len(options) and set(order) == set(options):
        return list(order)
    return list(options)


def correct_keys(question):
    question_type = normalize_type(question.get("type"))
    answer = question.get("answer")
    if question_type == "single_choice":
        return [answer] if isinstance(answer, str) else []
    if question_type == "multiple_choice":
        return [key for key in answer if isinstance(key, str)] if isinstance(answer, list) else []
    if question_type == "true_false":
        if isinstance(answer, bool):
            return ["A"] if answer else ["B"]
        if isinstance(answer, str) and answer.strip().lower() in {"true", "false"}:
            return ["A"] if answer.strip().lower() == "true" else ["B"]
    return []


def accepted_answers(question):
    values = question.get("accepted_answers")
    if isinstance(values, list):
        return [str(value).strip() for value in values if str(value).strip()]
    answer = question.get("answer")
    if normalize_type(question.get("type")) == "short_answer" and isinstance(answer, str) and answer.strip():
        return [answer.strip()]
    return []


def answer_matches(question, response):
    question_type = normalize_type(question.get("type"))
    if question_type == "short_answer":
        expected = accepted_answers(question)
        normalized = normalize_answer_text(response)
        return bool(expected) and any(normalize_answer_text(item) == normalized for item in expected)
    keys = set(correct_keys(question))
    if question_type == "multiple_choice":
        selected = set(response) if isinstance(response, list) else set()
        return bool(keys) and selected == keys
    if question_type == "true_false" and isinstance(response, bool):
        response = "A" if response else "B"
    return bool(keys) and response in keys


def validate_question(question, position=1):
    errors = []
    warnings = []
    if not isinstance(question, dict):
        return [f"#{position}: question is not an object"], warnings
    qid = str(question.get("id") or "").strip()
    label = qid or f"#{position}"
    raw_type = question.get("type")
    question_type = normalize_type(raw_type)
    if question_type is None:
        return [f"{label}: unknown type {raw_type!r}"], warnings
    if raw_type is None:
        warnings.append(f"{label}: missing type, assumed single_choice")
    elif str(raw_type).strip().lower() not in VALID_TYPES:
        warnings.append(f"{label}: type alias {raw_type!r} normalized to {question_type}")
    if not qid:
        errors.append(f"{label}: missing id")
    for field in ("question", "explanation", "trap"):
        value = question.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label}: empty {field}")
    topic = question.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        errors.append(f"{label}: empty topic")

    options = options_for(question)
    if question_type in CHOICE_TYPES:
        raw_options = question.get("options")
        if not isinstance(raw_options, dict):
            errors.append(f"{label}: options must be an object")
        elif len(raw_options) < 2:
            errors.append(f"{label}: needs at least 2 options")
        elif len(raw_options) > 8:
            warnings.append(f"{label}: {len(raw_options)} options; 8 or fewer reads better")
        invalid_keys = [key for key in options if not re.fullmatch(r"[A-Z]", str(key))]
        if invalid_keys:
            errors.append(f"{label}: option keys must be single uppercase letters, got {invalid_keys}")
        empty_options = [key for key, value in options.items() if not isinstance(value, str) or not value.strip()]
        if empty_options:
            errors.append(f"{label}: empty or non-text option for {empty_options}")
        normalized_values = [
            re.sub(r"\s+", " ", value.strip().lower())
            for value in options.values()
            if isinstance(value, str) and value.strip()
        ]
        if len(normalized_values) != len(set(normalized_values)):
            warnings.append(f"{label}: duplicate option text")
        order = question.get("order")
        if order is not None:
            if not isinstance(order, list) or len(order) != len(options) or set(map(str, order)) != set(map(str, options)):
                errors.append(f"{label}: order must list every option key exactly once")
        answer = question.get("answer")
        if question_type == "single_choice":
            if not isinstance(answer, str) or answer not in options:
                errors.append(f"{label}: answer must be one option key")
        else:
            if not isinstance(answer, list) or len(answer) < 2:
                errors.append(f"{label}: multiple_choice answer must list at least 2 keys")
            elif len(set(answer)) != len(answer):
                errors.append(f"{label}: duplicate answer keys")
            elif any(not isinstance(key, str) or key not in options for key in answer):
                errors.append(f"{label}: answer key not in options")
    elif question_type == "true_false":
        if options and question.get("options"):
            warnings.append(f"{label}: true_false ignores options; remove them")
        answer = question.get("answer")
        if not isinstance(answer, bool) and not (isinstance(answer, str) and answer.strip().lower() in {"true", "false"}):
            errors.append(f"{label}: true_false answer must be true or false")
    elif question_type == "short_answer":
        if question.get("options"):
            errors.append(f"{label}: short_answer must not define options")
        accepted = accepted_answers(question)
        raw_accepted = question.get("accepted_answers")
        if not isinstance(raw_accepted, list) or not raw_accepted:
            errors.append(f"{label}: short_answer needs accepted_answers")
        elif any(not isinstance(value, str) or not value.strip() for value in raw_accepted):
            errors.append(f"{label}: accepted_answers must contain non-empty text")
        else:
            accepted = accepted_answers(question)
            if len({normalize_answer_text(value) for value in accepted}) != len(accepted):
                warnings.append(f"{label}: duplicate accepted answers")
        answer = question.get("answer")
        if answer is not None:
            if not isinstance(answer, str) or not answer.strip():
                errors.append(f"{label}: short_answer answer must be text when present")
            elif normalize_answer_text(answer) not in {normalize_answer_text(value) for value in accepted}:
                warnings.append(f"{label}: answer is not one of accepted_answers")

    sources = question.get("sources")
    count = question.get("source_count")
    if sources is not None and not isinstance(sources, list):
        errors.append(f"{label}: sources must be a list")
    if count is not None and (not isinstance(count, int) or count < 1):
        errors.append(f"{label}: source_count must be a positive integer")
    if isinstance(sources, list) and isinstance(count, int) and count != len(sources):
        warnings.append(f"{label}: source_count {count} does not match sources {len(sources)}")
    return errors, warnings


def validate_questions(data):
    errors = []
    warnings = []
    if not isinstance(data, list) or not data:
        return ["question data must be a non-empty list"], warnings, {"questions": 0, "by_type": {}, "topics": []}
    ids = set()
    topics = set()
    by_type = {}
    for position, question in enumerate(data, 1):
        question_errors, question_warnings = validate_question(question, position)
        errors.extend(question_errors)
        warnings.extend(question_warnings)
        if not isinstance(question, dict):
            continue
        qid = str(question.get("id") or "").strip()
        if qid:
            if qid in ids:
                errors.append(f"{qid}: duplicate id")
            ids.add(qid)
        topic = str(question.get("topic") or "").strip()
        if topic:
            topics.add(topic)
        question_type = normalize_type(question.get("type"))
        if question_type:
            by_type[question_type] = by_type.get(question_type, 0) + 1
    stats = {"questions": len(data), "by_type": by_type, "topics": sorted(topics)}
    return errors, warnings, stats


def load_questions_file(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".js", ".mjs"} or "window.QUIZ_DATA" in text:
        match = re.search(r"window\.QUIZ_DATA\s*=\s*(\[.*\])\s*;?", text, re.S)
        if not match:
            raise ValueError("window.QUIZ_DATA array not found")
        data = json.loads(match.group(1))
    else:
        data = json.loads(text)
    if isinstance(data, dict) and isinstance(data.get("questions"), list):
        data = data["questions"]
    if not isinstance(data, list):
        raise ValueError("expected a JSON list or an object with a questions list")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", type=Path)
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    args = parser.parse_args()

    try:
        data = load_questions_file(args.file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"invalid input: {exc}", file=sys.stderr)
        return 2

    errors, warnings, stats = validate_questions(data)
    if args.strict:
        errors = errors + [f"warning: {warning}" for warning in warnings]
    report = {
        "file": str(args.file),
        "stats": stats,
        "errors": errors,
        "warnings": warnings,
        "strict": args.strict,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        types = ", ".join(f"{key}={value}" for key, value in sorted(stats["by_type"].items()))
        print(f"questions={stats['questions']} topics={len(stats['topics'])} types={types or '-'}")
        print(f"errors={len(errors)} warnings={len(warnings)}")
        for error in errors[:30]:
            print(f"  error: {error}")
        for warning in warnings[:30]:
            print(f"  warning: {warning}")
        print("PASS" if not errors else "FAIL")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
