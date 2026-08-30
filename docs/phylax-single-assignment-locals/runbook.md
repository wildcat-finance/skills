# runbook: resolve single-assignment locals for Phylax rules

This runbook derives from the receipted study. Issue #502 is one bounded
classification capability, so one auditable step both scaffolds and
demonstrates it. The repository already supplies its layout, Python pin,
licences, CI and Phylax CLI. This step verifies those foundations and does not
replace them.

```version-relations
phylax | plugins/hexaemeron/skills/phylax/EVOLUTION.md | next-generation-after-integration-base
```

## Step 1: resolve and demonstrate eligible local bindings

**Goal.** Add one shared same-function resolver that exposes eligible local
values to P002, P004 and P008 without claiming branch, rebinding, attribute,
comprehension, closure or interprocedural analysis.

**Entry.** The clean run branch at
`7e97b5195d5b0e43146b4200f26cd41b89003413`, with the Fiat study and this
runbook receipted, the focused Phylax checker suite green at 79 tests under the
repository-declared Python 3.14.6 interpreter, and the complete audit synopsis
set verified current. Existing repository layout, Python pin, licences and CI
are the scaffold; no dependency, toolchain or workflow change enters this
step.

**Exit.** P002 reports an assigned subprocess string command; P004 reports a
credential-named value in assigned argv without erasing the existing
name-first signal; P008 reports an assigned dangerous callable while assigned
literal dynamic input and assigned `yaml.SafeLoader` or `yaml.CSafeLoader`
remain clean. Reassignment, late assignment, branch-local writes, attributes,
subscripts, destructuring, comprehensions, parameters, nested scopes,
closures, module scope, cycles and over-depth chains earn no resolution.
Finding codes, sink locations, reason-bearing suppression, fixed diagnostics
and secret-free text and JSON output remain unchanged.

The Phylax contract and generation ledger describe that exact boundary while
retaining the complete mature frontier tuple. The portable Promise Machine
copy and coverage digest match the canonical source. Byte-identical tracked
copies of the receipted study and runbook exist under
`docs/phylax-single-assignment-locals/`; the configured Fiat audit record and
its generated synopsis are current; the Horos boundary describes the final
tracked tree; and every command below exits zero:

```bash
python3 -c 'import platform; assert platform.python_version() == "3.14.6"'
cmp .hexaemeron/study.md docs/phylax-single-assignment-locals/study.md
cmp .hexaemeron/runbook.md docs/phylax-single-assignment-locals/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_phylax_checker
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/phylax-single-assignment-locals/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/phylax-single-assignment-locals/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/phylax-single-assignment-locals/study.md docs/phylax-single-assignment-locals/runbook.md plugins/hexaemeron/skills/phylax/SKILL.md plugins/hexaemeron/skills/phylax/EVOLUTION.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/phylax-single-assignment-locals/runbook.md
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 scripts/run_checks.py
git diff --check
```

**Files.** Change
`plugins/hexaemeron/skills/phylax/scripts/phylax.py`,
`plugins/hexaemeron/tests/test_phylax_checker.py`,
`plugins/hexaemeron/skills/phylax/SKILL.md`,
`plugins/hexaemeron/skills/phylax/EVOLUTION.md`, and
`tests/promise_machine_coverage.json`. Create byte-identical tracked copies at
`docs/phylax-single-assignment-locals/study.md` and
`docs/phylax-single-assignment-locals/runbook.md`. Regenerate the matching
Phylax files under
`.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/phylax/`
with `python3 scripts/portable_promise_machine.py sync`. Permit the configured
Fiat audit record and generated synopsis companion, plus
`.horos/boundary.json`, only when their owning phase or deterministic generator
changes them. No other product path is in scope without a study amendment.

**Tests.** Before changing the resolver, add focused fixtures for the five
baseline probes and record their exact red classifications. Add positive and
safe-neighbour cases for positional and keyword subprocess args, direct and
aliased runners, P004's name-first ordering, assigned dangerous callables,
dynamic literal input, and safe YAML loaders. Add refusal cases for every
excluded binding shape, forward assignment, cycles and depth exhaustion.
Retain reason-bearing and bare pragma behaviour, P000 through P008 neighbours,
sink-line anchoring, and fixed text/JSON diagnostics with a sentinel value that
must not appear. Preserve all 79 existing focused tests and report the final
count.

