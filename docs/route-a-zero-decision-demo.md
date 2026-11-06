# Demo: routing a filed zero

The working prototype from [the study](route-a-zero-decision-study.md), item 1,
run against the live GitHub API from a clean clone of this delivery. It shows
`hexctl init` answering a filed `Fiat-Required: 0` with a directive instead of a
refusal, and `issue-check` unchanged.

## Where it ran

A clean clone of `fiat/1345-route-a-zero-decision-and-gate-the-line-tha-step-5-update-the-prose-advance-the-led`
at `a040cdc417284053846389680bae740253cb8b9f`, with a local `main` branch created
at that commit so `init`'s base resolves. Run on 2026-09-13 against
[skills#1337](https://github.com/wildcat-finance/skills/issues/1337), which
declares `Fiat-Required: 0`.

## Command 1: init against the filed zero

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py init \
  --task-issue https://github.com/wildcat-finance/skills/issues/1337 \
  --topic 'routing probe' --base main
```

Exit 0. Standard error empty. `git status --short` empty afterwards: no run
state, worktree or branch. Standard output is one line, 847 bytes, SHA-256
`0a47a550e760441706e209085635402f736cab48d9f93d235bf5f0fc095f0d35`:

```json
{"do": "pull-request", "reason": "the task issue declares `Fiat-Required: 0`", "task_issue": "https://github.com/wildcat-finance/skills/issues/1337", "repository": "wildcat-finance/skills", "number": "1337", "fiat_required": 0, "route": "do the work as one independent pull request; no run state, worktree or branch was created and none is owed", "run_state": null, "worktree": null, "branch": null, "carryover": [{"id": "none", "disposition": "none", "reference": "the repair is both: split the two signals the one variable carries, and give the case a home outside the snapshot"}], "task_issue_closure": {"issue": "https://github.com/wildcat-finance/skills/issues/1337", "required_before_merge": "Closes wildcat-finance/skills#1337", "gate": "the issue closes on that pull request; no Fiat receipt is owed because no run exists to record one"}}
```

The `carryover` row is the real one from #1337's body, which is what shows the
issue was read rather than stubbed.

## Command 2: issue-check

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py issue-check \
  --issue https://github.com/wildcat-finance/skills/issues/1337
```

Exit 0. Standard error empty. Standard output, 322 bytes:

```text
wildcat-finance/skills#1337: clean
queue: framework-N (queue labels: observation)
Fiat-Required: 0 (one independent pull request)
carryover: 1 row(s), 0 filed, 0 pointing at an existing issue
  none | none | the repair is both: split the two signals the one variable carries, and give the case a home outside the snapshot
```

`issue-check` reports shape and is not the run gate, so this delivery leaves it
as it was.

## Before this delivery

The same `init` command against the same issue, from a clean clone of step 1's
head `979a213d886b79cd6bfa183dccf05ba65dbeecd4`, exits 1. Its refusal ends by
naming the edit that turns the refusal off, and it leaves `.hexaemeron/` behind
in the calling checkout. That sentence is the reason this delivery exists, so it
is described here and not reproduced.

## Reproducing it

The directive above was identical, byte for byte, when first recorded at step 2
on 2026-09-07 and again at step 5 on 2026-09-13, across the three steps between
them that added the provenance block and the window gate. The route exits before
either runs.

The output depends on #1337's live body as well as on these bytes. The
`carryover` reference is read from the issue, so an edit to that row changes the
directive. A run against an unchanged #1337 reproduces the bytes above; a run
after the issue changes will not, and the difference will be confined to what
the issue says.
