---
name: benchmark-research
description: Research and audit a user-defined benchmark catalog, collecting traceable original examples and producing one compact, reviewable PDF per chapter. Use for benchmark surveys and evaluation handbooks, not for claiming model scores or running experiments.
---

# Benchmark research

Use the user's catalog and requested taxonomy as the scope. Give every listed benchmark or protocol variant a stable ID and its own detailed entry; shared underlying data does not make variants interchangeable. Preserve the user's distinctions between chapters, metrics, datasets, protocols, and proposals. Do not silently drop unresolved entries.

Before collecting, read [the evidence rules](references/evidence.md). Prefer the official release, paper supplement, author repository, and pinned dataset files. Use mirrors or derivative datasets only after checking record identity and explaining exactly which official version or split they do and do not establish. Record the access attempt and error for gated or missing originals. A project page, abstract, synthetic illustration, configuration row, or nearby benchmark is not an original test case.

For each entry, explain the task, inputs and outputs, model requirements, evaluation protocol and metric, official category fields, covered and uncovered categories, real cases, gold-answer visibility, source version/split/record locator, dependencies, redistribution rights, and remaining gaps. Keep original case content separate from your explanation. If no original is public or the item is a protocol/metric, state that plainly. “A case was found” never means “the full dataset or all categories were collected,” and source auditing never implies that a model evaluation was run.

Use [the delivery format](references/delivery-format.md) when the user requests a handbook or PDF. It preserves the five-column overview (`Benchmark | 具体数据例子 | 数据分类 | 题目类型 | 模型需要做到`), one detailed section per entry, and one compact PDF per chapter. Optimize layout without changing case values, omitting necessary context, hiding gaps, or substituting a summary for the original. Store long inputs and permitted attachments in addressable files, with relative path, record locator, and SHA-256 in the handbook. Only bundle data whose redistribution rights have been checked; when rights are uncertain, publish metadata and a pinned source link instead.

Maintain machine-readable inventory, entry audit, and public-file manifest as described in [the record contract](references/record-contract.md). After rendering, run `scripts/audit_delivery.py --root <output-dir> --check-pdf` to check coverage, file hashes, chapter PDFs, and structural links. Also inspect rendered page samples from every chapter, including tables, code, formulas, images, long cases, and chapter boundaries; record which pages were actually inspected. Correct failures and rerun the checks. The script checks structure, not factual accuracy, licenses, or visual quality.

Report the audited entry count, chapter/PDF count, status distribution, still-missing originals, source and rights limitations, and paths to the manifest and review log. Publish to an external repository only when that action is in the user's authorized scope. The research report's case data and this skill's source code have separate redistribution decisions.