The source-bound Elenchus runner contract for any audit repair is exact: test
command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected report schema
`elenchus.unittest.v1`; report file `.elenchus/fiat-502-step-1.json`. The report
path must be fresh. A missing, stale, empty, malformed, zero-test or
infrastructure-failed report is `inconclusive`, not guard evidence.

**Disciplines.** phylax: untrusted Python source reaches a new binding index,
so parsing stays source-only, ambiguity fails unresolved, and diagnostics stay
fixed and secret-free. ephoros: none, because this local CLI adds no unattended
path or telemetry and preserves path, sink line, code, message and exit as its
operator signals. metron: none, because no performance budget or optimisation
claim exists; one collection pass and bounded resolution are structural
limits, not a speed result. elenchus: the five observed misclassifications are
captured red before the cause-level resolver change and retained as regression
guards under the exact runner above. hypomnema: the governed Phylax ledger is
the standing home for this skill-local decision and rejected broad-dataflow
alternatives; the tracked study and runbook preserve the accepted
specification without minting a repository-wide ADR.

Implementation order inside the step is fixed: preserve the red probe results;
add the smallest shared binding index and resolver; turn the focused suite
green; update the public contract, generation row and coverage digest;
synchronise the portable payload; copy the receipted documents; regenerate the
Horos boundary; run the complete exit set; then enter Fiat audit and prose
gates. Any need for general control flow, taint, type inference, another
finding code, a dependency, a changed runner grammar or changed mature
frontier bytes stops the step for a study amendment.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Exit: P002 reports an assigned
subprocess string command; P004 reports a credential-named value in assigned
argv without erasing the existing name-first signal; P008 reports an assigned
dangerous callable while assigned literal dynamic input and assigned
`yaml.SafeLoader` or `yaml.CSafeLoader` remain clean. Reassignment, late
assignment, branch-local writes, attributes, subscripts, destructuring,
comprehensions, parameters, nested scopes, closures, module scope, cycles and
over-depth chains earn no resolution. Finding codes, sink locations,
reason-bearing suppression, fixed diagnostics and secret-free text and JSON
output remain unchanged. The Phylax contract and generation ledger describe
that exact boundary while retaining the complete mature frontier tuple. The
portable Promise Machine copy and coverage digest match the canonical source.
Byte-identical tracked copies of the receipted study and runbook exist under
`docs/phylax-single-assignment-locals/`; the configured Fiat audit record and
its generated synopsis are current; the Horos boundary describes the final
tracked tree; and every command below exits zero:

```bash
python3 -c 'import platform; assert platform.python_version() == "3.14.6"'
cmp .hexaemeron/study.md docs/phylax-single-assignment-locals/study.md
cmp .hexaemeron/runbook.md docs/phylax-single-assignment-locals/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_phylax_checker
python3 plugins/hexaemeron/tests/run_tests.py
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/phylax-single-assignment-locals/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/phylax-single-assignment-locals/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/phylax-single-assignment-locals/study.md docs/phylax-single-assignment-locals/runbook.md plugins/hexaemeron/skills/phylax/SKILL.md plugins/hexaemeron/skills/phylax/EVOLUTION.md
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 scripts/run_checks.py
git diff --check
```

**Why.** The receipted Exit incorrectly applied Brevitas report mode to this
completeness-oriented specification. Brevitas excludes that document class,
and B010 correctly refuses its one-section report shape. Protasis and
Imprimatur remain the specification's applicable mechanical prose gates.

**Steps touched.** Step 1's Exit.

