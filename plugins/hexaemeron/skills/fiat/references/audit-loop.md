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
2. Append every finding to the audit file (`config audit.log_path`,
   default `audit/AUDIT.md`), even when the count is zero:

   ```markdown
   ## Step <n>, round <r> -- <date>

   | id | severity | file | finding | status |
   | --- | --- | --- | --- | --- |
   | S3-R2-01 | high | src/Market.sol | ... | fixed in <sha> |

   Leads not pursued: <what and why, or "none">
   ```

3. Apply fixes on the stacked branch: `<step-branch><suffix>` (suffix from
   `config audit.stacked_suffix`, default `--audit`), with a PR targeting
   the step branch. Fixes accumulate there across rounds; the audit file
   commits alongside them.
4. Record the round:

   ```text
   hexctl audit-round --findings <n> --log audit/AUDIT.md --fixes-commit <sha>
   ```

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

## Non-Solidity steps

When a step touches no Solidity and no configured skill applies, the round
is still real: review the diff for the risk register's concerns, log the
result, record the round. The suite waiver in the `security_suite` receipt
covers why the Pashov pair did not run; it does not excuse skipping the
look.

## Honesty

Log only rounds that ran. A findings count of zero asserts the suite
executed against the current tree and returned nothing -- if the suite did
not run, there is no round to record, and saying otherwise poisons the
ledger the whole loop stands on.
