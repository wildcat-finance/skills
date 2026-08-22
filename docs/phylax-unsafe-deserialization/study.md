# study: add unsafe deserialization to Phylax's mechanical subset

## assumptions

Assuming, unless corrected:

1. The run starts from `main` at
   `64096f4d89fc821ab9d91d075cd86be7e7bb92b5`; the run branch and local
   `main` resolved to that commit before this study.
2. Issue #324 authorizes one Python rule under the next free code, `P008`, for
   exactly `pickle.load`, `pickle.loads`, `marshal.load`, `yaml.load` without
   a safe loader, and `eval` or `exec` over a non-literal first argument.
   `marshal.loads` is conspicuously close but not named, so it stays outside
   this packet rather than arriving by typo correction.
3. The rule is source-local and import-aware, not a taint analysis. A literal
   for `eval` or `exec` means an inline `str` or `bytes` `ast.Constant`;
   f-strings, names, calls and other expressions are non-literal even when a
   human can infer their value from nearby code.
4. The safe YAML family is `SafeLoader` and `CSafeLoader`, whether passed as
   the second positional argument or `Loader=` through a resolved module or
   direct-import alias. `safe_load` stays clean. `FullLoader`, `Loader`,
   `UnsafeLoader`, a locally assigned loader name and an unknown subclass do
   not satisfy the mechanically visible exception.
5. This is generation work on mature `phylax-v1.2.0`, not a frontier
   reopening. The implementation remains standard-library-only, supports
   Python 3.9 and 3.12.13, contains no Solidity, and should record
   `phylax-v1.3.0` while retaining the current frontier line and digest.

These readings make one independently testable lint capability. No module
decomposition is needed. The one material wording ambiguity is
`marshal.load` versus `marshal.loads`; this study takes the literal issue scope
and records the latter as an open exclusion.

## 1. problem statement

Phylax says never to unpickle external data and never to parse JSON with
`eval`, but its parser implements no deserialization or dynamic-execution
finding. `Visitor.visit_Call` currently classifies subprocess calls and output
writers only. A file containing any of the following reaches a clean Phylax
result today:

```python
import pickle
import yaml

payload = pickle.loads(download())
document = yaml.load(receive(), Loader=yaml.FullLoader)
result = eval(request_text)
```

The users are contributors running the Phylax gate and reviewers relying on
its stated mechanical boundary. A working prototype emits `P008` at each
recognized unsafe call, keeps named safe neighbours clean, preserves
`P000`-`P007`, and never imports, executes or deserializes target source.

The final demo path is:

```bash
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

The prototype is demonstrated only when all five conditions hold:

- Module, module-alias, direct-import and direct-import-alias forms report
  `P008` for the exact pickle, marshal and YAML calls named above.
- Bare `eval` and `exec`, plus resolved `builtins` aliases, report only when
  the first argument is not an inline string or bytes constant.
- `yaml.safe_load`, `yaml.load` with resolved `SafeLoader` or `CSafeLoader`,
  JSON parsing, unrelated `.load` methods and non-target calls remain clean.
- A reason-bearing existing pragma suppresses `P008`, a bare pragma does not,
  diagnostics contain no inspected payload text, and `P000`-`P007` fixtures
  keep their classifications.
- Every demo command exits zero, including the focused tests on Python 3.9
  and 3.12.13 and the tree-wide Phylax scan.

Before implementation, the focused Phylax suite passes 61/61 on Python 3.9.6
and 3.12.13, and `phylax.py plugins tests` exits zero. Those facts establish a
green starting point and the absent rule; they are not implementation proof.

## 2. prior art

### in this repository

- `plugins/hexaemeron/skills/phylax/scripts/phylax.py` already supplies an AST
  visitor, import-alias sets, source-local call resolution, fixed findings and
  the reason-bearing line suppression filter. The new rule belongs in that
  Python visitor; no target import or runtime library is needed.
- `plugins/hexaemeron/tests/test_phylax_checker.py` pairs hostile specimens
  with safe neighbours and checks both text and JSON secrecy. Its current
  subprocess tests show the house preference for import-bound resolution and
  explicit exclusions rather than a broad name match.
- `plugins/hexaemeron/skills/phylax/SKILL.md` states the two never-rules while
  describing only seven parser-settled rules. `EVOLUTION.md` and
  `skills/VERSIONING.md` show that a meaningful non-frontier behavior change
  increments generation and retains the mature frontier digest.
- `plugins/ariadne/tests/test_untrusted_input.py` is the nearest marketplace
  hostile-input precedent: bounded JSON parsing rejects oversized, deeply
  nested and duplicate-key documents. `plugins/lemma/chunkers/markdown.py`
  already uses `yaml.safe_load` as a clean repository neighbour.

The last two merged pull requests touching the Phylax surface were read before
the options below:

- PR #481, `flag credential-named values in subprocess argv`, established the
  current source-local Python visitor at this base. Its carried-forward alias
  rebinding, attribute/subscript, assigned-value and `**kwargs` exclusions stay
  outside P008; the new rule must not imply dataflow merely because it resolves
  imports. Its generation row is the direct bookkeeping precedent.
- PR #442, `Ephoros catches telemetry keyed by wallet address across Python
  and TypeScript`, changed Phylax's boundary prose. Its accepted Python
  limitation remains: a pragma-shaped `#` inside a string can satisfy the
  line-based suppression filter. Its TypeScript lexer recursion lead is still
  open but unrelated to this Python AST rule, so this run does not absorb it.

