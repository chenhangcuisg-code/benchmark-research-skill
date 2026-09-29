"""Verify preservation, permission boundaries, routes, packaging, and corruption detection."""
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

SKILL = Path(__file__).resolve().parents[1] / 'benchmark-research'
sys.path.insert(0, str(SKILL / 'scripts'))
from dashboard_engine import build, validate_project, safe_path
from audit_dashboard import audit


class DashboardTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'sources').mkdir()
        (self.root / 'books').mkdir()
        (self.root / 'books/A1.md').write_text('Fixture chapter', encoding='utf-8')
        (self.root / 'sources/allowed.json').write_bytes(b'\xef\xbb\xbf' + '{\r\n"answer": 0, "text": "原文 unchanged"\r\n}'.encode('utf-8'))
        (self.root / 'sources/private.json').write_text('not allowed to bundle', encoding='utf-8')
        self.allowed = {p:{'path':p, 'rights':'allowed','sha256':hashlib.sha256((self.root/p).read_bytes()).hexdigest()}
                        for p in ['sources/allowed.json','books/A1.md']}
        self.case_md = 'Original fixture\n\n`sources/allowed.json` and `sources/private.json`\n\n```json\n{"answer":0,"text":"原文 unchanged"}\n```\n\n<script>throw 1</script><a href="javascript:alert(1)" onclick="alert(2)">bad</a>'
        self.data = {'title':'Fixture', 'audit_date':'2026-09-29', 'groups':[{'id':'A','title':'Tasks','description':'Fixture'}],
                     'statuses':[{'id':'partial','label':'Partial','note':'Fixture'}],
                     'chapters':[{'id':'A1','title':'Chapter','group':'A','entries':['A1-001'],'markdown':'books/A1.md'}],
                     'entries':[{'id':'A1-001','chapter':'A1','name':'Example','status':'partial','status_group':'partial',
                                 'markdown':'Read [case](#case/case-1).','source_markdown':'books/A1.md','cases':['case-1']}],
                     'cases':[{'id':'case-1','title':'Fixture case','markdown':self.case_md,'owners':['A1-001'],'chapters':['A1']}]}

    def test_build_preserves_records_omits_private_and_audits_zip(self):
        out, archive = self.root/'dashboard', self.root/'delivery.zip'
        report=build(self.data,self.root,out,self.allowed,SKILL/'assets/dashboard',archive)
        self.assertEqual(report['entries'],1)
        self.assertEqual(audit(out,archive)['issues'],[])
        d=json.loads((out/'catalog.json').read_text(encoding='utf-8'))
        private=next(f for f in d['files'] if f['path']=='sources/private.json')
        allowed=next(f for f in d['files'] if f['path']=='sources/allowed.json')
        preview=(out/allowed['preview']).read_text(encoding='utf-8')
        raw=json.loads(preview.split(']=',1)[1].removesuffix(';\n'))
        self.assertEqual(raw.encode('utf-8'),(self.root/'sources/allowed.json').read_bytes())
        self.assertFalse(private['available'])
        self.assertNotIn('url',private)
        with zipfile.ZipFile(archive) as z:
            self.assertFalse(any('private.json' in p for p in z.namelist()))
        shard=d['content_shards']['case/case-1']
        rows=json.loads((out/shard).read_text(encoding='utf-8').removeprefix('window.BD_acceptContent(').removesuffix(');\n'))
        record=next(r for r in rows if r['id']=='case/case-1')
        self.assertEqual(record['markdown'],self.case_md)
        self.assertNotIn('<script',record['html'])
        self.assertNotIn('javascript:',record['html'])
        self.assertNotIn('onclick',record['html'])
        (out/'app.js').write_text('corrupted',encoding='utf-8')
        self.assertTrue(any('hash mismatch' in i for i in audit(out)['issues']))

    def test_changed_approved_source_fails(self):
        (self.root/'sources/allowed.json').write_text('changed',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'changed since manifest'):
            build(self.data,self.root,self.root/'dashboard',self.allowed,SKILL/'assets/dashboard')

    def test_missing_case_backlink_and_path_traversal_fail(self):
        self.data['cases'][0]['owners']=[]
        with self.assertRaises(ValueError):validate_project(self.data)
        for path in ['../secret','C:/secret','/secret','sub\\secret']:
            with self.assertRaises(ValueError):safe_path(self.root,path)


if __name__=='__main__':unittest.main()
