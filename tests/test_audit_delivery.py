"""Behavioral checks using synthetic metadata, with no benchmark content."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "benchmark-research/scripts/audit_delivery.py"
SPEC = importlib.util.spec_from_file_location("audit_delivery", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class AuditDeliveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.md = self.root / "books/chapters/A1.md"
        self.md.parent.mkdir(parents=True)
        self.md.write_text(
            "# A1\n\n"
            "| Benchmark | 具体数据例子 | 数据分类 | 题目类型 | 模型需要做到 |\n"
            "|---|---|---|---|---|\n"
            "| Example benchmark | source row | task A | choice | choose |\n\n"
            "### A1-001 Example benchmark\n\nSource: synthetic metadata only.\n",
            encoding="utf-8",
        )
        self.pdf = self.root / "pdf/chapters/A1.pdf"
        self.pdf.parent.mkdir(parents=True)
        self.pdf.write_bytes(b"synthetic placeholder; PDF opening disabled in this test")
        write_json(self.root / "inventory.json", {"chapters": [{
            "id": "A1", "title": "A1", "markdown": "books/chapters/A1.md",
            "pdf": "pdf/chapters/A1.pdf", "entries": [{"id": "A1-001", "name": "Example benchmark"}],
        }]})
        write_json(self.root / "audit/entries.json", {"entries": [{
            "id": "A1-001", "chapter": "A1", "name": "Example benchmark",
            "kind": "dataset", "status": "verified",
            "category_coverage": {"covered": ["task A"], "missing": []},
            "cases": [{"source_url": "https://example.org/pinned", "release": "rev1",
                       "split": "test", "record_locator": "row 0",
                       "source_sha256": "a" * 64, "rights": "metadata_only"}],
            "gaps": [],
        }]})
        paths = ["inventory.json", "audit/entries.json", "books/chapters/A1.md", "pdf/chapters/A1.pdf"]
        write_json(self.root / "delivery/manifest.json", {"files": [
            {"path": path, "sha256": hashlib.sha256((self.root / path).read_bytes()).hexdigest(), "rights": "allowed"}
            for path in paths
        ]})

    def test_complete_structure_passes(self) -> None:
        report = MODULE.audit(self.root, check_pdf=False)
        self.assertEqual(report["issues"], [])
        self.assertEqual((report["chapter_count"], report["entry_count"]), (1, 1))

    def test_modified_chapter_fails_hash_and_overview(self) -> None:
        self.md.write_text("# A1\n### A1-001 Example benchmark\n", encoding="utf-8")
        issues = MODULE.audit(self.root, check_pdf=False)["issues"]
        self.assertTrue(any("hash mismatch" in item for item in issues))
        self.assertTrue(any("five-column overview" in item for item in issues))

    def test_uncovered_verified_category_fails(self) -> None:
        path = self.root / "audit/entries.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["entries"][0]["category_coverage"]["missing"].append("task B")
        write_json(path, data)
        issues = MODULE.audit(self.root, check_pdf=False)["issues"]
        self.assertTrue(any("verified with uncovered" in item for item in issues))


if __name__ == "__main__":
    unittest.main()
