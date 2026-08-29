# Runbook: a job-scoped model inference proxy

This runbook derives from the receipted study at `.hexaemeron/study.md`. It
delivers the component prototype against a synthetic accepted-JobSpec adapter
and a loopback provider. It does not claim the #698 signed-JobSpec join, the
#699 VM channel, a live provider, or the #702 Fiat integration while those
interfaces remain unavailable.

## Step 1: Define and compile the proxy policy

**Goal.** Scaffold the Phylax-owned proxy and deterministically compile one
closed, credential-free policy from digest-bound accepted-job evidence.

**Entry.** Run branch
`fiat/700-proxy-model-traffic-without-giving-the-worke` at
`7e449ba35e1519d28b33f06225c4c4137b548a23`, with the receipted study and
runbook as the only run-local artefacts and Python pinned to 3.13.15.

**Exit.** Tracked copies of the study and runbook preserve the receipted bytes,
apart from any mechanically necessary relative-link rebasing. ADR-042 records
the per-job normalised-protocol choice, its digest join, the rejected generic
proxy and guest-token alternatives, and the provider non-exfiltration limit.
The normative Phylax reference fixes the `model-proxy-policy/v1` vocabulary,
canonical JSON subset, hard implementation ceilings, version rule, outcome
codes, and synthetic adapter boundary. A standard-library CLI and library
strictly parse bounded accepted-job evidence, recompute its JobSpec digest,
resolve a closed code-owned loopback provider profile, reject unknown or
duplicate fields and permissive defaults, emit byte-stable policy JSON, and
verify its SHA-256 against a golden vector. The policy and all diagnostics are
credential-free. The existing repository licence and Python pin are reused;
the existing Hexaemeron and root suites are the CI hook. Prove the exit with
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/phylax/scripts/model_proxy.py compile-policy --accepted-job plugins/hexaemeron/tests/fixtures/model-proxy-v1/accepted-job.json --expect plugins/hexaemeron/tests/fixtures/model-proxy-v1/policy.json`,
`mise exec python@3.13.15 -- python3 -m unittest plugins.hexaemeron.tests.test_phylax_model_proxy -v`,
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py`,
`mise exec python@3.13.15 -- python3 -m unittest discover -s tests`, and
`mise exec python@3.13.15 -- python3 scripts/portable_promise_machine.py check`.

**Files.** Create `docs/phylax-model-proxy/{study.md,runbook.md}`,
`docs/decisions/ADR-042-use-a-job-scoped-model-proxy.md`,
`plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md`,
`plugins/hexaemeron/skills/phylax/scripts/model_proxy.py`,
`plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/{__init__.py,canonical.py,errors.py,policy.py,profiles.py}`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`, and the accepted-job,
policy, and rejection fixtures under
`plugins/hexaemeron/tests/fixtures/model-proxy-v1/`; update only the generated
portable-runtime copies of those canonical files and any deterministic Horos
boundary data required by the repository checks.

**Tests.** Add golden accepted-job, canonical-policy, and policy-digest cases;
missing, extra, duplicate, null, boolean-as-integer, floating, negative, zero,
oversized, excessive-depth, invalid-Unicode, stale-digest, unknown-schema,
unknown-profile, model/profile disagreement, feature-enabled, content-log,
diagnostic-consent, data-class, lifetime, and hard-ceiling refusals. Verify
that key order does not change canonical bytes, every declared policy field
changes the digest, no credential field is representable, and old or future
versions refuse explicitly. The step audit runner contract is test command
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py {report}`,
report format `elenchus.unittest.v1`, report file
`.elenchus/fiat-700-model-proxy-step-1.json`.

**Disciplines.** phylax: untrusted accepted-job bytes become an authority-bearing
policy, so bounded reads, closed fields, digest recomputation, and no secret
crossing apply. ephoros: compiler results expose only safe schema, profile,
digest, and fixed refusal codes; no metrics backend is introduced. metron:
none, hard size and time ceilings are safety limits rather than a speed claim.
elenchus: every malformed vector is a cause-level guard and an unexpected
exception is a refusal defect. hypomnema: the wire and policy choice is costly
to reverse, so ADR-042 and the normative reference are its durable homes.

## Step 2: Enforce the guest framing boundary

**Goal.** Parse and emit one bounded provider-independent text operation over
an abstract ordered byte stream without admitting provider-native authority.

