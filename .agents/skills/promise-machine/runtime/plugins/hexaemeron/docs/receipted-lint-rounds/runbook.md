# Runbook: receipted lint results on hexctl audit-round

Three steps. Each is one pull request stacked on the one below it. Both suites run at
every boundary:

```text
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
```

The second is 176 of 177 at entry and stays there. `ForgeReports` errors because
`forge` cannot be installed in this container, which is true on `main` as well.

## Step 1: Classify a round, and wire up the config key that was already there

**Goal.** Give the controller one function that answers whether a round must carry
lint results, driven by the `security_suite` receipt with the `solidity` config key as
the override. No change to what `audit-round` accepts.

**Entry.** The run branch `fiat/receipted-lint-results-as-structured-fields-on-h` off
`main` at `f7d76cf`. `DEFAULT_CONFIG["solidity"]` is `"auto"` and nothing reads it.

**Exit.** `solidity_round(state)` returns False when the `security_suite` receipt is a
waiver string, True when it is a list of ids, and follows the config key when that key
is `true` or `false` rather than `auto`. Both suites green, with the Hexaemeron count
up by the new tests and still 1 error from `forge`.

**Files.**

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` (the classifier, and the config
  key validated where the other config values are)
- `plugins/hexaemeron/docs/receipted-lint-rounds/study.md` (new, the study)
- `plugins/hexaemeron/docs/receipted-lint-rounds/runbook.md` (new, this file)
- `plugins/hexaemeron/tests/test_hexctl.py` (tests for the classifier)

**Tests.** The classifier against: a waiver string, a waiver with different casing and
leading space, a list of suite ids, an empty list, a receipt that is neither, and each
of the three config values. A rejected `config set solidity` value. Expect roughly 12
new tests.

## Step 2: Take the three lint results, and refuse a non-Solidity round without them

**Goal.** `audit-round` accepts `--phylax-exit`, `--ephoros-exit` and
`--hypomnema-exit`, requires all three on a non-Solidity round, stores them on the
round, and refuses a round that reports no findings beside a non-zero lint exit.

**Entry.** Step 1's exit state.

**Exit.** A non-Solidity round without the three flags is refused with a message
naming them. A complete round records all three on the ledger. A round with
`--findings 0` and any non-zero exit is refused. A Solidity round still works with no
lint flags. A state file written before this step still loads and still reports.
Both suites green.

**Files.**

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` (`cmd_audit_round`, the parser,
  and the readers that must tolerate an absent field)
- `plugins/hexaemeron/tests/test_hexctl.py` (the new refusals, and the 21 existing
  `audit-round` call sites)

**Tests.** The refusal with none of the three, with one missing, and with two missing.
Acceptance with all three. The consistency refusal, and its inverse: a non-zero exit
beside a non-zero findings count is accepted. A Solidity round unchanged. A round
recorded by the previous version of the controller still read by `done audit`, `next`
and `status`. Non-integer, negative and float exits refused by the parser. Expect
roughly 20 new tests, plus the existing call sites updated.

## Step 3: Say so everywhere, then demonstrate

**Goal.** Bring Fiat's own instructions, the audit-loop reference, the ledger and the
marketplace prose into agreement with the new receipt, and run the new controller
end to end.

**Entry.** Step 2's exit state.

**Exit.** `SKILL.md`'s receipt table shows the three flags on the `audit-round` row.
`references/audit-loop.md` states that the round is recorded with the exits rather
than only with the outcomes in prose. `EVOLUTION.md` carries one new row on the
evolution axis with a recomputed digest, and the held frontier moves. Every
marketplace-context block and the root selection table agree. The demonstration below
runs against a throwaway state directory and behaves.

```text
hexctl audit-round --findings 0                      # refused, names the three flags
hexctl audit-round --findings 0 --phylax-exit 0 \
  --ephoros-exit 0 --hypomnema-exit 0                # accepted
```

Both suites green.

**Files.**

- `plugins/hexaemeron/skills/fiat/SKILL.md` (the receipt table and the frontmatter
  version)
- `plugins/hexaemeron/skills/fiat/references/audit-loop.md`
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`
- `plugins/hexaemeron/README.md`, `plugins/hexaemeron/AGENTS.md` and the other
  surfaces carrying the shared context block
- `.claude-plugin/marketplace.json`, `plugins/hexaemeron/.claude-plugin/plugin.json`,
  `plugins/hexaemeron/.codex-plugin/plugin.json`, `.agents/skills/fiat/SKILL.md`,
  root `README.md`

**Tests.** No new tests. `tests/test_evolution_contract.py`,
`tests/test_marketplace_prose.py` and `plugins/hexaemeron/tests/test_fiat_skill.py`
are the proof, plus the demonstration.
