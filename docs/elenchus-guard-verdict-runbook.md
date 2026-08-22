# Runbook: carry the Elenchus guard verdict into Fiat audit rounds

This generation run starts at
`cd48583be2caeace32b14638dbdd85692b73a004` on
`fiat/327-elenchus-2-feed-the-guard-verdict-into-fiat`. The installed
controller created the run before it understood guard declarations. Fresh
fixtures and the receipted runbook bytes prove the new behaviour.

Every step starts from the exact ref emitted by `hexctl next`. Every step ends
with its focused and repository checks green. The implementation phase records
the red-before-fix result before production code changes. Every Fiat-created
commit uses `git commit -S`, passes `git verify-commit`, and contains exactly
one of each required trailer:

```text
Co-authored-by: Shoggoth <shoggoth@wildcat.finance>
Wildcat-Origin: shoggoth
```

After a push or GitHub merge, GitHub must report `verified: true` and
`reason: valid` for every new commit.

## Step 1: Install the guard-report test path and accepted specification

**Goal.** Commit exact copies of the accepted study and runbook, then add the
repository-owned unittest report emitter needed to test guard declarations in
the next step.

**Entry.** Exact base `cd48583be2caeace32b14638dbdd85692b73a004`; the
study and runbook receipts are accepted; no product source has changed.

**Exit.** The tracked study and runbook match their receipted sources byte for
byte. A standard-library emitter runs named unittest selectors and writes one
fresh `unittest-json-v1` report to the caller's exact path. Its own tests cover
assertion failure, error, skip, clean execution, zero tests, interrupted
completion, invalid selectors, output replacement and bounded writes. The
emitter does not import or change `hexctl.py`. A Horos scan is stable on its
second run. Focused tests, both repository suites, Promise Machine, prose,
tree, diff, signature and trailer checks pass.

```bash
cmp .hexaemeron/study.md docs/elenchus-guard-verdict-study.md
cmp .hexaemeron/runbook.md docs/elenchus-guard-verdict-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/elenchus-guard-verdict-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/elenchus-guard-verdict-runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_emit_unittest_report -v
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/elenchus-guard-verdict-study.md docs/elenchus-guard-verdict-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/elenchus-guard-verdict-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 -m unittest tests.test_boundary_currency
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
git diff --check
git verify-commit <commit-sha>
```

**Files.** `docs/elenchus-guard-verdict-study.md`;
`docs/elenchus-guard-verdict-runbook.md`;
`plugins/hexaemeron/tests/emit_unittest_report.py`;
`plugins/hexaemeron/tests/test_emit_unittest_report.py`;
`.horos/boundary.json`; `audit/AUDIT.md` only when audit rounds append to it.

**Tests.** Add the emitter tests before changing the controller. Run the
emitter-focused test, both repository suites, Promise Machine checks, exact
document comparisons, Horos stability, prose, tree, diff, signature and
trailer gates. Expected focused count is at least eight new cases.

**Disciplines.** protasis: tracked copies preserve the accepted contract.
phylax: the emitter accepts selectors and a report path, so it must use no
shell and must confine and bound its write. ephoros: the fresh structured
report is the bounded signal. metron: none, no performance claim. elenchus:
the emitter makes later red-before-fix evidence machine-readable. hypomnema:
the study and runbook preserve the design; the durable interface record lands
in step 2.

## Step 2: Bind the guard declaration to Warden and audit-round

**Goal.** Parse one source-bound guard declaration, carry it in the Warden
packet, and preserve the reported Elenchus verdict in the audit-round receipt.

**Entry.** Step 1's signed and audited head; the repository-owned report
emitter and its tests pass; tracked specifications match their receipts; the
controller still has no guard field.

**Exit.** One exact `elenchus-guard` block in a receipted runbook step formally
declares a bug-fix step. `next` refuses malformed, duplicate, ambiguous,
missing-after-declaration or digest-drifted source. Its Warden packet contains
the exact command fields, step identity, source and command digests, and the
signed implementation ref. It names `--guard-status` as owed. `audit-round`
accepts and stores exactly `guarded`, `unguarded`, `passed` or `inconclusive`
for a declared step, refuses a missing or unknown value, and refuses the flag
for an ordinary step. Legacy runs remain readable and acquire no claim. The
three lint exits and clean-close rules keep their current meaning. The ADR,
Fiat audit instructions and Warden role describe the new boundary without
adding issue #453's closure policy. Focused red-before-fix evidence and all
complete gates pass.

