# Record an open issue's status where the census reads it

## 1. Problem statement

An open issue's requirement changes after filing. It gets narrowed by work that
landed, subsumed by a later issue, or invalidated by a change to `main`. The
correction goes into the comment thread, and the census that compiles the
contributor-facing queue reads bodies. So the queue offers work against a
requirement nobody holds any more, and nothing about the issue says so.

This builds the repository half of the fix: a delimited status block with a
fixed marker contract, a checker that reads it, and a report-only signal naming
open issues whose body has gone stale. It is for the person or agent choosing
the next job, and for the census that compiles the queue.

A working prototype means `hexctl issue-check` accepts a body carrying a
well-formed status block, refuses a malformed one, and refuses a body whose only
markers sit inside a fenced code span. The check that proves it is
`python3 -m unittest discover -s tests` green, plus `hexctl issue-check --issue
https://github.com/wildcat-finance/skills/issues/1057` exiting zero against the
filed issue once its block is added.

## 2. Prior art

**In this repository.** `hexctl issue-check` already reads an issue body for
contract markers. It arrived at `c148ab9a`, `feat(fiat): gate a run on what its
issue filed`, merged as pull request 1040 on 2026-08-31, which is the most
recent merged change to this surface and the only one. It parses one unfenced
`Fiat-Required` line through `_unfenced_markdown_lines` and one fenced
`carryover` block through `fenced_block_rows`, and reports both questions at
once. Three call sites read a body through it:
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py:4565` in `init`,
`:5327` in the `issue-check` command, and `:8865` for the run pull request's
`## Carried forward` section.

Pull request 1040's own `## Carried forward` block carries one row,
`agent-instruction-token-counts | none | ...`, recording that measurement and
parity records keep their token counts unchanged because re-measuring needed an
Ollama run that was not available. That item is a non-goal here. It belongs to
the agent-instruction fixture surface that issue #1030 covers, and nothing in
this topic reads or writes those counts.

`docs/decisions/ADR-014-reallocate-the-live-wave-atlas-from-a-complete-census.md`
put issue bodies outside the authorised mutation and rejected writing metadata
into them. Its amendment of 2026-08-31, merged as `9783e263`, authorises one
bounded write: a single block at the top of an open issue's body delimited by
`<!-- status:start -->` and `<!-- status:end -->`, recording status,
supersession, or a changed requirement. Wave assignment stays milestone-only.
Filing prose outside the block is not rewritten. The Atlas dependency extractor
must skip the block.

**Related filings.** #837 records the same failure inside documents: at
`23d6bfdf`, `docs/disposable-fixture-signing/study.md:234` still reads "Ten
sites in six files" while the correction to seven files begins at line 740, with
nothing at line 234 saying a correction exists. #838 measured the comment-thread
cost across 213 issues and 583 closed pull requests: 436 carried-forward items,
344 naming no issue or pull request, 245 with no register anywhere. #497 records
the Atlas dependency extractor reading a `depends on` line as a declaration
about the issue that contained it, which is why the block must be skippable.
#941 records that an issue with no milestone is invisible to `/api/job`. #894 is
open against ADR-014 for a different defect and is untouched here.

**Cost of the chosen host.** #892 records that any change to `hexctl.py` turns
two digest-bound subsystems red and names neither. #1030 records the same shape
on a skill document: one logical digest recorded in four places, and seven
reconciliation passes for one version bump. Both are the accepted cost of the
selected design and are named as such in item 3.