**Still holding.** Step 1: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: Change
`plugins/hexaemeron/skills/phylax/scripts/phylax.py`,
`plugins/hexaemeron/tests/test_phylax_checker.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`plugins/hexaemeron/skills/phylax/SKILL.md`,
`plugins/hexaemeron/skills/phylax/EVOLUTION.md`, and
`tests/promise_machine_coverage.json`. Create byte-identical tracked copies at
`docs/phylax-single-assignment-locals/study.md` and
`docs/phylax-single-assignment-locals/runbook.md`. Regenerate the matching
Phylax files under
`.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/phylax/`
with `python3 scripts/portable_promise_machine.py sync`. Permit the configured
Fiat audit record and generated synopsis companion, plus
`.horos/boundary.json`, only when their owning phase or deterministic generator
changes them. No other product path is in scope without a study amendment.
Complete replacement Tests: Before changing the resolver, add focused fixtures
for the five baseline probes and record their exact red classifications. Add
positive and safe-neighbour cases for positional and keyword subprocess args,
direct and aliased runners, P004's name-first ordering, assigned dangerous
callables, dynamic literal input, and safe YAML loaders. Add refusal cases for
every excluded binding shape, forward assignment, cycles and depth exhaustion.
Retain reason-bearing and bare pragma behaviour, P000 through P008 neighbours,
sink-line anchoring, and fixed text/JSON diagnostics with a sentinel value that
must not appear. Preserve all 79 existing focused tests and report the final
count. Update
`ConformanceTests.test_skill_package_marketplace_coverage_and_portable_versions_are_exact`
to require the controller-projected Phylax generation in both the canonical
contract and evolution ledger while retaining its canonical/portable parity
assertions. The source-bound Elenchus runner contract for any audit repair is
exact: test command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`;
report format `unittest-json-v1`; expected report schema
`elenchus.unittest.v1`; report file `.elenchus/fiat-502-step-1.json`. The report
path must be fresh. A missing, stale, empty, malformed, zero-test or
infrastructure-failed report is `inconclusive`, not guard evidence.

**Why.** The complete Hexaemeron suite exposed one existing integration guard
that intentionally pins the canonical and portable Phylax version bytes. The
generation-only increment makes that assertion stale, so its named test must
advance with the governed ledger rather than be bypassed.

**Steps touched.** Step 1's Files and Tests.

**Still holding.** Step 1: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Exit: P002 reports an assigned
subprocess string command; P004 reports a credential-named value in assigned
argv without erasing the existing name-first signal; P008 reports an assigned
dangerous callable while assigned literal dynamic input and assigned
`yaml.SafeLoader` or `yaml.CSafeLoader` remain clean. Reassignment, late
assignment, branch-local writes, attributes, subscripts, destructuring,
comprehensions, parameters, nested scopes, closures, module scope, cycles and
over-depth chains earn no resolution. Finding codes, sink locations,
reason-bearing suppression, fixed diagnostics and secret-free text and JSON
output remain unchanged. The Phylax contract and generation ledger describe
that exact boundary while retaining the complete mature frontier tuple. The
portable Promise Machine copy and coverage digest match the canonical source.
Byte-identical tracked copies of the receipted study and runbook exist under
`docs/phylax-single-assignment-locals/`; the configured Fiat audit record and
its generated synopsis are current; and the Horos boundary describes the
final tracked tree.

The complete Hexaemeron runner is executed and recorded but is not promoted to
an in-scope green claim while exact base
`7e97b5195d5b0e43146b4200f26cd41b89003413` already fails its Homologia
check-map ownership predicate, Node 26 fixture-version predicate, macOS
long-path checkpoint fixture, and root-audit digest pin. The candidate must
introduce no additional failure or error, and both Phylax suites must be green.
Every in-scope command below exits zero:

