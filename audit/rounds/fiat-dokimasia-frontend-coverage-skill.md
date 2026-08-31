## Step 1, round 1 -- 2026-08-31T20:42:09Z

Audit schema: fiat-audit-round/v2

Covered: path-traversal=reviewed; partial-write=reviewed; subprocess-and-network=reviewed; cap-exhaustion=reviewed; target-repository-write=reviewed; router-corpus-drift=reviewed; evidence-digest-binding=reviewed; marketplace-boundary=reviewed; workbook-bytes=not-applicable; workbook-lineage=not-applicable; inventory-fidelity=not-applicable; disposition-closure=not-applicable

Not checked: no inventory, workbook or reconciliation code exists, so nothing was audited for parser, cap or lineage behaviour; no application checkout was read and no spreadsheet was opened; the Pashov pair did not run under the recorded security-suite waiver, since the step ships no Solidity; the regrade establishes that 40 isolated contexts agreed with the corpus, not that the corpus expectations are themselves right.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/dokimasia/docs/reports/selection/ | All 18 committed selection reports record `command` as `python3 .hexaemeron/design/build_design_evidence.py`. That path resolves only inside the controller's own run directory, which `.gitignore` excludes, so a reader who clones the repository cannot run the command the evidence names. The committed generator is at `plugins/dokimasia/docs/design/build_design_evidence.py`. The field cannot be corrected in this run: changing a report's bytes moves its SHA-256, the digests recorded in `design-evidence.json`, the record digest, and the `design-lock` block the runbook and the study receipt both pin, and the record is immutable after `done study` with no design-amendment transition available. Mitigated in 1de8557ce710f16537d852f10f4ae8e449bd7d3a by naming the discrepancy and the runnable path in the plugin README. The evidence itself remains checkable: `design_evidence.py --transition design-lock` verifies every recorded digest against the committed bytes. | accepted, mitigated in 1de8557ce710f16537d852f10f4ae8e449bd7d3a |

Leads not pursued: the committed generator can rewrite the locked record if somebody edits a candidate and runs it, which would break the `design-lock` block; the digest gate catches that rather than preventing it, and closing the hole would mean making a committed script refuse to write, which is out of scope for a scaffold. The plugin's reads of its own `SKILL.md`, `EVOLUTION.md` and law copy are unbounded, which is accepted for files it ships and would not be for the untrusted inputs a later step opens. RS-33 passed here after failing in four earlier runs; framework-73 owns that case and this round makes no claim about why it moved.

## Step 1, round 2 -- 2026-08-31T20:46:06Z

Audit schema: fiat-audit-round/v2

Covered: path-traversal=reviewed; partial-write=reviewed; subprocess-and-network=reviewed; cap-exhaustion=reviewed; target-repository-write=reviewed; router-corpus-drift=reviewed; evidence-digest-binding=reviewed; marketplace-boundary=reviewed; workbook-bytes=not-applicable; workbook-lineage=not-applicable; inventory-fidelity=not-applicable; disposition-closure=not-applicable

Not checked: the same negative space as round 1; no inventory, workbook or reconciliation code exists to audit, no application checkout was read, no spreadsheet was opened, and the Pashov pair still did not run under the recorded security-suite waiver.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the accepted item from round 1 stands unchanged.

## Step 2, round 1 -- 2026-08-31T21:45:15Z

Audit schema: fiat-audit-round/v2

Covered: inventory-fidelity=reviewed; path-traversal=reviewed; cap-exhaustion=reviewed; subprocess-and-network=reviewed; target-repository-write=reviewed; partial-write=reviewed; evidence-digest-binding=reviewed; marketplace-boundary=reviewed; router-corpus-drift=not-applicable; workbook-bytes=not-applicable; workbook-lineage=not-applicable; disposition-closure=not-applicable

