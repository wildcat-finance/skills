## Step 1, round 1 -- 2026-09-06T10:03:20Z

Audit schema: fiat-audit-round/v2

Covered: restore-tail-spoof=reviewed; prefix-truncation=reviewed; path-delta-smuggling=reviewed; anchor-substitution=reviewed; boundary-widening=reviewed; multiple-relocations=reviewed; semantic-transport-confusion=reviewed; source-or-policy-drift=reviewed; ref-or-ancestry-drift=reviewed; diagnostic-leak=reviewed; concurrent-read=reviewed; legacy-reanchor=reviewed

Not checked: the Pashov Solidity suite, waived because the step changes no Solidity; the outer archive, signature, service, clean-machine, lineage, and routing work assigned to issues #861 through #867; live GitHub checks, remotes, push, and controller mutation; and exclusion of same-account mutation after the final userspace read.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The transparent-restore proof accepted a syntactically valid `source_state_sha256` without recomputing it from the reconstructed producer state, and its single-relocation guard rejected only a restore at the imported prefix tail rather than a prior restore anywhere in that prefix. The first omission left the recorded producer-state join unchecked; the second admitted a multiply relocated prefix contrary to the fixed design. | fixed in `21faa1b08dfdb1ff8823cede9a78bc4d411113b3` by recomputing the exact producer state-file digest and refusing any prior `checkpoint:restore`; hostile digest and earlier-restore cases fail on the parent and pass on the fixed tree |

Leads not pursued: the capsule manifest is unavailable to a later identity read, so its digest remains a recorded restore receipt field rather than independently replayed manifest evidence; native restore already verifies the manifest before publishing that receipt, and outer carrier proof belongs to #861. No persistent telemetry was added to the read-only command. The full Hexaemeron suite passed 2,360/2,360, the root suite passed 1,389/1,389, Phylax, Ephoros, and Hypomnema each exited 0 with `clean`, Horos regenerated the current boundary, and `git diff --check` exited 0. The exact audit declaration is `--audit-filter sapheneia:sapheneia`; it records application of the bounded audit-record pass and does not make the controller proof of this record's semantics.

## Step 1, round 2 -- 2026-09-06T10:23:27Z

Audit schema: fiat-audit-round/v2

Covered: restore-tail-spoof=reviewed; prefix-truncation=reviewed; path-delta-smuggling=reviewed; anchor-substitution=reviewed; boundary-widening=reviewed; multiple-relocations=reviewed; semantic-transport-confusion=reviewed; source-or-policy-drift=reviewed; ref-or-ancestry-drift=reviewed; diagnostic-leak=reviewed; concurrent-read=reviewed; legacy-reanchor=reviewed

Not checked: the Pashov Solidity suite, waived because the step changes no Solidity; the outer archive, signature, service, clean-machine, lineage, and routing work assigned to issues #861 through #867; live GitHub checks, remotes, push, and controller mutation; and exclusion of same-account mutation after the final userspace read.

Elenchus verdict: unguarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | low | .horos/boundary.json | The round-1 audit evidence commit added two tracked files without regenerating the Horos boundary count. Both root boundary-currency tests therefore reported `.horos/boundary.json#counts`: the committed `files_walked` value was 2,629 while a fresh scan found 2,631. | fixed in this audit commit by deterministic Horos regeneration; the two exact tests and the full root suite pass on the refreshed tree |

Leads not pursued: round 1's semantic fix and hostile guards remain unchanged, signed, and green. The Hexaemeron suite passed 2,360/2,360; the first root run exposed only S1-R2-01, its two exact tests then passed 2/2, and the repaired full root suite passed 1,389/1,389. Phylax, Ephoros, and Hypomnema each exited 0 with `clean`; no checkpoint boundary, controller code, schema, or policy changed. The exact audit declaration is `--audit-filter sapheneia:sapheneia`; it records application of the bounded audit-record pass and does not make the controller proof of this record's semantics.
