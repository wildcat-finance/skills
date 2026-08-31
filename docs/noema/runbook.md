# Runbook: prototype Noema as a model-native sliced instruction IR

This runbook derives from `.hexaemeron/study.md` at SHA-256
`4a7c0e7bdfc3d44535d36d3666b3272436d1662463aabc6c82380bd554e5ffec`.
It delivers one shadow-mode root prototype in five stacked pull requests.
Existing Markdown remains authoritative throughout. No step changes a plugin,
marketplace, router, Promise Machine claim, CI workflow, #909 path or external
repository. ADR-054 exists on another active ref, so this run reserves ADR-055
against the refs observed during study; integration must refuse a collision
rather than overwrite another record.

## Step 1: freeze the Noema contract and verified seed inventory

**Goal.** Commit the receipted specification, shadow-authority decision,
version-1 public contract, closed schema, safe CLI scaffold and exact inventory
of the operator-supplied evidence before implementing its semantics.

**Entry.** The clean run branch at
`7e97b5195d5b0e43146b4200f26cd41b89003413`, with the study receipted at
SHA-256 `4a7c0e7bdfc3d44535d36d3666b3272436d1662463aabc6c82380bd554e5ffec`,
this runbook receipted, current-main audit synopses verified, and none of the
declared Noema product paths present. The exact repository interpreter is
Python 3.14.6. The public evidence archive is 24,907 bytes with SHA-256
`1e1eb5e9908551f1337b7ec58a37ae7f37fd97e41d5ac424bc4992eb1d11b540`.

**Exit.** `docs/noema/study.md` and `docs/noema/runbook.md` match the
receipted artifacts byte for byte. ADR-055 records the decision to evaluate a
typed sliced IR in shadow mode, the rejected full-codec, prose-summary and
opaque-carrier options, and the fact that only a later record may reverse
Markdown authority. `docs/noema-v1.md` fixes the closed core types, operator
semantics, canonical-source and projection roles, digest rules, resource caps,
stable refusal families, source-binding boundary, runtime operations,
evaluation boundary and recovery. The JSON schema parses and fixes the closed
inventory, lock, manifest, result and evidence shapes used by later steps.

`tests/fixtures/noema-v1/seed-inventory.json` names the archive, public URL,
all 17 relative paths, sizes and SHA-256 values from #942. `verify-seed` reads a
caller-supplied archive without extracting or executing it, rejects unsafe or
unexpected members and prints one bounded digest result. The scaffold exposes
only `about`, `verify-seed` and help; every unimplemented operation refuses by
name. No plugin or #909 path changes, and every command below exits zero:

