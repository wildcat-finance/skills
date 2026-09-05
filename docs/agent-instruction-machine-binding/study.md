# Study: make a bound instruction document editable off one machine

Issue [skills#1098](https://github.com/wildcat-finance/skills/issues/1098).
Run branch `fiat/1098-make-a-bound-instruction-document-editable`, cut from
`main` at `bacb34c0d49a83dea0c4463a61b2cf1525fec60b`.

## Assumptions

Stated before the content that rests on them. Each will be proceeded on unless
corrected.

1. Python 3.14.6, the interpreter in `.python-version`, with stdlib `unittest`.
   The run host reports 3.14.6, so the local suite and CI agree on the version.
2. No new third-party dependency. `scripts/agent_instruction.py` is stdlib-only
   at 3,836 lines and the repository has no lockfile at its root.
3. `agent_instruction.py measure` may be invoked once in the whole delivery.
   The port `127.0.0.1:11434` is held free for that one call, and a re-measure
   evicts an unrelated job.
4. `gpt-oss:120b` is cold at 65,369,799,840 bytes. `ollama ps` lists nothing
   loaded, and the profile's own adapter argv caps a call at `--max-time 170`,
   so warming the model before measuring is a step requirement rather than a
   convenience.
5. The reviewed span of each bound source is the unit that carries meaning. An
   edit that leaves those bytes identical has not changed what the recorded
   token counts are counts of. This assumption chooses the selected design; if
   it is wrong, the selection is wrong.
6. `tests/promise_machine_coverage.json` stays the whole-file digest register
   for this capability. Six of its `agent_instruction` rows move on a bound
   source edit today.
7. Parity evidence cannot be made deterministic. `parity.json` records what two
   model families answered, and no function replaces an observation.

## 1. Problem statement

Three instruction documents are bound into `tests/fixtures/agent-instruction-v1`
by whole-file SHA-256:

```text
plugins/hexaemeron/skills/fiat/SKILL.md
plugins/horos/skills/horos/SKILL.md
PROMISE_MACHINE.md
```

Editing any of them starts the reconciliation sequence
[skills#1030](https://github.com/wildcat-finance/skills/issues/1030) records.
The mechanical part can be done by hand. The last part cannot. On a clean
checkout at `bacb34c0` an out-of-span edit to `fiat/SKILL.md`, with every
mechanical pass applied, refuses:

```text
{"code":"WAI-E-DIGEST.CORPUS","node_path":"$.evidence.measurement_record","outcome":"refused"}
```

That refusal was reproduced in this study, not quoted. Only
`agent_instruction.py measure` can reissue the record honestly, and it runs
through a loopback adapter pinned to one macOS install.

The person this is for is a contributor who edits one of those three files.
Today the work divides by which file it touches rather than by what it is
worth. The table in #1098 sorts the token-cost findings of
[skills#1066](https://github.com/wildcat-finance/skills/issues/1066) into
deliverable and undeliverable, and the only deliverable row is the one that
does not touch `fiat/SKILL.md`. That table is the reading taken here; #1066
itself was not opened during this study.

A working prototype here means one thing. An edit to a bound source that
leaves its reviewed span byte-identical reconciles with mechanical passes
alone, on a machine with no model, and the repository gate goes green. An edit
that changes reviewed bytes still refuses, because those bytes are what the
recorded counts are counts of.

The demo path, run from the repository root on a host with no Ollama:

```bash
printf '\n<!-- demo -->\n' >> plugins/hexaemeron/skills/fiat/SKILL.md
python3 scripts/prove_agent_instruction_reconciliation.py reconcile
python3 scripts/agent_instruction.py check \
  --manifest tests/fixtures/agent-instruction-v1/manifest.json
python3 -m unittest discover -s tests
```

The third and fourth commands exit zero, and no model was consulted.

## 2. Prior art

### In this repository

`scripts/agent_instruction.py` holds the codec, the manifest checker and both
evidence adapters. `_corpus_sha256` at line 3276 digests one subject:
`schema`, `risk_classes`, `binding_count`, `question_count`,
`mutation_count`, `fixtures`. `fixtures` carries each source's whole-file
`sha256` and each derived artefact's `sha256`, so the corpus digest moves
whenever a bound source moves, whether or not the reviewed bytes moved. That
digest was reproduced from the manifest bytes in this study and matches the
`934acac1ec92d524eb1c7e9a1b82f945143e00ac838f9ba2ae39bdad93a38eda` recorded in
`measurement.json`.

Two evidence records bind it, not one. `_load_evidence_artifacts` compares both
`measurement.json` and `parity.json` against the manifest corpus digest, at
lines 3259 and 3261. The issue names only the measurement record. Parity is
worse placed, because it needs two model families rather than one tokenizer.

The measured source is the reviewed span, not the whole file:
`measure_manifest` slices `source_file[start:end]`, and `documents[0].source.bytes`
is 4328, which is exactly `22773 - 18445`. Only `compact.wai` and `model.json`
carry the whole-file digest, `compact.wai` as the `h64:` field of its `S`
record. Replacing one 64-character digest with another leaves the byte count
unchanged and the token count free to move, which is why the counts are the
part that cannot be reconciled by hand.

`docs/decisions/ADR-062-encode-a-closed-agent-instruction-model.md` settles
that the measurement should exist and that whole-file binding is right. It also
records the thin margin: under length-prefixed offsets the three-document token
gate "moved from a one-token saving to a one-token regression" depending on how
one embedded SHA-256 segmented. `WAI-E-MEASURE.NON_NEGATIVE_DELTA` refuses a
non-negative `delta_tokens`, which is `-76` today and was `-52` when PR #991
landed. A re-measure is not a formality.

`.github/workflows/repo.yml` line 35 runs `python3 -m unittest discover -s tests -v`
on `ubuntu-latest` for every pull request, with no path filter and a comment
explaining why it cannot have one. `tests/check-map-v1.json` declares the same
argv as `root-suite`. Neither file names `measure` or `parity`; grepping both
for `agent_instruction`, `measure` and `parity` returns nothing. So the gate is
real and blocking, and the tool that satisfies it after a source edit is not
part of it.

`tests/promise_machine_coverage.json` binds the checker, the manifest, two
documents, fifteen fixture artefacts and six evidence files by whole-file
digest, with thirteen named test selectors. Two of those selectors,
`test_stale_measurement_report_refuses` and `test_stale_parity_report_refuses`,
are the fail-closed guards a route must not quietly remove.

### The last two merged pull requests that changed this

[PR #1100](https://github.com/wildcat-finance/skills/pull/1100), commit
`7bcffa97`, is the most recent. It is route 4 of the issue's four: the refusal
now names the tokenizer, the runtime and the client. Its body carries three
items forward, and each is answered here.

- "Replacing the pinned tokenizer, excluding the embedded digest from the
  measured corpus, and publishing the runtime all remain open, and #1098 says
  that choice is Protasis's." Carried forward as content: those are candidates
  one, two and three of section 4, and the design record selects between them.
- "The third regresses reconciliation behaviour, which only exists under one of
  the other three routes, so it is left with them." Carried forward as content:
  acceptance check three is criterion `span-shift-regression` in the design
  record, pending at `integration`.
- "The fourth holds by construction, a refusal writes no output file." Carried
  forward with a correction. That establishes only that a refused `measure`
  writes nothing. It does not establish that an accepted record's counts belong
  to the bytes recorded beside them, which is criterion
  `unmeasured-token-counts`.

PR #1100's guidance sentence is attached to two call sites only, both
`WAI-E-ADAPTER.EXECUTABLE_CHANGED` inside `_verify_profile_identity`.
`VERSION_CHANGED`, `IDENTITY_CHANGED`, `TOKENIZER.MISMATCH`,
`WAI-E-ADAPTER.EXECUTABLE` and the adapter's own `UNAVAILABLE` and `TIMEOUT`
carry no detail. A contributor on `ubuntu-latest` reaches
`EXECUTABLE_CHANGED` first, because `/usr/bin/curl` exists there with a
different digest, so acceptance check two holds for that host. A slim container
with curl anywhere but `/usr/bin/curl` reaches `WAI-E-ADAPTER.EXECUTABLE`
instead and is told nothing. Recorded in the register as
`refusal-detail-coverage`.

[PR #991](https://github.com/wildcat-finance/skills/pull/991), commit
`0c2803e7`, registered the prototype. Its body carries forward a boundary that
constrains candidate one: the recorded result "applies only to the three bound
source fragments, exact profiles, prompt, runtimes, bootstrap, and 2026-08-30
observations", and "Models and adapters remain evidence producers, not
instruction authorities". Nothing in that body was left unfinished for a
successor to pick up; the three open routes come from #1100.

### Audit records

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check <target-root>`
was run from the target root and exits zero. Every listed pair reports
`committed=match`, so verified synopses are the normal reading view and were
used. In-scope sources, and which view was read:

| in-scope source | view read | evidence for the choice |
| --- | --- | --- |
| `audit/rounds/fiat-909-compact-lossless-agent-instruction-language.md` | `.synopsis.md` | whole-set check exit 0, `committed=match`, `source_sha256=597dd7bb…` |
| `audit/AUDIT.md` | `AUDIT_SYNOPSIS.md` | whole-set check exit 0, `committed=match`; grepped for this subject and it carries one unrelated `tokenizer` mention |
| `plugins/hexaemeron/audit/AUDIT.md` | `AUDIT_SYNOPSIS.md` | whole-set check exit 0, `committed=match`, `source_sha256=8acff29e…` |
| `plugins/horos/audit/` | neither | the directory does not exist, so there is no record for the second bound source's owner |

The #909 round is the one that built this capability: twenty rounds, thirty
findings, every one `fixed`, and no finding left open. Elenchus verdicts are
`guarded` where recorded and `null` on the rounds that recorded none. Findings
are retained by id above. Two matter here.

`S4-R3-01` established that "source now trust-anchors the exact tokenizer and
family profile record digests before any identity or adapter launch", with a
rebound profile refusing `WAI-E-DIGEST.PROFILE`. A route that swaps the
tokenizer has to keep that anchor, and its own profile record then becomes the
thing to anchor.

The Step 1 `Not checked` field excludes, by name, "external repositories,
network services, credentials, native Windows, and CI". The portability of the
measurement adapter was therefore never audited. The gap #1098 reports is one
the audit record says out loud was not looked at, which is why it surfaced as
an observation rather than a finding.

Leads not pursued across those twenty rounds are all step-scoped restatements
of prior green guards and one note that the source-bound runner is plain UTF-8
unittest text with no structured Elenchus adapter. None of them concerns
adapter portability, so none is carried forward here.

`plugins/hexaemeron/audit/AUDIT.md` records ten findings against `hexctl.py`
and `hook_gate.py` from 15 August 2026, all fixed except `F-10`, accepted as a
documented escape hatch. Its legacy rounds carry `[missing legacy field:
audit-schema]`, `covered`, `not-checked` and `elenchus-verdict`, which remain
unknown. Nothing there touches this capability; it is in scope only because
`fiat/SKILL.md` is one of the bound sources.

### Outside this repository and organisation

Named by identifier, and not fetched during this run: `tiktoken` and
HuggingFace `tokenizers` are the two obvious vendored deterministic tokenizers
candidate one would reach for, and an OCI image is what candidate three would
publish. RFC 8785 JSON Canonicalisation Scheme is the standard analogue of the
`canonical_record_bytes` form this fixture already uses, and it too fixes bytes
before digesting them. `in-toto` statements, which the Ariadne skill already
reads and writes in this repository, are the standing pattern for measuring
once and attesting rather than re-measuring. None of these is proposed as a
dependency by the selected design.

## 3. Constraints and non-goals

Starting ref `bacb34c0d49a83dea0c4463a61b2cf1525fec60b` on `main`, branch
`fiat/1098-make-a-bound-instruction-document-editable`. Toolchain: Python
3.14.6 from `.python-version`, stdlib only, `unittest` discovery from `tests`.

Ruled out by the user, and not reopened:

- Whether the measurement should exist, and whether whole-file source binding
  is right. ADR-062 settles both.
- Editing any of the three bound documents as part of this delivery. The
  reconciliation is what is being built; a bound source edit is what proves it,
  and that proof belongs in a test fixture rather than in the live corpus.
- More than one `measure` invocation across the whole delivery.

Deferred past the prototype:

- Reducing #1030's reconciliation to one command. The selected design cuts the
  passes from seven files to five and removes the model from all of them, which
  is a smaller claim than #1030's. That issue stays filed.
- `tests/test_agent_instruction` needing `127.0.0.1:11434` both answered and
  silent, [skills#1127](https://github.com/wildcat-finance/skills/issues/1127).
  Not fixed here, and named in the register as `port-dependent-suite` because it
  decides whether a step's own exit command can be believed.
- Reissuing `parity.json` under any route. The selected design makes that
  unnecessary rather than cheaper.
- Repository-wide conversion of instruction prose to the compact form, which
  ADR-062 already places out of scope.

Boundaries this delivery holds to:

- **Always.** Both `python3 -m unittest discover -s tests` and
  `python3 -m unittest tests.test_agent_instruction` before a commit. The
  imprimatur lint on every shipped document. `agent_instruction.py check` over
  the manifest after any fixture change.
- **Ask first.** Invoking `measure`, once, and only after `gpt-oss:120b` is
  warm and `ollama ps` shows it loaded. Changing the `wildcat-agent-instruction/v1`
  compact encoding. Changing what `promise_machine_coverage.json` binds.
  Touching `.github/workflows/repo.yml` or `tests/check-map-v1.json`. Adding
  any dependency.
- **Never.** Hand-write a token count. Delete or weaken
  `test_stale_measurement_report_refuses` or
  `test_stale_parity_report_refuses` to make a suite pass. Edit one of the three
  bound documents to make the fixture agree with itself. Record an
  `observed_on` date for bytes no tokenizer read. Claim a `measure` run
  happened when it did not.

## 4. Design options

Route 4 of the issue, refusing early with a message naming the machine, landed
as `7bcffa97` in PR #1100. It is treated as done rather than as a candidate.
Four candidates remain. The prose below explains them; the selection is made in
`.hexaemeron/design-evidence.json` from measured values, not from this prose.

**`deterministic-tokenizer`.** Replace the pinned local model with a vendored
deterministic tokenizer and leave the measured corpus definition alone. The
trade: reproducibility anywhere, bought by giving up the provenance that makes
the recorded figures worth recording, and PR #991's boundary says that
provenance is the claim. It also does not reach the fault. `parity.json` binds
the same corpus digest and records what two model families answered, so a
source edit still leaves a record only 83,138,857,312 bytes of model weights
can reissue.

**`digest-neutral-corpus`.** Take the embedded whole-file source digest out of
the measured bytes and out of the corpus subject, and keep the whole-file
binding in the manifest where review needs it. The measured projection replaces
every bound whole-file digest with one fixed 64-character placeholder, and the
corpus subject binds the reviewed span digest and the projection digests
instead of the whole-file digest and the raw artefact digests. The trade: one
`measure` run when it lands, and a measurement record that must say plainly
which projection it measured, or it records a count beside bytes that are not
the artefact's bytes.

**`published-profile`.** Publish a container or a second recorded profile so
the pinned adapter runs somewhere besides one laptop. The trade: keeps both
reproducibility and provenance, and adds a release burden of the same
83,138,857,312 bytes of weights, per contributor rather than once. It also
leaves the token counts moving on every out-of-span edit, so every such edit
still spends a measurement, against a budget of one.

**`evidence-outside-corpus`.** Stop comparing each committed evidence record's
corpus digest to the manifest. The trade is the cheapest and the worst: an edit
costs nothing, and the recorded counts stop being counts of anything the
repository can check. It is in the record so that its refusal is measured
rather than assumed.

Every criterion is computed by `.hexaemeron/scripts/design_probe.py` from the
committed fixture bytes, one real out-of-span edit, the local Ollama blob
sizes, and one real `agent_instruction.py check` run. The probe refuses to
score unless it first reproduces `measurement.json`'s recorded corpus digest
from the manifest, and unless the real out-of-span run refuses exactly
`WAI-E-DIGEST.CORPUS` at `$.evidence.measurement_record`. Both self-checks
pass.

| candidate | `reissue-model-bytes` | `unmeasured-token-counts` | `enforced-corpus-bindings` | `reconciliation-file-passes` | `landing-model-measure-runs` | `measured-byte-churn` |
| --- | --- | --- | --- | --- | --- | --- |
| `deterministic-tokenizer` | 83,138,857,312 | 0 | 2 | 7 | 0 | 5,034 |
| `digest-neutral-corpus` | 0 | 0 | 2 | 5 | 1 | 0 |
| `published-profile` | 83,138,857,312 | 0 | 2 | 7 | 0 | 5,034 |
| `evidence-outside-corpus` | 0 | 2 | 0 | 5 | 0 | 5,034 |

Three selection gates remove three candidates. `reissue-model-bytes` at most
zero removes `deterministic-tokenizer` and `published-profile`, because both
leave a record after an out-of-span edit that only model weights can reissue.
`unmeasured-token-counts` at most zero and `enforced-corpus-bindings` at least
one both remove `evidence-outside-corpus`. `digest-neutral-corpus` is the only
candidate that fails no gate, so it is the frontier under `unique-frontier`.

It is not free, and the record says so. `landing-model-measure-runs` is 1 for
`digest-neutral-corpus` and 0 for every other candidate: changing what the
corpus contains needs one final measurement under the new definition. That is
the whole measurement budget, spent once, to make every later edit cost none.

## 5. Risk register seed

The concerns below are what the audit loop should look hardest at. Two of them
sit outside the code being written and are here because they decide whether a
step's own exit command can be believed.

`measure-sign-flip` is the one that can end the delivery. ADR-062 records the
three-document token gate moving between a one-token saving and a one-token
regression on how one embedded SHA-256 segmented. Under the selected design
that digest becomes a fixed placeholder, which removes the source of that
movement but changes the measured bytes once. If the single permitted run
returns a non-negative `delta_tokens`, `WAI-E-MEASURE.NON_NEGATIVE_DELTA`
refuses and there is no second run to fall back on.

```risk-register
measure-sign-flip | the one permitted measure run under the new corpus definition | delta_tokens stays negative, and the step records the observed value rather than asserting it will
projection-honesty | the measurement record's document digests | every recorded count names the exact bytes measured, and the projection is declared in the record rather than implied
whole-file-binding-loss | the manifest source entries | the whole-file digest is still bound and still checked, so removing it from the measured subject does not remove it from review
corpus-subject-closure | _corpus_sha256's subject | no field silently leaves the digested subject beyond the two the design names, and the change is refused if it widens
stale-guard-retention | test_stale_measurement_report_refuses and test_stale_parity_report_refuses | both selectors still fail on a stale record after the change, and neither is deleted or weakened
in-span-edit-refusal | an edit inside a reviewed span | the corpus digest still moves and check still refuses, because those bytes are what the counts are counts of
span-offset-shift | an edit before a reviewed span start | the recorded start and end are re-derived, and the regression covers the before case as well as the after case
reconcile-tool-writes | the reconciliation tool's writes into the fixture tree | writes are confined below the fixture root, atomic, and leave no half-written artefact when killed
refusal-detail-coverage | every adapter refusal a contributor can reach | a missing or differently-sited client executable names the tokenizer and the machine, not only the digest node that failed
coverage-row-currency | the agent_instruction row of tests/promise_machine_coverage.json | all six digests the reconciliation moves are updated, and the bound selector list still resolves
port-dependent-suite | 127.0.0.1:11434 during any step exit command | the step records the port's state alongside the result, so a green run is not read as evidence of a green CI run
warm-model-precondition | the state of gpt-oss:120b before the measure call | ollama ps lists the model loaded before the call, because a cold 65 GB load exceeds the profile's own 170-second cap
```

## 6. Glossary seeds

- **Bound source.** One of the three Markdown documents the manifest pins by
  whole-file SHA-256.
- **Reviewed span.** The `start` to `end` byte range of a bound source that a
  reviewer signed off, and the only part of it the measurement counts.
- **Measured stream.** One byte sequence handed to the tokenizer: a reviewed
  span, a canonical model, or a compact document.
- **Measured projection.** The transform applied to a measured stream before
  counting. Today it is the identity; the selected design makes it replace each
  bound whole-file digest with a fixed placeholder.
- **Corpus subject.** The six manifest fields `_corpus_sha256` digests, whose
  digest authenticates both evidence records.
- **Reconciliation.** The passes that bring the fixture back into agreement
  after a bound source changes.
- **Out-of-span edit.** A bound source edit that leaves its reviewed span
  byte-identical. The case this delivery makes cheap.
- **In-span edit.** A bound source edit that changes reviewed bytes. The case
  that must keep costing a measurement.
- **Pinned adapter.** The `ollama-loopback-generate/v1` profile, bound to
  `/usr/bin/curl`, one Ollama build, one version string and one model blob.

## 7. Sources

- `tests/fixtures/agent-instruction-v1/manifest.json`, digest
  `c7f0bea52aee68f3c561fd95f8648a74695cf25182b89d9f177ef4d5e3d71775` as
  `check` reports it.
- `tests/fixtures/agent-instruction-v1/evidence/measurement.json`, corpus
  digest `934acac1ec92d524eb1c7e9a1b82f945143e00ac838f9ba2ae39bdad93a38eda`,
  `tokenizer_id` `gptoss-120b-ollama-0.32.15`, `observed_on` 2026-08-30,
  `source_tokens` 2528, `compact_tokens` 2175, `delta_tokens` -76.
- `tests/fixtures/agent-instruction-v1/evidence/parity.json`, same corpus
  digest, `family_ids` `qwen35-aeon-27b-q4-k-m` and `gptoss-120b-mxfp4`, 18
  results.
- `tests/fixtures/agent-instruction-v1/evidence/tokenizer-profile.json` and
  `family-profiles.json`.
- `scripts/agent_instruction.py`: `_corpus_sha256` line 3276,
  `measure_manifest` line 3290, `_load_evidence_artifacts` line 3200,
  `_verify_profile_identity` line 1450, `_run_bounded` line 1330,
  `_adapter_identity_detail` line 1430.
- `docs/decisions/ADR-062-encode-a-closed-agent-instruction-model.md` and
  `docs/agent-instruction-language-v1.md`.
- `.github/workflows/repo.yml` line 35; `tests/check-map-v1.json` entry
  `root-suite`.
- `tests/promise_machine_coverage.json`, key `agent_instruction`.
- Issues 1098, 1030, 1066, 1127. Pull requests 1100 and 991.
- `audit/rounds/fiat-909-compact-lossless-agent-instruction-language.synopsis.md`,
  `audit/AUDIT_SYNOPSIS.md`, `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`.
- Machine state observed on 3 September 2026 on the run host: `/usr/bin/curl`
  `5ab042572ea0e068644e3b8f9e8dd1ad197bfcf33d199316615b46ddc4390a41`,
  `/Applications/Ollama.app/Contents/Resources/ollama`
  `eee609f0a6da58b978d453e0385fd0e3496e6cf319c639875669b51cb4277d2d`,
  `ollama version is 0.32.15`, blob
  `6be6d66a3f546d8c19b130dc41dc24b2fc159f84ffbc76a0ee0676205083cf5a` present at
  65,369,799,840 bytes, `ollama ps` empty, `/api/version` answering.
- `.hexaemeron/design-evidence.json` digest
  `969dbc4a8d8ce31b34e3b90662c3c75c8336d45bccc969de01dc618b702275f4`, its 24
  reports under `.hexaemeron/reports/`, and the probe that produced them at
  `.hexaemeron/scripts/design_probe.py`.

## 8. Signals, and the questions behind them

[ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal
must carry. Four questions, and the step that answers each.

1. "Did the one permitted `measure` call actually read the model, or did it time
   out on a cold load?" Both failures are `WAI-E-ADAPTER.UNAVAILABLE` today,
   because `--max-time 170` makes curl exit non-zero and `_run_bounded` maps a
   non-zero exit to that code at line 1415. The measure step must record the
   `ollama ps` output and the elapsed time of the first call beside the record
   it writes, so the two are distinguishable afterwards.
2. "This contributor's reconciliation refused. Was it their edit or their
   machine?" The reconciliation tool emits, per run, the bound source it
   changed, whether the reviewed span moved, which files it rewrote, and
   whether any model was consulted. An out-of-span edit that reports a model
   consultation is a defect in the tool.
3. "The gate is red on a pull request that only touched prose. Which digest?"
   `check` already emits one refusal record with a code and a node path. The
   step that adds the reconciliation tool keeps that record as the tool's own
   failure output rather than printing a summary over it.
4. "Was this run's green suite green for the right reason?" Recorded as
   `port-dependent-suite`. Every step exit that runs the suite records whether
   `127.0.0.1:11434` answered, because that decides which half of
   `tests/test_agent_instruction` was exercised.

## 9. Boundaries, per capability

[phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary
list and the controls. This delivery opens three, and closes a fourth it must
not widen.

- **The reconciliation tool's writes.** It rewrites four committed files inside
  the fixture tree from bytes it computed. Worth taking: a path that escapes
  the fixture root, or a partial write that leaves an artefact whose digest
  verifies against a manifest that no longer matches. The control is the one
  already in the file: `write_confined_atomic` with `_open_parent`, reused
  rather than reimplemented. The register cites this as `reconcile-tool-writes`.
- **The corpus subject.** The change narrows what authenticates two evidence
  records. Worth taking: a field that leaves the subject unnoticed, after which
  a manifest edit stops invalidating a record it should invalidate. The control
  is a test that asserts the subject's exact field set, so widening or
  narrowing it fails rather than passing quietly, cited as
  `corpus-subject-closure`.
- **The subprocess the adapter spawns.** Unchanged by the selected design, and
  it stays unchanged. The pinned argv, the fixed environment, the digest checks
  before launch and the output caps are all audited controls from `S4-R3-01`.
  Register id `refusal-detail-coverage` covers only the message a refusal
  carries, not the launch path.
- **Model output in the instruction path.** Closed already, and not reopened.
  ADR-062 and PR #991 both state that models and adapters are evidence
  producers, not instruction authorities. The selected design keeps the model
  out of the reconciliation entirely, which narrows this boundary rather than
  widening it.

## 10. The budget, or its absence

[metron](../../plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget
carries and how it is checked. There is one budget here, and it is a count
rather than a duration.

The reconciliation of an out-of-span edit must consult the model zero times and
must complete in one command. Measured by:

```bash
python3 .hexaemeron/scripts/design_probe.py --root . \
  --candidate digest-neutral-corpus --criterion reissue-model-bytes
```

which must report `"value": 0`, and by the demo path in section 1 running to
completion on a host with no Ollama installed.

There is no wall-clock budget for the reconciliation. It rewrites four fixture
files totalling 12,202 bytes plus the 207,481-byte coverage register, and
`agent_instruction.py check` over the whole manifest returned in 0.15 seconds
on this host, so a duration target would be measuring noise.

The `measure` call itself has a hard bound rather than a budget: the profile's
argv caps one call at `--max-time 170` and `timeout_seconds` at 180, and there
are ten calls in a run. That is a precondition to satisfy, recorded as
`warm-model-precondition`, not a target to optimise.

## 11. The fail-closed posture

[elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage
order and the guard rule. What stops the run:

- A `measure` call that returns `WAI-E-MEASURE.NON_NEGATIVE_DELTA`. There is no
  second call, so the delivery stops and the observed value is reported rather
  than a route around it being invented, cited as `measure-sign-flip`.
- `agent_instruction.py check` refusing at any node after a reconciliation.
  A reconciliation that leaves the manifest refusing has not reconciled.
- Either stale-evidence selector failing to fail on a stale record. Register id
  `stale-guard-retention`.
- An in-span edit that reconciles without a measurement. That is the fault
  being fixed, inverted, and it stops the run.

The guard convention: every fix lands with a test that fails on the
implementation parent and passes on the fixed tree, in
`tests/test_agent_instruction.py`, named for the mechanism rather than for the
finding id. This matches the #909 round's own record, where each of the thirty
findings is "fixed and regression-tested in this commit" against a named
parent. A step's audit claim names
`python3 -m unittest tests.test_agent_instruction` with one `{report}`
argument, UTF-8 unittest text as the report format, and a report file under
`.hexaemeron/`, because that runner is what the existing coverage row binds.

The one qualification: a red or green local run of that module tells you less
than it appears to, for the reason `port-dependent-suite` records. With
`127.0.0.1:11434` answered by `ollama 0.32.15` and the model cold, the module
ran 310 tests and reported `OK` on this host at `bacb34c0`. With the port
silent, #1127 records unstable failure sets. A step exit therefore names
`python3 -m unittest discover -s tests`, the root suite, and records the port's
state beside the result.

## 12. Decisions and their homes

[hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which
decisions earn a record and where each one lives. Two are expensive to reverse.

**What the measured corpus contains.** Once the corpus subject narrows and a
measurement is recorded against it, reverting means another measurement, and
the budget is one. This earns its own decision record, as a new ADR under
`docs/decisions/`, taking the next free number at the time the step lands
rather than a number reserved now. It cites ADR-062 rather than amending it,
because ADR-062's two settled questions stay settled: the measurement still
exists, and the whole-file binding is still in the manifest. What changes is
which digest authenticates a count.

**How a measurement declares what it measured.** The record gains a field
naming its projection. That is a schema change to
`wildcat-agent-instruction-measurement/v1`, so it lives in
`docs/agent-instruction-language-v1.md` beside the rest of the version-1
contract, and in the schema file the runtime pins. A reader who finds a
`compact.sha256` that does not match `compact.wai` on disk has to be able to
find out why from the contract, not by reading the checker.

Two decisions do not earn a record. The reconciliation tool's name and
subcommand layout are cheap to change and belong in its own module docstring.
The choice of a 64-character zero placeholder over any other fixed filler is
arbitrary within the constraint that it be the same length as a SHA-256 hex
digest, and belongs in a comment at the projection function.

### Amendment -- 2026-09-03

**What changed.** The deferral "Reissuing `parity.json` under any route. The
selected design makes that unnecessary rather than cheaper." is wrong for the
landing change. `scripts/agent_instruction.py:3258-3260` compares both
`measurement.json` and `parity.json` against `_corpus_sha256(manifest)` and
refuses each with `WAI-E-DIGEST.CORPUS`. That subject includes `fixtures`,
which carries every bound source's whole-file digest, so switching the subject
moves the digest once and stales both records once. The landing therefore costs
one `measure` run over `gpt-oss:120b` and one `parity` run over
`gpt-oss:120b` and `qwen3.8-27b-aeon:q4_k_m`, 82 GB of weights across two
models rather than one.

**Why.** The deferral held for every later out-of-span edit, which is what the
design buys, and was read across to the landing change where it does not hold.
The criterion `landing-model-measure-runs` counted `measure` invocations and so
recorded 1 rather than the parity run beside it. The user accepted the
two-model landing cost before the runbook was written and holds the machine
quiet for step 3 alone. No candidate, criterion or selection changes: every
other candidate pays the same parity reissue on every bound-source edit instead
of once, which is why `reissue-model-bytes` removed two of them.

**Steps touched.** Step 3.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step
5: entry holds; exit holds. Step 6: entry holds; exit holds.