**Entry.** The controller-provided Step 2 branch starts at the signed Step 1
head whose exact policy compiler, golden digest, tracked specifications, and
all Step 1 exit commands are green.

**Exit.** The framing core consumes four-byte unsigned big-endian lengths,
checks the policy and compiled caps before allocation, accepts strict UTF-8
JSON with unique object names and a closed text-request schema, and emits only
the closed `model-response/v1` shape. It handles fragmented and concatenated
frames without reordering or accepting trailing ambiguity. Sequence numbers
are assigned by the trusted core; guest-supplied job ids, sequence numbers,
URLs, methods, models, headers, tools, uploads, remote references, images,
storage, or lifecycle fields refuse with fixed content-free codes. Streaming
and multiplexing remain unavailable. Prove the exit with
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/phylax/scripts/model_proxy.py check-frames --manifest plugins/hexaemeron/tests/fixtures/model-proxy-v1/framing-cases.json`,
the focused unittest command from Step 1, the full Hexaemeron runner, the root
unittest suite, and the portable check.

**Files.** Create
`plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/framing.py` and
`plugins/hexaemeron/tests/fixtures/model-proxy-v1/framing-cases.json`; change
`model_proxy.py`, `test_phylax_model_proxy.py`, and the normative reference;
update only their generated portable-runtime copies and deterministic Horos
boundary data.

**Tests.** Cover one-byte fragmentation, every length-prefix split, two frames
in one read, incomplete and trailing bytes, zero and over-cap lengths, declared
versus actual length disagreement, invalid UTF-8, lone surrogates, duplicate
names, excessive depth/collections/strings/scalars, unknown or missing fields,
integer coercion, alternate operation/version, guest identities and sequence,
all forbidden provider features, deterministic response bytes, and bounded
sanitised errors. The step audit runner contract is test command
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py {report}`,
report format `elenchus.unittest.v1`, report file
`.elenchus/fiat-700-model-proxy-step-2.json`.

**Disciplines.** phylax: the guest controls every input byte, so the length,
UTF-8, JSON, schema, memory, identity, and feature boundaries fail before
allocation or authority selection. ephoros: fixed frame-stage and refusal-code
events answer where parsing stopped without retaining input. metron: none,
incremental bounds are safety controls and no throughput claim is made.
elenchus: fragmented, combined, malformed, and oversized frames remain minimal
parent-red guards for parser fixes. hypomnema: no new decision record is owed;
the framing grammar extends the Step 1 normative reference and ADR.

## Step 3: Cross the provider boundary without exposing the credential

**Goal.** Map one admitted operation through a closed provider profile while
keeping authentication and destination authority outside the guest.

**Entry.** The controller-provided Step 3 branch starts at the signed Step 2
head with the Step 1 policy and Step 2 framing exits green.

**Exit.** A trusted provider layer maps the normalised request through the
code-owned profile, reads a canary credential only after policy admission,
constructs the fixed authentication header internally, and validates a bounded
upstream response before normalising it. A standard-library HTTPS connector
fixes scheme, hostname, port, path family, method, TLS hostname verification,
content encoding, and the resolved address set; private, loopback, link-local,
multicast, unspecified, documentation, and other disallowed production
addresses refuse. Automatic redirects and CONNECT are absent, and every 3xx
is terminal. Tests use an injected loopback transport and resolver: the
provider fixture sees the canary, while guest frames, events, errors, receipts,
argv, environment snapshots, and the test output tree do not. No live provider
call occurs. Prove the exit with
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/phylax/scripts/model_proxy.py provider-demo --manifest plugins/hexaemeron/tests/fixtures/model-proxy-v1/provider-cases.json`,
the focused unittest command, full Hexaemeron runner, root unittest suite, and
portable check.

**Files.** Create
`plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/{provider.py,transport.py}`
and `plugins/hexaemeron/tests/fixtures/model-proxy-v1/provider-cases.json`;
change `profiles.py`, `model_proxy.py`, `test_phylax_model_proxy.py`, and the
normative reference; update only their generated portable-runtime copies and
deterministic Horos boundary data.

**Tests.** Cover exact request mapping, credential injection after admission,
credential-source failure, no credential in guest-visible or retained
surfaces, arbitrary scheme/host/port/path/method/model/header attempts,
guest-supplied authorization, CONNECT, every redirect class, DNS answer
changes, empty/multiple/special addresses, unpinned connection targets, TLS
hostname and certificate failure, chunked and content-length response floods,
unexpected encoding/status/type, duplicate/unknown/malformed response fields,
usage disagreement, raw error sanitisation, secret echo, and connection close.
The step audit runner contract is test command
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py {report}`,
report format `elenchus.unittest.v1`, report file
`.elenchus/fiat-700-model-proxy-step-3.json`.

