"""Audit dashboard graph, packaged hashes, content routes, and script shards.

Does not replace a real-browser interaction check or a source/rights review.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urlsplit
import zipfile


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe(root, path):
    p = PurePosixPath(path)
    if not path or p.is_absolute() or '..' in p.parts or '\\' in path or ':' in path:
        raise ValueError(f'Unsafe path: {path}')
    target = root.joinpath(*p.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes root: {path}')
    return target


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls, self.active = [], []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {'href', 'src'} and value:
                self.urls.append(value)
                if re.match(r'^(javascript|vbscript):', value, re.I):
                    self.active.append(value)
            if name.lower().startswith('on'):
                self.active.append(name)
        if tag in {'script', 'iframe', 'object', 'embed', 'form'}:
            self.active.append(tag)


def audit(root, zip_path=None):
    issues = []
    try:
        catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
        manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return {'issues': [str(exc)]}
    members = set()
    for item in manifest['files']:
        path = item['path']
        if path in members:
            issues.append(f'Duplicate manifest member: {path}')
        members.add(path)
        try:
            target = safe(root, path)
            if item.get('rights') != 'allowed':
                issues.append(f'Non-allowed packaged member: {path}')
            if not target.is_file() or digest(target) != item['sha256']:
                issues.append(f'Missing file or hash mismatch: {path}')
        except ValueError as exc:
            issues.append(str(exc))
    ids = {}
    for kind, plural in [('entry', 'entries'), ('case', 'cases'), ('file', 'files')]:
        values = [r['id'] for r in catalog[plural]]
        if len(values) != len(set(values)):
            issues.append(f'Duplicate {kind} IDs')
        ids[kind] = set(values)
    entries = {e['id']:e for e in catalog['entries']}
    cases = {c['id']:c for c in catalog['cases']}
    file_paths = {f['path'] for f in catalog['files']}
    assigned = [eid for c in catalog['chapters'] for eid in c['entries']]
    if Counter(assigned) != Counter(entries.keys()):
        issues.append('Chapter-entry membership mismatch')
    for e in entries.values():
        for cid in e['cases']:
            if cid not in cases or e['id'] not in cases[cid]['owners']:
                issues.append(f'Missing case/backlink: {e["id"]} / {cid}')
    for c in cases.values():
        for eid in c['owners']:
            if eid not in entries or c['id'] not in entries[eid]['cases']:
                issues.append(f'Missing entry/backlink: {c["id"]} / {eid}')
    for f in catalog['files']:
        if f['available']:
            if f.get('url') not in members:
                issues.append(f'File not packaged: {f["path"]}')
            elif digest(safe(root, f['url'])) != f['sha256']:
                issues.append(f'Source hash mismatch: {f["path"]}')
            if f.get('preview') and f['preview'] not in members:
                issues.append(f'Missing preview script: {f["path"]}')
    expected = {'entry/'+eid for eid in entries} | {'case/'+cid for cid in cases}
    if set(catalog['content_shards']) != expected:
        issues.append('Content route inventory mismatch')
    records = {}
    internal_links = 0
    for path in set(catalog['content_shards'].values()):
        try:
            if path not in members:
                raise ValueError(f'Unmanifested content shard: {path}')
            text = safe(root, path).read_text(encoding='utf-8')
            rows = json.loads(text.removeprefix('window.BD_acceptContent(').removesuffix(');\n'))
            for row in rows:
                if row['id'] in records:
                    issues.append(f'Duplicate content record: {row["id"]}')
                records[row['id']] = row
                if catalog['content_shards'].get(row['id']) != path:
                    issues.append(f'Wrong content shard route: {row["id"]}')
                if hashlib.sha256(row['markdown'].encode()).hexdigest() != row['sha256']:
                    issues.append(f'Content hash mismatch: {row["id"]}')
                if set(row['files']) - file_paths:
                    issues.append(f'Unknown content file reference: {row["id"]}')
                parser = Links()
                parser.feed(row['html'])
                if parser.active:
                    issues.append(f'Active HTML content: {row["id"]}')
                for url in parser.urls:
                    if url.startswith('#'):
                        kind, _, key = url[1:].partition('/')
                        if kind not in ids or unquote(key) not in ids[kind]:
                            issues.append(f'Broken internal route: {row["id"]}: {url}')
                        internal_links += 1
                    elif not urlsplit(url).scheme and url not in members:
                        issues.append(f'Broken local resource: {row["id"]}: {url}')
        except (OSError, ValueError) as exc:
            issues.append(str(exc))
    if set(records) != expected:
        issues.append('Content records lost or extra')
    indexed = set()
    for path in catalog['search_shards'] + catalog['attachment_search_shards']:
        try:
            if path not in members:
                raise ValueError(f'Unmanifested search shard: {path}')
            text = safe(root, path).read_text(encoding='utf-8')
            for row in json.loads(text.removeprefix('window.BD_acceptSearch(').removesuffix(');\n')):
                kind, _, key = row['id'].partition('/')
                if row['id'] in indexed or kind not in ids or key not in ids[kind]:
                    issues.append(f'Invalid/duplicate search record: {row["id"]}')
                indexed.add(row['id'])
        except (OSError, ValueError) as exc:
            issues.append(str(exc))
    if expected - indexed:
        issues.append(f'{len(expected - indexed)} entries/cases absent from search index')
    if zip_path:
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            if set(names) != members | {'manifest.json'} or len(names) != len(set(names)):
                issues.append('ZIP membership mismatch')
            if archive.testzip():
                issues.append('ZIP CRC error')
    return {'chapters': len(catalog['chapters']), 'entries': len(entries), 'cases':len(cases),
            'content_records':len(records), 'search_records':len(indexed), 'internal_links':internal_links,
            'packaged_members':len(members), 'issues':issues}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--zip', type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    report = audit(args.root, args.zip)
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    print(text)
    return bool(report['issues'])


if __name__ == '__main__':
    raise SystemExit(main())
