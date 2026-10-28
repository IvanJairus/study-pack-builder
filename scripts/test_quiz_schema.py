#!/usr/bin/env python3
"""Regression tests for the flexible question schema and type-aware dedup."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import quiz_schema

ROOT = Path(__file__).resolve().parent.parent


def base_question(**overrides):
    question = {
        "id": "Q1",
        "type": "single_choice",
        "topic": "Foundation",
        "question": "What is an SLO?",
        "options": {"A": "A target", "B": "A contract"},
        "answer": "A",
        "explanation": "SLO is a target.",
        "trap": "SLO is not an SLA.",
    }
    question.update(overrides)
    return question


class SchemaTests(unittest.TestCase):
    def test_single_choice_with_two_options(self):
        errors, warnings, stats = quiz_schema.validate_questions([base_question()])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertEqual(stats["by_type"]["single_choice"], 1)

    def test_multiple_choice_with_five_options(self):
        question = base_question(
            type="multiple_choice",
            options={key: f"Option {key}" for key in "ABCDE"},
            answer=["A", "C"],
        )
        errors, warnings, _ = quiz_schema.validate_questions([question])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_true_false_uses_boolean(self):
        question = base_question(type="true_false", answer=True)
        question.pop("options")
        errors, warnings, _ = quiz_schema.validate_questions([question])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_short_answer_accepts_variants(self):
        question = base_question(
            type="short_answer",
            accepted_answers=["mean time to recovery", "MTTR"],
        )
        question.pop("options")
        question.pop("answer")
        errors, warnings, _ = quiz_schema.validate_questions([question])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        self.assertTrue(quiz_schema.answer_matches(question, "M.T.T.R."))
        self.assertTrue(quiz_schema.answer_matches(question, "Mean Time To Recovery"))
        self.assertFalse(quiz_schema.answer_matches(question, "mean time between failures"))

    def test_rejects_one_option(self):
        question = base_question(options={"A": "Only"})
        errors, _, _ = quiz_schema.validate_questions([question])
        self.assertTrue(any("at least 2 options" in error for error in errors))

    def test_rejects_answer_outside_options(self):
        question = base_question(answer="C")
        errors, _, _ = quiz_schema.validate_questions([question])
        self.assertTrue(any("answer must be one option key" in error for error in errors))

    def test_rejects_multiple_choice_with_one_key(self):
        question = base_question(type="multiple_choice", answer=["A"])
        errors, _, _ = quiz_schema.validate_questions([question])
        self.assertTrue(any("at least 2 keys" in error for error in errors))

    def test_rejects_short_answer_without_variants(self):
        question = base_question(type="short_answer", accepted_answers=[])
        question.pop("options")
        question.pop("answer")
        errors, _, _ = quiz_schema.validate_questions([question])
        self.assertTrue(any("accepted_answers" in error for error in errors))

    def test_short_answer_with_answer_but_no_variants_does_not_crash(self):
        question = base_question(type="short_answer", answer="MTTR")
        question.pop("options")
        question.pop("accepted_answers", None)
        errors, _, _ = quiz_schema.validate_questions([question])
        self.assertTrue(any("accepted_answers" in error for error in errors))

    def test_dedup_is_type_aware_and_flags_answer_conflict(self):
        raw = [
            base_question(id="A1", source="set1"),
            base_question(id="A2", source="set2", type="multiple_choice", answer=["A", "B"]),
            base_question(id="A3", source="set1", answer="B"),
            base_question(id="A4", source="set2", answer="A"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "raw.json"
            output = Path(directory) / "clusters.json"
            source.write_text(json.dumps(raw), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "dedup_questions.py"), str(source), "--out", str(output)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            clusters = json.loads(output.read_text(encoding="utf-8"))["clusters"]
            self.assertEqual(len(clusters), 2)
            conflict = next(entry for entry in clusters if entry["type"] == "single_choice")
            self.assertTrue(conflict["answer_conflict"])


if __name__ == "__main__":
    unittest.main()
