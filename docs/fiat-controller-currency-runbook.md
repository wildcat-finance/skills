# Runbook: controller currency guarantee

### Source receipts

```text
study sha256: ebc957fd8570d36f39b2e1597d09f61369498c390b9f4ef7a2158d7ed764cbee
starting ref: 08512d4ada7b1d7418e1af213be0d4b8c1494b6d
run branch: fiat/controller-currency-guarantee
```

The topic is one capability with four dependency-ordered steps, per the
study's decomposition decision: no module table, because nothing ships or
verifies separately. Step 1 freezes the accepted proposition in the tracked
tree. Step 2 lands the observation and the init gate with their tests and the
decision record. Step 3 exposes the same observation as a subcommand and gives
the Kronos loop its re-pin boundary. Step 4 aligns the documentation and every
version surface, appends both generation rows, and demonstrates the demo path
from the study's problem statement. Ledger versions, the ADR number and the
package version are global identifiers that concurrent runs take first, so
each is picked at the step that writes it, after re-reading the tree, and no
earlier step names one.

## Step 1: Publish the accepted controller-currency specification

**Goal.** Commit byte-identical tracked copies of the receipted study and
runbook, with their structure, lexicon, links and reading boundary checked
before any controller code changes.

**Entry.** The exact run branch `fiat/controller-currency-guarantee` at
starting ref `08512d4ada7b1d7418e1af213be0d4b8c1494b6d`; the study receipt
names SHA-256
`ebc957fd8570d36f39b2e1597d09f61369498c390b9f4ef7a2158d7ed764cbee`. No
tracked file from this run exists at entry.

**Exit.** The following all hold:

1. `docs/fiat-controller-currency-study.md` is byte-identical to the
   receipted `.hexaemeron/study.md`.
2. `docs/fiat-controller-currency-runbook.md` is byte-identical to the
   receipted `.hexaemeron/runbook.md`.
3. Protasis accepts both tracked artefacts, Imprimatur reports no defect on
   either, and every relative link resolves from the publication location.
4. The deterministic Horos scan describes the resulting tracked tree.
5. The root and Hexaemeron suites remain green and `git diff --check`
   exits 0.

**Files.** Create only:

- `docs/fiat-controller-currency-study.md`;
- `docs/fiat-controller-currency-runbook.md`;
- `.horos/boundary.json` only when the deterministic Horos scan changes it;
- `audit/AUDIT.md` only for append-only Warden round records.

No canonical skill, script, test, manifest, ledger, CI file, or dependency
changes in this step's implementation.

**Tests.** None written; copy the two receipted artefacts without rewriting
them, then run:

```bash
cmp -s .hexaemeron/study.md docs/fiat-controller-currency-study.md
cmp -s .hexaemeron/runbook.md docs/fiat-controller-currency-runbook.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-controller-currency-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-controller-currency-runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-controller-currency-study.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-controller-currency-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
git diff --check
```

The source-bound Elenchus runner contract for any audit repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-controller-currency-step-1.json
```

The report path must be fresh. A missing, stale, empty, malformed, or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: none, because this step adds static Markdown and no
new input or execution boundary. ephoros: none, because it adds no unattended
operation. metron: none, because it makes no performance claim. elenchus:
byte-identity, link, structural, boundary, and suite regressions stop the
step and any repair uses the exact runner above. hypomnema: the tracked study
and runbook are the durable homes the accepted proposition selected.

## Step 2: Observe controller currency at init and refuse a proven-behind pin

**Goal.** `hexctl init` observes the running controller's route, pin and
upstream head through bounded reads, refuses a `behind` verdict by name
unless a waiver flag records a reason, and writes controller provenance into
the init transition and receipts.

**Entry.** Step 1's signed, audited, prose-checked branch tip. The entry
controller records only topic, base and run branch at init, and a fabricated
behind pin starts a run silently; preserve that red reproduction before
changing the mechanism.

**Exit.** The following all hold:

1. One observation function resolves the running controller's own file to a
   route (`git-backed`, `managed`, or `in-repo-source`), a pin or an explicit
   null, and, on the git-backed route only, one bounded `git ls-remote`
   upstream head or an explicit null. A missing, malformed, wrong-kind or
   oversized registry, a timeout, and a malformed remote line each read as
   `unknown` with a named warning, never a traceback and never a false
   `current` or `behind` (study risks `registry-hostile-input`,
   `route-misdetection`, `verdict-honesty`).
2. `init` under verdict `behind` refuses by name with exit 1 before any
   worktree, state, ledger or breadcrumb exists, stating the pin, the
   observed head, and the two exits: re-pin through the host's installer, or
   pass the waiver flag with a reason.
3. `init --controller-currency-waiver '<reason>'` proceeds on `behind` and
   records the reason; an empty reason is refused (study risk
   `waiver-visibility`).
4. Every init transition and receipt carries the controller's ledger version,
   route, pin or null, observed head or null, verdict, and waiver reason or
   null; verdicts `current`, `no-pin`, `managed` and `unknown` proceed, and
   `unknown` warns on stderr.
5. The remote URL comes only from the marketplace clone's config under the
   plugins root derived from the controller's own resolved file; no
   target-repository or environment value reaches the call, and no raw child
   output, URL or registry byte appears in any diagnosis, transition or
   receipt (study risks `upstream-read-surface`, `url-source-confusion`,
   `secret-echo`).
6. Runs recorded before this change stay loadable: `load_state`, `status` and
   `verify` accept state without the new receipt (study risk `state-compat`).
7. One ADR under `docs/decisions/` records the three decisions the study
   named expensive to reverse: init observing the network, refusal only on
   proof, and the verdict vocabulary. Its number is chosen when it is
   written, after re-reading the tracked decisions directory.
8. Both suites are green, Imprimatur reports no defect on the ADR, the
   deterministic Horos scan describes the tree, and `git diff --check`
   exits 0.

**Files.** Change or create only:

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`;
- `plugins/hexaemeron/tests/test_hexctl.py`, plus fixtures under
  `plugins/hexaemeron/tests/fixtures/` as the new cases need them;