**Audit records.** The whole-set currency check
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check
<target-root>` exits zero from the run worktree, with every committed synopsis
matching its freshly derived bytes, so synopses are the authorised reading view.
`plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` was read for the Fiat controller:
two rounds, ten findings at step 0, all fixed except F-10, which is accepted as
a documented hook escape hatch. Its leads not pursued are `os.replace`
atomicity across filesystems, concurrent `hexctl` invocations against one state
directory, and ANSI passthrough via `status --json`. None is touched by this
topic. `audit/AUDIT_SYNOPSIS.md` was read for the root record.

**An evidence gap.** Sapheneia is in scope as a candidate owner and has no audit
record at all: no `plugins/sapheneia/audit/` directory, no source and no
synopsis. Nothing was read for it because nothing exists to read, and this is
recorded rather than treated as a clean result. It also has no `scripts/`
directory, so it carries no mechanical checker; its issue-shape promise is
model-graded, which #884 records as evidence standing on a fixture no model
runs.

**Outside.** GitHub's issue API permits a body edit with no time limit, which is
what makes the block possible at all. Measured over the 100 most recently filed
open issues on 2026-08-31: 41 carry `lastEditedAt`, and issues #410 through #423
were edited 4.53 days after filing. Ten of the 137 open issues already carry an
ad-hoc `## Status` heading, all filed on or after 29 August, enforced by
nothing.

## 3. Constraints and non-goals

The run was cut from `main` at `51fb586e41f67bff1cd53bed8414e3fc63ff48cb`. The
base advanced to `9783e263` after `init`, carrying the ADR-014 amendment this
study depends on, so the integrate phase owes a `sync-run` receipt. Python is
whatever `python3` resolves to on the runner; the suite entry point is
`python3 -m unittest discover -s tests`. Controller `fiat-v5.46.1` under
Hexaemeron `1.6.20`.

Non-goals. The Atlas is a separate repository, so teaching its dependency
extractor to skip the block is stated as an obligation here and delivered there.
Assigning waves is milestone work and #941 owns it. Correcting ADR-014's
milestone misstatement is #894's. Retrofitting the block onto the 137 open
issues is not attempted; the prototype proves the contract on one. Judging
whether a status claim is true is out of scope, exactly as the carryover reader
reads shape and never judgement.

## 4. Design options

Three candidate hosts for the contract. The design record at
`.hexaemeron/design-evidence.json` is the selection interface; this prose only
explains the candidates.

**extend-issue-check.** Add status-block parsing to the existing reader in
`hexctl.py`. Keeps one parser of issue bodies, and the three existing call sites
pick the check up without new wiring. The trade is the host: 578,307 bytes an
agent must read to change it, 134 milliseconds per invocation, and 31 digest
bindings to reconcile on every edit.

**repo-root-script.** A new `scripts/issue_status.py` with its own check-map
scope, following the precedent of `scripts/promise_machine.py` and
`scripts/dead_code.py`. Cheapest by every measure taken: 1,607 bytes of host, 25
milliseconds, no digest bindings. The trade is a second module parsing the same
issue body, which is the second source of truth ADR-014 refused.

**sapheneia-operation.** Put the contract in Sapheneia's durable-record
operation, which owns agent-authored issue and comment shape. Correct by the
roster's own boundaries. The trade is that Sapheneia carries no executable
script, so this still adds a second parser, and 11 digest bindings name its
paths.

The measured matrix eliminates the second and third on the one hard selection
gate, `single-body-parser` at most 1, and leaves one survivor. The chosen design
is the slowest and largest of the three, and that is the trade taken to keep one
reader of the contract.

## 5. Risk register seed

The block is read from an issue body, which is text a stranger can write. The
concerns below are what the audit loop enumerates.

```risk-register
fenced-decoy | markers quoted inside a code span in an issue body | a body whose only markers sit in a fence carries no block, and a quoted specimen decides nothing
unclosed-block | an opened block with no terminator | an unterminated block refuses rather than consuming the rest of the body
duplicate-block | two opened blocks in one body | two blocks refuse, because a body carrying two has made no statement
body-size | an issue body fetched over REST | the existing byte cap refuses an oversized body before parsing, so a decision never rests on unread bytes
control-characters | block content rendered to a terminal | control characters are refused or stripped, matching the carryover row reader
extractor-collision | issue numbers written inside the block | the block is delimited so the Atlas dependency extractor can skip it, and #497 is the specimen of what happens when it cannot
digest-drift | the 31 bindings that pin the controller digest | the step reconciles every binding it invalidates, and the suite names the controller when it does not
```

## 6. Glossary seeds

**Status block.** One span in an open issue's body, delimited by
`<!-- status:start -->` and `<!-- status:end -->`, holding the issue's current
status, supersession, or changed requirement.

