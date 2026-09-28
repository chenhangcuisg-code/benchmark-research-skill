#!/usr/bin/env python3
"""Check the structural contract of a benchmark research handbook.

This deliberately cannot verify source identity, factual accuracy, rights, or page design.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

HEADER = "| Benchmark | 具体数据例子 | 数据分类 | 题目类型 | 模型需要做到 |"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ENTRY_HEADING = re.compile(r"^###\s+([A-Za-z0-9]+-[0-9]+)\s+(.+)$", re.M)
KINDS = {"dataset", "suite", "protocol", "metric", "tool", "proposal"}
STATUSES = {"verified", "partial", "restricted", "unavailable", "not_applicable"}
RIGHTS = {"allowed", "metadata_only", "private", "unknown"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_path(root: Path, value: str) -> Path:
    posix = PurePosixPath(value)
    if not value or posix.is_absolute() or ".." in posix.parts or "\\" in value:
        raise ValueError(f"unsafe relative path: {value!r}")
    target = root.joinpath(*posix.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"path resolves outside output root: {value!r}")
    return target


def overview_rows(markdown: str) -> int:
    lines = markdown.splitlines()
    try:
        index = next(i for i, line in enumerate(lines) if line.strip() == HEADER)
    except StopIteration:
        return -1
    if index + 1 >= len(lines) or not re.fullmatch(r"\|[\s:|-]+\|", lines[index + 1].strip()):
        return -1
    rows = 0
    for line in lines[index + 2 :]:
        if not line.strip().startswith("|"):
            break
        if line.count("|") != 6:
            return -1
        rows += 1
    return rows


def audit(root: Path, check_pdf: bool) -> dict:
    issues: list[str] = []
    try:
        inventory = read_json(root / "inventory.json")["chapters"]
        entries = read_json(root / "audit/entries.json")["entries"]
        manifest = read_json(root / "delivery/manifest.json")["files"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return {"chapter_count": 0, "entry_count": 0, "status_counts": {}, "issues": [f"required JSON: {exc}"]}

    if not isinstance(inventory, list) or not isinstance(entries, list) or not isinstance(manifest, list):
        return {"chapter_count": 0, "entry_count": 0, "status_counts": {}, "issues": ["chapters, entries and files must be lists"]}

    public_paths: set[str] = set()
    for file in manifest:
        if not isinstance(file, dict):
            issues.append("manifest file item is not an object")
            continue
        path, sha = file.get("path"), file.get("sha256")
        if not isinstance(path, str):
            issues.append("manifest file path missing")
            continue
        if path in public_paths:
            issues.append(f"duplicate manifest path: {path}")
        public_paths.add(path)
        if file.get("rights") != "allowed":
            issues.append(f"non-redistributable manifest item: {path}")
        if not isinstance(sha, str) or not SHA256.fullmatch(sha):
            issues.append(f"invalid manifest SHA-256: {path}")
        try:
            target = safe_path(root, path)
            if not target.is_file():
                issues.append(f"missing manifest file: {path}")
            elif isinstance(sha, str) and SHA256.fullmatch(sha) and digest(target) != sha:
                issues.append(f"manifest hash mismatch: {path}")
        except ValueError as exc:
            issues.append(str(exc))

    for required in ("inventory.json", "audit/entries.json"):
        if required not in public_paths:
            issues.append(f"required ledger absent from manifest: {required}")

    entry_by_id: dict[str, dict] = {}
    status_counts: Counter[str] = Counter()
    for entry in entries:
        if not isinstance(entry, dict):
            issues.append("entry audit item is not an object")
            continue
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            issues.append("entry without ID")
            continue
        if entry_id in entry_by_id:
            issues.append(f"duplicate entry audit ID: {entry_id}")
        entry_by_id[entry_id] = entry
        kind, status = entry.get("kind"), entry.get("status")
        if kind not in KINDS:
            issues.append(f"{entry_id}: invalid kind {kind!r}")
        if status not in STATUSES:
            issues.append(f"{entry_id}: invalid status {status!r}")
        else:
            status_counts[status] += 1
        cases = entry.get("cases", [])
        coverage = entry.get("category_coverage", {})
        if not isinstance(cases, list) or not isinstance(coverage, dict):
            issues.append(f"{entry_id}: cases/coverage must be list/object")
            continue
        covered, missing = coverage.get("covered"), coverage.get("missing")
        if not isinstance(covered, list) or not isinstance(missing, list):
            issues.append(f"{entry_id}: covered/missing category lists required")
        if status in {"verified", "partial"} and kind in {"dataset", "suite"} and not cases:
            issues.append(f"{entry_id}: {status} dataset/suite has no original case locator")
        if status == "verified" and kind in {"dataset", "suite"} and isinstance(missing, list) and missing:
            issues.append(f"{entry_id}: verified with uncovered principal categories")
        if status == "not_applicable" and kind in {"dataset", "suite"}:
            issues.append(f"{entry_id}: dataset/suite cannot be not_applicable")
        if status in {"partial", "restricted", "unavailable"} and not entry.get("gaps"):
            issues.append(f"{entry_id}: unresolved status without explicit gaps")
        for i, case in enumerate(cases):
            if not isinstance(case, dict):
                issues.append(f"{entry_id} case {i}: not an object")
                continue
            for field in ("source_url", "release", "split", "record_locator"):
                if not isinstance(case.get(field), str) or not case[field].strip():
                    issues.append(f"{entry_id} case {i}: missing {field}")
            if not isinstance(case.get("source_sha256"), str) or not SHA256.fullmatch(case["source_sha256"]):
                issues.append(f"{entry_id} case {i}: invalid source SHA-256")
            if case.get("rights") not in RIGHTS:
                issues.append(f"{entry_id} case {i}: invalid rights")

    chapter_ids: set[str] = set()
    inventory_ids: set[str] = set()
    pdf_reader = None
    if check_pdf:
        try:
            from pypdf import PdfReader

            pdf_reader = PdfReader
        except ImportError:
            issues.append("--check-pdf requires pypdf (python -m pip install pypdf)")
    chapter_pages: dict[str, int] = {}
    for chapter in inventory:
        if not isinstance(chapter, dict):
            issues.append("chapter item is not an object")
            continue
        code = chapter.get("id")
        if not isinstance(code, str) or not code:
            issues.append("chapter without ID")
            continue
        if code in chapter_ids:
            issues.append(f"duplicate chapter ID: {code}")
        chapter_ids.add(code)
        chapter_entries = chapter.get("entries", [])
        if not isinstance(chapter_entries, list):
            issues.append(f"{code}: entries must be a list")
            continue
        expected: dict[str, str] = {}
        for item in chapter_entries:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("name"), str):
                issues.append(f"{code}: malformed inventory entry")
                continue
            entry_id, name = item["id"], item["name"]
            if entry_id in inventory_ids:
                issues.append(f"duplicate inventory entry ID: {entry_id}")
            inventory_ids.add(entry_id)
            expected[entry_id] = name
            audit_entry = entry_by_id.get(entry_id)
            if audit_entry is None:
                issues.append(f"{entry_id}: absent from entry audit")
            elif audit_entry.get("chapter") != code or audit_entry.get("name") != name:
                issues.append(f"{entry_id}: chapter/name differs between inventory and audit")
        for key in ("markdown", "pdf"):
            path = chapter.get(key)
            if not isinstance(path, str):
                issues.append(f"{code}: missing {key} path")
                continue
            if path not in public_paths:
                issues.append(f"{code}: {key} absent from public manifest: {path}")
            try:
                target = safe_path(root, path)
            except ValueError as exc:
                issues.append(str(exc))
                continue
            if not target.is_file():
                issues.append(f"{code}: missing {key}: {path}")
                continue
            if key == "markdown":
                body = target.read_text(encoding="utf-8")
                rows = overview_rows(body)
                if rows != len(expected):
                    issues.append(f"{code}: five-column overview has {rows} rows; expected {len(expected)}")
                headings = ENTRY_HEADING.findall(body)
                heading_ids = [entry_id for entry_id, _ in headings]
                for entry_id, name in expected.items():
                    if heading_ids.count(entry_id) != 1:
                        issues.append(f"{code}: expected one detailed heading for {entry_id}")
                    elif next(hname for hid, hname in headings if hid == entry_id) != name:
                        issues.append(f"{code}: heading name differs for {entry_id}")
                for extra in set(heading_ids) - set(expected):
                    issues.append(f"{code}: heading {extra} absent from inventory")
            elif pdf_reader is not None:
                try:
                    reader = pdf_reader(str(target))
                    chapter_pages[code] = len(reader.pages)
                    if not reader.pages:
                        issues.append(f"{code}: empty PDF")
                except Exception as exc:
                    issues.append(f"{code}: PDF cannot be read: {exc}")

    for extra in set(entry_by_id) - inventory_ids:
        issues.append(f"entry audit ID absent from inventory: {extra}")
    return {
        "chapter_count": len(chapter_ids),
        "entry_count": len(inventory_ids),
        "status_counts": dict(sorted(status_counts.items())),
        "pdf_pages": chapter_pages,
        "issues": sorted(set(issues)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="handbook output root")
    parser.add_argument("--check-pdf", action="store_true", help="open every chapter PDF with pypdf")
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    args = parser.parse_args()
    result = audit(args.root, args.check_pdf)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)
    return 1 if result["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