The configured audit record, `audit/AUDIT.md`, was also read before design:

- `Phylax TypeScript boundaries`, rounds 1 and 2, found and fixed an unbounded
  TypeScript read with a 1 MiB cap, then closed with zero further findings.
  P008 adds no TypeScript work and does not alter that cap.
- `Phylax credential argv`, step 1 round 1, closed with zero findings while
  preserving source-local exclusions. Its diagnostic-secrecy and
  classification-regression checks apply directly to the new rule.

### in the organisation

Authenticated public GitHub code searches over `wildcat-finance` returned no
Python hits for `pickle.load`, `pickle.loads`, `marshal.load`, `yaml.load`,
`eval(` or `exec(`. No reusable public organization implementation was
established. This says nothing about private or unindexed repositories;
Ariadne's in-marketplace hostile-input tests remain the closest observed
organizational precedent.

### outside the organisation

- Python's `pickle` documentation says malicious pickle data can execute
  arbitrary code during unpickling and distinguishes untrusted JSON parsing
  from that execution risk.
- Python's `marshal` documentation says the format is not secure against
  malicious data and rejects unmarshalling from an untrusted or
  unauthenticated source.
- Python's built-in function documentation warns that both `eval` and `exec`
  execute arbitrary code when handed untrusted input.
- PyYAML's documentation directs untrusted input to `safe_load`; its loader
  table names `SafeLoader` and the LibYAML-backed `CSafeLoader` as the safe
  family.
- Bandit's official B506 implementation is useful parser prior art: it flags
  `yaml.load` unless `SafeLoader` or `CSafeLoader` is supplied by keyword or
  second position. Phylax can adopt that narrow grammar without adopting
  Bandit as a dependency.

## 3. constraints and non-goals

### constraints

- Start from `main` at
  `64096f4d89fc821ab9d91d075cd86be7e7bb92b5` and stay within issue #324.
- Allocate `P008`; preserve the CLI, output schemas, exit codes, suppression
  syntax and the meaning of `P000` through `P007`.
- Resolve only exact module/direct-import aliases for `pickle`, `marshal`,
  `yaml` and `builtins`, plus bare `eval` and `exec`. Do not claim runtime
  identity after reassignment or infer where the first argument came from.
- Add no dependency, subprocess, network call, target-source import,
  deserialization or checker write. Findings carry path, line, code and a
  fixed explanation, never argument contents.
- Record `phylax-v1.3.0` on the generation axis while retaining status
  `mature`, revision `off-chain-boundary-controls`, current-frontier text,
  next job `None -- mature`, and digest
  `3d0057bb195f303c0e40b5782bf59ab0cba53e3172478c6a331d5990236ac604`.

### non-goals