**Disciplines.** phylax: name resolution, TLS, HTTP, credentials, provider
bytes, redirects, errors, and cleanup are live trust boundaries closed by the
profile and bounded connector. ephoros: safe profile, disclosure-state,
outcome-family, byte-count, token-count, and duration signals replace raw
traffic diagnostics. metron: none, the loopback timing is feasibility evidence
only. elenchus: each origin, redirect, response, and credential counterexample
must fail on the parent before its cause is repaired. hypomnema: the provider
profile rules extend ADR-042 and the normative reference; no live-provider
retention record is created before a provider is selected.

## Step 4: Enforce lifecycle, quotas, and content-free receipts

**Goal.** Make disclosure admission atomic, propagate cancellation and expiry,
and retain bounded evidence without retaining model content.

**Entry.** The controller-provided Step 4 branch starts at the signed Step 3
head whose policy, framing, and provider-boundary exits are green.

**Exit.** One runtime instance serves one job and accepted JobSpec digest.
Before disclosure it atomically reserves request count, request bytes, counted
input tokens, concurrency, maximum output tokens, response bytes, and remaining
wall time. The pinned profile counts the exact mapped input; unknown counters
refuse. Trusted cancellation and the earlier of absolute expiry and the
elapsed deadline measured by Python's `time.monotonic_ns()` clock mark the job terminal before closing I/O, admit no later
request, and discard late responses. A restart cannot resume the job. The
bounded no-follow receipt sink writes one activation, at most one record per
consumed sequence, and one terminal record, each no larger than 4,096 UTF-8
bytes and containing only allowlisted ids, digests, versions, counts, timings,
disclosure state, and outcome codes. Pre-disclosure receipt failure prevents
the call; terminal receipt failure withholds the response and stops the job.
Operator text is rendered from the exact policy and states what leaves the
machine, the named destination/profile, retention rule, disabled features,
limits, and the provider non-exfiltration qualification. Prove the exit with
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/phylax/scripts/model_proxy.py lifecycle-demo --manifest plugins/hexaemeron/tests/fixtures/model-proxy-v1/lifecycle-cases.json`,
the focused unittest command, full Hexaemeron runner, root unittest suite, and
portable check.

**Files.** Create
`plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/{lifecycle.py,receipts.py,operator.py}`
and `plugins/hexaemeron/tests/fixtures/model-proxy-v1/lifecycle-cases.json`;
change `model_proxy.py`, `test_phylax_model_proxy.py`, and the normative
reference; update only their generated portable-runtime copies and
deterministic Horos boundary data.

**Tests.** Cover exact and over-limit sequential and concurrent count, byte,
token, output, response, and concurrency reservations; rollback and terminal
paths; request floods; cross-job identity; second activation; absolute expiry
and expiry measured by `time.monotonic_ns()`; cancellation before admission and during transport; late
response suppression; completion/cancel/expiry races; unknown tokenizer;
provider-usage under/over-reporting; receipt count/size/schema/mode; duplicate
terminal events; symlink, directory, pre-existing target, restrictive umask,
short write, partial write, replacement, and unavailable sink failures; secret,
prompt, response, content-digest, raw URL/header/error/provider-id absence; and
operator-text/policy parity. The step audit runner contract is test command
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py {report}`,
report format `elenchus.unittest.v1`, report file
`.elenchus/fiat-700-model-proxy-step-4.json`.

**Disciplines.** phylax: concurrency, time, filesystem, partial writes,
secrets, and late provider output are the step's boundaries, with atomic
reservation and fail-closed publication. ephoros: bounded lifecycle and
request receipts answer the four study questions without content-bearing
labels or raw diagnostics. metron: none, clocks and quotas enforce security
ceilings rather than performance. elenchus: race schedules, killed writes, and
late responses are deterministic guards and partial test output is never a
pass. hypomnema: receipt and lifecycle vocabularies extend the normative
reference; operator-facing disclosure belongs with that contract.

## Step 5: Demonstrate hostile conformance and publish the Phylax contract

**Goal.** Prove the complete loopback component against every #700 hostile
case and ship its bounded public ownership and dependency claims.

