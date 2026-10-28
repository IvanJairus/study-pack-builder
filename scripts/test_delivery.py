#!/usr/bin/env python3
"""Regression tests for delivery gates, inventory, and abbreviation sync."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "assets" / "site-template"


class DeliveryTests(unittest.TestCase):
    def run_cli(self, *args, cwd=ROOT):
        return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, cwd=cwd, check=False)

    def test_abbreviations_are_in_sync(self):
        result = self.run_cli(ROOT / "scripts" / "build_abbreviations.py", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("up to date", result.stdout)

    def test_template_passes_strict_delivery_gate(self):
        result = self.run_cli(
            ROOT / "scripts" / "check_site.py",
            "--root", TEMPLATE,
            "--brief", TEMPLATE / "sumber" / "project-brief.json",
            "--quiz", TEMPLATE / "assets" / "quiz-data.js",
            "--min-topics", 2,
            "--strict",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_unconfirmed_brief_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = json.loads((TEMPLATE / "sumber" / "project-brief.json").read_text(encoding="utf-8"))
            brief.pop("confirmed_at", None)
            path = Path(directory) / "brief.json"
            path.write_text(json.dumps(brief), encoding="utf-8")
            result = self.run_cli(
                ROOT / "scripts" / "check_site.py",
                "--root", TEMPLATE,
                "--brief", path,
                "--quiz", TEMPLATE / "assets" / "quiz-data.js",
                "--min-topics", 2,
                "--strict",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("not confirmed", result.stdout)

    def test_inventory_roles_and_ssot(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            sources = base / "sources"
            sources.mkdir()
            (sources / "content.md").write_text("# Content\n", encoding="utf-8")
            (sources / "session.m4a").write_bytes(b"audio")
            (sources / "question-bank.pdf").write_bytes(b"pdf")
            brief = {
                "sources": "sources",
                "ignore": [],
                "ssot": ["content.md"],
                "source_roles": [{"pattern": "*.m4a", "role": "secondary"}],
            }
            brief_path = base / "brief.json"
            brief_path.write_text(json.dumps(brief), encoding="utf-8")
            out = base / "inventory.json"
            result = self.run_cli(ROOT / "scripts" / "source_inventory.py", sources, "--out", out, "--brief", brief_path, "--base", base)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["ssot"], ["sources/content.md"])
            roles = {item["path"]: item["role"] for item in data["sources"]}
            self.assertEqual(roles["sources/content.md"], "primary")
            self.assertEqual(roles["sources/session.m4a"], "secondary")
            self.assertEqual(roles["sources/question-bank.pdf"], "assessment")

    def test_confirm_brief_writes_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "brief.json"
            path.write_text(json.dumps({
                "goal": "test",
                "sources": ".",
                "output": ".",
                "language": "en",
                "exam": {"questions": 1},
                "outputs": {"website": True},
                "theme": {"mode": "light"},
            }), encoding="utf-8")
            result = self.run_cli(ROOT / "scripts" / "confirm_brief.py", path, "--by", "tester")
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["confirmed_by"], "tester")
            self.assertTrue(data["confirmed_at"])
            check = self.run_cli(ROOT / "scripts" / "confirm_brief.py", path, "--check")
            self.assertEqual(check.returncode, 0, check.stderr)


if __name__ == "__main__":
    unittest.main()
