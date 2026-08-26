# Runbook: read the audit synopsis rather than the whole log after signing-key rotation

This runbook derives from the receipted study with SHA-256
`df46736642f007c4ebe7be9b902921b0cef09a338632c39c067f53eaa53f01dc`.
Issue 369 remains one delivery boundary: Protasis learns when a derived audit
synopsis is safe to read and how to fall back without weakening the
authoritative source. The earlier construction is evidence only. Its
implementation signature is revoked, so this run rebuilds the product from
the exact clean base and earns new receipts.

## Step 1: Publish the verified synopsis reading contract

**Goal.** Make a verified per-source audit synopsis the normal Protasis study
read view while keeping direct authoritative-source reading as the honest,
available fallback.

**Entry.** Start from branch `fiat/369-read-audit-synopsis-resigned` at
`1efec4de762e3b30c1d677371643c0e5e12667ed`, with the study receipt above,
Protasis `4.7.0`, and the `amendment-block-check` frontier unchanged. Commit
`c67c39b39b0e031c4f51ef32317e442d58785480` and every descendant are excluded
from this branch's ancestry. The repository's existing layout, Python
toolchain, CI, and Apache-2.0 licence remain the scaffold.

**Exit.** Commit byte-identical tracked copies of the receipted study and this
runbook. Add a focused guard that is red on the entry tree and green after the
change. Amend Protasis item 2 and its pre-receipt checklist with both supported
source/view mappings, the exit-zero whole-set currency gate, direct-source
fallback, preserved evidence fields, and truthful per-source reporting.
Advance only the Protasis generation to `protasis-v4.8.0`; keep the complete
frontier line and digest byte-identical. Stage the complete tracked file set
before the final Horos write, stage both Horos outputs, repeat the write, and
require no generated drift. Create a fresh signed commit whose history starts
at the entry commit, excludes the revoked implementation, and verifies under
replacement signing subkey
`A0CC410C7BA3DEFC032B3FAA2C9B298EB3D5E57A`. The following checks all exit
zero on the finished tree:

```sh
cmp .hexaemeron/study.md docs/protasis-audit-synopsis-read-view-study.md
cmp .hexaemeron/runbook.md docs/protasis-audit-synopsis-read-view-runbook.md
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/protasis-audit-synopsis-read-view-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/protasis-audit-synopsis-read-view-runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_fiat_skill

set -o pipefail
run_unittest_modules() {
  find "$1" -maxdepth 1 -type f -name 'test_*.py' -print0 |
    xargs -0 -n 1 -P 12 sh -c '
      fiat_test_file=$1
      fiat_test_output=$(python3 -m unittest -q "$fiat_test_file" 2>&1)
      fiat_test_exit=$?
      if [ "$fiat_test_exit" -ne 0 ]; then
        printf "%s\n%s\n" "$fiat_test_file" "$fiat_test_output"
      fi
      exit "$fiat_test_exit"
    ' sh
}
run_unittest_modules tests
run_unittest_modules plugins/hexaemeron/tests

python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/protasis-audit-synopsis-read-view-study.md docs/protasis-audit-synopsis-read-view-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/protasis/SKILL.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
git diff --exit-code -- .horos/boundary.json .horos/candidates.json
git diff --check
git merge-base --is-ancestor c67c39b39b0e031c4f51ef32317e442d58785480 HEAD && exit 1 || test $? -eq 1
git verify-commit HEAD
```

**Files.** `docs/protasis-audit-synopsis-read-view-study.md`,
`docs/protasis-audit-synopsis-read-view-runbook.md`,
`plugins/hexaemeron/skills/protasis/SKILL.md`,
`plugins/hexaemeron/skills/protasis/EVOLUTION.md`,
`plugins/hexaemeron/tests/test_fiat_skill.py`, `.horos/boundary.json`, and
`.horos/candidates.json`.

**Tests.** Add one focused prose-contract test in
`plugins/hexaemeron/tests/test_fiat_skill.py`. It must fail against the entry
tree because item 2 and the checklist do not yet require a verified view,
whole-set currency, both mappings, source fallback, retained negative space,
or truthful read-mode reporting; it must pass after both passages carry those
rules. Keep every existing test. The focused module moves from 88 to 89 tests,
the root suite remains 396 tests, and the Hexaemeron suite moves from 1,167 to
1,168 tests. Elenchus runner contract for this step: test command
`python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`,
report format `unittest-json-v1`, report file
`.elenchus/protasis-audit-synopsis-step-1.json`.

