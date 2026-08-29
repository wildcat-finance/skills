## Step 1, round 1 -- 2026-08-29T17:57:15Z

Audit schema: fiat-audit-round/v2

Covered: base-resolution-race=reviewed; integration-branch-loss=reviewed; legacy-reanchor=reviewed; anchor-mismatch=reviewed; repository-substitution=reviewed; boundary-substitution=not-applicable; working-commit-substitution=not-applicable; ledger-prefix-substitution=not-applicable; canonical-json-drift=reviewed; policy-projection-drift=not-applicable; observation-overclaim=not-applicable; semantic-transport-confusion=not-applicable; path-or-secret-leak=reviewed; concurrent-read=not-applicable; scope-bleed-508-547=reviewed; scope-bleed-561-682=reviewed; schema-compatibility=reviewed

Not checked: none

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Plain status rendered the run branch as targeting the immutable starting SHA, so the separately retained integration branch disappeared from the operator view. | fixed and guarded on the stacked audit branch |

Leads not pursued: Git command-scope configuration can supply the effective origin seen by this process; Step 1 does not claim process-environment isolation, and no persisted credential or mismatched effective origin was found.

## Step 1, round 2 -- 2026-08-29T18:11:33Z

Audit schema: fiat-audit-round/v2

Covered: base-resolution-race=reviewed; integration-branch-loss=reviewed; legacy-reanchor=reviewed; anchor-mismatch=reviewed; repository-substitution=reviewed; boundary-substitution=not-applicable; working-commit-substitution=not-applicable; ledger-prefix-substitution=not-applicable; canonical-json-drift=reviewed; policy-projection-drift=not-applicable; observation-overclaim=not-applicable; semantic-transport-confusion=not-applicable; path-or-secret-leak=reviewed; concurrent-read=not-applicable; scope-bleed-508-547=reviewed; scope-bleed-561-682=reviewed; schema-compatibility=reviewed

Not checked: none

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | low | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | A full annotated-tag object SHA passed the peeled commit check, so Git created the worktree at its target commit while the state and anchor retained the tag-object SHA as the initial commit. | fixed and guarded on the stacked audit branch |

Leads not pursued: none. The round-1 process-scoped Git-origin lead was reviewed: the controller reads one credential-free effective Git config value, refuses multiple values, and verification recomputes the same join; no persisted credential or mismatched repository identity was observed.

## Step 1, round 3 -- 2026-08-29T18:19:10Z

Audit schema: fiat-audit-round/v2

Covered: base-resolution-race=reviewed; integration-branch-loss=reviewed; legacy-reanchor=reviewed; anchor-mismatch=reviewed; repository-substitution=reviewed; boundary-substitution=not-applicable; working-commit-substitution=not-applicable; ledger-prefix-substitution=not-applicable; canonical-json-drift=reviewed; policy-projection-drift=not-applicable; observation-overclaim=not-applicable; semantic-transport-confusion=not-applicable; path-or-secret-leak=reviewed; concurrent-read=not-applicable; scope-bleed-508-547=reviewed; scope-bleed-561-682=reviewed; schema-compatibility=reviewed

Not checked: none

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: none

## Step 2, round 1 -- 2026-08-29T20:19:48Z

Audit schema: fiat-audit-round/v2

Covered: base-resolution-race=reviewed; integration-branch-loss=reviewed; legacy-reanchor=reviewed; anchor-mismatch=reviewed; repository-substitution=reviewed; boundary-substitution=reviewed; working-commit-substitution=reviewed; ledger-prefix-substitution=reviewed; canonical-json-drift=reviewed; policy-projection-drift=reviewed; observation-overclaim=reviewed; semantic-transport-confusion=reviewed; path-or-secret-leak=reviewed; concurrent-read=reviewed; scope-bleed-508-547=reviewed; scope-bleed-561-682=reviewed; schema-compatibility=reviewed

Not checked: waived: non-Solidity Python controller-state identity work; bundled Solidity audit suite does not apply

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Python numeric equality let Boolean or floating state identifiers satisfy integer anchor, step, and audit joins, so malformed captured state could mint an identity. | fixed and guarded in c44550a13e2618da22dd3aeb709741c10ae2646b |
| S2-R1-02 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Legacy verification forwarded a hostile receipted source path to stderr, allowing an absolute path or credential-shaped segment to escape before the fixed identity refusal. | fixed and guarded in c44550a13e2618da22dd3aeb709741c10ae2646b |
| S2-R1-03 | low | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Revalidating an accepted observation imported the validator with bytecode writes enabled, so read-only checkpoint identity could create `__pycache__`. | fixed and guarded in c44550a13e2618da22dd3aeb709741c10ae2646b |

Leads not pursued: none

## Step 2, round 2 -- 2026-08-29T20:39:47Z

Audit schema: fiat-audit-round/v2

Covered: base-resolution-race=reviewed; integration-branch-loss=reviewed; legacy-reanchor=reviewed; anchor-mismatch=reviewed; repository-substitution=reviewed; boundary-substitution=reviewed; working-commit-substitution=reviewed; ledger-prefix-substitution=reviewed; canonical-json-drift=reviewed; policy-projection-drift=reviewed; observation-overclaim=reviewed; semantic-transport-confusion=reviewed; path-or-secret-leak=reviewed; concurrent-read=reviewed; scope-bleed-508-547=reviewed; scope-bleed-561-682=reviewed; schema-compatibility=reviewed

Not checked: waived: non-Solidity Python controller-state identity work; bundled Solidity audit suite does not apply

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: none