```bash
python3 -c 'import platform; assert platform.python_version() == "3.14.6"'
cmp .hexaemeron/study.md docs/noema/study.md
cmp .hexaemeron/runbook.md docs/noema/runbook.md
python3 scripts/noema.py verify-seed --archive /private/tmp/noema-v0-evidence.zip --inventory tests/fixtures/noema-v1/seed-inventory.json
python3 -m unittest tests.test_noema.NoemaScaffoldTests -v
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/noema/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/noema/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/noema/study.md docs/noema/runbook.md docs/noema-v1.md docs/decisions/ADR-055-evaluate-noema-as-a-sliced-instruction-ir.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py scripts tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py scripts tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs scripts
python3 scripts/run_checks.py
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Create `docs/noema/study.md`, `docs/noema/runbook.md`,
`docs/noema-v1.md`,
`docs/decisions/ADR-055-evaluate-noema-as-a-sliced-instruction-ir.md`,
`schemas/noema-v1.schema.json`, `scripts/noema.py`, `tests/test_noema.py`,
`tests/fixtures/noema-v1/README.md` and
`tests/fixtures/noema-v1/seed-inventory.json`. Permit `.horos/boundary.json`
only for the deterministic tracked-tree update and the configured Fiat audit
record plus generated synopsis only in their owning phase. Change no other
product path without a receipted study amendment.

**Tests.** Add at least 15 `NoemaScaffoldTests` for the two receipted-copy
digests, exact Python pin, schema JSON and closed top-level keys, version magic,
CLI help and stable unimplemented refusals, archive and member byte caps,
duplicate and extra member refusal, traversal, absolute path, link and special
file refusal, archive digest mismatch, per-file size/digest mismatch and one
valid inventory verification. The fixture builder uses only synthetic bytes;
the exit command separately verifies the operator archive. The source-bound
Elenchus runner for any audit repair is
`python3 tests/run_tests.py --elenchus-report {report}`; report format
`unittest-json-v1`; expected schema `elenchus.unittest.v1`; report file
`.elenchus/fiat-942-step-1.json`. The report path must be fresh, and missing,
stale, malformed, empty, zero-test or infrastructure-failed output is
`inconclusive`.

**Disciplines.** phylax: a supplied ZIP crosses a new ingestion boundary, so
the archive is bounded and inventoried without extraction or execution, and
the focused suite drives hostile members. ephoros: this is an operator-run CLI
with no unattended path; one bounded result names archive digest, member count
and refusal while emitting no member bytes. metron: none, because this step
freezes budgets but makes no measured compression claim. elenchus: no product
failure exists at entry; an audit repair must use the exact structured runner
above and preserve a parent-red guard. hypomnema: ADR-055 is the standing home
for the cross-repository authority direction and all rejected designs before
the tracked study ships.

## Step 2: build the canonical graph, module lock and text projection

**Goal.** Implement a bounded standard-library parser, type checker, formatter,
module registry, semantic diff and reversible tokenizer-profile text projection
for the closed version-1 graph.

**Entry.** Step 1's pull request is integrated into the run branch; its tracked
study, runbook, ADR, public contract, schema, inventory, CLI scaffold and tests
are unchanged and green. The seed reference code remains outside the product
and has not been executed or copied into `scripts/`.

**Exit.** Canonical `.noe` parses to one closed NIR and formats back to the
same UTF-8 bytes with LF and final LF. Duplicate ids, unknown operators or
types, bad arity, unsafe Unicode, unresolved references, type mismatch,
relation cycles, ambient or cyclic imports, stale module/compiler/profile
digests, alias collision, unbounded quantification and every exact or
limit-plus-one resource specimen refuse with stable `NOE-E-*` codes before a
partial graph is returned. Modules carry qualified signatures and pure graph
definitions; locks bind complete module, compiler, kernel and profile bytes.

The baseline ASCII projection recovers the same NIR together with its manifest
and cannot overload an alias by arity or collide with a reserved opcode,
predicate, literal id or visible value. Typed literals preserve kind and exact
bytes and remain inert. `semantic-diff` reports every changed effect, gate,
authority, scope, evidence class, literal, transition and precedence edge in a
closed machine-readable record. Confined commands read regular files, refuse
symlinks and special files, and write atomically with a target-independent
temporary name. `self-test` exercises one complete graph/module/profile round
trip. Every command below exits zero:

```bash
python3 scripts/noema.py self-test
python3 -m unittest tests.test_noema.CanonicalSourceTests tests.test_noema.GraphValidationTests tests.test_noema.ModuleLockTests tests.test_noema.ProjectionTests tests.test_noema.SemanticDiffTests tests.test_noema.PathBoundaryTests -v
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py scripts tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py scripts tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs scripts
python3 scripts/run_checks.py
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Change `scripts/noema.py`, `schemas/noema-v1.schema.json`,
`docs/noema-v1.md`,
`docs/decisions/ADR-055-evaluate-noema-as-a-sliced-instruction-ir.md` and
`tests/test_noema.py`. Create bounded valid and invalid samples only below
`tests/fixtures/noema-v1/codec/`, core module bytes below
`tests/fixtures/noema-v1/modules/`, and the baseline profile below
`tests/fixtures/noema-v1/profiles/`. Permit the deterministic Horos boundary
and configured audit record/synopsis updates. No #909, plugin, dependency,
toolchain, CI, Promise Machine or marketplace file is in scope.

