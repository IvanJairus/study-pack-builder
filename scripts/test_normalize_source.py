#!/usr/bin/env python3
"""Regression tests for mixed-format normalization."""
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import normalize_source

ROOT = Path(__file__).resolve().parent.parent


DOCX_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Bagian Satu</w:t></w:r></w:p>
<w:p><w:r><w:t>Paragraf dari DOCX tentang modal.</w:t></w:r></w:p>
<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Komponen</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Nilai</w:t></w:r></w:p></w:tc></w:tr>
<w:tr><w:tc><w:p><w:r><w:t>CET1</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>4.5 persen</w:t></w:r></w:p></w:tc></w:tr></w:tbl>
</w:body></w:document>"""


def build_docx(path):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", DOCX_XML)


def build_xlsx(path):
    shared = """<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<si><t>Pertanyaan</t></si><si><t>Jawaban</t></si><si><t>Apa itu LDR?</t></si><si><t>Loan to deposit ratio</t></si></sst>"""
    workbook = """<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Likuiditas" sheetId="1" r:id="rId1"/></sheets></workbook>"""
    relationships = """<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="worksheet" Target="worksheets/sheet1.xml"/></Relationships>"""
    sheet = """<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>
<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row>
<row r="2"><c r="A2" t="s"><v>2</v></c><c r="B2" t="s"><v>3</v></c></row>
<row r="4"><c r="A4" t="inlineStr"><is><t>Apa itu NSFR?</t></is></c><c r="B4" t="inlineStr"><is><t>Net stable funding ratio</t></is></c></row>
</sheetData></worksheet>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", relationships)
        archive.writestr("xl/sharedStrings.xml", shared)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)


def build_epub(path):
    container = """<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>"""
    opf = """<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf"><manifest><item id="c1" href="chapter1.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/></spine></package>"""
    chapter = """<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml"><head><title>Bab Operasional</title></head><body><h1>Risiko Operasional</h1><p>Kejadian dicatat.</p></body></html>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", opf)
        archive.writestr("OEBPS/chapter1.xhtml", chapter)


class NormalizeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.sources = self.root / "sources"
        self.sources.mkdir()
        (self.sources / "notes.txt").write_text("Paragraf pertama.\n\nParagraf kedua.\n", encoding="utf-8")
        (self.sources / "summary.md").write_text(
            "# Konsep\n\nLikuiditas penting.\n\n| Tahap | Keluaran |\n|---|---|\n| Ukur | LCR |\n\n```text\nLCR = HQLA / NCO\nNSFR = ASF / RSF\n```\n",
            encoding="utf-8",
        )
        (self.sources / "page.html").write_text(
            "<html><head><title>Materi</title></head><body><nav>Menu</nav><h1>Pasar</h1><p>VaR mengukur kerugian.</p><table><tr><th>Istilah</th><th>Arti</th></tr><tr><td>VaR</td><td>Value at Risk</td></tr></table><script>ignore()</script></body></html>",
            encoding="utf-8",
        )
        (self.sources / "bank.csv").write_text("Pertanyaan,Jawaban\nApa itu LCR?,Rasio\nApa itu NSFR?,Rasio\n", encoding="utf-8")
        build_docx(self.sources / "materi.docx")
        build_xlsx(self.sources / "bank.xlsx")
        build_epub(self.sources / "buku.epub")
        self.out = self.root / "out" / "normalized.jsonl"

    def tearDown(self):
        self.directory.cleanup()

    def run_cli(self, *extra):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "normalize_source.py"), str(self.sources), "--out", str(self.out), *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def records(self):
        return [json.loads(line) for line in self.out.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_all_formats_and_anchors(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        records = self.records()
        formats = {record["format"] for record in records}
        self.assertEqual(formats, {"txt", "md", "html", "csv", "docx", "xlsx", "epub"})
        refs = {record["ref"] for record in records}
        self.assertIn("Likuiditas!row:4", refs)
        self.assertIn("row:2", refs)
        self.assertIn("paragraph:2", refs)
        self.assertIn("chapter:1!line:1", refs)
        texts = [record["text"] for record in records]
        self.assertFalse(any("Menu" in text for text in texts))
        self.assertTrue(any(text.startswith("Komponen: CET1") for text in texts))
        self.assertTrue(any(record["section"] == "Likuiditas" for record in records))
        self.assertTrue(any(record["format"] == "epub" for record in records))
        self.assertTrue(any(record["unit"] == "code" and "\n" in record["text"] for record in records))
        table_rows = [record for record in records if record["format"] == "md" and record["unit"] == "row"]
        self.assertEqual(len(table_rows), 1)
        self.assertIn("Tahap: Ukur", table_rows[0]["text"])

    def test_summary_is_written(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads((self.out.with_suffix(".summary.json")).read_text(encoding="utf-8"))
        self.assertEqual(summary["totals"]["errors"], 0)
        self.assertEqual(summary["totals"]["files"], 7)
        self.assertGreater(summary["totals"]["records"], 10)

    def test_long_blocks_are_split(self):
        result = self.run_cli("--max-chars", "25")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any("!part:2" in record["ref"] for record in self.records()))

    def test_rejects_xml_entities(self):
        with self.assertRaises(normalize_source.AdapterError):
            normalize_source.safe_xml(b'<!DOCTYPE x [<!ENTITY y "z">]><root/>')


if __name__ == "__main__":
    unittest.main()
