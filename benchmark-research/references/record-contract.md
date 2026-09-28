# Minimal machine-readable contract

Paths below are relative to the output root. The script accepts extra fields, so projects can add richer evidence without changing this contract.

`inventory.json`:

```json
{"chapters":[{"id":"A1","title":"Example chapter","markdown":"books/chapters/A1.md","pdf":"pdf/chapters/A1.pdf","entries":[{"id":"A1-001","name":"Example benchmark"}]}]}
```

`audit/entries.json`:

```json
{"entries":[{"id":"A1-001","chapter":"A1","name":"Example benchmark","kind":"dataset","status":"partial","category_coverage":{"covered":["official task A"],"missing":["official task B"]},"cases":[{"source_url":"https://example.org/pinned-file","release":"immutable revision","split":"test","record_locator":"row 0","source_sha256":"<64 lowercase hex digits>","rights":"metadata_only"}],"gaps":["Official test annotations are gated"]}]}
```

Allowed `kind`: `dataset`, `suite`, `protocol`, `metric`, `tool`, `proposal`. Allowed `status`: `verified`, `partial`, `restricted`, `unavailable`, `not_applicable`. A `verified` dataset/suite needs authentic case locators and no uncovered principal categories. A `partial` entry needs an authentic case; otherwise use `restricted` or `unavailable`. `not_applicable` is for a non-dataset item, not a convenient way to hide missing data. A case locator is metadata, not permission to redistribute the case itself.

`delivery/manifest.json`:

```json
{"files":[{"path":"books/chapters/A1.md","sha256":"<64 lowercase hex digits>","rights":"allowed"},{"path":"pdf/chapters/A1.pdf","sha256":"<64 lowercase hex digits>","rights":"allowed"}]}
```

List every public deliverable, including inventory and audit ledgers, but exclude restricted, uncertain, or local-only originals. Generate hashes after the final render. `scripts/audit_delivery.py` verifies listed hashes and rejects unsafe paths or non-`allowed` files. An offline ZIP, if created, should contain only manifest-listed files; check its member names and CRC independently.

The structural audit also expects each chapter Markdown to contain the exact five-column header and a unique `### <ID> ...` heading for every inventory entry. It compares inventory IDs with entry-audit IDs and requires each chapter's Markdown and PDF in the manifest. The script's checks do not replace reading the report or confirming factual sources and licenses.