**Tests.** Extend the focused module to at least 100 total tests. Cover every
core type and operator, canonical key/record order, LF/final-LF, exact UTF-8
lengths, every literal kind, type and reference closure, stable rule ids,
module signature and pure-macro checks, lock identity, projection recovery,
alias injectivity, semantic-diff field coverage, no-op diffs, source and tape
idempotence, all item-10 caps at limit and limit-plus-one, very long decimals,
duplicate JSON keys, path confinement, maximum leaf names, partial writes,
sync failures, symlinks, directories, FIFOs and no leaked temporary file. For
an audit repair use `python3 tests/run_tests.py --elenchus-report {report}`;
format `unittest-json-v1`; schema `elenchus.unittest.v1`; fresh report
`.elenchus/fiat-942-step-2.json`, with every incomplete or infrastructure
result classified `inconclusive`.

**Disciplines.** phylax: untrusted source, JSON, tape and paths enter a parser
and atomic writer, so bounds, duplicate rejection, no shell, no dynamic
execution, regular-file confinement and hostile fixtures are gates. ephoros:
the local commands answer digest, count, verdict, controlling node and output
questions through one bounded `noema-result/v1` line; no daemon, metric or alert
is introduced. metron: none, because reversible encoding is proved but no
token saving or speed is claimed. elenchus: each observed codec failure gets
minimal parent-red bytes and the exact runner above before repair. hypomnema:
the public contract documents grammar, interface and refusals; ADR-055 records
only authority and architecture so parser mechanics are not duplicated there.

## Step 3: build conservative slicing and the non-executing policy runtime

**Goal.** Implement dependency-closed operation/state slicing and the five
bounded policy operations without giving the runtime an external-effect path.

**Entry.** Step 2's pull request is integrated; canonical source, locked
modules, baseline projection, semantic diff, confined I/O and their focused
tests pass. One synthetic complete graph is available for runtime fixtures,
and no source-bound skill specimen has been admitted yet.

**Exit.** `select(operation,state,target,tools,authority,facts)` roots the
requested operation and possible effects, partially evaluates only checked
facts, retains unknown guards, closes every reachable definition, literal,
promise, handoff, authority constraint, prohibition, order edge, exception,
refusal and recovery, and emits a canonical manifest over the full graph. A
checked-false guard may omit a rule only with its fact and evidence digest in
the manifest. Recomputing the same inputs yields identical included/omitted id
sets, tape and digests; changed facts or graph yield a declared changed result.

`check` returns permit, refuse or unknown and the controlling node. Permission
never cancels prohibition, conflicting requirements need a typed higher-authority
override, and consequence-2/3 effects default deny without applicable authority
and satisfied gates. `next` enables only a transition whose event, state and
guard are established and keeps authored effect order. `literal` reveals only
a reachable typed literal. `explain` produces a labelled non-authoritative
render and no policy input can consume that render. The runtime has no shell,
network, Git, GitHub, file-mutation or external-effect operation.

The synthetic runtime demonstration covers allowed consequence 0, refused
consequence 3, unknown guard retention, checked-false omission, ordered next
transition, reachable literal and non-authoritative explanation. Every command
below exits zero:

