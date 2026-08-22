# runbook: add unsafe deserialization to Phylax's mechanical subset

This runbook derives from `.hexaemeron/study.md` at the receipted digest. The
topic is one source-local Python lint capability, so one auditable step both
scaffolds and demonstrates it. The repository already supplies the layout,
root and plugin licences, standard-library Python 3.9/3.12 compatibility, and
CI workflows; issue #324 does not authorize replacing those foundations or
touching CI. This step verifies them and commits the study and runbook copies.

## Step 1: add and demonstrate P008 unsafe-deserialization lint

**Goal.** Add one import-aware `P008` AST rule for the exact unsafe
deserialization and dynamic-execution calls in issue #324, with public prose,
generation bookkeeping and guards for every claimed hostile and safe shape.

**Entry.** The clean run branch at
`64096f4d89fc821ab9d91d075cd86be7e7bb92b5`, with the Fiat study and this
runbook receipted, the existing focused Phylax suite green at 61/61 on Python
3.9.6 and 3.12.13, and the pre-change tree-wide Phylax scan clean. The root and
Hexaemeron licences, current repository layout and existing workflows remain
the scaffold; no dependency, toolchain-pin or CI change enters this step.

**Exit.** `P008` reports the exact import-resolved `pickle.load`,
`pickle.loads`, `marshal.load`, unsafe `yaml.load`, and non-literal `eval` or
`exec` shapes in the study; all named safe neighbours remain clean; diagnostics
do not contain payload text; `phylax-v1.3.0` retains the mature frontier bytes;
the study and runbook are committed under
`docs/phylax-unsafe-deserialization/`; and every command in this demo path
exits zero:

```bash
/usr/bin/python3 -B -m unittest plugins.hexaemeron.tests.test_phylax_checker
uv run --python 3.12.13 python -m unittest plugins.hexaemeron.tests.test_phylax_checker
uv run --python 3.12.13 python plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
uv run --python 3.12.13 python plugins/hexaemeron/tests/run_tests.py
uv run --python 3.12.13 python -m unittest discover -s tests
uv run --python 3.12.13 python -m unittest tests.test_evolution_contract
uv run --python 3.12.13 python scripts/promise_machine.py check
uv run --python 3.12.13 python plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/phylax-unsafe-deserialization/study.md
uv run --python 3.12.13 python plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/phylax-unsafe-deserialization/runbook.md
uv run --python 3.12.13 python plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/phylax-unsafe-deserialization/*.md plugins/hexaemeron/skills/phylax/SKILL.md plugins/hexaemeron/skills/phylax/EVOLUTION.md
uv run --python 3.12.13 python plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
uv run --python 3.12.13 python plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
uv run --python 3.12.13 python plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Change
`plugins/hexaemeron/skills/phylax/scripts/phylax.py`,
`plugins/hexaemeron/tests/test_phylax_checker.py`,
`plugins/hexaemeron/skills/phylax/SKILL.md`,
`plugins/hexaemeron/skills/phylax/EVOLUTION.md`, and
`tests/promise_machine_coverage.json`; create exact committed copies at
`docs/phylax-unsafe-deserialization/study.md` and
`docs/phylax-unsafe-deserialization/runbook.md`; append the Fiat audit record
to `audit/AUDIT.md`; and regenerate `.horos/boundary.json` only if its scan
changes that tracked file. No other path is in scope without a study amendment.

**Tests.** First add hostile fixtures for every named call family and observe
the focused suite fail because `P008` is absent. Then add safe neighbours for
module and direct-import aliases, `SafeLoader` and `CSafeLoader` in positional
and keyword forms, `yaml.safe_load`, literal string and bytes dynamic source,
`marshal.loads`, JSON and unrelated `.load` methods. Cover reason-bearing and
bare pragmas, fixed text/JSON diagnostics with a sentinel payload, alias
rebinding as an explicit source-local limitation, and unchanged `P000` through
`P007` classifications. The 61 existing focused tests plus every new named
case must pass on Python 3.9.6 and 3.12.13; the command output records the final
count.

**Disciplines.** phylax: this step changes the parser-settled hostile-source
boundary and must remain parse-only with fixed diagnostics. ephoros: none,
because the local CLI adds no unattended service or telemetry path and its
existing path/line/code/exit signals are tested. metron: none, because the
issue makes no performance claim and the design adds no recursive analysis.
elenchus: reproduce the missing-rule failures before the fix, then retain
fixtures that fail if the cause-level visitor logic is removed. hypomnema:
record the public grammar and source-local trade in `SKILL.md`, `EVOLUTION.md`
and the committed study/runbook instead of adding a repository-wide ADR.

Implementation order inside the step is fixed: preserve the red fixture
output; add the smallest import-aware visitor grammar; turn the focused suite
green on both Python versions; update the public contract, generation row and
digest pin; copy the receipted documents; run the full demo; then enter the
Fiat audit and prose gates. Any need for `marshal.loads`, scope/dataflow
analysis, a dependency, CI, another call family or changed mature-frontier
bytes stops the step for a study amendment.
