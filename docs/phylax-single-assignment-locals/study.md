# resolve single-assignment locals for Phylax rules

## assumptions

- "same function scope" means one `FunctionDef` or `AsyncFunctionDef`. Module, class, lambda, comprehension, generator and nested-function bindings do not qualify.
- "assigned exactly once" means a direct statement in that function body with one simple `Name` target and a value. A simple valued `AnnAssign` may qualify; chained, unpacking, attribute and subscript targets do not.
- The qualifying write must precede the use. Any other binding or deletion of the same name in that function, including a parameter, import, augmented assignment, named expression, loop target, exception name or pattern capture, disqualifies resolution.
- Assignments under `if`, `match`, loops, `try`, `with` or another compound statement are branch-sensitive and therefore excluded even when static syntax makes a path look obvious.
- Resolution is a bounded, source-only substitution used by P002, P004 and P008. It does not execute code, prove types, infer taint, follow attributes, or establish interprocedural facts.
- Existing rules remain conservative when a name cannot be proved eligible. This work adds the issue's narrow positive cases; it does not turn a previously reported dangerous call into a clean result except where a proven single assignment exposes an existing safe neighbour such as a literal `eval` input or `yaml.SafeLoader`.
- Issue #502 is optional generation work on mature `phylax-v1.4.0`. Integration may add one generation row, but the frontier status, revision, next job and digest stay byte-for-byte unchanged.

## 1. Problem statement

Phylax presently understands the expression written directly at a sink but not the same expression placed in one local. That creates three related classification defects:

- P002 misses a subprocess string command held in a local.
- P004 misses credential-named values when the subprocess argv expression is held in a local.
- P008 misses an assigned dangerous callable, and overclaims assigned literal dynamic-execution input and assigned safe YAML loader as dangerous.

Build one narrow function-local resolver for those three existing rules. A working prototype resolves only an eligible preceding single assignment, retains each rule's current finding code, runner/import grammar, suppression line, diagnostic text and no-secret output, and refuses to infer through every excluded form above.