**Entry.** The controller-provided Step 5 branch starts at the signed Step 4
head with policy, framing, provider, lifecycle, quota, receipt, and operator
exits green.

**Exit.** One closed manifest drives a positive component demo plus distinct
arbitrary-URL, DNS-rebinding, redirect, credential-header, unsupported-method,
unsupported-model, oversized, nested, request-flood, response-flood, cross-job,
replay-after-expiry, and call-after-cancellation cases. The CLI reports one
safe fixed outcome per row, refuses omitted, duplicate, stale-digest, unknown,
or unexecuted rows, and exits nonzero unless every expected result occurs. The
positive row proves policy and JobSpec digest binding, loopback credential
injection, normalised response, bounded receipts, operator disclosure, and
complete canary/content absence from guest-visible and retained surfaces. It
states that the #698 acceptance receipt, #699 launch receipt, live provider,
public pilot, and end-to-end digest join are not established. Phylax's public
skill contract and generation ledger name the new capability without changing
its mature frontier; the Hexaemeron package takes its smallest unused patch
version and every host manifest, marketplace entry, Promise Machine coverage
digest, portable copy, and Horos boundary agrees. Prove the exit with
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/phylax/scripts/model_proxy.py conformance --manifest plugins/hexaemeron/tests/fixtures/model-proxy-v1/manifest.json`,
`mise exec python@3.13.15 -- python3 -m unittest plugins.hexaemeron.tests.test_phylax_model_proxy -v`,
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py`,
`mise exec python@3.13.15 -- python3 -m unittest discover -s tests`,
`mise exec python@3.13.15 -- python3 scripts/portable_promise_machine.py check`,
the changed-plugin and root checks required by `AGENTS.md`, the exact
Imprimatur, Phylax, Ephoros, Hypomnema, frontmatter, version-propagation,
evolution-contract, marketplace-prose, Horos-currency, audit-synopsis, and
`git diff --check` gates over the final tree.

**Files.** Create
`plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/conformance.py` and
`plugins/hexaemeron/tests/fixtures/model-proxy-v1/manifest.json`; change
`plugins/hexaemeron/skills/phylax/{SKILL.md,EVOLUTION.md}`, its agent metadata,
the normative reference, CLI/library, focused tests and fixtures,
`plugins/hexaemeron/README.md`, both Hexaemeron plugin manifests, both root
marketplace registries, `tests/promise_machine_coverage.json`, all generated
portable-runtime copies of changed canonical files, and `.horos/boundary.json`
only where deterministic repository tools require them.

**Tests.** Add manifest schema, digest, completeness, uniqueness, order,
expected-outcome, and no-skips guards; one independent case for every hostile
acceptance item; positive-path policy/launch placeholders; exact safe summary;
canary and content-shape scans over guest frames, receipts, events, diagnostics,
argv, environment fixture, and produced tree; operator disclosure parity;
dependency-gated end-to-end status; old Phylax behaviour preservation; exact
skill/package version separation; evolution-axis preservation; marketplace and
portable-copy parity; and deterministic Horos currency. The step audit runner
contract is test command
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py {report}`,
report format `elenchus.unittest.v1`, report file
`.elenchus/fiat-700-model-proxy-step-5.json`.

**Disciplines.** phylax: the final manifest must cover every opened boundary
and cannot turn synthetic adapters into a live-network claim. ephoros: the demo
emits complete safe outcomes, counts, sizes, timings, digests, disclosure
states, and cleanup state with bounded cardinality. metron: none, final counts
and elapsed time are evidence that all rows ran, not a speed budget. elenchus:
every confirmed defect retains a parent-red, fixed-green hostile row and no
missing or skipped row can pass. hypomnema: ADR-042, the normative reference,
the skill contract, evolution ledger, and operator disclosure are reconciled;
the final proof explicitly preserves the #698/#699 dependency boundary.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Tests: Add golden accepted-job, canonical-policy, and policy-digest cases;
missing, extra, duplicate, null, boolean-as-integer, floating, negative, zero,
oversized, excessive-depth, invalid-Unicode, stale-digest, unknown-schema,
unknown-profile, model/profile disagreement, feature-enabled, content-log,
diagnostic-consent, data-class, lifetime, and hard-ceiling refusals. Verify
that key order does not change canonical bytes, every declared policy field
changes the digest, no credential field is representable, and old or future
versions refuse explicitly. The step audit runner contract is test command
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py {report}`,
report format `unittest-json-v1`, report file
`.elenchus/fiat-700-model-proxy-step-1.json`.

