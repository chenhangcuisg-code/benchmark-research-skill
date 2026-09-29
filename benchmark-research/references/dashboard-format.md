# Searchable benchmark dashboard

The main route is **chapter → benchmark → original case → data/source file**. Every route should be bookmarkable and work on reload. Preserve protocol variants as separate entries even when they share cases. Show backlinks from a shared case to its referring entries. Existing PDF bookmarks can supply exact page links; do not guess pages from an earlier edition.

## Reading and searching

Use chapter cards for orientation and an entry directory for scanning. Offer filters based on the actual inventory, plus status groups when useful. A display group is an analyst navigation aid: retain the original audit state and explain the mapping rather than renaming `partial` to `verified`.

Give each entry an overview, complete explanation, original-case list, and source/attachment list. Keep all five overview fields available. Offer readable JSON fields alongside unchanged raw JSON; retain complete code, input context, candidates, answer encoding, and hashes. Load large records when opened, paginate large result sets, and keep surrounding navigation usable. Do not rely on embedding huge PDFs or dumping full JSON into every card.

On every directory card and directly below each entry title, explain what a typical question looks like (`task`) and which capability it assesses (`requirement`). Keep the full fields in the overview as well. When the source wording is too terse or noisy, add a concise, clearly scoped explanation for that entry without changing the original source fields.

Place a clickable original project or paper source immediately below the title on both directory cards and entry pages when the reviewed entry cites one. Use a precisely linked local source PDF page when the entry has no external source. Keep source links for paper examples and constructed study examples distinct from the entry-level source.

When a source paper prints a useful example but the released dataset row is unavailable, a case card may use `source_kind: "paper_example"`. Name it “论文示例”, link the primary PDF to the exact page and figure/table, summarize only the shown input and answer, and state which row, split, gold, context or attachment remains missing. Keep the original audit status. Do not count a paper example as an obtained official test row or silently reassign it to a more specific version or category.

For internal study, source-linked `study_example` cards may illustrate the task when no public row can be obtained. Mark every such input and answer as constructed, link the benchmark description as the **task basis** directly below the title, and state that it cannot replace a released row or hidden gold. Use `public_row` only for a record whose source row and answer have been checked. These cards can remove empty reading views while the original audit state and remaining data or protocol limits stay visible.

Treat supplemental study cards as provisional. When a later source recovery changes an entry to `located` or adds an authentic original case, remove the superseded study card from the delivered reader while retaining its dated audit trail. Rebuild and recheck the case routes and browser fixtures; a hardcoded study-card route can become stale after a successful recovery. Do not let an older proxy card obscure the newly verified row or count it twice.

When the user requires authentic cases, do not fill gaps with constructed `study_example` cards. Check the original release, a public dataset or mirror, and a paper or other independent source for each unresolved entry. Record the actual URLs, outcomes, and reason a candidate cannot be matched to the requested version. If three independent attempts still do not yield a verifiable case, leave the case list empty and expose `case_gap_reason` plus `case_gap_attempts` on that entry; the dashboard shows the three source links in the empty case view. Keep `mirror_row` visibly separate from an official `public_row` and state when identity against a gated release remains unverified.

Search the actual text. Distinguish directory-field search from full original-case and selected-attachment search. State which files are included, display loading/completion or failure, and ensure a record near the end of the index is findable. A filename search must not be described as full-text data search. Full corpus caches can remain outside the index, with that scope disclosed. Zero results must be distinguishable from a failed or unfinished index load.

## Reusable builder

`scripts/dashboard_engine.py` and `assets/dashboard/` provide a local static reader. Build dependencies are `Markdown` and `beautifulsoup4`. There are no runtime CDNs or web services. Classic local script shards allow the reader and attachment previews to work when `fetch(file://...)` is forbidden.

```bash
python scripts/dashboard_engine.py --root REPORT_ROOT --data dashboard-records.json --manifest delivery/manifest.json --output REPORT_ROOT/dashboard --zip REPORT_ROOT/delivery/dashboard.zip
python scripts/audit_dashboard.py --root REPORT_ROOT/dashboard
```