The demonstration path is the focused checker suite:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_phylax_checker
```

It starts at 79 passing tests on `main`. The prototype must add red-then-green fixtures for the five live probes and the exclusion matrix. At the study base the probes produce:

```text
assigned P002 command       -> []
assigned P004 argv          -> []
assigned literal eval       -> P008
assigned SafeLoader         -> P008
assigned pickle callable    -> []
```

The intended post-change classifications are P002, P004, clean, clean and P008 respectively. The same focused suite must also prove that reassignment, branch-local writes, attributes, comprehensions and cross-function flow do not earn resolution.

## 2. Prior art

### current repository

`plugins/hexaemeron/skills/phylax/scripts/phylax.py` already has the right source-only substrate:

- `_boundary_bindings` pre-collects import evidence without importing the target.
- `_starts_process` resolves the existing source-local subprocess forms.
- `_boundary_modules`, `_safe_yaml_loader` and `_check_p008` classify import-bound calls and YAML loaders.
- `visit_Call` owns P002, P004 and the P008 dispatch; `visit_Assign` currently checks only credential literals.
- the TypeScript-only `_assigned_object` performs a lexical previous-assignment lookup, but it neither proves exactly one write nor models Python function scope. It is nearby prior art, not a reusable correctness argument.

`plugins/hexaemeron/tests/test_phylax_checker.py` is the shared classification and diagnostic-secrecy harness. Its current fixtures cover P000-P008, subprocess import shapes, P004 inline argv, P008 late and conflicting imports, safe YAML loader forms, dynamic literals, suppression and cross-scope collisions. The repository-declared Python 3.14.6 interpreter passed all 79 focused tests at this base and remains the release authority.

Simple AST assignment extraction also exists in `scripts/dead_code.py`, `scripts/contributors.py` and Ariadne tests. Those readers deliberately handle literal declarations; none is a general scope or dataflow engine. Repository search found no existing Python function-local single-assignment resolver.

### shipped studies and audit evidence

`docs/phylax-credential-argv/study.md` deliberately selected an inline argv subtree and excluded separately assigned argv. `docs/phylax-unsafe-deserialization/study.md` selected source-local import-aware AST analysis and excluded assignment, general lexical scope, taint and control flow. This issue accepts only the common single-assignment slice of those exclusions; it does not silently absorb the rest.

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited zero for the complete target. I therefore read the fresh `audit/AUDIT_SYNOPSIS.md` view, not `audit/AUDIT.md`. The in-scope records are:

- `Phylax credential argv, step 1, round 1`: `review-code`, `review-tests` and `review-records` are clean. Separately assigned argv is an explicit lead not pursued and is accepted here. `API_TOKEN` grammar, attribute/subscript values, star expansion, `**kwargs`, runner rebinding and flag interpretation remain outside scope.
- `Phylax unsafe deserialization, step 1, round 1`: S1-R1-01 medium, late-import discovery, fixed and guarded; S1-R1-02 low, conflicting import identities, fixed and guarded. Assignment/scope/taint/control-flow work remained excluded.
- round 2: S1-R2-01 low, ambiguous identities could emit the wrong family-specific diagnostic, fixed and guarded.
- round 3: S1-R3-01 medium, a cross-scope YAML alias could displace a built-in dynamic call, fixed and guarded.
- round 4: no new finding; the final code, test and record reviews were clean. The existing source-local exclusions remained deliberate.

For all five legacy entries, `audit-schema`, `Covered`, `Not checked` and `Elenchus verdict` are recorded as `[missing legacy field: ...]` and remain unknown. Their risk tables are useful evidence but do not repair those missing fields. Their named leads not pursued remain open unless this study explicitly accepts or preserves them. No dedicated P002 audit block was discovered in the verified root synopsis; P002 evidence therefore comes from current source, tests and git history rather than an invented audit verdict. No in-scope Phylax record exists in `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`.

### last semantically relevant merged pull requests

- [PR #486](https://github.com/wildcat-finance/skills/pull/486), merged as `454bf3c9`, added P008. Its four audit rounds went `2 -> 1 -> 1 -> 0`, and its body carries forward `marshal.loads`, relative/wildcard/dynamic imports, assignment/general lexical scope/taint/control flow, custom-loader proofs, pragma-in-string behaviour and Python file-size policy. This study accepts only eligible local assignment resolution and preserves every other item.
- [PR #481](https://github.com/wildcat-finance/skills/pull/481), merged as `64096f4d`, added P004 inline argv scanning. Its body explicitly leaves `env=`, separately assigned argv and local runner names out. This study accepts separately assigned argv only; it preserves the other runner and argument-shape limits.

Local merge `68039a87` says `Merge pull request #666` and touched the Phylax test path only to remove duplicated whole-tree lint coverage. Public issue and pull endpoints for #666 return 404, and GitHub's commit-to-pull association for that merge is empty. That is negative evidence: no public body exists to carry semantic unfinished work, and the local diff changes test plumbing rather than P002/P004/P008 semantics. It does not displace #486 and #481 as the last two semantically relevant merged pull requests.

### outside prior art

