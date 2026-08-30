# Prototype Noema as a model-native sliced instruction IR

## 1. Problem statement

Issue [#942](https://github.com/wildcat-finance/skills/issues/942) asks whether
the governed part of an agent skill can move from repeatedly loaded prose to a
closed instruction graph, selected by task state and checked by a small policy
runtime. The existing issue [#909](https://github.com/wildcat-finance/skills/issues/909)
answers a narrower question: its reviewed model stays derived from authored
Markdown and its compact `WAI1` bytes encode the whole reviewed model. Noema
tests typed native authoring, dependency-closed slices and an enforcement
boundary for consequential effects. It does not supersede #909.

The supplied seed is useful evidence and an unsafe implementation base. Its
three specimen tapes, full Brevitas tape and subset parser reproduce
`OK roundtrip=4 structures=6 malformed=3 semantic=7 digest-mutations=4`, but
the parser has a global handwritten predicate-arity table, no typed module
bodies, no source-span validator, no module lock, no slice manifest and no
policy runtime. Importing those bytes unchanged would preserve the questions,
not answer them.

A working prototype has one repository command that can:

1. parse, type-check, format and recover byte-identical canonical `.noe`;
2. project and recover the same graph under a digest-bound text profile;
3. select a conservative operation/state slice with a manifest naming every
   included and omitted node and the evidence for each omission;
4. answer `select`, `check`, `next`, `literal` and `explain` without executing
   an external effect; and
5. verify four source-bound specimens, hostile mutations, fixed compression
   gates and separately recorded fresh-context answers.

The deterministic acceptance command will be
`python3 scripts/noema.py verify --manifest tests/fixtures/noema-v1/manifest.json`.
Focused proof will be `python3 -m unittest tests.test_noema -v`. Model contexts
remain outside those commands: an offline `emit-evaluation`/`tally-evaluation`
pair will bind one fresh context per case and refuse a result that does not name
two genuinely distinct family identities. The issue is accepted only if the
verified record meets item 10's fixed gates; a measured rejection is a valid
design outcome.

## 2. Prior art

The target paths `docs/noema/`, `schemas/noema-v1.schema.json`,
`scripts/noema.py`, `tests/test_noema.py` and `tests/fixtures/noema-v1/` do not
exist at the starting ref. `git log --first-parent --merges` over those exact
paths returns no pull request, so there are no two merged changes to read for
the new target itself. The last two merged pull requests on the nearest
model-evaluation boundary are the useful substitutes:

**[#922](https://github.com/wildcat-finance/skills/pull/922)**, merged as
`a8289d46`, added an offline packet/tally driver for 38 isolated router-selection
contexts. Its applicable carried items are retained here: prompts contain no
answers, every context receives one case, duplicate answer ids refuse, the
manifest is written last, and a committed result records one grading rather
than a rerun guarantee. Its open tree-binding gap becomes a Noema requirement:
each evaluation record binds the source tree, graph, projection, kernel,
profile and case-set digests.

**[#851](https://github.com/wildcat-finance/skills/pull/851)**, merged as
`d1ca7ba5`, added Homologia and forced the router corpus regrade that #922 later
made repeatable. It established two limits that carry here. Agreement between
two implementations is not correctness, and a model result without the tree it
graded cannot distinguish model variance from changed instructions. Noema's
graph equality is therefore structural evidence; semantic adequacy still needs
source-span review and fresh-context cases.

Pull request [#755](https://github.com/wildcat-finance/skills/pull/755) is the
adjacent provider-boundary precedent. Its job-scoped model proxy keeps
credentials and provider-native authority out of a worker and treats synthetic
conformance as component evidence. Noema reuses the separation, not the proxy:
committed tooling emits and tallies bounded packets offline, and any live
adapter remains a separately authorised operator surface.

The controlling prior design is still the open #909 stack. Pull request
[#921](https://github.com/wildcat-finance/skills/pull/921) freezes
`wildcat-agent-instruction/v1`; pull request
[#937](https://github.com/wildcat-finance/skills/pull/937) implements its
bounded canonical codec at audited head `7305e750`. The following lessons are
content for this run:

- preserve the Promise claim itself, not only its authority fields;
- count every literal occurrence across direct validation and decoding;
- enforce per-value and aggregate bounds before numeric conversion;
- require one physical source path identity so sibling spans cannot evade
  overlap checks; and
- derive atomic temporary names independently of the caller's leaf length.

The current-main whole-set audit-synopsis check exited 0. The views read were
`audit/AUDIT_SYNOPSIS.md` for the root history and
`audit/rounds/fiat-904-grade-the-router-corpus-from-a-driver-rather.synopsis.md`
for #922. The #909 record is PR-local, so its synopsis is outside current-main
currency; both
`audit/rounds/fiat-909-compact-lossless-agent-instruction-language.md` and its
synopsis were read directly from audited head `7305e750`. No finding from that
record is treated as fixed on `main` until its stack lands.

Outside the repository, no format or library is selected. The hypothesis is
about this corpus and its existing Python pin; adopting a serialization or
provider SDK before the graph contract exists would choose the dependency
before the semantics.

## 3. Constraints and non-goals

The starting ref is `7e97b5195d5b0e43146b4200f26cd41b89003413` on
`main`. At least four other agents are changing the repository, so every step
uses the dedicated Fiat stack and regenerates shared derived files only when
its own tracked paths require them. It does not rebase, retarget, close or edit
#909, #921, #937 or their branches. Compatible ideas may be reimplemented from
their public contract; unmerged code is not copied across the stack.

The prototype is root tooling, not a plugin or selectable skill. It changes no
marketplace manifest, runtime router, existing `SKILL.md`, Promise Machine
claim, CI workflow or external repository. A later accepted design may earn a
separate registration or migration run.

Python uses the exact `.python-version` interpreter. Canonical validation,
slicing, policy decisions, packet emission and tallying use the standard
library. Tokenizer and model-family programs are external, digest-bound
adapters with explicit argv; adding a dependency, downloading a model, sending
source to a network, using a credential or incurring paid endpoint use is
ask-first.

Non-goals for this issue:

- lossless translation of arbitrary English, custom model training or a claim
  that a reviewed graph captures an author's unexpressed intent;
- repository-wide conversion, Shoggoth migration or an authority flip for any
  existing skill;
- raw tokenizer ids, binary/base64 prompt transport or an opaque substitution
  cipher whose dictionary cost is omitted;
- executing repository, publication, deployment, security or financial
  effects from the Noema runtime; and
- universal model-family parity, tokenizer stability or safety beyond the
  exact profiles, cases and records observed.

Source-to-graph review remains a human evidence boundary. Unsupported governed
meaning blocks migration and appears as an explicit unsupported remainder;
display prose and rationale may remain source-bound, non-authoritative
sidecars.

## 4. Design options

**A. Extend the active `wildcat-agent-instruction/v1` stack.** Rejected for
this run. #909 fixes Markdown as authored authority and compact bytes as a full
derived view. Noema tests a different authority endpoint plus operation/state
slicing. Mixing both into the active stack would make #909 review moving
ground, erase the control design and create avoidable conflicts with #921 and
#937.

**B. Encode prose as a private binary or token substitution table.** Rejected.
The seed measured Fiat Markdown at 13,628 `o200k_base` tokens and its
gzip/base64 and gzip/base85 forms at 19,173 and 19,707. Ten aliases cut one
Brevitas tape from 479 to 455 tokens, while their 73-token legend raised first
use to 528. A carrier win without grammar, dictionary and behavioral cost is a
shell game, plus opaque bytes discard ordinary Git review.

**C. Keep Markdown authoritative and emit task-specific prose summaries.**
Rejected as the final design. It can save tokens, but authority checks still
depend on a model interpreting prose and an omitted prohibition has no
deterministic witness. This remains a useful baseline in the evaluation.

**D. Build a closed typed graph with canonical `.noe`, digest-bound modules,
provider text projections, a conservative slicer and a non-executing policy
runtime.** Chosen. Canonical source is a line-oriented, non-English semantic
program with stable rule ids and typed inert literals. A projection may shorten
reserved opcodes and qualified predicates only when its manifest recovers the
same graph and includes its dictionary cost. The runtime computes policy
answers from the graph and supplied checked facts; models consume slices and
propose effects but do not decide their own authority.

The trade is a larger trusted computing base: parser, type checker, module
registry, projector, slicer and policy evaluator all become security-sensitive.
That cost is accepted only for a bounded shadow prototype. Five stacked steps
separate contract, codec, slicing/runtime, specimens and evaluation so each
layer can be rejected without converting a skill or changing authority.

## 5. Risk register seed

```risk-register
source-omission | governed Markdown spans | every byte span is mapped to one reviewed node or one explicit unsupported remainder; overlap, gap and stale-source checks refuse
semantic-drift | canonical source, graph and projection | source-to-graph review is recorded, graph round trips are byte-identical, and semantic diff names every changed effect, gate, authority, scope, evidence class, literal and precedence edge
slice-omission | a rule omitted from one operation/state slice | false guards need recorded facts; unknown guards remain; effect closure retains prohibitions, authority, order, exceptions, refusal and recovery
authority-confusion | capability, authority, execution, receipt and verification | each is a separate type and no transition infers another; consequence-2/3 checks default deny without applicable authority and satisfied gates
module-drift | imported predicate or macro meaning | locks bind full module bytes, compiler and profile digests; missing, stale, cyclic or ambient imports refuse
alias-collision | tokenizer-profile projection | aliases are injective across reserved opcodes, predicates, literal ids and visible values; the projector refuses collision or overload
literal-injection | instruction-shaped path, quote, text, command, URL or error bytes | literals are length-bound inert nodes and require a separately authorised effect before use
parser-exhaustion | untrusted `.noe`, manifests, facts and tapes | byte, line, node, depth, import, literal, expansion and output caps apply before allocation or integer conversion; no partial graph escapes a refusal
profile-mismatch | tokenizer, vocabulary, kernel or projection change | exact executable or vocabulary identity and digests are recorded and reread; unlike profiles are never compared as one cohort
hidden-overhead | bootstrap, definitions, aliases or cached prefix | reports separate every component and count first use, steady state, full canonical and corpus-amortised totals under the same tokenizer
evaluation-contamination | fresh-context model comparison | one case per context, answer-free packets, exact case-set equality, distinct family identities and source/tree/profile digests are mandatory
provider-boundary | external tokenizer or model process | explicit argv, cleared environment allowlist, public synthetic inputs, timeout, output cap and no shell; credentials, network and paid use remain ask-first
derived-drift | semantic diff, render, tape, manifest or evidence record | deterministic regeneration and digest comparison refuse stale checked-in views; binary caches carry no review authority
parallel-stack | #909 or current-main movement | no #909 path changes; each step rechecks ancestry and regenerates only its own derived counts against its actual tree
```

## 6. Glossary seeds

- **NIR.** The closed typed graph recovered from canonical source. Graph
  identity is a digest of canonical bytes and locked module meanings.
- **`.noe`.** The canonical line-oriented review and authorship surface. It
  contains structural opcodes, qualified predicates, stable ids and typed
  literal references, with no governing prose.
- **Module.** A finite, digest-bound set of predicate signatures and pure graph
  definitions. It cannot alter a core opcode.
- **Projection.** A deterministic text representation for a declared tokenizer
  profile. It is derived and must recover the same NIR with its manifest.
- **Slice.** Dependency closure for one operation, state, target, tool set,
  authority input and fact set.
- **Slice manifest.** The commitment to the full graph, compiler, inputs,
  included and omitted ids, omission facts, reachable definitions and literals,
  emitted projection and every digest.
- **Policy runtime.** The bounded, non-executing implementation of `select`,
  `check`, `next`, `literal` and `explain`.
- **Unsupported remainder.** A source span with no admitted semantics. It is
  visible evidence that blocks authority migration and grants nothing.
- **Prompt-only mode.** The fallback that gives a model the complete reachable
  kernel, dictionary and slice. Every one of those tokens counts.
- **Shadow mode.** Markdown remains authoritative while Noema output is checked
  as derived evidence. This issue never leaves shadow mode.

## 7. Sources

- Issue [#942](https://github.com/wildcat-finance/skills/issues/942), including
  its fixed acceptance gates and public evidence attachment.
- `noema-v0-evidence.zip`, 24,907 bytes, SHA-256
  `1e1eb5e9908551f1337b7ec58a37ae7f37fd97e41d5ac424bc4992eb1d11b540`;
  all 17 listed source files and the clean archive test were read.
- Issue [#909](https://github.com/wildcat-finance/skills/issues/909), pull
  requests [#921](https://github.com/wildcat-finance/skills/pull/921) and
  [#937](https://github.com/wildcat-finance/skills/pull/937), and audited head
  `7305e750f06c5180f380d0e54af71e825e32587e`.
- On the #909 head: `docs/agent-instruction-language-v1.md`,
  `docs/compact-agent-instruction-language/study.md`,
  `docs/compact-agent-instruction-language/runbook.md`,
  `docs/decisions/ADR-051-encode-a-closed-agent-instruction-model.md`, and both
  `audit/rounds/fiat-909-compact-lossless-agent-instruction-language` views.
- Merged pull requests [#922](https://github.com/wildcat-finance/skills/pull/922),
  [#851](https://github.com/wildcat-finance/skills/pull/851) and
  [#755](https://github.com/wildcat-finance/skills/pull/755), plus current-main
  `audit/AUDIT_SYNOPSIS.md` and #922's current synopsis.

## 8. Signals, and the questions behind them

Every command is operator-run; there is no daemon, unattended scheduler or
on-call alert. Ephoros's questions still determine the result record. An
operator needs to know which source, graph, module set, profile, facts and
operation were read; whether a decision was permit, refuse or unknown; which
node controlled it; what was omitted and why; what recovery remains; and
whether output bytes were committed atomically.

Each command emits one bounded
`noema-result/v1` JSON line carrying command, correlation id, input and output
digests, counts, verdict or refusal code, controlling node and output path when
one exists. `select` also writes a manifest; `check` and `next` name the rule or
transition; `literal` names the typed literal; `explain` labels its render
non-authoritative. No result contains full source, literal payloads, prompts,
model output or credentials.

Evaluation records add case id, isolated-context nonce, declared model family
and exact model/profile identity. The tally reports required-answer agreement,
refusals and unknowns per family and representation. These are run evidence,
not telemetry about future prompts. There is no production metric or alert to
invent for a local prototype.

## 9. Boundaries, per capability

- **Imports the seed.** Only the public archive whose exact size and SHA-256
  appear in item 7. Extraction rejects absolute paths, traversal, links,
  special files, unexpected names, duplicate names, excess bytes and any
  per-file digest mismatch. Imported specimens are reference fixtures; seed
  Python is never executed or installed.
- **Reads and writes repository files.** Paths resolve beneath the repository
  or a declared fixture root, with regular-file, symlink and size checks.
  Derived output uses a target-independent sibling temporary name, fsync and
  atomic replacement. No shell interpolation or evaluator consumes source.
- **Parses and projects instructions.** The grammar, types, opcodes and keys are
  closed. Validation completes before a graph or tape is returned. Unknown
  syntax, types, ids, references, modules, profiles and trailing bytes refuse
  with stable codes.
- **Selects and checks policy.** The runtime receives checked facts as data,
  closes a slice and returns a decision. It has no subprocess, network, Git,
  GitHub or mutation capability. A permit result authorises nothing outside the
  caller's separately recorded authority; it never performs the effect.
- **Runs external profiles.** Offline emit/tally is the default. An optional
  tokenizer or model adapter accepts an explicit digest-bound argv list,
  minimal environment allowlist, timeout and output cap. New dependencies,
  model downloads, credentials, network/source disclosure and paid calls need
  the operator's separate recorded authority before execution.

Human source-span review, model comprehension and the truth of supplied facts
remain outside deterministic validation. The result record says `checked`,
`recorded`, `measured` or `unknown` for the relation actually established and
does not strengthen one into another.

## 10. The budget, or its absence

Compression is the reason for the work, so Metron's baseline/change rule is a
gate. The seed numbers are prior evidence, not the official baseline. Each
official run counts the same exact corpus under the same profile before and
after projection and reports bytes and real tokenizer counts separately for
Markdown source, canonical `.noe`, full projection, operation slice, literals,
kernel, reachable definitions and corpus-amortised totals.

The fixed semantic-token gates from #942 are:

- first-use kernel + definitions + slice at most 70% of relevant Markdown;
- steady-state slice at most 40%; and
- complete canonical Noema at most 55% of the declared source corpus.

Critical authority, permission/prohibition, negation, unknown-guard, ordering,
exact-literal and consequence-3 vectors must pass 100%. Results must name
OpenAI, Anthropic, Google and one open-weight tokenizer profile; an unavailable
exact tokenizer remains `unknown`. Behavioral evidence needs two genuinely
different agent families. Aliases, two versions of one family and unrecorded
endpoints do not satisfy that count.

Resource caps for version 1 are fixed before implementation: 1,048,576 input
bytes, 65,536 bytes per physical line, 16,384 records, 16,384 graph nodes,
64 imports, depth 64, 65,000 bytes per literal, 786,432 aggregate decoded
literal bytes, 65,536 expanded macro nodes, 4,096 members in any finite
quantifier set and 1,048,576 output bytes. The implementation may lower a cap
only before Step 1's contract is receipted and with the reason recorded; it may
not raise or omit one after a hostile fixture reaches it.

No wall-clock performance claim is made. External adapters use explicit
timeouts for safe operation, while speed is recorded only as diagnostic
context and cannot rescue a semantic or token-gate failure.

## 11. The fail-closed posture

Stable refusal families cover syntax, canonical form, type, bounds, reference
closure, source binding, module/profile digest, alias collision, slice closure,
authority, path/I/O and evaluation binding. A refusal returns no partial graph,
slice, decision, tape or evidence record. Atomic output keeps the old complete
file or the new complete file; a durability uncertainty still reports refusal.

Unknown facts stay unknown. A checked-false guard may omit its dependent rule
only with that fact in the manifest; an unknown guard keeps the rule. Permission
does not cancel prohibition. Conflicting requirements refuse unless a typed
override names higher authority, scope and evidence. Consequence-2/3 effects
default deny without applicable authority even when no explicit prohibition is
present.

Failure blocks only the dependent output or policy answer. Inspection,
`explain`, source repair, manifest repair, rerun and safe exit remain available
when their own inputs validate. The validator never edits a failing source to
make it pass.

Elenchus governs every defect found after implementation: preserve the exact
failing bytes, reduce them to the smallest case, make the guard fail against
the parent, fix the cause, then retain the guard. A changed answer without a
changed semantic digest is a high-severity evaluation finding; a changed
semantic digest without a named semantic diff is a high-severity codec finding.

## 12. Decisions and their homes

The expensive decision is the authority direction. This run chooses shadow
mode: existing Markdown remains authoritative, canonical Noema and every
projection remain derived, and the policy runtime is non-executing. The final
ADR at `docs/decisions/ADR-<next>-evaluate-noema-as-a-sliced-instruction-ir.md`
must choose accept, narrow or reject from the recorded gates. It must reconcile
#909's full-derived-codec conclusion, state the measured trade, and name the
separate evidence and run that a later authority reversal would require.

The public grammar, types, bounds, stable refusal codes, module/profile lock,
slice and runtime interfaces live in `docs/noema-v1.md` and
`schemas/noema-v1.schema.json`. The implementation lives in
`scripts/noema.py`; source-bound specimens, manifests, mutations, tokenizer
profiles and evaluation records live under `tests/fixtures/noema-v1/`; focused
guards live in `tests/test_noema.py`. The receipted study and runbook are copied
byte for byte into `docs/noema/` before product implementation.

The five ordered steps are: freeze the contract and verified seed inventory;
build the canonical graph, module lock and projection; build conservative
slicing and the policy runtime; bind four specimens plus hostile mutations;
then measure, run or tally the authorised fresh-context evaluation and write
the ADR. The last step stops at its entry if two authorised family runs cannot
be established. A stop records unknown evidence; it does not weaken the gate,
invent parity or hold earlier shadow-mode tooling out as accepted Noema.
