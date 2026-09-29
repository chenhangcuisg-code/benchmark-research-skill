# Original-case and source audit

Treat these as independent claims: the benchmark exists; its official source is identified; a precise release and split are identified; a real record is obtained; major categories are represented; an answer or scoring target is public; the scoring environment can be run; the record may be redistributed. Evidence for one claim does not prove the others.

For each source, record the canonical URL, publisher/author, release tag or immutable revision when available, filename, retrieval date, SHA-256 of the retrieved file, access status, license statement and its scope. A moving `main` branch or dataset viewer is a discovery lead; pin the underlying file before treating it as reproducible evidence. Keep local snapshots separate from public packages.

For each case, retain the original input, necessary context and constraints, candidates, and public gold answer or target. Preserve modalities: images, audio, video, repository state, tools, hidden tests, and execution environment may be essential to the task. If a field is unavailable, mark it unavailable; do not infer it from a model output or paper example. Cite a stable record ID or zero-based row number, split/configuration, file path or JSON Pointer, source revision, and local snapshot hash. If a PDF excerpt is all that exists, label it as a paper example and do not call it a released dataset row.

Audit the role of each linked item separately from whether its URL resolves. A released dataset row, repository task file, documentation demo, system prompt, model evaluation trace, paper example, and third-party mirror are different evidence types. Record `evidence_role`, `case_completeness`, and whether official row identity was verified; a real file or a successful HTTP check does not itself make a complete original task. For a mirror, compare original identifiers, field values, and model-visible bytes or pixels where possible, and disclose any absent official per-file hash. Keep the status of a parent benchmark unchanged when only a related example or partial input was found.

Classify categories using the source's `subject`, `type`, `task`, `config`, or equivalent fields. Distinguish author-defined categories from analyst groupings. State which principal categories have actual cases and which remain uncovered. A single row cannot demonstrate complete category coverage.

Use these entry states consistently:

| State | Meaning |
|---|---|
| `verified` | Primary claims checked; real cases cover the documented principal categories, and remaining dependency/gold limits are disclosed. |
| `partial` | At least one authentic case is found, but source identity, categories, context, gold, protocol, or attachments remain incomplete. |
| `restricted` | The identified source requires access, registration, or permission and the needed originals have not been obtained. |
| `unavailable` | Searches and access attempts are documented, but no authentic original has been obtained. |
| `not_applicable` | The item is a metric, protocol, tool, or unpublished proposal without an independent published question set. Document its host dataset or publication status. |

If a public derivative or author mirror is found, preserve its own ID, revision, hash, and rights. Record the tested identity relationship (e.g., ID intersection and field equality) and the missing official components. Never silently promote derivative rows to a gated official split. For `restricted` or `unavailable`, log the attempted URL, HTTP/error response or exact absence, date, and next plausible lead. Do not bypass access controls.

Rights review is per artifact. A dataset card's license may not cover individual paper full texts, third-party images, contest statements, or hidden tests. Use `allowed`, `metadata_only`, `private`, or `unknown` for each case/file. Put only `allowed` files in a public package; `unknown` defaults to metadata and source locator. Brief quotations still require attribution and should stay within applicable limits.

Check repeated excerpts across the whole public package, not only one card. When the underlying corpus has mixed or uncertain rights, use category, pinned source revision, split, row or archive-member locator, and full-record hash in public cards; keep the full input in an authorized local research copy and link to the publisher's access point. Check every embedded link as well as the card's primary URL, and record all owners when several cards reuse one source. Do not publish expiring signed CDN redirect URLs as stable source locators.

## Complete-collection gate

Apply this gate when the user says every benchmark must have complete data or forbids partial collection. Define the scope in the inventory: entire public release, all requested splits/categories, or one complete task per principal category. A complete task includes every model-visible input and attachment plus the public answer, grading target, or runnable scoring protocol needed to interpret it. Private held-out tests are separate from a complete public release; identify them without claiming access. An answer is not missing merely because an official open-ended protocol intentionally uses a judge, but the rubric and judge dependency must be present.

For each requested entry, record a machine-readable completeness verdict with evidence for source identity, release/split, category coverage, input/context, attachments, answer or scoring target, and rights. A source URL or locally cached file alone is insufficient. If any required component is missing, retain the item and its exact blocking condition in the ledger; do not silently omit it, substitute a different benchmark, or promote a paper example to an official row. Search author supplements and independent archives as leads, but compare IDs and field values against an official version before accepting a mirror. Continue independent work on other entries while access-dependent items remain blocked. Final publication under this gate requires zero unresolved requested entries; a provisional research snapshot must be labeled provisional and must not be presented as the completed deliverable.