- Taint, control-flow or interprocedural analysis; following input through a
  name, attribute, subscript, container, assignment, return value or
  `**kwargs`.
- `marshal.loads`, `pickle.Unpickler.load`, YAML `load_all`,
  `unsafe_load`/`full_load`, `ast.literal_eval`, dynamic imports or another
  serializer not named by issue #324.
- Proving that input is external, that an inline `eval` string is benign, or
  that a custom YAML loader subclass is safe. P008 settles syntax, not runtime
  provenance or behavior.
- Repairing the TypeScript lexer recursion lead, the line-based pragma-in-a-
  string limitation, Python file-size policy, CI or another plugin's surface.
- Reopening the mature frontier, changing its digest, advancing evolution or
  epoch, or minting a held job.

### explicit unknowns

- Whether omission of `marshal.loads` in the issue was deliberate is unknown.
  The build excludes it; adding it requires a study change or later ticket.
- Public organization search cannot establish private-repository practice.
- A bare local callable named `eval` or `exec` is syntactically indistinguishable
  from the built-in without scope analysis. P008 treats the bare spelling as
  the built-in boundary; the existing reason-bearing pragma is the escape for
  a deliberate local collision.
- A loader held in a local name may be safe at runtime, but source-local alias
  resolution cannot establish that fact. P008 reports it unless the accepted
  loader binding is visible in the call expression.

### operating boundaries

**Always.** Add hostile fixtures and observe them fail before changing the
visitor. Keep a safe neighbour for every call family. Run the focused tests,
full Hexaemeron and root suites, evolution and Promise Machine checks, the
tree-wide Phylax/Ephoros/Hypomnema lints, prose gates and Horos check before
commit.

**Ask first.** Add a dependency; include `marshal.loads` or another call;
widen into dataflow, scope resolution or target execution; change a public
finding field or suppression behavior; touch CI; or alter any mature-frontier
field.

**Never.** Deserialize or execute a fixture to classify it; import inspected
source; place live secrets or payload data in tests or diagnostics; delete a
safe neighbour; weaken `P000`-`P007`; edit vendored source; or claim an unrun
command passed.

Expected implementation and record paths are:

- `plugins/hexaemeron/skills/phylax/scripts/phylax.py` and
  `plugins/hexaemeron/tests/test_phylax_checker.py`.
- `plugins/hexaemeron/skills/phylax/SKILL.md`, `EVOLUTION.md`, and
  `tests/promise_machine_coverage.json`.
- `docs/phylax-unsafe-deserialization/study.md` and
  `docs/phylax-unsafe-deserialization/runbook.md`.
- `audit/AUDIT.md` for rounds and `.horos/boundary.json` if regeneration
  changes the classified tracked tree.

## 4. design options

### option A: import-aware AST classification (chosen)

Extend the existing visitor with canonical bindings for the named modules,
functions and safe YAML loaders. Resolve a call only from those bindings or a
bare `eval`/`exec`. Classify its first argument and YAML loader expression from
the current call node, emit `P008`, then let the existing suppression and
rendering paths handle the result.

This construction reuses the checker's existing AST and alias idiom, can test
every claimed shape directly, and never runs target code. It trades away
runtime provenance, assignment following, custom safe loaders and semantic
name resolution.

### option B: spelling-only call matching

Match terminal names such as `.load`, `eval` and `exec` without import
resolution. The patch would be shorter, but ordinary file readers and local
methods would become findings while aliased unsafe calls would escape. The
lower line count buys a rule contributors will learn to suppress.

### option C: dataflow or an external analyzer

Track values from inputs into dangerous calls, or add Bandit/Semgrep and map
its findings into Phylax. This can distinguish external data and cover more
aliases, but it opens scope, dependency, version, output-mapping and false-
positive questions absent from the issue. It also costs more to understand
than the surrounding checker.

Option A is the lowest-comprehension-cost design that meets the literal issue.
It gives up semantic completeness in exchange for one visible source-local
grammar beside the existing rules. Option B is too noisy; Option C pretends a
larger security claim than this generation packet can support.

## 5. risk register seed

