## Step 1, round 1 -- 2026-08-31T20:42:09Z

Audit schema: fiat-audit-round/v2

Covered: path-traversal=reviewed; partial-write=reviewed; subprocess-and-network=reviewed; cap-exhaustion=reviewed; target-repository-write=reviewed; router-corpus-drift=reviewed; evidence-digest-binding=reviewed; marketplace-boundary=reviewed; workbook-bytes=not-applicable; workbook-lineage=not-applicable; inventory-fidelity=not-applicable; disposition-closure=not-applicable

Not checked: no inventory, workbook or reconciliation code exists, so nothing was audited for parser, cap or lineage behaviour; no application checkout was read and no spreadsheet was opened; the Pashov pair did not run under the recorded security-suite waiver, since the step ships no Solidity; the regrade establishes that 40 isolated contexts agreed with the corpus, not that the corpus expectations are themselves right.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/dokimasia/docs/reports/selection/ | All 18 committed selection reports record `command` as `python3 .hexaemeron/design/build_design_evidence.py`. That path resolves only inside the controller's own run directory, which `.gitignore` excludes, so a reader who clones the repository cannot run the command the evidence names. The committed generator is at `plugins/dokimasia/docs/design/build_design_evidence.py`. The field cannot be corrected in this run: changing a report's bytes moves its SHA-256, the digests recorded in `design-evidence.json`, the record digest, and the `design-lock` block the runbook and the study receipt both pin, and the record is immutable after `done study` with no design-amendment transition available. Mitigated in 1de8557ce710f16537d852f10f4ae8e449bd7d3a by naming the discrepancy and the runnable path in the plugin README. The evidence itself remains checkable: `design_evidence.py --transition design-lock` verifies every recorded digest against the committed bytes. | accepted, mitigated in 1de8557ce710f16537d852f10f4ae8e449bd7d3a |

Leads not pursued: the committed generator can rewrite the locked record if somebody edits a candidate and runs it, which would break the `design-lock` block; the digest gate catches that rather than preventing it, and closing the hole would mean making a committed script refuse to write, which is out of scope for a scaffold. The plugin's reads of its own `SKILL.md`, `EVOLUTION.md` and law copy are unbounded, which is accepted for files it ships and would not be for the untrusted inputs a later step opens. RS-33 passed here after failing in four earlier runs; framework-73 owns that case and this round makes no claim about why it moved.
