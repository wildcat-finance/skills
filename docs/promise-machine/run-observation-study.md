# Observable run record study

Assuming, unless corrected:

1. This ordinary issue-bound delivery starts from `main` at
   `454bf3c9930c94985e5eb6179f3b01be2bf741c2`; it changes no skill frontier,
   version, manifest, or CI workflow.
2. `promise-machine-run-observation/v1` is a host-neutral JSON Lines
   interchange format plus validator, not a recorder or transcript reader.
3. The root Promise Machine owns the shared validation boundary. Ephoros
   supplies observability principles without becoming a suite-wide store.
4. Python 3 and its standard library are sufficient. No schema dependency,
   network service, host SDK, or telemetry collector is added.
5. Token counts are optional and recorded only when a host or provider exposes
   them. Missing counts remain unknown and are never estimated from text.

## 1. Problem statement

[Issue #434](https://github.com/wildcat-finance/skills/issues/434) asks for one
versioned, host-neutral record of observable work between Promise Machine and
Fiat control transitions. Current controller state records transitions, but it
does not give later reviewers a comparable event record for capability use,
duration, exit status, retries, repository identities, evidence, refusals,
unknowns, handoffs, or observed outcome. Host transcripts are neither stable
nor a safe evidence interface. Hidden model reasoning is not observable and
must refuse if presented as an observation.

A working prototype provides:

- a closed per-event schema identified as `promise-machine-run-observation/v1`;
- a bounded standard-library JSONL validator with stable text and JSON findings;
- valid success, refusal, retry, and cross-skill handoff records;
- required negative records for missing run identity, invalid order, unbound
  evidence, evidence-class or subject strengthening, and hidden reasoning;
- optional source-bound token counts and explicit unknowns; and
- one focused demonstration that exercises all accepted and refused cases.

```bash
python3 -m unittest tests.test_run_observation -v
python3 scripts/run_observation.py check tests/fixtures/run-observation/valid/success.jsonl
python3 scripts/run_observation.py check tests/fixtures/run-observation/invalid/hidden-reasoning.jsonl --json
python3 -m unittest discover -s tests
```

Validator exit zero establishes only structural and relational acceptance of
the named bytes. It establishes neither completeness, external truth, cause,
model quality, delivery correctness, nor authority to mutate a repository.

## 2. Prior art

Repository conventions already provide most components:

- `PROMISE_MACHINE.md` defines exact evidence classes and preserves unknowns;
- `scripts/promise_machine.py` supplies bounded reads, duplicate-key refusal,
  deterministic findings, and text/JSON result parity;
- `.hexaemeron/ledger.jsonl` shows JSON Lines is suitable for ordered records
  while remaining controller state rather than general telemetry;
- `tests/promise_machine_coverage.json` binds promises to exact evidence and
  refuses unsupported strengthening;
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` supplies run, issue, step,
  role, refusal, recovery, and handoff concepts without owning this schema; and
- `plugins/hexaemeron/skills/metron/scripts/metron.py` preserves measured
  durations without defining a general observation envelope.

[PR #474](https://github.com/wildcat-finance/skills/pull/474) keeps receipted
operator statements distinct from truth. [PR
#469](https://github.com/wildcat-finance/skills/pull/469) is the precedent for
a suite-wide root promise and generated copies. [PR
#293](https://github.com/wildcat-finance/skills/pull/293) established stable
finding codes, evidence preservation, and checker/report parity.

The Promise Machine and issue #446 rounds in `audit/AUDIT.md` require bounded
regular files, repository confinement, deterministic diagnostics, exact
evidence subjects/classes, and no promotion of a recorded assertion to truth.
The current Phylax surface also refuses unsafe deserialisation and credentials
in subprocess arguments. This validator uses JSON only, executes no record
content, and invokes no subprocess.

External prior art is limited to the [OpenTelemetry Logs Data
Model](https://opentelemetry.io/docs/specs/otel/logs/data-model/), [W3C Trace
Context](https://www.w3.org/TR/trace-context/), [RFC
3339](https://www.rfc-editor.org/info/rfc3339/), [JSON
Lines](https://jsonlines.org/), and OpenTelemetry's [generative-AI metric
conventions](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/gen-ai-metrics.md).
The format borrows timestamps, correlation, streaming, and optional exposed
token counts without claiming complete compatibility.

## 3. Constraints and non-goals

- Every event repeats the exact schema id and run id, with a contiguous
  positive sequence, unique event id, RFC-3339 time, stable type, and
  correlation id.
- One `run.started` opens the record and one `run.finished` closes it. Parent,
  capability, retry, handoff, and evidence references point backward.
- Repository paths are slash-separated and relative: no absolute path, `..`,
  execution, or implicit file read follows from a recorded value.
- Argument information is bounded metadata. Raw prompts, completions, tool
  output, credentials, signed payloads, environment values, and hidden
  reasoning are forbidden.
- Evidence references name subject, source, selector or digest, and one exact
  Promise Machine class. Outcomes and handoffs preserve class and subject.
- Host, model, and token facts appear only when exposed. Placeholder identities
  and estimated token counts refuse; absence stays unknown.
- Input is a confined regular UTF-8 file with one object per line, final
  newline, duplicate-key refusal, and fixed byte, line, event, nesting, string,
  and collection ceilings.
- Every source pointer in the study and runbook is a backticked repository path
  or absolute URL, so byte-identical publication remains location-independent.
- The correct Horos currency command is
  `python3 plugins/horos/skills/horos/scripts/horos.py check .`. The obsolete
  spelling `horos.py scan . --check` is a known exit-2 specimen and must not
  appear in a receipted runbook command block.

The run does not implement capture, transcript ingestion, redaction, storage,
search, a database, dashboard, model criticism, automatic issue filing, Fiat
receipt binding, or cross-run diagnosis. Issues #435, #436, and #449 retain
those boundaries. No record selects a skill or authorises a tool call,
repository mutation, deployment, security conclusion, financial conclusion,
or model-quality conclusion.

**Always.** Run focused and root tests, Promise checks, the three non-Solidity
discipline lints, prose gates, the exact Horos command, and `git diff --check`.

**Ask first.** Add a dependency, change a public field or stable finding code,
widen paths or inline payloads, touch CI, bind Fiat receipts, or add capture.

**Never.** Store secrets or transcripts, represent hidden reasoning, estimate
tokens, accept unbound evidence, strengthen a class or subject, delete a
refusing fixture, execute input, or claim an unrun check.

The bundled `x-ray`, `solidity-auditor`, and `fizz` suite is waived because the
delivery is JSON, Python, fixtures, and Markdown with no Solidity. Phylax,
Ephoros, Elenchus, Hypomnema, hostile-input tests, and the audit loop remain due.

## 4. Design options

### A. Root schema plus standalone validator, chosen

Add `schemas/promise-machine-run-observation-v1.schema.json`, a bounded
`scripts/run_observation.py`, fixtures, tests, operator documentation, a root
Promise declaration and generated copies. This gives later producers one
contract without coupling it to Fiat. The trade is a new root executable and
an explicit schema/runtime drift obligation.

### B. Put observations in Fiat's ledger

Rejected because it couples high-volume work events to controller integrity,
makes Fiat the only producer, and pre-empts issue #436's separate binding job.

### C. Make OpenTelemetry canonical

Rejected because v1 needs an offline repository contract, exact Promise
Machine evidence semantics, deterministic fixtures, and a narrower payload
boundary than a general exporter envelope.

### D. Publish prose examples only

Rejected because examples cannot enforce identity, order, correlation,
evidence binding, or hidden-reasoning refusal and cannot emit stable findings.

The closed event union covers `run.started`, `capability.started`,
`capability.finished`, `transition.refused`, `retry.scheduled`,
`handoff.recorded`, and `run.finished`. Optional token usage contains only
non-negative host/provider-reported input and output counts, source, scope, and
an exposed accounting identity. No derived cost or quality verdict exists.

Recorded facts are emitter-supplied event bytes, exposed identities, counts,
duration, Git identities, references, refusals, recoveries, handoffs, and final
status. Inferred facts name a deterministic rule and prior event ids. Unknowns
name an unavailable field and reason and never satisfy a required identity,
binding, or positive outcome.

## 5. Risk register seed

```risk-register
unbounded-input | caller-supplied JSONL bytes and event count | per-line, total-byte, event-count, nesting, string, and collection limits refuse before unbounded work
unsafe-path | caller input path and repository paths inside events | accept one confined regular file and treat recorded paths as checked strings, never instructions
unsafe-deserialisation | caller JSON values | parse JSON with duplicate-key checks and closed typed shapes; no pickle, YAML object construction, import, eval, or execution
schema-drift | JSON Schema and Python relational validator | tests bind schema id, required fields, enums, and every executable relation
event-order | sequence, lifecycle, retry, and final relationships | fixtures cover gaps, duplicates, forward references, unmatched finishes, invalid retries, and events after finish
correlation-gap | correlation, parent, capability, and handoff ids | every reference resolves backward within the same run
evidence-binding | evidence ids, subjects, selectors, and outcomes | every consumed id resolves to an earlier definition with non-empty subject and exact class
evidence-promotion | outcome and handoff subject/class | any mismatch refuses; no universal class ranking is introduced
hidden-reasoning | rationale, thought, chain-of-thought, or internal-reasoning fields | closed objects and forbidden-name checks reject the claim at any depth
sensitive-payload | arguments, output, environment, prompts, and completions | only bounded metadata, digests, and references are allowed
optional-host-facts | unavailable host, model, or token data | omit or record unknown; placeholders and estimates refuse
token-accounting | exposed usage counts | non-negative integers name source, scope, and accounting identity and imply neither price nor quality
deterministic-report | stable text and JSON findings | one sorted finding model feeds both formats and parity tests compare them
partial-record | truncation or interrupted write | missing newline, malformed last line, absent finish, and unresolved starts refuse without mutation
command-drift | documented repository commands | execute every runbook command or its syntax/help path before receipt and retain known invalid spellings as negative evidence
```

Audit probes should combine faults: an oversized final line after valid events,
a symlinked input, nested duplicate keys, cross-run retry, handoff subject
change, Boolean token counts, hidden-reasoning names at depth, truncation, and
an event after finish.

## 6. Glossary seeds

- `Run observation`: one checked JSONL record for one run, not a transcript.
- `Event`: one self-identifying JSON object on one line.
- `Correlation id`: a bounded join key, not proof that no event is missing.
- `Capability`: a stable host-exposed operation name plus bounded metadata.
- `Evidence reference`: a source-bound pointer with subject, selector or
  digest, and one exact Promise Machine class.
- `Observed outcome`: final recorded status, distinct from why an agent chose it.
- `Unknown`: a named fact the emitter could not establish; it authorises no
  positive transition.
- `Token usage`: optional exposed counts, not an estimate, price, or quality
  measure.
- `Finding code`: a stable `RO` identifier emitted in text and JSON.

## 7. Sources

Repository sources: `PROMISE_MACHINE.md`, `AGENTS.md`,
`scripts/promise_machine.py`, `tests/test_promise_machine_contract.py`,
`tests/promise_machine_coverage.json`,
`plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/skills/phylax/SKILL.md`,
`plugins/hexaemeron/skills/phylax/scripts/phylax.py`,
`plugins/hexaemeron/skills/ephoros/SKILL.md`,
`plugins/hexaemeron/skills/metron/SKILL.md`,
`plugins/hexaemeron/skills/elenchus/SKILL.md`,
`plugins/hexaemeron/skills/hypomnema/SKILL.md`, and `audit/AUDIT.md`.

Web sources: [issue #434](https://github.com/wildcat-finance/skills/issues/434),
its [token-telemetry comment](https://github.com/wildcat-finance/skills/issues/434#issuecomment-5377113228),
[PR #474](https://github.com/wildcat-finance/skills/pull/474), [PR
#469](https://github.com/wildcat-finance/skills/pull/469), and [PR
#293](https://github.com/wildcat-finance/skills/pull/293), plus the external
standards cited in section 2.

## 8. Signals, and the questions behind them

Ephoros governs the persistent signal shape.

1. Which event caused refusal? Stable code, line, event id, and correlation id.
2. Did a retry follow its failed attempt? Backward retry and capability links.
3. Did a handoff preserve subject, scope, time domain, and class? Exact
   producer, consumer, and evidence references.
4. Was token use exposed? Source-bound counts answer when present; otherwise an
   unknown names the gap.

The validator is a bounded command, not a service. It needs deterministic
findings and exit status, not a metric backend, exporter, dashboard, or alert.

## 9. Boundaries, per capability

Phylax governs the off-chain boundary.

- Input: one confined regular file, fixed limits, UTF-8, duplicate-key refusal,
  depth/collection checks, and no rewrite.
- Content: closed objects, metadata-only arguments, reference indirection,
  forbidden sensitive/reasoning fields, and no execution.
- Repository metadata: validate relative paths and full Git ids as strings;
  do not open named paths or run Git from record content.
- Evidence/handoff: bind backward to exact subject/class definitions.
- Output: fixed bounded findings, no raw-value echo, canonical JSON, and parity
  tests.

No URL fetch, credential read, subprocess, model call, external service, or new
dependency is introduced.

## 10. The budget, or its absence

Metron supplies no optimisation budget because no speed claim exists. The
validator has denial-of-service ceilings for total bytes, line bytes, event
count, nesting, strings, and collections, each exercised by a refusal test.
Changing them for performance reasons requires a measured baseline and study
amendment.

## 11. The fail-closed posture

Elenchus governs observed failures. Unsafe input identity, malformed JSONL,
wrong schema/run identity, unknown fields, broken order, unresolved references,
subject/class change, hidden-reasoning claims, raw payloads, and invalid
optional telemetry each produce a stable finding and non-zero exit. The command
never repairs, truncates, skips, or rewrites input. Every defect found in build
or audit receives a minimal red guard before its fix.

## 12. Decisions and their homes

Hypomnema places the standing decision at
`docs/decisions/ADR-014-define-the-promise-machine-run-observation-record.md`;
ADR-014 is unused at the pinned base. The schema belongs at
`schemas/promise-machine-run-observation-v1.schema.json`, relational checks at
`scripts/run_observation.py`, examples under
`tests/fixtures/run-observation/`, executable expectations at
`tests/test_run_observation.py`, operator prose under
`docs/promise-machine/run-observation-v1.md`, and the narrow authority in
`PROMISE_MACHINE.md` and its generated copies. Study and runbook copies live
under `docs/promise-machine/`; audit evidence appends to `audit/AUDIT.md`.

Two dependency-ordered steps are sufficient:

1. Publish byte-identical study/runbook copies, ADR-014, and the refreshed
   Horos boundary.
2. Build, bind, harden, document, and demonstrate the complete schema and
   validator, including every issue acceptance case and combined audit probe.

The first step leaves only reviewable prose. The second remains one capability:
the schema has no acceptance without its validator and demonstration.