```risk-register
source-parse | tracked Python source crossing the checker boundary | source is parsed as AST only and is never imported executed or deserialized
call-identity | imported names crossing into dangerous-call classification | only exact module and direct-import bindings plus bare eval and exec receive P008
pickle-scope | pickle call syntax at the deserialization boundary | load and loads report while dumps and unrelated load methods remain clean
marshal-scope | marshal call syntax at the deserialization boundary | load reports and the excluded loads spelling has a named negative fixture
yaml-loader | the Loader argument deciding YAML object construction | SafeLoader and CSafeLoader aliases pass while absent unknown and unsafe loaders report
dynamic-source | the first eval or exec argument at the code-execution boundary | inline string and bytes constants stay clean while names calls and f-strings report
alias-rebinding | source-local binding evidence beside runtime reassignment | tests state that imports are resolved but assignment and scope dataflow are not
suppression-line | P008 crossing the existing reason-bearing pragma filter | a stated reason suppresses and a bare pragma does not while the accepted string quirk stays unchanged
diagnostic-output | inspected source influencing text and JSON findings | messages name the call family but never repeat the argument or payload value
classification-drift | new visitor branches beside P000 through P007 | the full existing fixture suite retains every prior code and safe neighbour
analysis-work | extra AST traversal on a parsed Python file | the implementation visits each relevant call locally and adds no recursive dataflow or target execution
partial-run | an interrupted or failed lint test or prose command | no clean result commit or receipt is accepted from an incomplete or non-zero command
ledger-integrity | generation bookkeeping at the mature Phylax frontier | only generation advances while the revision frontier next job and digest remain unchanged
```

There is no funds arithmetic, external service call, upgrade path or signing-
key custody in this change. The checker adds no subprocess, network fetch or
filesystem write. Secret and payload custody is limited to not copying
inspected argument contents into diagnostics. Existing Python reads and
`ast.parse` remain the input path; the audit should review work amplification,
but this issue makes no new file-size policy.

## 6. glossary seeds

- `P008`: the proposed single finding code for the exact unsafe loader and
  dynamic-execution syntax in issue #324.
- `dangerous call`: a call resolved to an in-scope pickle, marshal, YAML or
  built-in execution function by the visitor's source-local binding table.
- `literal dynamic source`: an inline string or bytes `ast.Constant` passed as
  the first argument to `eval` or `exec`.
- `safe loader family`: PyYAML `SafeLoader` and `CSafeLoader`, including
  module and direct-import aliases visible in the call.
- `source-local`: classified from imports and the current call expression,
  without following assignments, control flow, values or runtime rebinding.

## 7. sources and checks

- Task and base: issue #324,
  <https://github.com/wildcat-finance/skills/issues/324>, and
  `main` at `64096f4d89fc821ab9d91d075cd86be7e7bb92b5`.
- Repository authority: `phylax.py`, `test_phylax_checker.py`, Phylax
  `SKILL.md`/`EVOLUTION.md`, `skills/VERSIONING.md`, Ariadne's
  `test_untrusted_input.py`, and Lemma's `markdown.py` safe YAML call.
- Change history: merged PRs #481 and #442; `audit/AUDIT.md` sections
  `Phylax credential argv` and `Phylax TypeScript boundaries`.
- Language and library authority: Python `pickle`, `marshal`, `eval` and
  `exec` documentation at <https://docs.python.org/3/library/> and PyYAML's
  documentation at <https://pyyaml.org/wiki/PyYAMLDocumentation>.
- Parser prior art: Bandit B506 documentation and implementation at
  <https://bandit.readthedocs.io/en/latest/plugins/b506_yaml_load.html> and
  <https://github.com/PyCQA/bandit/blob/main/bandit/plugins/yaml_load.py>.

Checks run for this study:

- `git rev-parse HEAD`, `main` and `origin/main` each returned the base commit
  above; the run worktree was clean before this artifact was written.
- `/usr/bin/python3 -B -m unittest plugins.hexaemeron.tests.test_phylax_checker`
  passed 61/61 on Python 3.9.6; the same suite independently passed 61/61 on
  Python 3.12.13.