Python's [`ast` documentation](https://docs.python.org/3.14/library/ast.html) exposes the binding shapes directly: `Assign` has target lists, while `AnnAssign` and `AugAssign` are distinct nodes and comprehension targets are explicit. Python's [`symtable` documentation](https://docs.python.org/3.14/library/symtable.html) supplies compiler scope identities but not the binding RHS and source-order substitution this feature needs. [LibCST's `ScopeProvider`](https://libcst.readthedocs.io/en/latest/_modules/libcst/metadata/scope_provider.html) models assignments and accesses across a much broader Python grammar. [Pyflakes](https://github.com/PyCQA/pyflakes) is useful precedent for per-file AST analysis that avoids importing targets, but adopting an external analyser would widen Phylax's dependency and semantics far beyond this wish.

## 3. Constraints and non-goals

- Base, target and `origin/main` are the same commit: `7e97b5195d5b0e43146b4200f26cd41b89003413`.
- The repository pins Python `3.14.6` in `.python-version` and `==3.14.*` in `pyproject.toml`. All receipted gates must run under that declared interpreter.
- Limit implementation to `plugins/hexaemeron/skills/phylax/scripts/phylax.py`, focused tests, Phylax mechanical prose, the tracked study/runbook copies and a generation-only evolution row. Do not change finding codes or output schema.
- Do not import or execute scanned Python. Add no third-party dependency, subprocess, filesystem write, network call, persistent cache or model call.
- Do not resolve module/class locals, closures, globals, nonlocals, nested scopes, attributes, subscripts, imports, parameters, destructuring, branches, comprehensions, loops, exception handlers, pattern captures or cross-function values.
- Do not add general reaching-definitions, taint, type, constant-folding, control-flow or interprocedural analysis. Do not interpret string flags or extend the credential grammar.
- Keep P002 tied to resolved subprocess runners, P004 tied to the existing inline-argv slot after local substitution, and P008 tied to the current import/call-family grammar. Do not absorb #323 or the unrelated model-proxy gaps #698, #699 and #702.
- Do not reopen or advance the mature frontier. A new generation row must retain `mature`, `off-chain-boundary-controls`, no next job, and digest `3d0057bb195f303c0e40b5782bf59ab0cba53e3172478c6a331d5990236ac604`.

Always: parse source only, fail conservatively on ambiguity, report at the sink call, preserve fixed diagnostics and prove every accepted/excluded binding shape with a fixture.

Ask first: any proposal to resolve another scope, infer a credential from its value, change the existing ambiguity posture, add a dependency, change a finding grammar, or change the mature frontier tuple.

Never: execute scanned code, print a scanned value, follow runtime imports, claim an unresolved name is safe, mutate controller state from an implementation step, or mint a held frontier job for #502.

## 4. Design options

### option A: one narrow function binding index and bounded resolver (selected)

Build a per-function index once, recording eligible direct-body assignments and every disqualifying write. Resolve a `Name` only when there is exactly one eligible prior write and no other binding of that name in the function. Follow eligible name-to-name chains with a visited set and a fixed maximum depth. Feed the resolved AST expression into the three existing rule seams.

Trade: this adds one small shared semantic layer and an explicit write taxonomy, but keeps rule identity, output and source-only operation intact. It is the cheapest design that prevents P002, P004 and P008 from inventing three subtly different meanings of "single assignment."

P004 has one rule-specific ordering constraint: test a visited `Name` against the existing credential grammar before substituting it. Thus `secret = read(); argv = ["tool", secret]` still reports `secret`; substitution is for exposing an argv expression, not erasing the existing name signal.

### option B: rule-local backward lookups

Teach each of P002, P004 and P008 to scan earlier statements for one assignment. This is initially shorter, but it duplicates scope, reassignment, branch, ordering and cycle policy three times. The implementations would drift and recreate the inconsistent classifications the issue groups together. Reject.

### option C: `symtable` plus AST mapping

Use Python compiler symbol tables for scope and a second AST pass for definitions and RHS nodes. This gets robust local/global/free classification, but `symtable` does not itself answer which RHS reaches a use or whether a binding is direct and preceding. Mapping the two representations costs more comprehension than the excluded grammar needs. Reject for this prototype.

### option D: LibCST, Pyflakes or another external semantic engine

Adopt a mature assignment/access model. This handles far more Python constructs and preserves concrete syntax, at the cost of a new dependency, a much larger trust surface and semantics that would have to be clipped back to this tiny promise. Reject; revisit only if a later approved job requests general Python scope analysis.

Implementation shape for option A:

1. Entering a function creates a scope record without traversing nested functions/classes/comprehensions as that scope.
2. Collect direct-body eligible assignments and all same-function disqualifying writes. Preserve statement order.
3. Resolve on demand only at P002 command, P004 argv and P008 callable/loader/dynamic-source seams. A missing, late, repeated, cyclic or over-depth binding returns unresolved.
4. P002 asks the existing string-command predicate about the resolved command expression. P004 walks the resolved argv expression, checking credential names before further substitution. P008 resolves the callable before current import-family matching and resolves only the loader and first positional dynamic-source expression before current safety/literal predicates.
5. Keep findings anchored to `ast.Call` so reason-bearing suppression and output locations do not move to assignment lines.

## 5. Risk register seed

The audit loop must enumerate every line; a clean overall suite is not a substitute for a disposition.

```risk-register
source-parse | untrusted Python source entering ast.parse and the visitor | the checker never imports executes evaluates or deserializes target code
scope-identity | names shared by module class nested and sibling function scopes | only the exact containing FunctionDef or AsyncFunctionDef supplies bindings
write-count | every syntax form that can bind or delete a local name | a second or unsupported binding disqualifies resolution instead of selecting a convenient write
statement-order | a sink before or after its only assignment | only a proven preceding binding resolves and forward references remain conservative
branch-exclusion | assignments nested below compound statements | branch loop try with match and comprehension writes never earn straight-line trust
resolution-cycle | chains such as a-equals-b and b-equals-a | a visited set and finite depth stop resolution and preserve the unresolved classification
p002-classification | the resolved subprocess command expression | assigned strings report P002 while list argv and unresolved names preserve existing behaviour
p004-name-first | credential names inside an assigned argv tree | the credential grammar runs before substitution so resolution cannot erase an existing signal
p008-call-identity | assigned pickle marshal yaml and dynamic-execution callables | resolution feeds current import ambiguity logic without bypassing the four fixed audit guards
safe-neighbour | assigned literal dynamic input and assigned SafeLoader or CSafeLoader | exact safe forms become clean while unknown custom and unsafe values still report
diagnostic-output | findings produced from source containing secret material | text and JSON retain fixed messages and never echo assignment values or payload sentinels
classification-drift | all checker families P000 through P008 and suppression | non-target rules messages locations and reason-bearing suppression remain guarded
analysis-work | large functions with many names and alias chains | collection is linear per function and resolution is memoized or bounded rather than rescanning per use
partial-run | an interrupted test lint or audit command | no partial output is promoted to a passing receipt and reruns start from complete source evidence
ledger-integrity | a generation row added to mature Phylax | version advances generation only and the complete frontier tuple and digest remain unchanged
```

## 6. Glossary seeds

eligible assignment: one direct-body simple-name `Assign`, or valued `AnnAssign`, that precedes the use and is the name's only binding in the function.

disqualifying write: any additional or excluded binding or deletion of the candidate name in the same function.

function scope: the exact `FunctionDef` or `AsyncFunctionDef` containing both assignment and sink, excluding nested scope bodies.

binding index: the per-function record of eligible assignments, disqualifying writes and source order.

resolver: the bounded source-only operation that replaces an eligible `Name` with its RHS AST expression.

sink: the existing subprocess or unsafe-deserialization/dynamic-execution call at which Phylax classifies and reports.

unresolved: no proof satisfying the eligible-assignment grammar; existing conservative rule behaviour applies.

safe neighbour: an expression the current rule already treats as clean when inline, such as a literal dynamic input or `yaml.SafeLoader`.

generation-only: a skill version row that records new artefacts without changing the mature frontier tuple or minting a next job.

## 7. Sources

- live scope and status: [issue #502](https://github.com/wildcat-finance/skills/issues/502), checked open, unassigned and labelled `wish` at study time.
- integration base: git commit `7e97b5195d5b0e43146b4200f26cd41b89003413`; `.python-version`; `pyproject.toml`.
- canonical Phylax contract and ledger: `plugins/hexaemeron/skills/phylax/SKILL.md`; `plugins/hexaemeron/skills/phylax/EVOLUTION.md`.
- implementation: `plugins/hexaemeron/skills/phylax/scripts/phylax.py`, especially `_boundary_bindings`, `_starts_process`, `_boundary_modules`, `_safe_yaml_loader`, `_check_p008`, `visit_Call`, `visit_Assign` and `_assigned_object`.
- fixtures: `plugins/hexaemeron/tests/test_phylax_checker.py`.
- shipped specifications: `docs/phylax-credential-argv/study.md`; `docs/phylax-unsafe-deserialization/study.md`.
- audit view: `audit/AUDIT_SYNOPSIS.md`, accepted only after `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited zero; `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` was searched and contains no in-scope Phylax record.
- merged history: [PR #486](https://github.com/wildcat-finance/skills/pull/486), merge `454bf3c9`; [PR #481](https://github.com/wildcat-finance/skills/pull/481), merge `64096f4d`; local negative evidence at merge `68039a87` for unavailable #666.
- upstream Python grammar and scope references: [`ast`](https://docs.python.org/3.14/library/ast.html); [`symtable`](https://docs.python.org/3.14/library/symtable.html).
- external alternatives: [LibCST `ScopeProvider`](https://libcst.readthedocs.io/en/latest/_modules/libcst/metadata/scope_provider.html); [Pyflakes](https://github.com/PyCQA/pyflakes).
- study schema: `plugins/hexaemeron/skills/protasis/SKILL.md`.

## 8. Signals, and the questions behind them

This is a deterministic local lint, not an unattended service. It needs no exporter, metric backend or new telemetry. The existing finding stream and command exit answer the useful operator questions:

1. Did analysis complete? The test/lint step emits its normal terminal summary and exit status; an interruption or nonzero exit is never recorded as clean.
2. Which sink was classified? The implementation/test step preserves `path`, sink-call `line`, finding `code` and fixed bounded `message` in text and JSON.
3. Which local-resolution family regressed? The focused test step names separate P002 command, P004 name-first argv, P008 callable, loader, literal, reassignment, branch and cross-scope cases.
4. Did generation mutate the mature frontier? The records step emits the evolution check and an exact before/after comparison of status, revision, next job and digest.

Signal ownership and field discipline remain with [Ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md); this study adds no second telemetry contract.

## 9. Boundaries, per capability

The build is held to [Phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md).

- Python parsing boundary: worth taking syntax and AST structure only. Control: `ast.parse`; never import, evaluate, call or deserialize target code; P000 remains the parse-failure path.
- local-binding boundary: worth taking an exact direct-body, preceding, single simple-name assignment. Control: explicit scope identity, all-write disqualification, branch exclusion, cycle/depth guard and unresolved fallback.
- subprocess boundary: worth taking only the current resolved subprocess runner plus command/argv expression. Control: no shell execution, no runner-name expansion, no flag interpretation and no `env=` widening.
- secret-material boundary: worth taking identifier spelling needed by the current `CREDENTIAL` grammar. Control: check names before substitution and emit only fixed diagnostics; never copy RHS values or payloads.
- P008 trust boundary: worth taking only the current source-local import families plus eligible local aliases and safe neighbours. Control: retain ambiguous-import, cross-scope and loader conservatism fixed by S1-R1-01/02, S1-R2-01 and S1-R3-01.
- repository-write boundary: worth taking only implementation, fixtures and governed records during later receipted steps. Control: no cache or target-file write from the checker; generation-only ledger verification; controller mutations remain controller-owned.

## 10. The budget, or its absence

No wall-time or throughput budget is justified: this is a local lint extension with no user-requested performance claim, and [Metron](../../plugins/hexaemeron/skills/metron/SKILL.md) forbids inventing one after the fact.

The structural work bound is nevertheless testable: one collection pass per function, then bounded or memoized resolution; no per-call full-function rescan. The audit inspects that property and the focused suite exercises long/cyclic chains. There is no benchmark command because no performance budget exists. The correctness command is:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_phylax_checker
```

It is evidence of behaviour, not a Metron performance measurement.

## 11. The fail-closed posture

The build is held to [Elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md). Stop on parse failure, ambiguous scope identity, any second or unsupported write, a non-preceding assignment, a branch-local definition, a resolution cycle/depth limit, a changed diagnostic, secret echo, a focused regression, stale audit view, failed prose/tree lint, failed evolution check or changed frontier tuple.

Each defect follows red, fix, green:

1. Add the smallest focused fixture that reproduces the wrong classification on the exact base.
2. Capture the expected current mismatch without treating a known red as a suite pass.
3. Make one semantic change.
4. Run the named fixture, the full focused checker suite and the complete selected repository gates.

The five baseline probes in section 1 are the initial red evidence. Exclusion fixtures are guard tests even when already green: they prevent the narrow resolver from becoming accidental control-flow analysis. A nonzero, interrupted or wrong-interpreter run cannot close the guard.

## 12. Decisions and their homes

Decision ownership remains with [Hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md).

- The exact eligible-assignment grammar, rejected broad alternatives and accepted exclusions are skill-local and live in the tracked `docs/phylax-single-assignment-locals/study.md` copy plus its runbook. They do not earn a repository-wide ADR.
- The implementation seam and name-first P004 ordering live beside the code in `plugins/hexaemeron/skills/phylax/scripts/phylax.py` and executable fixtures, not in a separate essay.
- The durable release fact lives in one new `plugins/hexaemeron/skills/phylax/EVOLUTION.md` generation row. It must say single-assignment locals were added for P002/P004/P008 and list the exclusions that remain.
- Audit dispositions live in the Fiat run's authoritative audit record and synopsis path chosen by the controller. Every risk-register id must be named reviewed or not applicable; legacy unknown fields remain unknown.
- No decision in this prototype changes repository-wide architecture, an external interface or the mature frontier. If implementation discovers that a general scope engine or dependency is required, stop and seek a new decision rather than smuggling one into #502.

The later implementation exit is complete only when the focused demonstration and selected full gates pass under Python 3.14.6, all tracked records agree, and the frontier tuple comparison is unchanged. This survey writes only this study artifact and does not receipt the controller.
