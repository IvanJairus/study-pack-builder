#!/usr/bin/env python3
"""Regression tests for the coverage manifest and coverage gate."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "assets" / "site-template"


class CoverageTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=ROOT, check=False)

    def test_template_coverage_passes(self):
        result = self.run_cli(
            ROOT / "scripts" / "check_coverage.py",
            "--coverage", TEMPLATE / "sumber" / "coverage.json",
            "--root", TEMPLATE,
            "--quiz", TEMPLATE / "assets" / "quiz-data.js",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_missing_question_mapping_fails(self):
        data = json.loads((TEMPLATE / "sumber" / "coverage.json").read_text(encoding="utf-8"))
        data["questions"]["mapped_ids"] = data["questions"]["mapped_ids"][:-1]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = self.run_cli(
                ROOT / "scripts" / "check_coverage.py",
                "--coverage", path,
                "--root", TEMPLATE,
                "--quiz", TEMPLATE / "assets" / "quiz-data.js",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("not mapped", result.stdout)

    def test_unresolved_unit_fails(self):
        data = json.loads((TEMPLATE / "sumber" / "coverage.json").read_text(encoding="utf-8"))
        data["units"][0]["status"] = "unresolved"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = self.run_cli(
                ROOT / "scripts" / "check_coverage.py",
                "--coverage", path,
                "--root", TEMPLATE,
                "--quiz", TEMPLATE / "assets" / "quiz-data.js",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("unresolved", result.stdout)

    def test_builder_creates_a_valid_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "coverage.json"
            build = self.run_cli(
                ROOT / "scripts" / "build_coverage.py",
                "--out", path,
                "--map", TEMPLATE / "assets" / "map-data.js",
                "--quiz", TEMPLATE / "assets" / "quiz-data.js",
                "--source", "source.md",
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            check = self.run_cli(
                ROOT / "scripts" / "check_coverage.py",
                "--coverage", path,
                "--root", TEMPLATE,
                "--quiz", TEMPLATE / "assets" / "quiz-data.js",
            )
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


if __name__ == "__main__":
    unittest.main()