**Disciplines.** phylax: repository-controlled paths and a fixed local
currency command keep data from becoming shell input. ephoros: no unattended
system is added; command exits, per-source diagnostics, and the study source
table are the finite signals. metron: no product performance claim or budget
applies. elenchus: observe the focused guard red on the entry tree before the
instruction changes, then keep it green; if an audit fix is made, classify the
complete source-bound report above. hypomnema: the Protasis generation row is
the durable home for the consumer-contract decision, while the tracked study
keeps the rejected alternatives and no new ADR is created.

### Amendment -- 2026-08-25

**What changed.** Complete replacement Entry: Start from branch
`fiat/369-read-audit-synopsis-resigned` at
`1efec4de762e3b30c1d677371643c0e5e12667ed`, with amended study receipt
`f442999bea9d178154371adafbd20cddb5b0dbcb8f23e888d252564ab7587cc9`,
Protasis `4.7.0`, and the `amendment-block-check` frontier unchanged. Commit
`c67c39b39b0e031c4f51ef32317e442d58785480` and every descendant are excluded
from this branch's ancestry. The repository's existing layout, Python
toolchain, CI, and Apache-2.0 licence remain the scaffold. Complete replacement
Exit: Commit byte-identical tracked copies of the amended study and this
runbook. Add a focused guard that is red on the entry tree and green after the
change. Amend Protasis item 2 and its pre-receipt checklist with both supported
source/view mappings, the exit-zero whole-set currency gate, direct-source
fallback, preserved evidence fields, and truthful per-source reporting.
Advance only the Protasis generation to `protasis-v4.8.0`; keep the complete
frontier line and digest byte-identical. Stage the complete tracked file set
before the final Horos write, stage both Horos outputs, repeat the write, and
require no generated drift. Create a fresh signed commit whose history starts
at the entry commit, excludes the revoked implementation, and is signed by the
Shoggoth primary key selected exactly as
`636EC19DE45DF10F3CE6206F57742DA1ABED6F46!`. The following checks all exit
zero on the finished tree:

```sh
cmp .hexaemeron/study.md docs/protasis-audit-synopsis-read-view-study.md
cmp .hexaemeron/runbook.md docs/protasis-audit-synopsis-read-view-runbook.md
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/protasis-audit-synopsis-read-view-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/protasis-audit-synopsis-read-view-runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_fiat_skill

set -o pipefail
run_unittest_modules() {
  find "$1" -maxdepth 1 -type f -name 'test_*.py' -print0 |
    xargs -0 -n 1 -P 12 sh -c '
      fiat_test_file=$1
      fiat_test_output=$(python3 -m unittest -q "$fiat_test_file" 2>&1)
      fiat_test_exit=$?
      if [ "$fiat_test_exit" -ne 0 ]; then
        printf "%s\n%s\n" "$fiat_test_file" "$fiat_test_output"
      fi
      exit "$fiat_test_exit"
    ' sh
}
run_unittest_modules tests
run_unittest_modules plugins/hexaemeron/tests

python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/protasis-audit-synopsis-read-view-study.md docs/protasis-audit-synopsis-read-view-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/protasis/SKILL.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
git diff --exit-code -- .horos/boundary.json .horos/candidates.json
git diff --check
git merge-base --is-ancestor c67c39b39b0e031c4f51ef32317e442d58785480 HEAD && exit 1 || test $? -eq 1
git verify-commit HEAD
git log -1 --format='%GF' HEAD | grep -Fx '636EC19DE45DF10F3CE6206F57742DA1ABED6F46'
```

**Why.** After the study and runbook receipts, the Creator explicitly chose a
signature by the Shoggoth primary key itself rather than by its valid signing
subkey. The study amendment records that corrected assumption.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds.

### Amendment -- 2026-08-25

