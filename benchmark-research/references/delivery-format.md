# Handbook and PDF format

Create one source Markdown and one PDF for each user-defined chapter. Chapter names and count come from the project, not from the sample handbook. Each chapter begins with its scope and a five-column overview in this exact order:

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
