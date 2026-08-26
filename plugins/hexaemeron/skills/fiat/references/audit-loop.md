# Audit loop

Budget accordingly: this phase is expected to take longer than the
implementation it audits. The loop runs the security suite against the
step's branch, logs everything, fixes on a stacked branch, and repeats
until a round comes back clean or the remaining leads are judged not worth
another pass.

## One round

1. Run the suite recorded in the `security_suite` receipt, in order: the
   `x-ray` pass first, then `solidity-auditor`. Both are vendored under
   `$PLUGIN_ROOT/skills/<name>/` (as defined in the entry skill) -- read
   each SKILL.md and follow
   it. Give each the step's full diff and the contracts it touches, not a
   summary. When the step ships Solidity under Foundry or Hardhat and
   `fizz` is in the suite, build or refresh the invariant fuzz suite on
   round 1 and re-run its campaigns on later rounds where contracts
   changed; campaign failures are findings like any other.
   The Warden packet also carries the exact source-bound `runbook_step`.
   For a fix, take the test command, report format, and report file from that
   step, run Elenchus against the fixes commit, and return its exact verdict.
2. Prepare every finding for the run's audit file, even when the count is
   zero. `init` derives it as `audit/rounds/<run branch with separators
   flattened>.md`, one record per run, and `hexctl next` names the exact path on
   every `audit-round` directive. Read it from there or from
   `config audit.log_path` rather than assuming a shared file: appending to one
   put the record in `sync-run`'s overlap set on every integration where
   anything else had merged. `audit/AUDIT.md` holds every round written before
   that change and takes no new ones.

   ```markdown
   ## Step <n>, round <r> -- 2026-08-23T02:17:46Z

   Audit schema: fiat-audit-round/v2

   Covered: <risk-id>=reviewed; <risk-id>=not-applicable

   Not checked: <negative space, or "none">

   Elenchus verdict: <guarded, unguarded, passed, inconclusive, or null>

   | id | severity | file | finding | status |
   | --- | --- | --- | --- | --- |
   | S3-R2-01 | high | src/Market.sol | ... | fixed in <sha> |

   Leads not pursued: <what and why, or "none">
   ```

   Before appending, freeze the table shape and protected evidence inventory,
   then apply Sapheneia's bounded audit-record operation; compact connective
   and process prose only. Compare the candidate item by item and refuse the
   append if it drops or changes a finding, qualification, unknown, negative
   result, identifier, number, link, severity, verdict, status, or unpursued
   lead. Existing audit history is append-only and stays untouched.

   Version 2 belongs to the per-run topology: the path identifies the run and
   the heading identifies only the step, round, and UTC time. The timestamp
   grammar is exactly `YYYY-MM-DDTHH:MM:SSZ`; offsets and fractional seconds
   are not accepted. Historical topic-bearing `fiat-audit-round/v1` records
   stay readable but are not
   reinterpreted as version 2. An explicitly tagged record must match its own
   grammar; untagged historical records remain legacy prose.

3. Apply fixes on the stacked branch: `<step-branch><suffix>` (suffix from
   `config audit.stacked_suffix`, default `--audit`), with a PR targeting
   the step branch. Fixes accumulate there across rounds; the audit file and its
   regenerated sibling commit alongside them. A legacy `AUDIT.md` source uses
   `AUDIT_SYNOPSIS.md`; `audit/rounds/<run>.md` uses
   `audit/rounds/<run>.synopsis.md`. Warden owns both changes in the same signed
   commit; the controller never rewrites either.
4. Record the round. The controller resolves and reads the configured log once
   and refuses a different `--log`. The latest stored same-log end offset is
   the next boundary. With no stored offset, the configured path's regular blob
   at the last locally verified commit is the baseline; a Git-proved absent path
   is byte zero. Missing, malformed, mismatched, oversized, changed, or
   unavailable evidence refuses rather than falling back. Only the appended
   delta is decoded and line-checked. It must have the exact separator implied
   by the preceding byte and contain one raw record in the grammar above at EOF.
   Earlier Markdown is not parsed or revalidated. Every check finishes before
   state or ledger mutation. The captured full log is rendered by the same
   bounded synopsis code, and its committed sibling must match fresh bytes.
   A missing, stale, lossy, oversized, or over-budget view refuses. The receipt
   records the canonical log path, schema, record timestamp, entry SHA-256,
   log end offset, and synopsis SHA-256 without printing record content:

   ```text
   hexctl audit-round --findings <n> --log <the directive's log_path> \
     --audit-filter sapheneia:sapheneia \
     --fixes-commit <sha> --elenchus-verdict <value>
   ```

   `--log` is optional and checked: supply it and it has to name the file the
   directive named, or the round is refused and records nothing. Omit it and the
   round records that same path, because the loop already required the record to
   go there. Either way the receipt cannot name a file the round never opened.

   `--audit-filter sapheneia:sapheneia` is required on every round, whether it
   found anything or produced a fix. The controller checks and records this
   exact checked operator declaration before mutating state or the ledger. It is
   not semantic proof that the Sapheneia pass preserved the candidate; the Warden's
   item-by-item comparison remains the evidence for that claim.

   `<value>` is exactly `guarded`, `unguarded`, `passed`, or `inconclusive`.
   The two flags are conditional as a pair: a fixes commit without a verdict,
   or a verdict without a fixes commit, is refused. A round with no fixes
   commit omits both and records `elenchus_verdict: null`. That form is
   complete for a Solidity round. A non-Solidity round owes the
   three lint exits as well, which the section below sets out; `hexctl next`
   names them when they are owed.