Not checked: no workbook parser and no reconciliation code exists, so nothing was audited for spreadsheet or disposition behaviour; the compiler was run against one framework's conventions and nothing establishes the rule set is complete for another; the Pashov pair did not run under the recorded security-suite waiver, since the step ships no Solidity.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/dokimasia/scripts/dokimasia_lib/inventory.py | `refusal_proofs` lowered the module-level `paths.MAX_FILES` to exercise the file-count cap and restored it in a `finally`. A declared read cap that a library function can lower is one another caller in the same process can observe lowered, and `inventory --check` is a user-facing verb rather than test-only code. Fixed by making the bound a parameter of `source_files`, so the declared value never moves. Guarded by a test that drives a refusal through the parameter and then asserts every declared cap is unchanged. | fixed in b2ebd65bc990160ce4a2af59cadab097ff6f21ec |
| S2-R1-02 | medium | plugins/dokimasia/scripts/dokimasia_lib/inventory.py | `_matchers` scanned a forty-token window after a `matcher` key and returned whatever it had found. A matcher list longer than that window was truncated with no signal, so a middleware guard would have been recorded as covering fewer paths than it does, and the gap would have been invisible in the inventory. Fixed by capping the scan at 512 tokens and refusing by name when the list does not close inside it. Guarded by a test that drives an unclosed matcher list and requires the refusal. | fixed in b2ebd65bc990160ce4a2af59cadab097ff6f21ec |

Leads not pursued: `read_source` decodes with `errors="replace"`, so a file carrying invalid UTF-8 under a source extension is scanned as replacement characters rather than refused. The byte cap bounds the damage and the scanner cannot produce an item from noise, so this is accepted rather than repaired. Export clauses are not alias-resolved, which records a name the module does not answer on; the inventory rules state it and the alternative is a scope resolver this step does not need.

## Step 2, round 2 -- 2026-08-31T21:47:21Z

Audit schema: fiat-audit-round/v2

Covered: inventory-fidelity=reviewed; path-traversal=reviewed; cap-exhaustion=reviewed; subprocess-and-network=reviewed; target-repository-write=reviewed; partial-write=reviewed; evidence-digest-binding=reviewed; marketplace-boundary=reviewed; router-corpus-drift=not-applicable; workbook-bytes=not-applicable; workbook-lineage=not-applicable; disposition-closure=not-applicable

Not checked: the same negative space as round 1; no workbook or reconciliation code exists to audit, the rule set was exercised against one framework only, and the Pashov pair still did not run under the recorded security-suite waiver.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the two accepted items from round 1 stand unchanged.

## Step 3, round 1 -- 2026-09-01T00:00:00Z

Audit schema: fiat-audit-round/v2

Covered: workbook-bytes=reviewed; workbook-lineage=reviewed; cap-exhaustion=reviewed; path-traversal=reviewed; partial-write=reviewed; evidence-digest-binding=reviewed; subprocess-and-network=reviewed; target-repository-write=reviewed; marketplace-boundary=reviewed; inventory-fidelity=not-applicable; router-corpus-drift=not-applicable; disposition-closure=not-applicable

Not checked: no reconciliation code exists, so nothing was audited for disposition behaviour; the reader was exercised against one producing application's output and nothing establishes it reads a workbook another tool writes; the status and source vocabularies are counted as written and not validated against a controlled list, which is deliberate and stated in the lineage rules; the Pashov pair did not run under the recorded security-suite waiver, since the step ships no Solidity.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | plugins/dokimasia/scripts/dokimasia_lib/xlsx.py | The member size cap was tested against `member.file_size`, which is a declaration the archive writes about itself. A container that understates the field walks past a cap checked only against it, so the stated bound on memory was not a bound an adversarial archive had to respect. Fixed by reading one byte past the cap through `ZipFile.open` and refusing when that byte arrives, which holds whatever the header claims. Guarded by a test that rewrites every declared size to zero, leaves the payloads intact, and requires a refusal. | fixed in 03e9439b |
| S3-R1-02 | high | plugins/dokimasia/scripts/dokimasia_lib/xlsx.py | Every part was handed to `xml.etree.ElementTree.fromstring`, which expands internal entity definitions. A probe against the reader confirmed the expansion rather than assuming it: a payload declaring nested entities parsed and produced the expanded text. The archive caps do not bound this, because the expansion happens in memory after the bytes are read, so a part of a few hundred bytes could cost gigabytes and no declared cap would fire. Fixed by refusing a document type or entity declaration before anything parses the part; a spreadsheet part never carries one, so the class closes outright rather than being bounded. Guarded by a hostile fixture carrying a three-level entity chain and a test requiring the refusal by name. | fixed in 03e9439b |
| S3-R1-03 | low | plugins/dokimasia/tests/test_xlsx.py | The over-size test lowered the module-level `MAX_MEMBER_BYTES` and restored it in cleanup. This is the pattern corrected as S2-R1-01 in `paths.MAX_FILES`, reintroduced in test code, where a mutated global can still be observed by anything sharing the process. Fixed by threading the cap as a parameter through `read_sheets`, `_checked_members` and `_read_member`, so the test lowers a bound for one call and the declared value never moves. | fixed in 03e9439b |