- `docs/decisions/ADR-<number chosen at write>-<slug>.md`;
- `.horos/boundary.json` only when the deterministic Horos scan changes it;
- `audit/AUDIT.md` only for append-only Warden round records.

No ledger, `SKILL.md`, reference or manifest changes in this step; every
global identifier is picked at step 4.

**Tests.** Extends `plugins/hexaemeron/tests/test_hexctl.py` with the gate
suite: fixtures for all three routes; the behind refusal; the waiver path and
its receipt; the provenance fields on every verdict; the missing, malformed,
wrong-kind and oversized registry; the timeout; the malformed `ls-remote`
line; and URL-source confinement. At least twelve new tests, each built as an
Elenchus guard: capture the pre-fix behaviour red, then prove the guard fails
when the gate call is removed. Then run:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/ADR-*.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The source-bound Elenchus runner contract for any audit repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-controller-currency-step-2.json
```

The report path must be fresh. A missing, stale, empty, malformed, or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: this step opens the run's one new network read and
two host filesystem reads; the study's boundary section governs their
controls. ephoros: exit status, stderr and the receipts are the signals, and
the new receipt answers "which controller drove this run"; no unattended
surface is added. metron: none, because no performance claim is made; the
worst added cost is one bounded timeout, stated in step 4's documentation.
elenchus: the silent-start red is captured first and every behaviour lands as
a guard test proven to fail without the gate. hypomnema: the three
expensive-to-reverse decisions land in one ADR in this step.

## Step 3: Expose the currency observation and give Kronos its re-pin boundary

**Goal.** A read-only `hexctl currency` subcommand reports the step 2
observation for every installed wildcat plugin with a stated exit contract,
and the Kronos loop runs it at the rescan boundary and reinstalls what is
behind before the next ranking.

**Entry.** Step 2's signed, audited, prose-checked branch tip. The
observation function exists and is tested; Kronos `SKILL.md` step 8 rescans
ledgers with no currency check.

**Exit.** The following all hold:

1. `hexctl currency` prints one row per installed wildcat-labs plugin
   carrying plugin name, package version, route, pin or null, observed head
   or null, and verdict; `--json` emits the same rows as JSON.
2. Its exit contract is 0 when nothing is behind, 3 while anything is behind,
   and 1 on a refusal; the observation reuses the step 2 bounded reads with
   at most one remote read per distinct marketplace origin (study risk
   `repin-partiality`).
3. Kronos `SKILL.md` names the re-pin boundary at its rescan step: run
   `hexctl currency`, reinstall every behind plugin through the host's own
   installer, refresh, and re-resolve paths before the next ranking, citing
   `plugin-currency.md` for the host mechanism rather than restating it.
4. Both suites are green, Imprimatur reports no defect on the changed Kronos
   prose, the deterministic Horos scan describes the tree, and
   `git diff --check` exits 0.

**Files.** Change only:

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`;
- `plugins/hexaemeron/tests/test_hexctl.py`, plus fixtures under
  `plugins/hexaemeron/tests/fixtures/` as the new cases need them;
- `plugins/hexaemeron/skills/kronos/SKILL.md`, loop text only;
- `.horos/boundary.json` only when the deterministic Horos scan changes it;
- `audit/AUDIT.md` only for append-only Warden round records.

No ledger, frontmatter version, reference or manifest changes in this step;
every global identifier is picked at step 4.

