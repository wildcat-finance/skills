# ADR-023: Store Kronos working state on a dedicated git ref

## Status

Accepted, 2026-08-24. Recorded for
[skills#462](https://github.com/wildcat-finance/skills/issues/462). Depends on
the dirty-tree rule recorded in
[docs/kronos-ranking-scoreboard/study.md](../kronos-ranking-scoreboard/study.md)
and on S2-R1-01, which forbids writing through a symlink at `.kronos`.

The product tree receipted this decision as ADR-022. Composition with current
`main` found that number already assigned to the run-observation capture
profile, so integration moved this record to ADR-023 without changing the
decision. The receipted study and runbook remain unchanged as evidence of the
product tree.

## Context

Kronos records each ranking pass in `.kronos/scoreboard.jsonl` and each park in
`.kronos/parked.jsonl`. Both files are gitignored on purpose. v0.3.0 recorded
the cost: the record lives on the machine that ran the loop. That was true when
the machine lasted. The collective now runs in remote sessions whose containers
are recycled between runs. Every fresh runner therefore starts with an empty
scoreboard and an empty parked lane.

A park is released by a person, never by infrastructure. Today the recycler
releases it. Committing the gitignored files into the working tree Fiat inspects
would dirty `git status --short` and stop the next Fiat `init`. Having Kronos
commit, branch or push that tree would break Kronos's first hard rule. A
symlink at `.kronos` is already refused.

## Decision

Kronos working state lives on `refs/heads/kronos/state`. `pull` and `push` copy
the two JSONL files through a throwaway clone under the system temp directory.
`record`, `park`, `unpark`, `show` and `parked` stay subprocess-free. A missing
ref is an empty start. An existing-ref pull failure refuses. A non-fast-forward
push refuses and leaves local files.

## Alternatives

- **File export and import only.** Cheapest. A park recorded on one runner
  stands on a fresh runner only if a person carries the files. A forgotten
  import looks exactly like an empty lane, which is the defect.
- **Operator-supplied real directory (`KRONOS_STATE_DIR`).** Recycled cloud
  runners do not mount such a volume unless the harness is changed, and a
  symlink there is already refused. A real directory still dies with the VM
  disk.
- **Tracked files under `docs/kronos/` or similar, committed by Fiat.** Shared
  history. Kronos would dirty a tracked file before Fiat `init`, or would have
  to commit, which v0.3.0 forbade for the target tree. Ranking would then
  require a product pull request.

## Consequences

A park recorded on one runner still stands on a fresh runner until a person
runs `unpark`. `show` reads scoreboard history that survived the previous
runner. `git status --short` in the scope stays empty after pull, record, park
and push.

The cost is a git subprocess on the sync verbs: fixed argv, no shell, a remote
name rather than a caller-supplied URL, timeouts and an output cap. A
contributor without push access to the canonical remote can still pull and can
still rank, but their parks stay local until someone who can push does so.
Concurrent writers are not merged; the later non-fast-forward push refuses.

Harnesses that want parks to survive a recycled runner grow against this ref,
not against a committed `.kronos/` on `main`.
