# Handbook and PDF format

Use this format for requested PDF deliverables. For searchable or large interactive catalogs, use [dashboard-format.md](dashboard-format.md) as the main reader and link existing PDFs as source views. The PDF requirements here do not apply to a dashboard-only delivery.

Create one source Markdown and one PDF for each user-defined chapter. Chapter names and count come from the project, not from the sample handbook. Each chapter begins with its scope and a five-column overview in this exact order:

When a chapter contains hundreds of entries or long original records, make a compact reading PDF without losing the evidence: keep the five-column overview and one detailed audit section per entry in the PDF, then place every cited full original in a stable per-entry machine-readable index. Each index record must point to the unchanged attachment, its actual SHA-256, original URL and revision, split/configuration, row or record ID, visible gold, rights, and exact missing fields. Link the index from the PDF and root index. Verify every referenced attachment hash and every local PDF link. Count referenced records separately from unique original records, since several entries may cite the same case. Keep one chapter per PDF (for example, one L or one B); do not concatenate a whole series into one large volume. Page reduction changes presentation only and must never upgrade a `partial` or `restricted` source state.

`Benchmark | 具体数据例子 | 数据分类 | 题目类型 | 模型需要做到`

The example cell gives a short authentic case cue and points to its detailed section, or says why no original is available. It must not silently use a fabricated question. Each inventory ID has exactly one `### <ID> <name>` detailed section. A useful section contains:

1. Item type and audit state; why this is an independent entry or protocol variant.
2. Official categories and source fields; covered versus missing categories.
3. Input, output, task constraints, model capability, metric, answer extraction, shots, and comparability limits.
4. One or more original cases for principal categories, with required context/candidates and visible gold status. Link long or multimodal attachments by path and hash.
5. Four distinct links: benchmark entry, original-data browser, full download, and protocol/license. Mark unavailable or gated links rather than using the project homepage for all four.
6. Exact release, split/config, record ID or row, retrieved file and SHA-256; known gaps and access attempts.

Use an appendix for the complete records actually cited in that chapter. Cross-chapter shared records need valid locations from each referring chapter. Large raw corpora are not automatically part of the public appendix. Keep the full values in permitted attachments; truncation in an overview cell is acceptable only when the detailed entry or attachment remains complete and linked.

Use readable CJK-capable fonts, predictable heading hierarchy, working internal/external links, bookmarks where practical, and clear page numbers. Keep tables within page width and prevent stranded headings. Compact scalar JSON arrays or whitespace only when parsing proves the values remain identical; do not compact prose, code, formulas, or multimodal references so aggressively that they become hard to review. Generate a visual review log with PDF hash and concrete page numbers sampled from every chapter. If a sample fails, fix and inspect it again.

Deliver a root index with chapter name, entry count, status counts and PDF link; source Markdown; a public manifest with hashes; audit ledgers; and, if useful, an offline ZIP containing only approved files. Run structural checks on every chapter and visually inspect representative pages. Report actual page totals without equating fewer pages with fuller evidence.