**What changed.** Complete replacement Exit: Commit byte-identical tracked
copies of the amended study and this runbook. Add a focused guard that is red
on the entry tree and green after the change. Amend Protasis item 2 and its
pre-receipt checklist with both supported source/view mappings, the exit-zero
whole-set currency gate, direct-source fallback, preserved evidence fields,
and truthful per-source reporting. Advance only the Protasis generation to
`protasis-v4.8.0`; keep the complete frontier line and digest byte-identical.
Stage the complete tracked file set before the final Horos write, stage both
Horos outputs, repeat the write, and require no generated drift. Create a fresh
signed commit whose history starts at the entry commit, excludes the revoked
implementation, and is signed by the Shoggoth primary key selected exactly as
`636EC19DE45DF10F3CE6206F57742DA1ABED6F46!`. The following checks all exit
zero on the finished tree:

```sh
cmp .hexaemeron/study.md docs/protasis-audit-synopsis-read-view-study.md
cmp .hexaemeron/runbook.md docs/protasis-audit-synopsis-read-view-runbook.md
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/protasis-audit-synopsis-read-view-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/protasis-audit-synopsis-read-view-runbook.md
python3 -m unittest plugins.hexaemeron.tests.test_fiat_skill

set -o pipefail
discover_unittest_classes() {
  python3 - "$1" <<'PY'
import importlib
import pathlib
import sys
import unittest

root = pathlib.Path(sys.argv[1])

def walk(node):
    for child in node:
        if isinstance(child, unittest.TestSuite):
            yield from walk(child)
        else:
            yield child

all_ids = []
selectors = []
for path in sorted(root.glob("test_*.py")):
    module_name = ".".join(path.with_suffix("").parts)
    module = importlib.import_module(module_name)
    tests = list(walk(unittest.defaultTestLoader.loadTestsFromModule(module)))
    classes = []
    for test in tests:
        if test.__class__ not in classes:
            classes.append(test.__class__)
    for cls in classes:
        names = sorted(name for name, value in vars(module).items() if value is cls)
        if not names:
            raise SystemExit(f"no module binding for {module_name} {cls!r}")
        selector = f"{module_name}.{names[0]}"
        selected = list(walk(unittest.defaultTestLoader.loadTestsFromName(selector)))
        expected_ids = sorted(test.id() for test in tests if test.__class__ is cls)
        actual_ids = sorted(test.id() for test in selected)
        if expected_ids != actual_ids:
            raise SystemExit(f"selector mismatch for {selector}")
        selectors.append(selector)
        all_ids.extend(actual_ids)

if not all_ids or len(all_ids) != len(set(all_ids)) or len(selectors) != len(set(selectors)):
    raise SystemExit(
        f"invalid unittest universe: tests={len(all_ids)} unique_tests={len(set(all_ids))} "
        f"selectors={len(selectors)} unique_selectors={len(set(selectors))}"
    )
for selector in sorted(selectors):
    print(selector)
PY
}
run_unittest_classes() {
  discover_unittest_classes "$1" |
    xargs -n 1 -P 12 sh -c '
      fiat_test_class=$1
      fiat_test_output=$(python3 -m unittest -q "$fiat_test_class" 2>&1)
      fiat_test_exit=$?
      if [ "$fiat_test_exit" -ne 0 ]; then
        printf "%s\n%s\n" "$fiat_test_class" "$fiat_test_output"
      fi
      exit "$fiat_test_exit"
    ' sh
}
run_unittest_classes tests
run_unittest_classes plugins/hexaemeron/tests

python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/protasis/SKILL.md plugins/hexaemeron/skills/protasis/EVOLUTION.md docs/protasis-audit-synopsis-read-view-study.md docs/protasis-audit-synopsis-read-view-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/protasis/SKILL.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
git diff --exit-code -- .horos/boundary.json .horos/candidates.json
git diff --check
git merge-base --is-ancestor c67c39b39b0e031c4f51ef32317e442d58785480 HEAD && exit 1 || test $? -eq 1
git verify-commit HEAD
git log -1 --format='%GF' HEAD | grep -Fx '636EC19DE45DF10F3CE6206F57742DA1ABED6F46'
```

**Why.** Module-level scheduling left the 370-test `test_hexctl.py` module as
a single long tail after the other workers became idle. Class-level selectors
preserve each class lifecycle, are checked against the discovered test ids
before execution, and let the available workers continue taking work.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds.
