"""Build a static, offline benchmark reader from normalized research records.

Requires Markdown and beautifulsoup4 at build time. The delivered reader uses
only local HTML/CSS/JavaScript and works under both file:// and static hosting.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
from urllib.parse import unquote, urlsplit
import zipfile

import markdown
from bs4 import BeautifulSoup

SOURCE_PATH = re.compile(r'(?<![\w/])(?:sources|assets|audit)[/\\][^\s`"\'<>|，；。\[\]{}()]+')
TEXT_EXTS = {'.json', '.jsonl', '.txt', '.csv', '.tsv', '.md', '.py', '.yaml', '.yml', '.lean'}
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}
SAFE_TAGS = {'p', 'br', 'hr', 'strong', 'em', 'b', 'i', 's', 'del', 'sub', 'sup', 'blockquote',
             'ul', 'ol', 'li', 'pre', 'code', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
             'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'img'}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_path(root, value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError(f'Invalid relative path: {value!r}')
    p = PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError(f'Path outside delivery: {value!r}')
    target = root.joinpath(*p.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Path resolves outside delivery: {value!r}')
    return target


def json_text(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


class Builder:
    def __init__(self, root, out, allowed):
        self.root, self.out, self.allowed = root.resolve(), out.resolve(), allowed
        self.files = {}
        self.generated = set()
        self.missing = set()
        self.search_attachment_bytes = 0

    def write(self, path, value):
        target = safe_path(self.out, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding='utf-8')
        self.generated.add(path)

    def resource(self, path):
        path = path.replace('\\', '/').strip().rstrip('。；，')
        if path in self.files:
            return self.files[path]
        try:
            target = safe_path(self.root, path)
        except ValueError:
            return None
        info = {'id': hashlib.sha256(path.encode()).hexdigest()[:20], 'path': path,
                'available': False, 'reason': '原交付清单未允许随包；保留来源定位'}
        self.files[path] = info
        if path not in self.allowed:
            return info
        entry = self.allowed[path]
        if entry.get('rights', 'allowed') != 'allowed':
            return info
        if not target.is_file():
            self.missing.add(path)
            info['reason'] = '原交付清单列有此文件，但本地文件缺失'
            return info
        digest = sha(target)
        if digest != entry['sha256']:
            raise ValueError(f'Approved file changed since manifest: {path}')
        dest = f'files/{digest}{target.suffix.lower()}'
        output = safe_path(self.out, dest)
        output.parent.mkdir(parents=True, exist_ok=True)
        if not output.exists() or output.stat().st_size != target.stat().st_size or sha(output) != digest:
            shutil.copyfile(target, output)
        self.generated.add(dest)
        info.update(available=True, reason=entry.get('reason', 'allowed'), sha256=digest,
                    size=target.stat().st_size, url=dest, kind=target.suffix.lower()[1:])
        # Classic-script loading works when an offline browser forbids fetch(file://).
        # Large files keep a direct download; no preview claims they are truncated originals.
        if target.suffix.lower() in TEXT_EXTS and target.stat().st_size <= 16 * 1024 * 1024:
            try:
                # Keep BOM and CRLF exactly; the reader can download these bytes
                # from a Blob when file:// browsers ignore the download attribute.
                content = target.read_bytes().decode('utf-8')
            except UnicodeError:
                return info
            info['preview'] = f'data/files/{info["id"]}.js'
            self.write(info['preview'], f'window.BD_FILES[{json_text(info["id"])}]={json_text(content)};\n')
        return info

    def path_from_url(self, url, source_path):
        url = unquote(url).replace('\\', '/')
        if url.startswith(('sources/', 'assets/', 'audit/', 'pdf/', 'books/')):
            return url.split('#')[0]
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path:
            return None
        base = self.root / Path(source_path).parent
        target = (base / parsed.path).resolve()
        if target.is_relative_to(self.root):
            return target.relative_to(self.root).as_posix()
        return None

    def render(self, body, source_path, case_routes):
        soup = BeautifulSoup(markdown.markdown(body, extensions=['tables', 'fenced_code', 'sane_lists']), 'html.parser')
        refs = set()
        # Remove active content and attributes from both raw HTML and Markdown URLs.
        for tag in list(soup.find_all(True)):
            if tag.name is None:
                continue
            if tag.name in {'script', 'style', 'iframe', 'object', 'embed', 'form', 'input', 'button', 'svg'}:
                tag.decompose()
                continue
            if tag.name not in SAFE_TAGS:
                tag.unwrap()
                continue
            attrs = dict(tag.attrs)
            tag.attrs = {}
            if tag.name == 'code' and attrs.get('class'):
                tag['class'] = [c for c in attrs['class'] if c.startswith('language-')]
            if tag.name == 'a':
                url = attrs.get('href', '')
                if url.startswith('#case/'):
                    tag['href'] = url
                elif url.startswith('#') and url[1:].lower() in case_routes:
                    tag['href'] = '#case/' + case_routes[url[1:].lower()]
                elif re.match(r'^https?://', url, re.I):
                    tag['href'], tag['target'], tag['rel'] = url, '_blank', 'noopener noreferrer'
                else:
                    path = self.path_from_url(url, source_path)
                    if path:
                        info = self.resource(path)
                        if info:
                            refs.add(path)
                            tag['href'] = '#file/' + info['id']
                            tag['class'] = 'file-link'
            elif tag.name == 'img':
                url = attrs.get('src', '')
                path = self.path_from_url(url, source_path)
                info = self.resource(path) if path else None
                if info:
                    refs.add(path)
                if info and info['available'] and Path(path).suffix.lower() in IMAGE_EXTS:
                    tag['src'], tag['alt'], tag['loading'] = info['url'], attrs.get('alt', '原始附件'), 'lazy'
                else:
                    label = soup.new_tag('span')
                    label.string = f'图片来源：{url}（本包未收录）'
                    tag.replace_with(label)
        for tag in list(soup.find_all('code')):
            if tag.find_parent('pre'):
                continue
            path = tag.get_text().replace('\\', '/')
            if re.match(r'^(sources|assets|audit)/', path):
                info = self.resource(path)
                if info:
                    refs.add(path)
                    anchor = soup.new_tag('a', href='#file/' + info['id'])
                    anchor['class'] = 'file-link'
                    tag.wrap(anchor)
        for match in SOURCE_PATH.finditer(body):
            path = match[0].replace('\\', '/').rstrip('.,;:')
            info = self.resource(path)
            if info:
                refs.add(path)
        # Literal case identifiers in B8–B14 become working links too.
        for tag in list(soup.find_all('code')):
            if tag.find_parent(['pre', 'a']):
                continue
            cid = case_routes.get(tag.get_text().lower())
            if cid:
                tag.wrap(soup.new_tag('a', href='#case/' + cid))
        plain = soup.get_text(' ', strip=True)
        return str(soup), plain, sorted(refs)

    def shards(self, records, prefix, callback, limit=900_000):
        mapping, paths, batch, size = {}, [], [], 0
        def flush():
            nonlocal batch, size
            if not batch:
                return
            path = f'data/{prefix}-{len(paths):03d}.js'
            paths.append(path)
            self.write(path, f'{callback}({json_text(batch)});\n')
            for record in batch:
                mapping[record['id']] = path
            batch, size = [], 0
        for record in records:
            n = len(json_text(record).encode('utf-8'))
            if size + n > limit:
                flush()
            batch.append(record)
            size += n
        flush()
        return mapping, paths


def validate_project(data):
    entry_ids = [e['id'] for e in data['entries']]
    case_ids = [e['id'] for e in data['cases']]
    chapter_ids = [c['id'] for c in data['chapters']]
    for label, ids in [('entry', entry_ids), ('case', case_ids), ('chapter', chapter_ids)]:
        if len(ids) != len(set(ids)):
            raise ValueError(f'Duplicate {label} IDs')
        if any(not re.fullmatch(r'[A-Za-z0-9_-]+', x) for x in ids):
            raise ValueError(f'Unsafe {label} ID')
    assigned = [eid for c in data['chapters'] for eid in c['entries']]
    if Counter(assigned) != Counter(entry_ids):
        raise ValueError('Chapter membership differs from entry inventory')
    case_map = {c['id']: c for c in data['cases']}
    for e in data['entries']:
        if e['chapter'] not in chapter_ids:
            raise ValueError(f'Unknown chapter for {e["id"]}')
        for cid in e['cases']:
            if cid not in case_map or e['id'] not in case_map[cid]['owners']:
                raise ValueError(f'Missing case or backlink: {e["id"]} / {cid}')
    for c in data['cases']:
        if not c['owners'] or set(c['owners']) - set(entry_ids):
            raise ValueError(f'Orphan or invalid case owners: {c["id"]}')


def build(data, root, output, allowed, template, zip_path=None):
    validate_project(data)
    root, output = Path(root).resolve(), Path(output).resolve()
    if root == output or not output.is_relative_to(root):
        raise ValueError('Output must be a dedicated subdirectory of the source root')
    output.mkdir(parents=True, exist_ok=True)
    b = Builder(root, output, allowed)
    routes = {c['id'].lower(): c['id'] for c in data['cases']}
    entry_map = {e['id']: e for e in data['entries']}
    details, search, entries, cases = [], [], [], []
    for chapter in data['chapters']:
        for key in ['pdf', 'markdown']:
            if chapter.get(key):
                b.resource(chapter[key])
    for kind, rows in [('entry', data['entries']), ('case', data['cases'])]:
        for index, item in enumerate(rows):
            source_md = item.get('source_markdown') or entry_map[item['owners'][0]]['source_markdown']
            rendered, plain, refs = b.render(item['markdown'], source_md, routes)
            if item.get('source_audit'):
                b.resource(item['source_audit'])
            detail = {'id': kind + '/' + item['id'], 'html': rendered, 'files': refs,
                      'markdown': item['markdown'], 'sha256': hashlib.sha256(item['markdown'].encode()).hexdigest()}
            details.append(detail)
            meta = {k:v for k,v in item.items() if k != 'markdown'}
            meta['files'] = refs
            (entries if kind == 'entry' else cases).append(meta)
            search.append({'id': detail['id'], 'text': plain})
            if index % 500 == 0:
                print(f'Render {kind}: {index + 1}/{len(rows)}', flush=True)
    detail_map, detail_shards = b.shards(details, 'content', 'window.BD_acceptContent')
    search_map, search_shards = b.shards(search, 'search', 'window.BD_acceptSearch', limit=1_200_000)
    # Complete selected-record attachments form their own searchable records,
    # with resource backlinks. Full corpus/cache snapshots are not search inputs.
    attachment_search = []
    for path, info in b.files.items():
        if info['available'] and info.get('preview') and any(x in path for x in ['case_attachments/', 'upper_selected/', '/attachment_']):
            content = safe_path(root, path).read_text(encoding='utf-8-sig')
            attachment_search.append({'id': 'file/' + info['id'], 'text': content})
            b.search_attachment_bytes += len(content.encode())
    _, attachment_shards = b.shards(attachment_search, 'attachments-search', 'window.BD_acceptSearch', limit=1_200_000)
    catalog = {k:v for k,v in data.items() if k not in {'entries', 'cases', 'diagnostics'}}
    catalog.update(entries=entries, cases=cases, files=list(b.files.values()), content_shards=detail_map,
                   search_shards=search_shards, attachment_search_shards=attachment_shards,
                   generated_at=datetime.now(timezone.utc).isoformat(),
                   search_scope='条目正文、原题章节，以及已允许随包的完整选中记录附件；不索引全量语料缓存。')
    b.write('data/catalog.js', 'window.BD_CATALOG=' + json_text(catalog) + ';\n')
    b.write('catalog.json', json.dumps(catalog, ensure_ascii=False, indent=2))
    for name in ['index.html', 'app.css', 'app.js']:
        b.write(name, (Path(template) / name).read_text(encoding='utf-8'))
    b.write('README.txt', '预训练评测研究看板\n\n解压完整 ZIP 后，用浏览器打开 index.html。搜索、筛选、收藏、比较、案例和附件预览均可离线使用。\n外部官方链接仍需联网。不要单独移动 index.html；保留 data/ 和 files/。\nSHA-256 文件清单见 manifest.json。catalog.json 可供二次分析。\n搜索范围：' + catalog['search_scope'] + '\n本看板继承原审核状态，没有运行模型评测。\n')
    if b.missing:
        raise ValueError(f'{len(b.missing)} approved referenced files missing: {sorted(b.missing)[:5]}')
    files = [{'path': path, 'sha256': sha(output / path), 'size': (output / path).stat().st_size,
              'rights': 'allowed'} for path in sorted(b.generated)]
    manifest = {'schema_version': 1, 'files': files,
                'rights_basis': 'Generated reader plus referenced files from the input delivery allowlist; no new rights inference.',
                'source_files': [f for f in b.files.values() if f['available']]}
    write_json(output / 'manifest.json', manifest)
    report = {'entries': len(entries), 'chapters': len(catalog['chapters']), 'cases': len(cases),
              'status_groups': dict(Counter(e['status_group'] for e in entries)),
              'pdf_page_links': sum(bool(e.get('pdf_page')) for e in entries),
              'packaged_source_files': sum(f['available'] for f in b.files.values()),
              'metadata_only_locators': sum(not f['available'] for f in b.files.values()),
              'content_shards': len(detail_shards), 'search_shards': len(search_shards),
              'indexed_attachment_count': len(attachment_search),
              'indexed_attachment_bytes': b.search_attachment_bytes,
              'output_files': len(files) + 1, 'output_bytes': sum(f['size'] for f in files),
              'diagnostics': data.get('diagnostics', []), 'issues': [], 'output': str(output)}
    if zip_path:
        zip_path = Path(zip_path).resolve()
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for item in files:
                archive.write(output / item['path'], item['path'])
            archive.write(output / 'manifest.json', 'manifest.json')
        with zipfile.ZipFile(zip_path) as archive:
            expected = {f['path'] for f in files} | {'manifest.json'}
            if len(archive.namelist()) != len(expected) or set(archive.namelist()) != expected or archive.testzip():
                raise ValueError('ZIP membership or CRC verification failed')
        report.update(zip=str(zip_path), zip_bytes=zip_path.stat().st_size, zip_sha256=sha(zip_path))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--data', type=Path, required=True, help='Normalized dashboard records')
    parser.add_argument('--manifest', type=Path, required=True, help='Explicit allowed-files manifest')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--zip', type=Path)
    args = parser.parse_args()
    data = json.loads(args.data.read_text(encoding='utf-8'))
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    allowed = {x['path']: x for x in manifest['files'] if x.get('rights') == 'allowed'}
    template = Path(__file__).resolve().parents[1] / 'assets/dashboard'
    print(json.dumps(build(data, args.root, args.output, allowed, template, args.zip), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