```bash
python3 scripts/noema.py runtime-self-test
python3 scripts/noema.py verify --manifest tests/fixtures/noema-v1/runtime/manifest.json
python3 -m unittest tests.test_noema.SliceTests tests.test_noema.PolicyCheckTests tests.test_noema.TransitionTests tests.test_noema.LiteralTests tests.test_noema.ExplainTests tests.test_noema.RuntimeResultTests -v
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py scripts tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py scripts tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs scripts
python3 scripts/run_checks.py
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Change `scripts/noema.py`, `schemas/noema-v1.schema.json`,
`docs/noema-v1.md`,
`docs/decisions/ADR-055-evaluate-noema-as-a-sliced-instruction-ir.md` and
`tests/test_noema.py`. Create the complete synthetic graph, facts, operations,
locks, expected slices, tapes and result records below
`tests/fixtures/noema-v1/runtime/`. Permit deterministic Horos and configured
audit record/synopsis changes. Change no adapter, external-service, plugin,
#909 or shared authority surface.

**Tests.** Add at least 80 runtime cases while preserving Step 2's focused
count. Cover true, false and unknown guards; nested unknowns; closure through
macros, promises, handoffs, exceptions and recovery; included and omitted id
partition; omission proof mismatch; stale inputs; deterministic manifests;
prohibition/permission conflict; authority precedence and scope; missing,
expired and over-broad exceptions; consequence levels 0 through 3; capability,
authority, done, receipt and verification separation; transition state/event/
guard/order; unreachable literals; instruction-shaped literal inertness; and
bounded result redaction. Audit repairs use
`python3 tests/run_tests.py --elenchus-report {report}`, format
`unittest-json-v1`, schema `elenchus.unittest.v1` and fresh report
`.elenchus/fiat-942-step-3.json`; inconclusive reports establish no guard.

**Disciplines.** phylax: facts, manifests and instruction-shaped literals are
hostile inputs; the runtime validates them and returns data without executing
model output or an effect. ephoros: each operation emits a correlated bounded
result answering which graph, facts, slice and rule controlled the outcome;
there is no unattended service, long-running job or alert. metron: none, since
closure size is recorded for later measurement but no compression verdict is
made. elenchus: a dropped constraint, wrong decision or changed manifest is a
concrete failure and must stay parent-red under the declared runner after its
cause is fixed. hypomnema: the public contract owns callable arguments,
returns, stable failures and the non-executing boundary; ADR-055 retains the
reason for that boundary.

## Step 4: bind the four specimens and hostile mutation corpus

**Goal.** Import the verified seed as inert reference evidence, author reviewed
Noema mappings for Fiat, Phylax, Sapheneia and full Brevitas, and prove their
source coverage and critical mutation behavior.

**Entry.** Step 3's pull request is integrated; the complete synthetic runtime
passes, the public source and runtime contract is fixed, the archive and all 17
source files still match Step 1's inventory, and the four canonical skill
sources are read from the current stacked base without modifying them.

**Exit.** All 17 seed files are copied byte-identically below a directory
labelled non-executable reference evidence, with archive and per-file digests
rechecked before the copy. No seed Python is imported or run. Each of the three
bounded tapes and the full Brevitas tape has a separately authored canonical
`.noe`, lock, full projection, operation slice, literal set, source-span map,
closed questions and expected policy answers. Source identities bind exact
repository paths and blob digests. Every governed span maps to one typed node
or an explicit unsupported remainder; gaps and overlaps refuse; remainders
grant no authority and keep the specimen in shadow mode.

The manifest declares and executes mutations for dropped negation, permission
for prohibition, swapped actor, widened scope, changed exact literal, stale
module, omitted dependency, unknown opcode, alias collision, unknown-guard
deletion, reordered effects, missing authority and consequence-3 bypass. Each
mutation refuses or yields its exact declared changed semantic digest, diff and
answer. Critical permission/prohibition, authority, negation, unknown-guard,
ordering, exact-literal and consequence-3 vectors pass 100%. The checked
source, canonical graph, full projection, operation slice, literals, kernel and
reachable definitions are distinct manifest objects. Every command below exits
zero:

```bash
python3 scripts/noema.py verify-seed --archive /private/tmp/noema-v0-evidence.zip --inventory tests/fixtures/noema-v1/seed-inventory.json
python3 scripts/noema.py verify --manifest tests/fixtures/noema-v1/manifest.json
python3 scripts/noema.py mutations --manifest tests/fixtures/noema-v1/manifest.json
python3 -m unittest tests.test_noema.SourceBindingTests tests.test_noema.SpecimenRoundTripTests tests.test_noema.MutationTests tests.test_noema.CriticalVectorTests -v
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py scripts tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py scripts tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs scripts
python3 scripts/run_checks.py
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Change `scripts/noema.py`, `schemas/noema-v1.schema.json`,
`docs/noema-v1.md`,
`docs/decisions/ADR-055-evaluate-noema-as-a-sliced-instruction-ir.md`,
`tests/test_noema.py` and `tests/fixtures/noema-v1/manifest.json`. Create
byte-identical reference files below
`tests/fixtures/noema-v1/seed-reference/` and specimen-owned source identity,
canonical `.noe`, locks, full/sliced projections, literals, source-span maps,
questions, answers and mutations below `tests/fixtures/noema-v1/specimens/`.
Permit deterministic Horos and configured audit record/synopsis updates. Do
not edit the four source skills, their plugins, generated copies or #909 paths.