```bash
python3 -c 'import platform; assert platform.python_version() == "3.14.6"'
cmp .hexaemeron/study.md docs/phylax-single-assignment-locals/study.md
cmp .hexaemeron/runbook.md docs/phylax-single-assignment-locals/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_phylax_checker
python3 -m unittest plugins.hexaemeron.tests.test_phylax_model_proxy.ConformanceTests.test_skill_package_marketplace_coverage_and_portable_versions_are_exact
python3 -m unittest tests.test_evolution_contract
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/phylax-single-assignment-locals/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/phylax-single-assignment-locals/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/phylax-single-assignment-locals/study.md docs/phylax-single-assignment-locals/runbook.md plugins/hexaemeron/skills/phylax/SKILL.md plugins/hexaemeron/skills/phylax/EVOLUTION.md
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Why.** The complete Hexaemeron run on the amended candidate returned three
failures and one error, all outside this step. Each exact predicate was then
reproduced unchanged on the entry commit. Repairing Homologia ownership, the
host Node installation, a pre-existing macOS path-length fixture, or the
root-audit pin would widen #502 and contaminate its regression evidence.

**Steps touched.** Step 1's Exit.

**Still holding.** Step 1: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Exit: P002 reports an assigned
subprocess string command; P004 reports a credential-named value in assigned
argv without erasing the existing name-first signal; P008 reports an assigned
dangerous callable while assigned literal dynamic input and assigned
`yaml.SafeLoader` or `yaml.CSafeLoader` remain clean. Reassignment, late
assignment, branch-local writes, attributes, subscripts, destructuring,
comprehensions, parameters, nested scopes, closures, module scope, cycles and
over-depth chains earn no resolution. Finding codes, sink locations,
reason-bearing suppression, fixed diagnostics and secret-free text and JSON
output remain unchanged. The Phylax contract and generation ledger describe
that exact boundary while retaining the complete mature frontier tuple. The
portable Promise Machine copy and coverage digest match the canonical source.
The tracked runbook is byte-identical to its receipted artifact. The tracked
study differs from its receipt only by rebasing exactly five Markdown links
from `.hexaemeron/` depth to
`docs/phylax-single-assignment-locals/` depth; a normalization check proves all
other bytes identical. The configured Fiat audit record and its generated
synopsis are current, and the Horos boundary describes the final tracked tree.

The complete Hexaemeron runner is executed and recorded but is not promoted to
an in-scope green claim while exact base
`7e97b5195d5b0e43146b4200f26cd41b89003413` already fails its Homologia
check-map ownership predicate, Node 26 fixture-version predicate, macOS
long-path checkpoint fixture, and root-audit digest pin. The candidate must
introduce no additional failure or error, and both Phylax suites must be green.
Every in-scope command below exits zero:

```bash
python3 -c 'import platform; assert platform.python_version() == "3.14.6"'
python3 -c 'from pathlib import Path; source = Path(".hexaemeron/study.md").read_text(); tracked = Path("docs/phylax-single-assignment-locals/study.md").read_text(); assert source.count("(../plugins/") == 5; assert tracked.count("(../../plugins/") == 5; assert tracked.replace("(../../plugins/", "(../plugins/") == source'
cmp .hexaemeron/runbook.md docs/phylax-single-assignment-locals/runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_phylax_checker
python3 -m unittest plugins.hexaemeron.tests.test_phylax_model_proxy.ConformanceTests.test_skill_package_marketplace_coverage_and_portable_versions_are_exact
python3 -m unittest tests.test_evolution_contract
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/phylax-single-assignment-locals/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/phylax-single-assignment-locals/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/phylax-single-assignment-locals/study.md docs/phylax-single-assignment-locals/runbook.md plugins/hexaemeron/skills/phylax/SKILL.md plugins/hexaemeron/skills/phylax/EVOLUTION.md
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

Complete replacement Files: Change
`plugins/hexaemeron/skills/phylax/scripts/phylax.py`,
`plugins/hexaemeron/tests/test_phylax_checker.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`,
`plugins/hexaemeron/skills/phylax/SKILL.md`,
`plugins/hexaemeron/skills/phylax/EVOLUTION.md`, and
`tests/promise_machine_coverage.json`. Create a path-rebased tracked study at
`docs/phylax-single-assignment-locals/study.md` and a byte-identical tracked
runbook at `docs/phylax-single-assignment-locals/runbook.md`. The study
publication changes only its five `../plugins/` link prefixes to
`../../plugins/`; the Exit normalization command checks exact content parity.
Regenerate the matching Phylax files under
`.agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/phylax/`
with `python3 scripts/portable_promise_machine.py sync`. Permit the configured
Fiat audit record and generated synopsis companion, plus
`.horos/boundary.json`, only when their owning phase or deterministic generator
changes them. No other product path is in scope without a study amendment.

**Why.** Hypomnema correctly rejected the receipted study's five
artifact-relative links after an exact copy moved them two directory levels
deeper. Rewriting the receipt would destroy evidence continuity; retaining the
broken links would ship false pointers. A closed five-token path rebase keeps
both properties checkable.

**Steps touched.** Step 1's Exit and Files.

**Still holding.** Step 1: entry holds; exit holds.