The input `--manifest` uses the `files` contract in [record-contract.md](record-contract.md). Only records explicitly marked `rights: allowed` enter the allowlist. An adapter for an existing repository may consume its established `included_files`/`local_only_files` split, documenting that choice. Do not infer permission from a file extension or Git tracking. The builder checks approved hashes before copying and keeps unknown references as metadata.

Use a small project adapter to normalize the actual source format; do not hardcode a previous catalog's 25 chapters, status vocabulary, or 1,871 entries into future tasks. The adapter should fail on unmatched or duplicate entries, lost case references, conflicting shared cases, and changes to original content. Markdown headings inside code fences are content, not entry boundaries. Tables may contain escaped pipes and embedded control characters; use stable IDs and verify names when mapping older tables by order.

The normalized JSON has these fields:

```json
{
  "title": "Benchmark research", "subtitle": "From tasks to evidence",
  "audit_date": "YYYY-MM-DD", "description": "Actual scope and limitations",
  "groups": [{"id":"A","title":"Capabilities","description":"User-defined scope"}],
  "statuses": [{"id":"partial","label":"Partially collected","note":"Actual remaining limits"}],
  "chapters": [{"id":"A1","title":"Chapter title","group":"A","entries":["A1-001"],"markdown":"books/chapters/A1.md","pdf":"pdf/chapters/A1.pdf","pages":1}],
  "entries": [{
    "id":"A1-001","chapter":"A1","name":"Example benchmark",
    "status":"partial","status_group":"partial",
    "example":"Authentic cue or explicit absence","category":"Source categories",
    "task":"Input and output","requirement":"Model capability",
    "protocol":"Metric and protocol","gaps":"Known limits",
    "markdown":"Complete reviewed explanation with source links",
    "source_markdown":"books/chapters/A1.md","source_audit":"audit/entries.json",
    "cases":["case-001"],"pdf":"pdf/chapters/A1.pdf","pdf_page":1
  }],
  "cases": [{"id":"case-001","title":"Original case identifier","markdown":"Complete original case and provenance","owners":["A1-001"],"chapters":["A1"]}]
}
```

PDF fields are optional. The reader requires the entry's original `source_markdown` path for resolving relative attachments. The example above defines metadata shape; it is not benchmark evidence. IDs use letters, numbers, `_` or `-`. Markdown is sanitized during rendering. No raw HTML may execute scripts or load arbitrary active content.

`primary_source_url` is optional entry metadata for the cited project or paper entrance shown below the title. Derive it from the reviewed entry text and prefer a labeled benchmark entrance over incidental links. When absent, the reader can fall back to the entry's local PDF page.

## Packaging and checks

The output contains `index.html`, local assets, sharded content/search, a machine-readable `catalog.json`, addressed attachments, and a manifest with SHA-256. Distribute the complete directory or ZIP, so links do not point outside it. Preserve original filenames in metadata even if packaged blobs are named by hash. Files over the preview threshold remain complete downloads and should be described accordingly.

Check repository landing-page links against what is actually published. A ZIP generated only on the local machine and ignored by Git must be described as a local artifact, not linked as if the repository hosts it. If a current ZIP is published separately, pin the exact release asset and version; do not silently link an older archive after rebuilding the dashboard. A README edit that enters the delivery manifest requires refreshing its hash and rebuilding the ZIP before the final integrity audit.

Run the structural audit and inspect the ZIP's member names and CRC. In an actual browser, check representative entries from each source format, shared cases, an attachment containing long input, a late full-text search hit, non-ASCII input, an empty result, back/forward/reload, export, and narrow-screen overflow. Test `file://` with network access blocked to substantiate offline support. For a converted report, compare all IDs and statuses with the existing audit and compare original fenced record content before and after extraction. Save screenshots and a concise review log with actual dimensions/routes.

Deliver the built reader and archive, the adapter/build command, and any retained PDF links. Repository documentation should lead with the dashboard opening instructions. Update the installed skill as well as its source checkout when the user asked to improve their skill, and report whether remote publication actually occurred.
