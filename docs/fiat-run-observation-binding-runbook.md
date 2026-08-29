# Runbook: bind companion run observations to Fiat receipts

### Source receipts

```text
study sha256: 9b368f9690686e832bf272db2e999813e907db82e2540fa64cc028fc6668dd92
starting ref: 5d6fc67bb6c861f2be631eef2d7bef3c01c73e84
```

The run has one capability and one step. Assemble the complete surface before
claiming any green product gate. The observation-binding receipt is
non-authorising: ordinary `hexctl verify` and delivery transitions remain
independent of observer availability. The explicit
`hexctl verify --observations` claim is the only transition that a missing or
failed observation blocks.

## Step 1: Bind and verify selected observation prefixes

**Goal.** Ship one versioned Fiat receipt that binds a validated companion
observation prefix to the immediately preceding ledger receipt, preserves
unbound tails, and refuses only the explicit dependent observation claim.

**Entry.** Exact branch cut from
`5d6fc67bb6c861f2be631eef2d7bef3c01c73e84`; controller state names issue #436,
this step, and the receipted study digest above. Before editing, demonstrate
that `hexctl observe --help` is absent and the focused normal-binding test does
not exist on the entry tree. Preserve both red results.

Signed local commit `6d0589ed813c4ec61184ed391caeff2d9572f638` is
prior art from the halted ADR-023 run. Mason may transplant its five-path
runtime and guard surface in one operation before assembling the remaining
ADR-024 tree. Its partial checks are not evidence for this run; every test and
gate below runs only after the complete declared tree exists.

**Exit.** The following all hold:

1. `hexctl observe` records either a checked available prefix or one explicit
   non-available capture state against the immediately preceding ledger entry,
   without changing the current phase.
2. `hexctl verify` remains green for legacy and observation-failed states.
   `hexctl verify --observations` recomputes every bound prefix or returns one
   stable `FOB` finding with a bounded recovery.
3. `scripts/run_observation.py check-prefix` accepts a safe unfinished prefix,
   retains all existing full-record checks, and refuses malformed or unclosed
   capability boundaries.
4. Replacement, truncation, reordered events, wrong-run association,
   event-count mismatch, contract drift, failed redaction, missing binding, and
   appended-event confusion have committed guards. Appending preserves the
   earlier prefix but reports the later bytes as unbound.
5. Existing version-1 ledgers verify without migration, generated Promise
   copies are byte-identical, the new promise is coverage-bound, ADR-024 records
   the decision, and the study and runbook copies are byte-identical to their
   receipts.
6. The demo test
   `plugins.hexaemeron.tests.test_run_observation_binding.ObservationBindingTests.test_normal_prefix_binds_to_the_selected_receipt`
   passes, followed by every command in Tests and Gates.

**Files.** Scope is limited to:

- `PROMISE_MACHINE.md` and the 14 generated plugin copies;
- `audit/AUDIT.md` for Warden's append-only round records;
- `docs/decisions/ADR-024-bind-run-observation-prefixes-to-fiat-receipts.md`;
- `docs/fiat-run-observation-binding-v1.md`;
- `docs/fiat-run-observation-binding-study.md`;
- `docs/fiat-run-observation-binding-runbook.md`;
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`;
- `plugins/hexaemeron/skills/fiat/SKILL.md`;
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`;
- `plugins/hexaemeron/tests/fixtures/run-observation-binding/cases.json`;
- `plugins/hexaemeron/tests/test_fiat_skill.py`;
- `plugins/hexaemeron/tests/test_hexctl.py` only if shared controller helpers
  need a compatibility guard;
- `plugins/hexaemeron/tests/test_run_observation_binding.py`;
- `scripts/run_observation.py`;
- `tests/test_run_observation.py`;
- `tests/promise_machine_coverage.json`;
- `tests/test_promise_machine_contract.py`;
- `.horos/boundary.json` only if the deterministic Horos scan proves the
  tracked-tree boundary changed.

No other file is in scope without a receipted study amendment and a re-derived
runbook. The implementation commit must include the byte-identical published
study and runbook copies. ADR-015 and ADR-022 remain accepted and unchanged;
ADR-024 adds the downstream Fiat choice.

**Tests.** Add the focused binding suite and extend the observation validator
and Promise coverage guards. The fixture manifest must enumerate at least the
normal case and the nine negative mechanisms in Exit. Run, in order:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_run_observation_binding -v
python3 -m unittest tests.test_run_observation -v
python3 -m unittest tests.test_promise_machine_contract -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
```

The source-bound Elenchus inputs for every repair are exact:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py {report}
report format: unittest-json-v1
report file: .elenchus/fiat-run-observation-binding.json
```

Warden must observe each new repair guard red against the unfixed signed parent
before accepting `guarded`. A missing, stale, empty, or infrastructure-failed
report is `inconclusive` and cannot close a finding.

**Disciplines.** phylax: the step accepts an appendable untrusted JSONL path and
must exercise confinement, limits, no-follow reads, and no-echo findings.
ephoros: the receipt and verification output must answer the four operator
questions from the study without new metrics or alerts. metron: none, because
the ceilings are hostile-input bounds and no performance change is claimed.
elenchus: every audit repair needs the exact source-owned reporter contract
above. hypomnema: ADR-024 records the durable evidence-boundary choice and the
operator document owns the interface guidance.

### Gates

Run every command after the complete implementation surface exists:

```bash
cmp -s .hexaemeron/study.md docs/fiat-run-observation-binding-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-run-observation-binding-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-run-observation-binding-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-run-observation-binding-runbook.md
python3 scripts/promise_machine.py sync --check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests scripts
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests scripts
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/ADR-024-bind-run-observation-prefixes-to-fiat-receipts.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-run-observation-binding-v1.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-run-observation-binding-study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-run-observation-binding-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/ADR-024-bind-run-observation-prefixes-to-fiat-receipts.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-run-observation-binding-v1.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-run-observation-binding-study.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/fiat-run-observation-binding-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m py_compile plugins/hexaemeron/skills/fiat/scripts/hexctl.py scripts/run_observation.py plugins/hexaemeron/tests/test_run_observation_binding.py
python3 -m json.tool plugins/hexaemeron/tests/fixtures/run-observation-binding/cases.json >/dev/null
git diff --check
```

The security suite is waived because the declared scope contains Python,
Markdown, and JSON only and changes no Solidity, Foundry, Hardhat, ABI, storage,
or on-chain behavior. Warden still performs the complete Phylax boundary
review and every risk-register disposition. Closure needs an independent
zero-finding round; a finding requires repair and another round. If the eighth
round still finds a defect, halt with one full cumulative carryover packet
before any restart rather than replaying partial trees.