Leads not pursued: the reader accepts a sheet whose rows are ragged and pads them to the widest cell reference, so a workbook with a stray far-right cell yields wide empty rows; the round trip catches any case this would drop and the cost is bounded by the cell cap. A shared-string table larger than the case count is read in full before any row is resolved, which is accepted because the member cap now binds the bytes that table can occupy. The status and source vocabularies observed in the reviewed workbook are not pinned anywhere, so a renamed status would import cleanly and reconcile differently; that belongs to the step that reconciles, not to the step that imports.

## Step 3, round 2 -- 2026-09-01T00:00:00Z

Audit schema: fiat-audit-round/v2

Covered: workbook-bytes=reviewed; workbook-lineage=reviewed; cap-exhaustion=reviewed; path-traversal=reviewed; partial-write=reviewed; evidence-digest-binding=reviewed; subprocess-and-network=reviewed; target-repository-write=reviewed; marketplace-boundary=reviewed; inventory-fidelity=not-applicable; router-corpus-drift=not-applicable; disposition-closure=not-applicable

Not checked: the same negative space as round 1; no reconciliation code exists, the reader was exercised against one producing application's output, the status and source vocabularies are still counted as written rather than validated, and the Pashov pair still did not run under the recorded security-suite waiver.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | high | plugins/dokimasia/scripts/dokimasia_lib/xlsx.py | Round 1 recorded the ragged-row cost as a lead not pursued, on the stated ground that it was bounded by the cell cap. There is no cell cap; that reasoning was wrong and this round is where it should have been caught. A sheet is stored sparsely, so the rightmost reference in a row decides the row's width when materialised, and the cost falls due after every archive cap has passed. Measured against the reader: a 15,686-byte archive of 2,000 rows, each carrying one cell at column XFD, materialises 32,768,000 cells and 258 MiB of resident memory, sixteen thousand times the archive, with no declared cap firing. At the 20,000-case cap the same shape reaches several gigabytes. Fixed by refusing a reference past a 256-column cap. Guarded by a hostile fixture and a test, and by a test asserting the benign fixture stays within the cap. The reviewed workbook is 20 columns wide. | fixed in 4f5eb025 |
| S3-R2-02 | medium | plugins/dokimasia/scripts/dokimasia_lib/xlsx.py | `_column` returned -1 for a reference carrying no column letters. That value indexed the row dictionary and then fell outside the range the row was built over, so the cell was dropped with no refusal and no signal. An import that loses a cell in silence is the failure the round trip exists to prevent, and the round trip could not see this one because the loss happened before a case was formed. Fixed by refusing a reference that names no column. Guarded by a hostile fixture and a test. | fixed in 4f5eb025 |
| S3-R2-03 | medium | plugins/dokimasia/scripts/dokimasia_lib/workbook.py | A declared split naming an identifier that no row carries was accepted and silently did nothing. The reviewer who wrote the declaration would then believe a compound row had been divided into atomic cases while the workbook still held it whole, and every later disposition would inherit that belief. The condition means either a mistyped declaration or the wrong workbook, and neither should import. Fixed by tracking which declared identifiers matched a row and refusing by name when any did not. Guarded by a test for the refusal and a test that a matching split still divides its row. | fixed in 4f5eb025 |

Leads not pursued: a shared-string table larger than the case count is still read in full before any row resolves, which the member cap bounds. The 256-column cap is a policy number, not a derived one; it is thirteen times the widest row in the reviewed workbook, and a legitimately wider sheet would refuse rather than degrade, which is the intended direction. The status and source vocabularies observed in the reviewed workbook remain unpinned, so a renamed status would import cleanly and reconcile differently; that belongs to the step that reconciles.