**Filing prose.** Everything in the body outside the status block, which records
what was observed when the issue was filed and is not rewritten.

**Stale body.** An open issue whose filing prose states a requirement that later
work has narrowed, subsumed, or invalidated, with no status block saying so.

**Census.** The compilation that turns open issues into the contributor-facing
queue, reading bodies and milestones.

## 7. Sources

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, commit `c148ab9a`, and its
  call sites at lines 4565, 5327 and 8865.
- Pull request https://github.com/wildcat-finance/skills/pull/1040 and its
  `## Carried forward` block.
- `docs/decisions/ADR-014-reallocate-the-live-wave-atlas-from-a-complete-census.md`
  at `9783e263`, including the 2026-08-31 amendment.
- Issues #837, #838, #894, #941, #497, #892, #1030, #884, and this run's #1057.
- `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` and `audit/AUDIT_SYNOPSIS.md`,
  both current under the whole-set check.
- `.hexaemeron/design-evidence.json` and the fifteen reports under
  `.hexaemeron/reports/`, each naming the exact command that produced it.

## 8. Signals, and the questions behind them

Two questions, both asked by whoever is choosing the next job rather than by an
operator at three in the morning, because this check runs from a terminal and a
workflow rather than as a service.

**"How many open issues have a body nobody has reconciled against `main`?"** The
report-only staleness command emits one count and one line per issue, so the
number moves visibly rather than being rediscovered by hand.

**"Did this issue's block change, and when?"** The block records its own date,
and GitHub's `lastEditedAt` carries the edit time, so a reader can tell a fresh
statement from one that predates the work it claims to describe.

The step that adds the staleness command emits both. Ephoros owns what each
signal must carry.

## 9. Boundaries, per capability

Two boundaries, both on text from outside the process.

**A candidate body read from a local path.** Worth taking because a body is
checked before it is published. The control is the existing bounded read with
its byte cap, reused rather than reimplemented.

**An issue body fetched from GitHub over REST.** Worth taking because the check
must work on a filed issue. The controls are the existing byte cap, the existing
refusal of a body above it, and treating every field as data. Phylax owns the
boundary list and the controls.

No new subprocess, no new credential, no new dependency, and no new network
destination beyond the GitHub REST reads the reader already performs.

## 10. The budget, or its absence

None, and here is why. The selected design's invocation cost was measured at 134
milliseconds against 25 for the cheapest alternative, and that difference is
recorded in the design matrix as the trade taken rather than as a budget to
hold. The check runs once per issue from a terminal or a workflow step, so a
hundred milliseconds is not a cost anyone waits on. The measurement command is
`python3 .hexaemeron/reports/measure.py --candidate extend-issue-check
--criterion check-latency`, and it stays available if that judgement is ever
questioned. Metron owns what a budget carries.

## 11. The fail-closed posture

A malformed block refuses and names what is wrong, in the shape the filing
contract already uses: both questions reported together so a filer fixing one
does not discover the other on the next attempt. An absent block is not a
refusal, because most bodies will not carry one and absence is the ordinary
case.

The staleness command is report-only and never gates, following ADR-053's
posture for dead-code discovery. It reports; a person decides.

A fix carries a test that fails against the unfixed tree and passes against the
fixed one, and the guard for the decoy case is the `decoy-safe` conformance
criterion, which blocks step 1 until its report exists. Elenchus owns the triage
order and the guard rule.

## 12. Decisions and their homes

Two decisions are expensive to reverse and one is already recorded.

**Authorising a body write at all** is recorded, in the ADR-014 amendment merged
as `9783e263`. Nothing further is owed.

**The marker contract** fixes bytes that other readers will match, including a
repository this run cannot change. It earns its own record at
`docs/decisions/ADR-0NN-fix-the-issue-status-block-markers.md`, numbered at
merge per #888, stating the exact delimiters, the one-block rule, and the
obligation the Atlas extractor inherits.

**Keeping one parser** is the selected design's whole justification and its cost
is 31 digest bindings per change. That belongs in the same record rather than a
second one, because a reader asking why the slow host was chosen is asking about
the marker contract's owner. Hypomnema owns which decisions earn a record.