- `/usr/bin/python3 -B plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
  exited zero and printed `clean`.
- Public issue and pull-request records supplied the exact scope, generation
  note, carried-forward limits and merge commits; public organization code
  search returned no reusable hit.

These checks establish the current state and a buildable syntax boundary. They
do not establish that Option A is implemented, that its future fixtures pass,
or that a clean P008 scan proves inspected data trustworthy.

## 8. signals and the questions behind them

`plugins/hexaemeron/skills/ephoros/SKILL.md` adds no telemetry gate because
this is a local lint, not an unattended service. The expected single runbook
step preserves two existing signals:

1. "Which call failed, and where?" Text output carries `path:line`, `P008` and
   a fixed family-specific message; JSON carries the same fields separately.
2. "Did the exact scan finish cleanly?" Exit zero plus `clean` answers yes.
   A finding, parse/read failure, bad invocation or interrupted command cannot
   supply that signal.

No event, metric, trace, correlation id or alert is warranted. The step tests
the current CLI signal shape instead of inventing an on-call surface.

## 9. boundaries per capability

`plugins/hexaemeron/skills/phylax/SKILL.md` governs the capability. The primary
boundary is hostile Python source entering `ast.parse` and influencing a gate
result. Code execution and checker integrity are worth taking there; parse-
only inspection, exact call bindings and negative fixtures close it.

The second boundary is YAML's loader expression. Arbitrary object
construction is worth taking; only a mechanically resolved `SafeLoader` or
`CSafeLoader` closes it. Unknown custom loaders fail closed into a finding and
can use the existing reason-bearing exception when a reviewer has evidence.

The third boundary is output. Payload contents and confidence in a clean scan
are worth taking; fixed messages, no AST value rendering, preserved `P000`
failures and non-zero findings close it. The risk ids `source-parse` through
`diagnostic-output` enumerate these checks.

No new host, dependency, subprocess, model output, agent tool, external API,
output path or persistent write boundary is introduced.

## 10. budget or its absence

`plugins/hexaemeron/skills/metron/SKILL.md` has no performance gate here.
Issue #324 makes no latency, memory or throughput claim, and the selected
design adds local classification to an AST already built for each Python
file. No speed-motivated change is authorized, so there is no before/after
budget to manufacture. The focused test command is a correctness gate, not a
benchmark. `analysis-work` remains an audit concern so a hidden recursive or
dataflow walk cannot masquerade as the chosen design.

## 11. fail-closed posture

`plugins/hexaemeron/skills/elenchus/SKILL.md` governs the failure already in
hand. Each hostile family fixture must be observed red against the current
visitor and green only after the cause-level P008 change. Every family also
gets a safe neighbour: safe loaders, literal dynamic source, unrelated methods
and excluded spellings must remain clean.

A changed prior code, safe-neighbour finding, payload value in output, target
execution, ledger mismatch, failed lint or any non-zero demo command stops the
step. Existing unreadable and invalid Python inputs remain `P000`; no new rule
may convert an incomplete analysis into `clean`. The guard tests stay in
`test_phylax_checker.py` and must fail when the P008 implementation is removed.

## 12. decisions and their homes

`plugins/hexaemeron/skills/hypomnema/SKILL.md` puts the behavior decision in
`plugins/hexaemeron/skills/phylax/EVOLUTION.md`. Its generation row should name
P008's exact call grammar, source-local trade and fixture evidence while
retaining the mature frontier bytes. `SKILL.md` owns the public mechanical-
subset description; changing it requires repinning its Promise Machine digest
in `tests/promise_machine_coverage.json`.

Exact committed copies of the receipted artifacts belong at
`docs/phylax-unsafe-deserialization/study.md` and
`docs/phylax-unsafe-deserialization/runbook.md`. Audit rounds append their
enumerated review to `audit/AUDIT.md`. No repository-wide ADR is warranted:
the change adds no shared schema, dependency, storage format or cross-plugin
ownership decision.

If implementation needs `marshal.loads`, semantic scope resolution, dataflow,
a custom-loader proof or another call family, amend this study before code.
The current generation row cannot silently widen a mature skill's claim.