**Tests.** Extends `plugins/hexaemeron/tests/test_hexctl.py`: a fixture cache
with mixed verdicts across the fourteen-plugin shape; the exit-code contract
on each; the `--json` row shape; one remote read per distinct origin; and the
refusal path. At least six new tests, each an Elenchus guard. Then run:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/kronos/SKILL.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The source-bound Elenchus runner contract for any audit repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-controller-currency-step-3.json
```

The report path must be fresh. A missing, stale, empty, malformed, or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: the same two host reads and one bounded remote read,
reused rather than widened; no new boundary opens. ephoros: the exit code is
the loop's signal, and "did the loop restore currency" is answered by exit 3
clearing on the next report. metron: none, because no performance claim is
made. elenchus: the guard convention continues; a failure surfaced here is
worked to its cause with the runner above. hypomnema: the Kronos loop text is
the operating record; its ledger row lands at step 4 with the other
identifiers.

## Step 4: Align the documentation and versions, and demonstrate

**Goal.** The documented mechanism becomes the enforced one, both governed
ledgers gain their generation row with frontmatter to match, the hexaemeron
package version moves across all five compared surfaces so `plugin update`
copies this change, and the study's demo path runs green.

**Entry.** Step 3's signed, audited, prose-checked branch tip. The gate and
subcommand are tested; `references/plugin-currency.md` still describes the
advisory-only mechanism; both ledgers stand as they did at the starting ref,
`fiat-v5.21.1` and `kronos-v0.6.0`. Re-read both ledgers, the tracked
decisions directory and the base before picking any identifier.

**Exit.** The following all hold:

1. `references/plugin-currency.md` documents the observation, the verdict
   vocabulary, the gate, the waiver, the provenance receipt, the `currency`
   subcommand and the Kronos re-pin boundary, and states both limits: the
   contract is currency at init, recorded, not currency for the run's
   duration, and the gate governs runs after the next re-pin, never the run
   that shipped it (study risk `bootstrap-limit`).
2. Fiat `SKILL.md` preflight step 3 reflects the enforced gate and cites
   `plugin-currency.md` rather than restating it.
3. `plugins/hexaemeron/skills/fiat/EVOLUTION.md` carries exactly one new
   generation row for this change, and
   `plugins/hexaemeron/skills/kronos/EVOLUTION.md` carries exactly one new
   generation row for the re-pin boundary; each retains its prior frontier
   revision and digest byte for byte, each version is picked after the entry
   re-read, and each `SKILL.md` frontmatter version matches its ledger
   (study risk `ledger-arithmetic`).
4. The hexaemeron package version moves on all five compared surfaces and
   `tests/test_version_propagation.py` passes:
   `plugins/hexaemeron/.claude-plugin/plugin.json`,
   `plugins/hexaemeron/.codex-plugin/plugin.json`,
   `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
   and the pinned `DELIVERY_PACKAGE_VERSIONS` map (study risk
   `version-propagation`).
5. The demonstration from the study's problem statement runs green through
   the suites: the behind refusal, the waiver with its receipt, the in-repo
   nulls, and the `currency` exit contract, all under the hexaemeron suite,
   followed by the repository proof commands below.
6. Imprimatur reports no defect on any changed prose surface.

**Files.** Change only:

- `plugins/hexaemeron/skills/fiat/references/plugin-currency.md`;
- `plugins/hexaemeron/skills/fiat/SKILL.md`, preflight step 3 and frontmatter
  version;
- `plugins/hexaemeron/skills/fiat/EVOLUTION.md`;
- `plugins/hexaemeron/skills/kronos/SKILL.md`, frontmatter version only;
- `plugins/hexaemeron/skills/kronos/EVOLUTION.md`;
- `plugins/hexaemeron/.claude-plugin/plugin.json`;
- `plugins/hexaemeron/.codex-plugin/plugin.json`;
- `.claude-plugin/marketplace.json`;
- `.agents/plugins/marketplace.json`;
- `tests/test_version_propagation.py`, the pinned map only;
- `.horos/boundary.json` only when the deterministic Horos scan changes it;
- `audit/AUDIT.md` only for append-only Warden round records.

**Tests.** None written beyond what steps 2 and 3 left; the propagation and
evolution suites already compare every touched surface. Then run:

```bash
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/references/plugin-currency.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The source-bound Elenchus runner contract for any audit repair is:

```text
test command: python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}
report format: unittest-json-v1
expected report schema: elenchus.unittest.v1
report file: .elenchus/fiat-controller-currency-step-4.json
```

The report path must be fresh. A missing, stale, empty, malformed, or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

**Disciplines.** phylax: none, because no boundary opens that steps 2 and 3
did not already control. ephoros: none beyond what the receipts already
carry; the documentation states the signals rather than adding one. metron:
none, because no performance claim is made; the one bounded timeout is
stated, not measured. elenchus: a demonstration regression stops the step and
uses the runner above. hypomnema: `plugin-currency.md` is the operator's
runbook, and the two ledger rows with the five version surfaces are the
durable record of what changed.
