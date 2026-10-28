#!/usr/bin/env python3
"""Cluster duplicate questions and choose one canonical wording per cluster.

Input: JSON list of questions, or an object with a "questions" list.
Each question needs at least: id, stem. Recommended: options, answer, topic, source.

Usage:
  python dedup_questions.py working/questions.json --out working/clusters.json
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

from quiz_schema import normalize_type


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(
        r"\b(the|a|an|and|or|of|to|in|on|for|with|is|are|was|were|be|by|from|that|this|it|as|at)\b",
        " ",
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def similarity(left: str, right: str) -> float:
    left, right = normalize(left), normalize(right)
    if not left or not right:
        return 0.0
    return difflib.SequenceMatcher(None, left, right).ratio()


def load_questions(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    questions = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(questions, list):
        raise ValueError("Expected a JSON list or an object with a questions list")
    for index, question in enumerate(questions, 1):
        stem = question.get("stem") or question.get("question")
        if not stem:
            raise ValueError(f"Question {index} has no stem or question")
        question["stem"] = stem
        if normalize_type(question.get("type")) is None:
            raise ValueError(f"Question {index} has an unknown type: {question.get('type')!r}")
        question.setdefault("id", f"Q{index:03d}")
    return questions


def question_type(question):
    return normalize_type(question.get("type")) or "single_choice"


def canonical_score(question):
    option_text = " ".join(str(value) for value in question.get("options", {}).values())
    accepted = question.get("accepted_answers")
    accepted_text = " ".join(str(value) for value in accepted) if isinstance(accepted, list) else ""
    return (len(question.get("stem", "")) + len(option_text) + len(accepted_text), len(question.get("options", {})))


def answer_signature(question):
    if question_type(question) == "short_answer":
        accepted = question.get("accepted_answers")
        values = accepted if isinstance(accepted, list) else []
        return tuple(sorted(str(value).strip().lower() for value in values))
    answer = question.get("answer")
    if isinstance(answer, list):
        return tuple(sorted(str(value) for value in answer))
    if isinstance(answer, dict):
        return json.dumps(answer, sort_keys=True)
    return answer


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("questions", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--threshold", type=float, default=0.82)
    ap.add_argument("--merge-threshold", type=float, default=0.86)
    args = ap.parse_args()

    try:
        questions = load_questions(args.questions)
    except Exception as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 2

    clusters = []
    for question in questions:
        placed = False
        for cluster in clusters:
            if question_type(question) != question_type(cluster[0]):
                continue
            if similarity(question["stem"], cluster[0]["stem"]) >= args.threshold:
                cluster.append(question)
                placed = True
                break
        if not placed:
            clusters.append([question])

    merged = True
    while merged:
        merged = False
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                if question_type(clusters[i][0]) != question_type(clusters[j][0]):
                    continue
                if any(
                    similarity(a["stem"], b["stem"]) >= args.merge_threshold
                    for a in clusters[i]
                    for b in clusters[j]
                ):
                    clusters[i].extend(clusters[j])
                    del clusters[j]
                    merged = True
                    break
            if merged:
                break

    output = []
    for cluster in sorted(clusters, key=lambda c: (-len(c), c[0]["id"])):
        canonical = max(cluster, key=canonical_score)
        signatures = {answer_signature(member) for member in cluster if "answer" in member or "accepted_answers" in member}
        entry = {
            "canonical": canonical,
            "members": [member["id"] for member in cluster],
            "frequency": len({member.get("source", member["id"].split("-")[0]) for member in cluster}),
            "size": len(cluster),
            "type": question_type(canonical),
            "answer_conflict": len(signatures) > 1,
        }
        if len(signatures) > 1:
            entry["answers"] = [list(signature) if isinstance(signature, tuple) else signature for signature in signatures]
        output.append(entry)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"clusters": output, "raw_count": len(questions), "unique_count": len(output)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"raw={len(questions)} unique={len(output)}")
    conflicts = [entry["canonical"]["id"] for entry in output if entry.get("answer_conflict")]
    if conflicts:
        print(f"answer_conflicts={conflicts}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