**Tests.** Add at least 60 source, specimen and mutation cases. Test archive
and imported-byte equality, exact source blob binding, span ordering and full
governed coverage, unsupported remainder behavior, all four source/graph/source
and graph/projection/graph round trips, deterministic regeneration, closed
question and answer sets, every declared hostile mutation, unchanged-digest
refusal and 100% critical-vector accounting. Preserve malicious strings in
every literal kind and assert they cannot mint a node, alias or effect. Audit
repairs use `python3 tests/run_tests.py --elenchus-report {report}`, format
`unittest-json-v1`, schema `elenchus.unittest.v1` and fresh report
`.elenchus/fiat-942-step-4.json`; any incomplete comparison is inconclusive.

**Disciplines.** phylax: an external archive and current skill bytes cross the
fixture boundary, so exact inventory, confined import, non-execution, source
digests and hostile literal tests are mandatory. ephoros: verification emits
bounded per-specimen counts, digests and mutation verdicts under one run id;
no prompt, source body or literal payload enters results. metron: none, because
this step fixes the comparison corpus and components but leaves all token
counts to Step 5's same-profile baseline. elenchus: each mutation is a named
counterexample; an unexpected clean or changed answer becomes the minimal
parent-red guard before repair. hypomnema: source-span provenance and review
belong in fixture manifests, public semantics in the contract and the authority
decision in ADR-055, avoiding a fourth narrative home.

## Step 5: measure, run the family evaluation and decide Noema

**Goal.** Record exact tokenizer/component measurements and isolated
source-versus-Noema behavior for two authorised model families, then accept,
narrow or reject the hypothesis in ADR-055.

**Entry.** Step 4's pull request is integrated; all four source-bound
specimens, critical vectors and hostile mutations pass. Exact OpenAI,
Anthropic, Google and one open-weight tokenizer profiles can be named or
recorded unavailable, and two genuinely distinct model-family contexts are
separately authorised with exact model identity, invocation boundary, public
input treatment and acquisition digests. If two family runs require an
unauthorised credential, network call, paid endpoint, model download, new
dependency or source disclosure, stop at this entry and ask the operator. Do
not substitute aliases, synthetic answers or two releases of one family.

**Exit.** `measure` establishes the Markdown baseline first and records bytes
and real-token counts separately for source, canonical `.noe`, full projection,
operation slice, literals, kernel, reachable definitions, first use, steady
state and corpus amortisation under each exact profile. Missing exact profiles
remain explicit unknowns. It applies the unchanged gates: first use at most
70%, steady state at most 40%, complete canonical Noema at most 55%, plus 100%
critical vectors. Unlike tokenizer identities are never compared as one
cohort, and dictionary, alias and kernel cost is never hidden.

`emit-evaluation` writes one answer-free source prompt and one Noema prompt per
case, one context nonce each, and a manifest written last. `tally-evaluation`
rejects duplicate, missing, extra, unknown or cross-paired answers; binds exact
tree, source, graph, kernel, projection, profile, case-set and model-family
identities; and reports each required decision, refusal and unknown separately.
At least two genuinely different families complete all critical cases with no
changed required answer between source and Noema. The record does not claim
future rerun agreement, model quality or semantic correctness beyond its cases.

ADR-055 states every measured count, gate verdict, family result, unknown and
failure. It chooses `accepted for continued shadowing`, `narrowed` or
`rejected`; names the trade against #909's whole-model codec; keeps Markdown
authoritative; and lists the exact later evidence required before native Noema
authorship or repository migration could be proposed. A failed threshold or
behavior case remains in the record and cannot be moved. The complete clean
demonstration and every command below exit zero:

```bash
python3 scripts/noema.py measure --manifest tests/fixtures/noema-v1/manifest.json --profiles tests/fixtures/noema-v1/profiles/measurement.json --output tmp/noema-measurement.json
cmp tmp/noema-measurement.json tests/fixtures/noema-v1/evidence/measurement.json
python3 scripts/noema.py emit-evaluation --manifest tests/fixtures/noema-v1/manifest.json --output tmp/noema-evaluation-packet
python3 scripts/noema.py tally-evaluation --packet tmp/noema-evaluation-packet/manifest.json --answers tests/fixtures/noema-v1/evidence/answers.json --output tmp/noema-evaluation.json
cmp tmp/noema-evaluation.json tests/fixtures/noema-v1/evidence/evaluation.json
python3 scripts/noema.py verify --manifest tests/fixtures/noema-v1/manifest.json
python3 scripts/noema.py mutations --manifest tests/fixtures/noema-v1/manifest.json
python3 -m unittest tests.test_noema -v
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/noema/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/noema/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/noema/study.md docs/noema/runbook.md docs/noema-v1.md docs/decisions/ADR-055-evaluate-noema-as-a-sliced-instruction-ir.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py scripts tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py scripts tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs scripts
python3 scripts/run_checks.py
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Change `scripts/noema.py`, `schemas/noema-v1.schema.json`,
`docs/noema-v1.md`,
`docs/decisions/ADR-055-evaluate-noema-as-a-sliced-instruction-ir.md`,
`tests/test_noema.py`, `tests/fixtures/noema-v1/manifest.json` and profile
records below `tests/fixtures/noema-v1/profiles/`. Create deterministic
measurement, answer-provenance and evaluation records below
`tests/fixtures/noema-v1/evidence/`. Permit deterministic Horos and configured
audit record/synopsis updates. Add no dependency, credential, provider SDK,
model bytes, raw response transcript, plugin, Promise Machine claim, README
entry, CI workflow, #909 file or external-repository change.

**Tests.** Add at least 40 measurement and evaluation-adapter cases using fake
local executables for every failure path, then run the exact authorised live
profiles only for the committed evidence. Cover component omission, dictionary
under-counting, changed executable or vocabulary digest, unavailable profile,
non-integer and negative counts, unlike cohorts, threshold boundaries, packet
partial writes, prompt answer leakage, one-case context binding, duplicate and
missing answers, family aliases, stale tree/profile/model ids, unknown answer
values, timeout, output cap, environment allowlist, secret-shaped output and
atomic reports. Audit repairs use
`python3 tests/run_tests.py --elenchus-report {report}`, format
`unittest-json-v1`, schema `elenchus.unittest.v1` and fresh report
`.elenchus/fiat-942-step-5.json`; an unavailable or contaminated live run is
evidence unknown, never a guarded result.

**Disciplines.** phylax: external tokenizer/model programs and model answers
cross the final boundary, so explicit argv, cleared environment allowlist,
timeouts, caps, digest-bound identities, no shell, public fixtures and no
credential in records are gates; live use remains operator-authorised.
ephoros: packet, measurement and tally records answer which exact context,
profile, case and digest produced each bounded verdict; this creates no
production telemetry or alert. metron: the source baseline precedes every
projection count, the same tokenizer/profile measures both sides, all
components and variance are retained, and a miss records rejection rather than
moving the limit. elenchus: any adapter, contamination, count or answer failure
is reduced under fake executables and guarded before the exact live case is
rerun. hypomnema: ADR-055 receives the measured choice, rejected alternatives,
unknowns and authority condition; the public contract and fixtures retain
interface and evidence details without turning the study into the standing
record.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Files: For Step 2, change `scripts/noema.py`, `schemas/noema-v1.schema.json`, `docs/noema-v1.md`, `docs/decisions/ADR-056-evaluate-noema-as-a-sliced-instruction-ir.md` and `tests/test_noema.py`; create bounded codec samples, core modules and the baseline profile below `tests/fixtures/noema-v1/`; permit deterministic Horos and configured audit record or synopsis updates; change no #909, plugin, dependency, toolchain, CI, Promise Machine or marketplace file. For Step 3, change those same five product files and create the complete runtime corpus below `tests/fixtures/noema-v1/runtime/`; permit the same generated audit files; change no adapter, external service, plugin, #909 or shared-authority surface. For Step 4, change those five product files plus `tests/fixtures/noema-v1/manifest.json`; create the seed reference below `tests/fixtures/noema-v1/seed-reference/` and specimen evidence below `tests/fixtures/noema-v1/specimens/`; permit the same generated audit files; change none of the four source skills, their plugins, generated copies or #909 paths. For Step 5, change those five product files plus `tests/fixtures/noema-v1/manifest.json` and profile records below `tests/fixtures/noema-v1/profiles/`; create evidence below `tests/fixtures/noema-v1/evidence/`; permit the same generated audit files; add no dependency, credential, provider SDK, model bytes, raw response transcript, plugin, Promise Machine claim, README entry, CI workflow, #909 file or external-repository change.

**Why.** After this run receipted its specification, `origin/main` added `ADR-055-stage-the-portable-sync-and-check-mirror-closure.md`; the repository uniqueness gate now rejects the Noema record under the same number. Renumbering only the Noema record to the next free number preserves both decisions and leaves the concurrent work untouched.

**Steps touched.** Steps 2, 3, 4 and 5.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Files: For Step 2, change `scripts/noema.py`, `schemas/noema-v1.schema.json`, `docs/noema-v1.md`, `docs/decisions/ADR-059-evaluate-noema-as-a-sliced-instruction-ir.md` and `tests/test_noema.py`; create bounded codec samples, core modules and the baseline profile below `tests/fixtures/noema-v1/`; permit deterministic Horos and configured audit record or synopsis updates; change no #909, plugin, dependency, toolchain, CI, Promise Machine or marketplace file. For Step 3, change those same five product files and create the complete runtime corpus below `tests/fixtures/noema-v1/runtime/`; permit the same generated audit files; change no adapter, external service, plugin, #909 or shared-authority surface. For Step 4, change those five product files plus `tests/fixtures/noema-v1/manifest.json`; create the seed reference below `tests/fixtures/noema-v1/seed-reference/` and specimen evidence below `tests/fixtures/noema-v1/specimens/`; permit the same generated audit files; change none of the four source skills, their plugins, generated copies or #909 paths. For Step 5, change those five product files plus `tests/fixtures/noema-v1/manifest.json` and profile records below `tests/fixtures/noema-v1/profiles/`; create evidence below `tests/fixtures/noema-v1/evidence/`; permit the same generated audit files; add no dependency, credential, provider SDK, model bytes, raw response transcript, plugin, Promise Machine claim, README entry, CI workflow, #909 file or external-repository change.

**Why.** After the first collision amendment, `origin/main` added `ADR-056-require-the-complete-plugin-graph.md` and the live registry now occupies ADR-055 through ADR-058. The repository uniqueness gate therefore rejects the Noema record at ADR-056. Moving only that unmerged record to the current next-free ADR-059 preserves every landed decision and the prior amendment history.

**Steps touched.** Steps 2, 3, 4 and 5.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Files: For Step 5, change `scripts/noema.py`, `schemas/noema-v1.schema.json`, `docs/noema-v1.md`, `docs/decisions/ADR-059-evaluate-noema-as-a-sliced-instruction-ir.md`, `tests/test_noema.py`, `tests/fixtures/noema-v1/manifest.json`, profile and kernel records below `tests/fixtures/noema-v1/profiles/`, and the canonical inputs, hostile mutations and derived records below `tests/fixtures/noema-v1/specimens/`; create evidence below `tests/fixtures/noema-v1/evidence/`; permit deterministic Horos and configured audit record or synopsis updates; add no dependency, credential, provider SDK, model bytes, raw response transcript, plugin, Promise Machine claim, README entry, CI workflow, #909 file or external-repository change.

**Why.** The first live family run exposed a prior-step implementation defect: all four specimens reuse one generic policy scaffold, several graph nodes do not express their bound Markdown spans, checked fact propositions are absent from evaluation context, and the 58-byte kernel does not define the projection grammar. The resulting 12-of-16 score measures model guessing rather than Noema comprehension. Step 5 must preserve that failed run, repair the evaluation boundary on the same selected design, and rerun the fixed gates before recording a decision.

**Steps touched.** Step 5.

**Still holding.** Step 5: entry holds; exit holds.
