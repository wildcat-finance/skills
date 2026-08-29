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