```elenchus-guard
{
  "test_command": "python3 plugins/hexaemeron/tests/emit_unittest_report.py {report} plugins.hexaemeron.tests.test_hexctl.GuardVerdictReceiptTests",
  "report_format": "unittest-json-v1",
  "report_file": ".elenchus/issue-327-step-2.json"
}
```

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/elenchus.py --ref HEAD --test-command "python3 plugins/hexaemeron/tests/emit_unittest_report.py {report} plugins.hexaemeron.tests.test_hexctl.GuardVerdictReceiptTests" --report-format unittest-json-v1 --report-file .elenchus/issue-327-step-2.json --require-guard
python3 -m unittest plugins.hexaemeron.tests.test_hexctl.GuardVerdictReceiptTests -v
python3 -m unittest plugins.hexaemeron.tests.test_elenchus_checker plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/ADR-012-bind-fiat-guard-verdicts-to-runbook-source.md plugins/hexaemeron/skills/fiat/references/audit-loop.md plugins/hexaemeron/agents/warden.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/ADR-012-bind-fiat-guard-verdicts-to-runbook-source.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
git diff --check
git verify-commit <commit-sha>
```

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`;
`plugins/hexaemeron/tests/test_hexctl.py`;
`plugins/hexaemeron/tests/test_fiat_skill.py`;
`plugins/hexaemeron/skills/fiat/references/audit-loop.md`;
`plugins/hexaemeron/agents/warden.md`;
`docs/decisions/ADR-012-bind-fiat-guard-verdicts-to-runbook-source.md`;
`tests/promise_machine_coverage.json`; `audit/AUDIT.md` for audit rounds.

**Tests.** Before editing `hexctl.py`, add the focused class and record its
failures for absent packet fields, absent receipt validation and source drift.
Keep each case as a regression test. Cover all four accepted verdicts, every
declared-source refusal, an ordinary step, a legacy state, lint coexistence,
state/ledger round trips, two byte-identical `next` calls and raw-output
exclusion. Use the step's guard block to prove those changed tests fail on the
unfixed parent and pass on the fixed tree.

**Disciplines.** protasis: implement only the accepted block, packet and
receipt contract. phylax: Markdown, JSON, command text and paths are untrusted;
retain bounded reads, exact selectors and argv execution without a shell.
ephoros: directive and ledger fields answer the operator questions; no new
service telemetry is warranted. metron: none, no speed claim. elenchus: the
block above owns the exact detached-parent guard command. hypomnema: ADR-012
owns the durable source-binding decision and rejected alternatives.

## Step 3: Publish the generations and demonstrate the four verdicts

**Goal.** Publish the Elenchus and Fiat generation changes, reconcile every
mutable surface, and demonstrate a complete guarded and ordinary audit path.

**Entry.** Step 2's signed and audited head; guard declaration, packet and
receipt tests pass; Elenchus still reads `elenchus-v1.1.0`, Fiat still reads
`fiat-v5.10.1`, and both frontier digests are unchanged.

**Exit.** Elenchus is `elenchus-v1.2.0` and Fiat is `fiat-v5.11.1`, each with
one generation row. Elenchus remains mature at revision
`observed-failure-root-cause` with digest
`08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b`.
Fiat retains revision `state-shape-validation`, issue #363 as its held target,
and digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`.
Hexaemeron package `1.5.5`, both manifests, both marketplaces, instructions,
README text, Promise Machine bindings and version tests agree. A fresh
temporary run demonstrates each stored verdict, required and forbidden flags,
source-drift refusal, an ordinary audit close, and legacy readability. No demo
claims that a caller-reported value proves execution. Horos is stable on a
second scan. All focused, complete, publication, prose, tree, diff, signature
and GitHub verification gates pass.

```bash
python3 -m unittest plugins.hexaemeron.tests.test_elenchus_checker plugins.hexaemeron.tests.test_emit_unittest_report plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill plugins.hexaemeron.tests.test_evolution tests.test_evolution_contract tests.test_marketplace_prose tests.test_version_propagation
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <all-changed-prose>
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py <each-applicable-prose-file>
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
git diff --check
git verify-commit <commit-sha>
gh api repos/wildcat-finance/skills/commits/<pushed-sha> --jq '.commit.verification | select(.verified == true and .reason == "valid")'
```

**Files.** `plugins/hexaemeron/skills/elenchus/EVOLUTION.md`;
`plugins/hexaemeron/skills/elenchus/SKILL.md`;
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`;
`plugins/hexaemeron/skills/fiat/SKILL.md`;
`plugins/hexaemeron/README.md`; both Hexaemeron manifests; both marketplace
manifests; version, evolution and marketplace tests;
`tests/promise_machine_coverage.json`; `.horos/boundary.json`;
`audit/AUDIT.md`.

**Tests.** Run a fresh checked-in-controller demo that records all four enum
values without changing their meaning. Recheck every Step 2 refusal and the
ordinary and legacy paths. Verify version arithmetic, one new generation row
per skill, byte-exact frontier preservation, package propagation, marketplace
text, Promise Machine digests and a stable Horos scan. Run the full suites and
all applicable prose, tree, diff, signature, trailer and remote-verification
gates.

**Disciplines.** protasis: publish only the accepted generation changes and
defer #429, #369, #453 and #363. phylax: the demo opens no path beyond the
bounded interfaces proven in step 2. ephoros: the demo proves the CLI and
ledger signals; no log, metric, trace or alert is added. metron: none, no
performance claim. elenchus: replay the detached-parent guard and all
compatibility specimens on the publication tree. hypomnema: the two ledger
rows record the generation decisions while both held frontiers stay intact.
