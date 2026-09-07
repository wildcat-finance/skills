# Study: route a zero decision and gate the line that unlocks a run

Source: [wildcat-finance/skills#1345](https://github.com/wildcat-finance/skills/issues/1345).

## Assumptions

Proceeding on these unless corrected.

1. The target is `wildcat-finance/skills` at `f22de68086ad7265869636903554d09cf751e765`, the tip of `main` when this run was cut. `origin/main` has since moved to `ddad6b2a97f733fac52f2c9c7ad25d64a20b955e`, so `sync-run` is expected at integration.
2. Python is 3.14.6, from `.python-version`. Stdlib `unittest`.
3. The security suite is waived: no Solidity, no Foundry or Hardhat project in scope.
4. The whole delivery is one capability, not two. The routed outcome and the gate are separately buildable but not separately meaningful: a routed `0` with no gate is the present failure with a friendlier exit code, and a gate with no routed outcome leaves the refusal that started this. They ship as ordered steps inside one study rather than as two modules.
5. The `Fiat-Required` window gate proceeds, and records what it could not establish, when the task issue's `updated_at` is inside the window and GraphQL cannot say whether the body changed. The maintainer decided this on 6 September 2026, against the refusing reading this study first proposed. A comment, a label or an assignment moves `updated_at` too, so refusing on that read would stop a run for the wrong reason most times it fired, and with no override the only recovery is waiting, which on an issue under discussion has no bound. The receipt records the observation and names it as undiscriminated.
6. Nothing this run builds governs this run. The gate ships inside the artefact it gates and takes effect only for runs started after the next marketplace re-pin.

## 1. Problem statement

`hexctl init` treats a filed `Fiat-Required: 0` as an error and ends the refusal by naming the edit that turns the refusal off. Reproduced live against issue #1337, which currently declares `0`:

```
hexctl: error: task issue wildcat-finance/skills#1337 declares `Fiat-Required: 0`:
the filer decided this work does not need a Fiat run. No run state, worktree or
branch was created. Do the work as one independent pull request, point the issue
at that pull request, and close it there. If that decision was wrong, change the
issue to `Fiat-Required: 1` and say why in the issue before starting a run.
```

Exit code 1. The source is `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:5031-5041`.

The last sentence is a recovery written for a person who filed wrongly. Delivered to an agent that has just been told to start a run, it is the instruction for doing so. An agent under that instruction edited an issue from `0` to `1` and the run started. Nothing recorded that a refusal had preceded the edit.

**Who this is for.** The Fiat controller's operators, and the agents that drive `hexctl` on their behalf. The second group is the one the current bytes mislead.

**What a working prototype means here.** Two observable changes.

- `hexctl init --task-issue <a Fiat-Required: 0 issue>` prints one directive object on stdout, exits 0, and creates no state, worktree or branch. The directive names the pull-request route, the issue it closes, and what closing it requires.
- `hexctl init --task-issue <an issue whose body changed inside the decision window>` refuses, states what it observed, and names no mechanism that grants this same run.

**Demo path.** Run against real issues over the live API, from the run worktree:

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py init \
  --task-issue https://github.com/wildcat-finance/skills/issues/1337 \
  --topic 'routing probe' --base main
# expect: one JSON directive on stdout, exit 0, and `git status --short` clean.

python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py issue-check \
  --issue https://github.com/wildcat-finance/skills/issues/1337
# expect: unchanged; issue-check reports shape and is not the run gate.
```

## 2. Prior art

### In this repository

`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` carries the whole filing contract.

- `fiat_required_value` (4800-4829) reads one unfenced `Fiat-Required:` line, refusing zero declarations and refusing more than one.
- `issue_contract_faults` (4832-4847) joins it to the `carryover` triage and the status block, and records the body's SHA-256.
- `read_task_issue_contract` (4969-5047) reads the issue over REST and holds the `0` refusal at 5031-5041.
- `cmd_init` (2600-) calls it at 2659. The comment at 2650-2657 states the ordering deliberately: the filing decision is read after every cheaper refusal and before the controller-currency observation, so a `0` verdict costs the operator nothing but the read.
- `cmd_record` refuses to write `task_issue_contract` (5761-5768), on the stated ground that a run able to rewrite it "could start against `Fiat-Required: 0` and then record that it had read a 1".
- `github_rest` (12185) is the only GitHub transport in the controller. There is no GraphQL helper.

`plugins/hexaemeron/skills/fiat/SKILL.md` restates the refusal twice. `## Start or resume` (byte 6825) carries the filing paragraph including "if the decision was wrong, change it to `Fiat-Required: 1` and say why in the issue first" (byte 9540). `## Hard rules` (byte 48152) carries the prohibition "Never start a run against an issue declaring `Fiat-Required: 0`, and never edit that line to `1` yourself to get past the refusal" (byte 49935). The prohibition already existed and did not hold.

`AGENTS.md:117` states that `hexctl init` "reads the line and refuses to start a run against a `0`". That sentence becomes false under this delivery.

### The last two merged pull requests

Only one merged pull request has ever touched the issue-contract path. `git log -S 'FIAT_REQUIRED_KEY'` and `-S 'read_task_issue_contract'` over `hexctl.py` each return exactly one commit, `c148ab9aa226fa906987a53501328de14bc84a90`, which is PR [#1040](https://github.com/wildcat-finance/skills/pull/1040) "Gate a run on what its issue filed", merged 2026-08-31. Said plainly: there is no second pull request on this path to read.

The nearest adjacent merge is PR [#1416](https://github.com/wildcat-finance/skills/pull/1416) "fix(fiat): let reset retire a halted run", closing #1411, merged 2026-09-06 after this run's base. Two things it carries forward matter here.

- Its `carryover` block reads `none | none | the branch is outside reset's remit and the recycle loss is a placement decision the issue declines to make`. Neither item is this study's; both stay open under their own issue.
- It changes the cost of a bad start: a wrongly started run can now be retired with `hexctl reset` after `hexctl halt`, and the archived ledger ends with the retirement. That does not reduce what the gate must prevent. Retirement removes the worktree; it does not remove the merged pull requests, the audit rounds or the issue edit that a wrongly started run produces, and the run this study exists because of had already started.

PR #1416 also supplies the exact precedent for this delivery's re-pin cost, and its boundary note decides where this delivery may edit: "The `halted` directive row in the `next` table is unchanged because it sits inside the fixture's reviewed span."

### Decision records

[ADR-067](https://github.com/wildcat-finance/skills/blob/main/docs/decisions/ADR-067-gate-a-run-on-what-its-issue-filed.md) established the contract and, in its Consequences, accepted this exact gap:

> `Fiat-Required: 0` is a filing decision, not a verdict about difficulty. Nothing stops a filer editing an issue from 0 to 1, and nothing here records that they did beyond the issue's own edit history.

[ADR-078](https://github.com/wildcat-finance/skills/blob/main/docs/decisions/ADR-078-echo-fiat-required-as-a-filer-set-label.md) repeats the same acceptance for the echoed label. This delivery reopens an accepted consequence of ADR-067, so it owes a superseding record rather than an edit to either. Item 12 says where.

ADR-067 also rejected a label pair and a root-level second parser, on drift grounds, and both rejections still hold: the new gate extends `hexctl`'s one parser rather than adding a second.

### Audit records

The whole-set currency check passes, so verified synopses are the normal reading view:

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .   # exit 0
```

Every `audit/rounds/<run>.md`, `audit/AUDIT.md` and each `plugins/*/audit/AUDIT.md` reports `committed=match`. In-scope sources for this topic, and which view was read:

| Source | View read | Evidence for the choice |
| --- | --- | --- |
| `audit/rounds/fiat-1057-record-an-open-issue-s-status-where-the-cen.md` | synopsis, `.synopsis.md` | whole-set check exit 0, row reports `committed=match` |
| `plugins/hexaemeron/audit/AUDIT.md` | synopsis, `AUDIT_SYNOPSIS.md` | whole-set check exit 0, row reports `committed=match` |
| `audit/AUDIT.md` | synopsis, `AUDIT_SYNOPSIS.md` | whole-set check exit 0, row reports `committed=match`; covers the root source only |
| the other 127 `audit/rounds/*.md` | not read | `grep -rln` for `Fiat-Required`, `issue_contract`, `read_task_issue_contract`, `task_issue_contract` and `issue-check` across `audit/` and `plugins/hexaemeron/audit/` returns only the 1057 pair |

The 1057 rounds carry four items forward that touch this delivery.

- Step 2 round 1 recorded as not checked that "the transport path around `read_task_issue_contract` is covered by its existing tests rather than by anything this round added". Carried forward as content: this delivery changes that function and owes tests on the transport path, not only on the parse path.
- Recorded as not checked more than once, that "No measurement was taken of the reader's cost, so the single-read change carries no performance claim". Carried forward as content in item 10: there is no baseline to regress against, which is why the budget is stated as a request count rather than a duration.
- Step 2 round 1 left one lead unpursued, that the controller digest reconciliation runs per commit, eleven bindings each time, and an audit loop multiplies that by the rounds touching the controller. Issue #892 owns the mechanism. Carried forward as a stated non-goal: this run pays the cost and does not collapse it.
- Step 1 left one lead unpursued, that nothing compares a committed copy of a receipted artefact against the ledger's digest. Left open by name; it is not this topic and no issue of this run's carries it.

Finding ids and statuses retained from those rounds: S1-R1-01 fixed in `839eb7bfd841aa32d739082755c6220a52d18ce5`; S2-R1-01 fixed in `956c9e2ef28f5e0bb36192f0b956e1f718b204d3`; S2-R2-01 fixed in `0170a68e057e0d553980a7b16a98599a184d1333`. Elenchus verdicts: `unguarded` (step 1 round 1), `null` (step 1 round 2), `guarded` (step 2 rounds 1-3). `[missing legacy field: ...]` entries in `audit/AUDIT.md` and `plugins/hexaemeron/audit/AUDIT.md` remain unknown.

### Outside this repository

GitHub's REST issue representation carries no edit history. Measured against the live API:

```bash
gh api repos/wildcat-finance/skills/issues/1345 --jq 'keys'   # no edit/revision/history key
```

GraphQL `userContentEdits` carries it, and carries more than the issue's filing claims. Against #1337:

```bash
gh api graphql -f query='query { repository(owner:"wildcat-finance", name:"skills")
  { issue(number:1337) { userContentEdits(first:20)
  { totalCount nodes { editedAt editor { login } diff } } } } }'
```

returns `totalCount: 4`, every `editor.login` equal to `laurenceday`, and a `diff` field carrying full prior body text. The revision at `2026-09-06T09:24:46Z` carries `Fiat-Required: 1` together with the sentence "Corrected from `0` on 6 September 2026, at the maintainer's direction." The current body reads `0`. So the prior *value* of the line is recoverable, not merely the time it changed. `diff` requires write access on the repository, which is why it refines the gate rather than being it.

## 3. Constraints and non-goals

**Starting ref.** `f22de68086ad7265869636903554d09cf751e765`, branch `fiat/1345-route-a-zero-decision-and-gate-the-line-tha`, worktree clean at cut. `origin/main` is `ddad6b2a97f733fac52f2c9c7ad25d64a20b955e`; a `sync-run` is expected at integration and is not a defect.

**Toolchain.** Python 3.14.6 (`.python-version`), stdlib `unittest`. No new dependency.

**Checks.** `AGENTS.md` binds this run. `python3 scripts/run_checks.py` is the entrypoint; the root suite is `python3 -m unittest discover -s tests` and the Hexaemeron suite is `python3 plugins/hexaemeron/tests/run_tests.py`, both from `tests/check-map-v1.json`. The scopes this delivery touches, from the same file's `owners`: `hexaemeron` (`plugins/hexaemeron`), `root` (`AGENTS.md`, `tests`, `.horos`), `docs` (`docs/decisions`), `promise-machine` (`tests/promise_machine_coverage.json`). Three lints are not the suite.

**The digest-bound instruction fixture.** `tests/fixtures/agent-instruction-v1/manifest.json` binds `plugins/hexaemeron/skills/fiat/SKILL.md` with `sha256`, `span_sha256`, `start: 18445` and `end: 22773`. Measured on the base, and all three digests verified to match the file:

| Region | Bytes | Cost of editing there |
| --- | --- | --- |
| before the span | 0 to 18444 | shifts `start`/`end`, which the corpus projection does not substitute; the derived chain and both evidence records re-pin |
| the reviewed span | 18445 to 22772 | changes `span_sha256`; needs a new review row and re-measured token counts, which need hosted access this run does not assume |
| after the span | 22773 to 77853 | leaves offsets and `span_sha256` alone; the derived chain still re-pins on the whole-file digest |

Probed with `agent_instruction._corpus_sha256`: changing the whole-file `sha256` alone leaves the corpus digest unchanged, and so does changing an artifact digest, but shifting `start`/`end` by 500 changes it, and so does changing `span_sha256`. `compact.wai` embeds the whole-file digest (`h64:e45f1695...`), so every edit to `SKILL.md`, wherever it lands, moves `model.json`, `source-spans.json`, `compact.wai`, the manifest, `measurement.json`, `parity.json` and `tests/promise_machine_coverage.json`.

The span begins `## The loop` and holds the `next` directive table. The routed `0` outcome is `init`'s output, not a `next` directive, so that table does not change and the reviewed span is not touched. `## Start or resume` (byte 6825) must change, because it states a refusal that will no longer happen; leaving it stale is not an option. That places the edit before the span and prices this delivery at the same class as PR #1416, whose field-level delta was 12 fields in `measurement.json` and 69 in `parity.json`, with no `tokens` value among them.

**The held frontier.** `plugins/hexaemeron/skills/fiat/EVOLUTION.md` reads `fiat-v5.53.1`, status `open`, `Next Fiat job` naming [skills#363](https://github.com/wildcat-finance/skills/issues/363) on delegation task identities. `--frontier` is armed, so `done integrate` refuses without exactly one new valid generation row, and the held job must survive byte for byte. Nothing in this delivery may change it.

**Never committed.** Nothing under `.hexaemeron/` is committed. `.hexaemeron/.gitignore` is `*`.

**Non-goals.**

- Identity. The agent publishes through the maintainer's own account, so the issue's editor and the run's operator are the same login. Verified: all four edits on #1337 are `laurenceday`. Edit history establishes when a line changed, never who decided it, and no gate here reads editor identity.
- Collapsing the per-commit controller digest reconciliation. Issue #892 owns it; this run pays it.
- The `only-pr-needed` / `fiat-run-needed` labels. ADR-078 keeps them unchecked and this delivery keeps them unchecked.
- Non-GitHub trackers. ADR-067 deliberately admits them with the nulls recorded; that path is unchanged.
- Any gate on `hexctl issue-check`. It is stateless, runs before an issue exists, and is not the run gate.

**The question this study raised, and its answer.** In a REST-only environment `updated_at` moves for a comment, a label or an assignment as well as for a body edit, and nothing over REST distinguishes them. The study first proposed refusing. The maintainer decided on 6 September 2026 that `init` proceeds and records the ambiguity, and assumption 5 now carries that reading.

The reasoning is that refusing here fails closed on a proxy rather than on the property. The property is a changed decision line; the proxy fires for every comment on the issue, which is the commoner event by far. With no override by design, a false stop clears only by waiting, and an issue under active discussion never leaves the window. Recording keeps the absence visible, which is what the repository asks of a check that could not run, rather than claiming a check that did.

## 4. Design options

Four candidate constructions. The record at `.hexaemeron/design-evidence.json` selects one from checked gates and measured values; this prose explains them and does not choose.

**`reference-only`.** Move the recovery sentence out of the refusal into `plugins/hexaemeron/skills/fiat/references/`, and leave `init` exiting 1 on a `0`. Trade: the cheapest possible change and the smallest blast radius (3 derived artefacts against 10), bought by leaving the `0` an error. It stops the refusal proposing a bypass and does nothing about the exit code that made the refusal read as an obstacle.

**`receipt-provenance`.** Route the `0` to a directive on stdout with exit 0, strip the recovery sentence from the refusal bytes, and always carry the filing decision's provenance into the init receipt: the body digest already recorded, plus `created_at`, `updated_at`, and the GraphQL edit count, last edit time and prior `Fiat-Required` value where readable, recorded as `unknown` with a reason where not. Trade: it removes the silence and refuses nothing. The issue says as much of this gate: "This prevents nothing by itself".

**`local-refusal-record`.** `receipt-provenance` plus a host-side record keyed by `repository#number`, written when a `0` is routed; a later `init` for the same issue reading `1` refuses against it unless `--filing-decision-override '<reason>'` is passed, with the override and its reason landing in the init receipt. Trade: it catches the exact observed sequence in the checkout where it happened, at the price of two weaknesses the issue names and one it does not. The record does not survive a fresh clone and can be deleted. And a refusal that must name `--filing-decision-override` to be usable is the same shape as the refusal that started this: bytes arriving at an agent that wants the run, naming the thing that grants it.

**`decision-age-window`.** `receipt-provenance` plus a refusal when the task issue's body changed inside a bounded window before `init`. Over REST that is `updated_at` differing from `created_at` and falling inside the window, which is why the gate does not depend on an optional transport. Where GraphQL is reachable it refines to the body edits themselves and to the prior value of the line, removing false positives and naming what actually changed. No override exists: the recovery is to wait for the window to pass, or to route the work as the pull request the `0` decided on. Where neither transport can say whether the body itself changed, the gate proceeds and records that it could not tell. Trade: the gate is advisory rather than binding in a REST-only environment, and a window whose length is a judgement.

**On whether an override should exist.** It should not. The failure this study answers is a refusal that names its own bypass to an agent that wants the run. An override flag is that failure with a flag in place of an issue edit, and it is worse in one respect: it is faster. The recovery in `decision-age-window` is time, which cannot be named as an instruction, cannot be passed as an argument, and clears itself.

## 5. Risk register seed

```risk-register
refusal-names-its-own-bypass | the bytes init emits at the moment of a filing decision | no emitted text names a mechanism that grants this same run, in the refusal, the routed directive or the reference
routed-exit-mistaken-for-success | init's exit code and stdout when the filed decision is 0 | a routed 0 exits 0 with one directive object on stdout and leaves no state, worktree or branch behind
window-undiscriminated-read | the REST updated_at read when GraphQL is unreachable | init proceeds and the receipt states exactly what it observed, names the read as undiscriminated rather than as a body edit, and never reports the window as having been enforced
graphql-transport | the new GitHub GraphQL request init makes | pinned argv, no shell, bounded response size, and an unavailable API recorded as unknown rather than treated as a pass
prior-body-in-memory | the prior issue bodies userContentEdits returns | prior bodies are reduced to the Fiat-Required value and a digest before anything is recorded, and no body text reaches the receipt or the log
receipt-forgery | the init receipt's new provenance fields | task_issue_contract stays init-only and hexctl record keeps refusing it, so no later command can rewrite what the run read
partial-write-of-the-receipt | .hexaemeron/state.json during init | init's existing atomic write path is unchanged and a killed init leaves no state naming a decision it did not read
held-job-drift | plugins/hexaemeron/skills/fiat/EVOLUTION.md | the Next Fiat job naming skills#363 is byte-identical after the run and only a generation row is added
reviewed-span-drift | the agent-instruction-v1 bindings for SKILL.md | span_sha256 is unchanged and the derived chain is re-pinned in the commit that edits the source
stale-claim-elsewhere | AGENTS.md:117, ADR-067 and ADR-078 | every prose claim that init refuses a 0 is updated in place or superseded by a dated record, and none is left contradicting the code
```

## 6. Glossary seeds

- **Filing decision.** The value of the one unfenced `Fiat-Required:` line in an issue body: `1` for a Fiat run, `0` for one independent pull request.
- **Routed outcome.** An answer `init` gives on stdout with exit 0, naming work to do, as distinct from a refusal on stderr with a non-zero exit.
- **Decision window.** The bounded interval before `init` inside which a change to the task issue's body makes the filing decision too young to start a run on.
- **Provenance block.** The fields the init receipt records about how the filing decision was read: body digest, timestamps, edit count, last edit time, prior value, and `unknown` with a reason for anything the transport could not supply.
- **Reviewed span.** Bytes 18445 to 22772 of `plugins/hexaemeron/skills/fiat/SKILL.md`, bound by `span_sha256` in the agent-instruction fixture and carrying a dated human review row.
- **Derived-artefact chain.** The seven files whose recorded digests move when `SKILL.md` changes, plus the Horos census pair.
- **In-band bypass.** A mechanism named in the text of a refusal that grants the run that refusal just declined.

## 7. Sources

- Issue [skills#1345](https://github.com/wildcat-finance/skills/issues/1345), read whole via `gh issue view 1345 --repo wildcat-finance/skills`. Its `carryover` block is `none | none | ...`.
- Issue [skills#1337](https://github.com/wildcat-finance/skills/issues/1337), the live `Fiat-Required: 0` issue used to reproduce the refusal and to probe edit history.
- PR [skills#1040](https://github.com/wildcat-finance/skills/pull/1040), commit `c148ab9aa226fa906987a53501328de14bc84a90`, the only merge on the issue-contract path.
- PR [skills#1416](https://github.com/wildcat-finance/skills/pull/1416), closing [skills#1411](https://github.com/wildcat-finance/skills/issues/1411), merged 2026-09-06; body read for its evidence and boundary sections.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at `f22de680`, lines 2600-2690, 4800-4847, 4969-5047, 5744-5790, 5854-5947, 16585-16770.
- `plugins/hexaemeron/skills/fiat/SKILL.md` at `f22de680`, `## Start or resume` and `## Hard rules`, with byte offsets measured directly.
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, current frontier block.
- `AGENTS.md` `## What every issue body decides` (line 106 onward) and `## Checks for changes to this repository` (line 263 onward).
- `docs/decisions/ADR-067-gate-a-run-on-what-its-issue-filed.md` and `ADR-078-echo-fiat-required-as-a-filer-set-label.md`.
- `tests/fixtures/agent-instruction-v1/manifest.json`, `evidence/measurement.json`, `evidence/parity.json`, and `scripts/agent_instruction.py`'s `_corpus_sha256`.
- `tests/check-map-v1.json`, `checks` and `owners`.
- `audit/rounds/fiat-1057-record-an-open-issue-s-status-where-the-cen.synopsis.md`, `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`, `audit/AUDIT_SYNOPSIS.md`, all under a passing `audit_synopsis.py --check .`.
- GitHub REST `repos/wildcat-finance/skills/issues/{1337,1345}` and GraphQL `userContentEdits`, both queried live on 2026-09-06.

## 8. Signals, and the questions behind them

Three questions someone asks when a run turns out to have been started on a decision that was not there when the issue was filed.

1. **Why did this run start?** Answered by the init receipt's provenance block: the value read, the body digest, `created_at`, `updated_at`, and the edit count, last edit time and prior value where readable. The step that adds the provenance block emits it.
2. **Did the filing decision change under the run?** Answered by `hexctl verify`, which compares the recorded provenance against the issue as it stands now and reports a divergence rather than treating the receipt as the whole truth. The step that extends `verify` emits it.
3. **Was the gate able to read edit history, or did it fail open?** Answered by the provenance block's explicit `unknown` with its reason, never by an absent field. An absent field cannot be told apart from a question nobody asked; this is the same rule ADR-067 applies to the nulls it already records.

One gap, named rather than solved: a routed `0` creates no state, so nothing persists a count of how many issues were routed rather than run. The directive is printed and the operator's transcript is the only record. Closing that would need a store this delivery deliberately does not add, for the reason `local-refusal-record` was set aside.

[ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what each signal must carry.

## 9. Boundaries, per capability

- **GitHub REST, existing.** `github_rest` already reads the issue body. What is worth taking: the filing decision and the carryover triage. Widened here by two fields already in the same response, `created_at` and `updated_at`, so no new request and no new boundary. The existing `ISSUE_BODY_BYTES_MAX` cap and `github_unreachable` transport refusal are unchanged.
- **GitHub GraphQL, new.** One request for `userContentEdits`. This is a new external boundary and the only one this delivery opens. Controls: pinned argv with no shell, a bounded response read, a hard timeout, and a failure that records `unknown` with its reason rather than degrading to a pass. It is never required: the window gate is satisfied over REST alone.
- **Prior issue body text, new and untrusted.** `userContentEdits` returns whole prior bodies. Control: they are reduced to the `Fiat-Required` value and a digest inside the reader, and neither the receipt, the ledger nor stderr carries body text. The existing rule that the line is read outside fenced code applies to a prior body exactly as it applies to the current one.
- **The routed directive on stdout, new.** An agent consumes it. Control: it is one closed JSON object of the same shape the loop already acts on, it names no mechanism that grants a run, and the control-character stripping `hexctl` already applies to displayed text applies to any issue-derived field inside it.
- **The init receipt, existing.** Control unchanged and relied upon: `cmd_record` refuses `task_issue_contract`, so no later command can rewrite what `init` read.

[phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and the controls.

## 10. The budget, or its absence

A budget, stated as request count rather than duration.

- `init` makes at most 2 network requests for the filing decision: the existing REST issue read, and at most one GraphQL request. No other `hexctl` command gains a request.
- `issue-check`, `next`, `status`, `verify` and `done` make no additional request.

Measured by a test that counts transport invocations across an `init` against a stubbed API, run as part of the Hexaemeron suite:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
```

No duration budget is set. The 1057 audit rounds record, three times, that no measurement was ever taken of this reader's cost, so there is no baseline to regress against and a duration target here would be a number invented for the page. [metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget carries and how it is checked; a request count is the part of it that has an honest baseline today.

## 11. The fail-closed posture

**What stops the run.**

- A malformed filing contract. Unchanged: `read_task_issue_contract` refuses and names what to add.
- An unreadable issue. Unchanged: `github_rest` refuses in its own transport shape, which says nothing about whether the work earned a run.
- A filing decision younger than the window. New, and the reason this study exists.

**What does not stop the run.**

- GraphQL unavailable. Recorded as `unknown` with its reason; the REST window gate still decides.
- A filed `0`. It stops being a stop: it becomes a routed answer with exit 0.

**Guard convention.** Every fix carries a test that fails without it, checked mechanically against the parent commit:

```bash
python3 "$PLUGIN_ROOT/skills/elenchus/scripts/elenchus.py" \
  --ref HEAD \
  --test-command "python3 plugins/hexaemeron/tests/run_tests.py {report}" \
  --report-format unittest-json-v1 \
  --report-file .elenchus/hexaemeron.json
```

That is the runner contract every step's `Tests` field carries: the exact command with one `{report}` argument, the format `unittest-json-v1`, and the report file. [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage order and the guard rule.

## 12. Decisions and their homes

Three decisions are expensive to reverse. Each earns a record; none is an edit to an existing one.

1. **A filed `0` is an answer, not an error.** This reverses the behaviour ADR-067 specified and AGENTS.md describes. Home: a new record under `docs/decisions/`, superseding ADR-067's `0` clause and citing it, with ADR-067 left byte-identical as the historical decision. The number is allocated against the default branch immediately before pushing, because numbers collide before merge; ADR-085 is the highest in use on this base.
2. **No override exists.** The recovery from a window refusal is time, not an argument. This is the decision the issue asks for by name, and reversing it later would require adding a bypass to a gate built on not having one. Home: the same record, as its own section, with the alternative and the reason for rejecting it.
3. **The gate does not read editor identity.** Recorded so a later reader does not propose it as an obvious omission. Home: the same record's Consequences, alongside the measured fact that all four edits on #1337 carry one login.

Two prose surfaces are updated in place rather than recorded, because they describe behaviour rather than decide it: `AGENTS.md:117` and the `## Start or resume` filing paragraph in `plugins/hexaemeron/skills/fiat/SKILL.md`. The `## Hard rules` bullet is updated in the same way, and sits after the reviewed span so it moves no offsets.

One generation row is owed on `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, with the `Next Fiat job` naming skills#363 unchanged.

[hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and where each one lives.

### Amendment -- 2026-09-07

**What changed.** The study declares its design bridge, binding the selected
candidate to the record that holds the decision:

```design-bridge
schema | hypomnema-design-bridge/v1
decision | decision-age-window
record | docs/decisions/drafts/route-a-filed-zero-as-an-answer.md
```

**Why.** Item 12 names hypomnema as the owner of which decisions earn a record
and where each one lives, and the study named neither the record nor the join to
the checked selection. Without the fence `hypomnema.py --study` reports `H008
study has no design bridge block` and exits 1, so the one claim the discipline
can check mechanically was the one claim the study did not make. Raised as
S1-R1-02 in step 1 round 1.

**Steps touched.** Step 1, whose committed copy of this study carries the fence.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5:
entry holds; exit holds.