5. Re-run from 1 against the fixed tree. The next round audits the tree
   with fixes applied, so a regression introduced by a fix gets caught.

## Exits

- **Clean round.** `--findings 0` recorded, then `hexctl done audit`. When
  earlier rounds found anything, the close demands fixes evidence
  (`--fixes-ref` or a `--fixes-commit` on some round).
- **No further leads.** Findings remain that are, on judgement, not worth
  another round (out of prototype scope, accepted risk, gas nits). Close
  with `done audit --no-further-leads --reason "..."` and leave the open
  items in the audit file marked `accepted`, with the reason.
- **Max rounds.** At `config audit.max_rounds` (default 8) the controller
  refuses further rounds and `next` returns `audit-verdict`: stop and put
  the choice to the user.

## Folding

`config audit.fold` is false by default: the stacked PR stays open as a
review artefact and the step's PR body links it. Set it true to merge the
stacked branch into the step branch once the loop closes, before the prose
phase.

Steps chain, so an unfolded fix branch costs more than a stray review
artefact: the next step branches from this step's branch, and fixes parked
elsewhere are missing from every step above it and from the run branch that
finally lands. Either set `config audit.fold true` for the run or commit the
fixes onto the step branch itself before the prose phase. Leave fixes on an
unmerged side branch only when nothing further will build on this step.

## Non-Solidity steps

When a step touches no Solidity and no configured skill applies, the round
is still real, and it has a mechanical part. Run the three bundled lints
against the changed tree and require exit 0 from each:

```text
python3 "$PLUGIN_ROOT/skills/phylax/scripts/phylax.py" <changed paths>
python3 "$PLUGIN_ROOT/skills/ephoros/scripts/ephoros.py" <changed paths>
python3 "$PLUGIN_ROOT/skills/hypomnema/scripts/hypomnema.py" <changed docs>
```

A non-zero exit is a finding like any other: log it, fix it on the stacked
branch, and run the next round against the fixed tree. Then review the diff
for the risk register's concerns the lints cannot see, log the result, and
record the round. The suite waiver in the `security_suite` receipt covers why
the Pashov pair did not run; it does not excuse skipping the look, and it does
not excuse skipping the lints.

The controller takes the three exits as fields, and refuses the round without
them:

```text
hexctl audit-round --findings <n> --log <the directive's log_path> \
  --audit-filter sapheneia:sapheneia \
  --phylax-exit <n> --ephoros-exit <n> --hypomnema-exit <n>
```

`next` names the exact audit-filter obligation on every round and the three
lint flags when the round owes them, so each requirement arrives before the
refusal does. A round reporting zero findings beside a non-zero exit is refused
as well: the log would otherwise say a lint failed while the ledger said the
round was clean.

Which rounds owe them comes from the `security_suite` receipt. A waiver means
these three are the mechanical part. A recorded list of suite ids means the
Pashov pair ran. Anything else is not a suite that ran, so the lints are
required. `config set solidity true` overrides that for a run whose receipt
cannot be read but which really is a Solidity one, and the override records
itself on the ledger.

When a round surfaces a failure -- a test gone red, a lint that will not come
clean, behaviour that stopped matching -- work it under `elenchus`: reproduce,
reduce, fix the mechanism, and guard it before the next round.

## Honesty

Log only rounds that ran. A findings count of zero asserts the suite
executed against the current tree and returned nothing -- if the suite did
not run, there is no round to record, and saying otherwise poisons the
ledger the whole loop stands on.

The verdict is checked-and-recorded operator evidence associated with a
verified fixes range. Fiat does not attest the Elenchus report bytes or infer
the value from stdout or an exit code. `unguarded`, `passed`, and
`inconclusive` stay distinct, recordable, and non-blocking here; issue 453 owns
the later evidence binding and production gate.