**Why.** The runner emits schema `elenchus.unittest.v1`, while the Elenchus CLI selects that parser with adapter id `unittest-json-v1`; the baseline field named the schema where the executable adapter id was required.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit broken. Step 3: entry holds; exit broken. Step 4: entry holds; exit broken. Step 5: entry holds; exit broken.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Tests: Cover one-byte fragmentation, every length-prefix split, two frames
in one read, incomplete and trailing bytes, zero and over-cap lengths, declared
versus actual length disagreement, invalid UTF-8, lone surrogates, duplicate
names, excessive depth/collections/strings/scalars, unknown or missing fields,
integer coercion, alternate operation/version, guest identities and sequence,
all forbidden provider features, deterministic response bytes, and bounded
sanitised errors. The step audit runner contract is test command
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py {report}`,
report format `unittest-json-v1`, report file
`.elenchus/fiat-700-model-proxy-step-2.json`.

**Why.** The runner emits schema `elenchus.unittest.v1`, while the Elenchus CLI selects that parser with adapter id `unittest-json-v1`; the baseline field named the schema where the executable adapter id was required.

**Steps touched.** Step 2.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit broken. Step 4: entry holds; exit broken. Step 5: entry holds; exit broken.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Tests: Cover exact request mapping, credential injection after admission,
credential-source failure, no credential in guest-visible or retained
surfaces, arbitrary scheme/host/port/path/method/model/header attempts,
guest-supplied authorization, CONNECT, every redirect class, DNS answer
changes, empty/multiple/special addresses, unpinned connection targets, TLS
hostname and certificate failure, chunked and content-length response floods,
unexpected encoding/status/type, duplicate/unknown/malformed response fields,
usage disagreement, raw error sanitisation, secret echo, and connection close.
The step audit runner contract is test command
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py {report}`,
report format `unittest-json-v1`, report file
`.elenchus/fiat-700-model-proxy-step-3.json`.

**Why.** The runner emits schema `elenchus.unittest.v1`, while the Elenchus CLI selects that parser with adapter id `unittest-json-v1`; the baseline field named the schema where the executable adapter id was required.

**Steps touched.** Step 3.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit broken. Step 5: entry holds; exit broken.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Tests: Cover exact and over-limit sequential and concurrent count, byte,
token, output, response, and concurrency reservations; rollback and terminal
paths; request floods; cross-job identity; second activation; absolute expiry
and expiry measured by `time.monotonic_ns()`; cancellation before admission and during transport; late
response suppression; completion/cancel/expiry races; unknown tokenizer;
provider-usage under/over-reporting; receipt count/size/schema/mode; duplicate
terminal events; symlink, directory, pre-existing target, restrictive umask,
short write, partial write, replacement, and unavailable sink failures; secret,
prompt, response, content-digest, raw URL/header/error/provider-id absence; and
operator-text/policy parity. The step audit runner contract is test command
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py {report}`,
report format `unittest-json-v1`, report file
`.elenchus/fiat-700-model-proxy-step-4.json`.

**Why.** The runner emits schema `elenchus.unittest.v1`, while the Elenchus CLI selects that parser with adapter id `unittest-json-v1`; the baseline field named the schema where the executable adapter id was required.

**Steps touched.** Step 4.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit broken.

### Amendment -- 2026-08-28

**What changed.** Complete replacement Tests: Add manifest schema, digest, completeness, uniqueness, order,
expected-outcome, and no-skips guards; one independent case for every hostile
acceptance item; positive-path policy/launch placeholders; exact safe summary;
canary and content-shape scans over guest frames, receipts, events, diagnostics,
argv, environment fixture, and produced tree; operator disclosure parity;
dependency-gated end-to-end status; old Phylax behaviour preservation; exact
skill/package version separation; evolution-axis preservation; marketplace and
portable-copy parity; and deterministic Horos currency. The step audit runner
contract is test command
`mise exec python@3.13.15 -- python3 plugins/hexaemeron/tests/run_tests.py {report}`,
report format `unittest-json-v1`, report file
`.elenchus/fiat-700-model-proxy-step-5.json`.

**Why.** The runner emits schema `elenchus.unittest.v1`, while the Elenchus CLI selects that parser with adapter id `unittest-json-v1`; the baseline field named the schema where the executable adapter id was required.

**Steps touched.** Step 5.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.
