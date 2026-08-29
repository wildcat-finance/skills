# Study: a job-scoped model inference proxy

Assuming, unless corrected:

1. The study starts from `main` at
   `7e449ba35e1519d28b33f06225c4c4137b548a23`; `HEAD`, local `main`, and
   `origin/main` resolved to that commit when the evidence was gathered on
   2026-08-28.
2. Issues [#698](https://github.com/wildcat-finance/skills/issues/698) and
   [#699](https://github.com/wildcat-finance/skills/issues/699) are dependency
   contracts, not delivered code. Both were open and unassigned when read.
3. The #698 implementation will eventually expose immutable accepted
   `jobspec/v1` bytes, their SHA-256 digest, the verified job identity and
   lifetime, and the inference-policy fields. This study does not choose the
   JobSpec signature or canonicalisation scheme for #698.
4. The #699 implementation will eventually expose one ordered, bounded guest
   byte stream for inference, a separate trusted-supervisor lifecycle channel,
   and a launch receipt bound to the accepted JobSpec digest. This study names
   an application protocol over that stream; it does not choose or implement
   the VM transport.
5. Version 1 of the proxy is text-only and non-streaming. Tools, remote URLs,
   uploads, files, images, audio, provider-side conversations, background
   execution, provider storage, dependency retrieval, and arbitrary headers
   are unavailable rather than conditionally passed through.
6. No live provider, deployment repository, credential source, or public pilot
   corpus has been selected. Component tests use a loopback provider fixture
   and a canary credential. A live adapter or pilot requires an explicit
   provider-specific decision and the later #705 evidence.
7. A policy field is mandatory unless the schema explicitly fixes it. The
   implementation must refuse a missing limit or unsupported value rather than
   inventing a permissive default.
8. Public-pilot prompts and responses are allowed only when the accepted
   JobSpec names an approved public-disclosure data class. Publication remains
   outside this issue and belongs to #704 and #705.

I proceed on these assumptions. A change to assumptions 2 through 8 changes
the study before it changes a runbook or implementation.

## 1. Problem statement

An untrusted, disposable worker needs model inference to complete a Fiat job,
but it must not receive a provider credential or regain general network access.
The operator needs a narrow disclosure channel whose destination, model,
method, schemas, limits, feature set, data class, lifetime, and receipts are an
exact, reviewable consequence of the accepted JobSpec.

The capability belongs to `hexaemeron:phylax`. Phylax already owns off-chain
URLs, secrets, model output, agent tools, provider disclosure, and bounded
requests. Ephoros supplies the signal contract used by the receipt design; it
does not become a second implementation owner. Protasis governs this study,
while Fiat remains unchanged because #702 separately owns the trusted
controller adapter.

The chosen prototype is one trusted proxy process per job, outside the guest.
It accepts an immutable activation from the trusted supervisor, compiles a
closed `model-proxy-policy/v1` from the already accepted JobSpec, binds that
policy to `jobspec_sha256`, and exposes only `model-request/v1` and
`model-response/v1` frames to the guest. The guest cannot select a URL, HTTP
method, model, provider header, credential, provider feature, retention mode,
or lifecycle action. A closed provider profile constructs the upstream request
and validates the upstream response. The proxy alone reads the credential and
injects it after policy, lifetime, and quota checks pass.

The capability decomposes into these ordered modules. They are runbook step
boundaries, not separately sufficient deliveries of #700.

| Module | Responsibility | Depends on | Observable proof |
| --- | --- | --- | --- |
| Policy contract | Strictly parse accepted JobSpec evidence, project the closed policy, and hash canonical policy bytes | A synthetic accepted-JobSpec fixture now; the #698 interface for integration | Golden policy bytes and digest; malformed or mismatched inputs refuse |
| Framing core | Parse one length-prefixed operation and emit one bounded normalised response | An abstract ordered byte stream; the #699 adapter later | Fragmented, concatenated, duplicate-key, deep, oversized, and unknown-field fixtures |
| Provider transport | Map the normalised operation through one pinned provider profile, inject the secret, hold a fixed TLS origin, reject redirects, and cap the raw response | Loopback HTTPS fixture now; a selected provider profile later | The fixture sees the expected credential while guest frames and records do not |
| Lifecycle, quotas, and receipts | Atomically reserve limits, enforce expiry and cancellation, discard late responses, and write bounded content-free records | Trusted supervisor control interface from #699/#702 for integration | Race, expiry, cancellation, receipt-failure, and cleanup tests |
| Hostile conformance and join | Exercise every #700 hostile case and bind proxy, JobSpec, and launch receipts by exact digests | All preceding modules; #698 and #699 for the real join | One manifest-driven command with a refusal/result record for every case |

`model-proxy-policy/v1` contains, at minimum, the schema id, job id,
`jobspec_sha256`, policy-compiler version, provider-profile id and version,
fixed HTTPS origin family and path family, operation, model, request and
response schema ids, approved data class, activation time, absolute expiry,
total wall deadline, every per-request and aggregate limit, disabled features,
content-log setting, diagnostic-consent state, and receipt-retention rule. The
canonical policy bytes contain no credential. `policy_sha256` is SHA-256 over
those bytes. Unknown fields, duplicate names, non-integer numeric limits,
unsupported Unicode forms, or a requested limit above an implementation or
provider-profile ceiling stop activation. Limits are rejected, not silently
clamped, so the digest describes what is actually enforced.

The guest protocol is deliberately smaller than a provider API. Each frame is
a four-byte unsigned big-endian byte count followed by strict UTF-8 JSON. The
length is checked against the accepted policy and a compiled ceiling before
allocation. JSON object names must be unique. The parser accepts only the
closed fields for a text request, applies explicit nesting, collection, string,
and scalar limits, and normalises no user-controlled URL or header into the
provider request. The proxy creates the request sequence number. Streaming and
multi-operation multiplexing are absent in version 1.

The provider-profile registry is trusted, versioned code. A profile fixes the
provider name, TLS hostname, port, path family, HTTP method, model, request
mapper, response parser, token-counter version, storage flags, disabled
features, credential source, and retention statement. At activation the proxy
resolves the fixed host, rejects private, loopback, link-local, multicast,
unspecified, documentation, and otherwise disallowed addresses, pins the
accepted address set, and keeps TLS hostname verification. The production
deployment also constrains the proxy process's egress to that address set and
port. Every 3xx response, `CONNECT`, alternate scheme or host, unexpected
content encoding, and unrecognised response shape is terminal for that
request. The proxy never follows an upstream redirect.

Quota accounting reserves a request number, request bytes, counted input
tokens, one concurrency slot, and the request's maximum possible output-token
and response-byte allowance atomically before disclosure. This prevents two
concurrent calls from each spending the last allowance. Input counting is done
by the exact, pinned provider-profile counter over the exact mapped provider
input. An unknown counter or model refuses the request. The provider's returned
usage is parsed and reconciled, but post-disclosure provider accounting is not
used as the sole preflight guard. A malformed or higher-than-reserved usage
value trips the job and no response reaches the guest.

Cancellation is a trusted-supervisor action, not a guest operation. It marks
the job terminal, closes an in-flight upstream exchange where the transport
allows, and always discards a late response. Expiry is the earlier of the
signed absolute JobSpec expiry and the elapsed-time deadline established at
activation. No new request begins at or after that point. A proxy restart does
not resume a job. Replay-nonce enforcement belongs to #698, but the proxy also
refuses a second activation for a live job id in its own process.

One bounded receipt is written for activation, one for each consumed request
sequence, and one for the terminal lifecycle event. Each record is capped at
4,096 UTF-8 bytes and the count is bounded by `max_requests + 2`. It carries
only the opaque job id, JobSpec and policy digests, proxy and profile versions,
model identifier, proxy-generated sequence, request and response byte counts,
input and output token counts, start/end times and duration, a fixed outcome
code, and the named limit or lifecycle cause. It carries no prompt, response,
content digest, raw URL, headers, credential, raw provider error, stack trace,
or provider request id. If the pre-disclosure receipt cannot be persisted, the
upstream call does not occur. If a terminal receipt cannot be persisted, the
response is withheld and the job stops with a bounded recovery marker.

Before launch, operator-facing text renders the immutable policy: provider,
destination family, model, data class, disabled features, storage and retention
settings, content-logging state, aggregate limits, and expiry. It also says
that the proxy constrains the allowed disclosure channel; it does not prove
that a provider will not retain, inspect, or exfiltrate disclosed content.

A working component prototype has this demo path:

1. Compile a golden accepted-JobSpec fixture into exact policy bytes and a
   stable digest, then start one proxy with a canary credential and loopback
   provider profile.
2. Connect a simulated guest through the abstract byte-stream adapter, submit
   one allowed text request, and receive one normalised response.
3. Show that the loopback provider received the credential, while the guest
   environment, frames, fixed diagnostics, receipts, and output tree contain
   neither the canary nor prompt or response bytes.
4. Run the hostile manifest, including URL, DNS-rebinding, redirect,
   credential-header, unsupported-method/model, oversized/deep payload, flood,
   cross-job identity, expiry, cancellation, and replay cases. Every case has a
   fixed refusal or terminal outcome.
5. Repeat with cancellation during an in-flight request and with expiry before
   a request; neither run releases a late response and both leave bounded
   terminal records.

The future end-to-end demo replaces only the synthetic accepted-JobSpec and
byte-stream adapters. It additionally requires the #698 acceptance receipt and
the #699 launch receipt to name the same JobSpec digest as the proxy activation
and terminal receipt. Any mismatch refuses before provider traffic.

The following criteria turn the requested result into checks:

- `SC-01`: a golden accepted JobSpec always produces byte-identical policy and
  digest; any source digest, policy field, compiler version, or golden byte
  change is visible.
- `SC-02`: a canary provider credential appears only at the loopback provider's
  trusted authentication boundary and never in the guest-visible or retained
  surfaces enumerated above.
- `SC-03`: only the profile's fixed provider, TLS hostname, path family, method,
  model, schemas, and data class can cross the boundary; all guest attempts to
  select or smuggle them refuse.
- `SC-04`: request count, bytes, tokens, concurrency, response bytes, and total
  wall time are enforced under concurrent as well as sequential calls.
- `SC-05`: tools, remote URLs, uploads, images, provider storage, redirects,
  and content diagnostics remain impossible in the no-consent profile.
- `SC-06`: cancellation and expiry stop admission, suppress late results, and
  produce exactly one terminal lifecycle outcome.
- `SC-07`: receipt count and size are bounded and no fixture content, content
  digest, credential, header, or raw provider error survives in them.
- `SC-08`: every hostile case named by #700 has an independently addressable
  fixture and expected outcome in the manifest.
- `SC-09`: the operator disclosure is derived from the same policy bytes and
  states provider retention and the non-exfiltration limitation.
- `SC-10`: end-to-end readiness is refused until #698 and #699 provide their
  exact interfaces and digest-bound evidence; component success is not
  reported as that join.

The focused proof command planned for the runbook is:

```bash
mise exec python@3.13.15 -- python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_phylax_model_proxy.py' -v
```

The final hostile demo command planned for the runbook is:

```bash
mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/phylax/scripts/model_proxy.py conformance --manifest plugins/hexaemeron/tests/fixtures/model-proxy-v1/manifest.json
```

Both commands can prove the component contract with synthetic adapters. They
cannot prove the #698/#699 join until those dependencies exist.

## 2. Prior art

### Current repository and programme state

There is no JobSpec verifier, isolated-worker launcher, vsock adapter, or model
inference proxy at the starting ref. Targeted searches for `JobSpec`, `vsock`,
model-proxy terms, common provider-key names, and inference-proxy terms found
no implementation. `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` builds
bounded delegation packets for Surveyor, Mason, Warden, and Scribe; its study
packet contains topic, target, base, and output path, not a signed JobSpec or a
runtime disclosure policy. That is evidence of the current boundary, not a
request to add proxy behaviour to Fiat.

Read-only GitHub code searches across public repositories in the
`wildcat-finance` organisation on 2026-08-28 returned no indexed match for
`vsock`, `"inference proxy"`, `OPENAI_API_KEY`, or `"model proxy"`. This is
negative evidence only for public indexed source; private, renamed, generated,
or unindexed code remains unknown.

The governing issue chain was read from GitHub on 2026-08-28:

- #698, `framework-29`, is open and owns signed, canonical `jobspec/v1`
  acceptance before launch. Its boundary says a signature authenticates bytes,
  not the truth of those bytes or authority to launch.
- #699, `framework-30`, is open, depends on #698, and owns the disposable guest,
  no host mount or secret, no NIC or general network, bounded scratch and
  resources, the small guest/host protocol carrier, and destruction evidence.
  It trusts the host and hypervisor and makes no TEE claim.
- #700, `framework-31`, is open and owns the trusted job-scoped inference
  proxy, exact policy, no guest credential, bounded content-free receipts,
  cancellation, expiry, provider disclosure, and the named hostile cases.
- #701 owns artifact collection and clean-tree verification; #702 owns the
  trusted Fiat supervisor/controller adapter; #703 owns reconciliation with
  ADR-028; #704 owns exact approval and fork-only publication; #705 owns the
  adversarial corpus, public patch-only pilot, and independent review. None is
  absorbed into this design.
- #706 is the Wave mu programme issue. It leaves provider, deployment
  repository, and several implementation choices undecided. A comment mentions
  an unadapted 60-specimen draft corpus but attaches no corpus and says it has
  not been run against Fiat. It is unavailable evidence, not an input to this
  prototype.

### Last two merged Phylax behaviour changes

The last two merged pull requests that changed Phylax behaviour were read in
full before drawing options:

- [PR #483](https://github.com/wildcat-finance/skills/pull/483), merged as
  `4eb656e9d3f8467d7500aa74288b016fe8091b03` on 2026-08-22, added the P008
  unsafe-deserialisation boundary. Four audit rounds fixed import-order,
  conflicting-identity, diagnostic-family, and bare-dynamic-name defects. Its
  accepted exclusions include `marshal.loads`, dynamic/wildcard/dotted import
  analysis, assignment and general scope/dataflow, custom-loader proofs, the
  pragma-in-string quirk, and a Python file-size policy. Those source-linter
  exclusions do not become proxy features and remain out of this work.
- [PR #480](https://github.com/wildcat-finance/skills/pull/480), merged as
  `fe3008c06a0a1a605f29b81a58468a09cdb95684` on 2026-08-22, added the
  credential-named subprocess-argv boundary. Its audit was clean within an
  exact source-local grammar. `API_TOKEN`, attributes and subscripts, assigned
  argv, star and keyword expansion, runner rebinding, and flag interpretation
  remain excluded. A runtime credential broker must not rely on that lexical
  check as its secret boundary.

[PR #666](https://github.com/wildcat-finance/skills/pull/666), merged later as
`68039a8756e60c7aae97439d1cce616c09986a24` on 2026-08-27, moved whole-tree
checker lints into a consolidated test. It changed test orchestration rather
than Phylax behaviour and carried no unfinished proxy work.

The two behaviour PRs advanced Phylax by generation while retaining its mature
frontier. That precedent supports a Phylax generation change for this new
normal behaviour; it does not reopen the held frontier or create a new
frontier job.

### Authoritative audit evidence

The required whole-set command ran from the target root and exited zero twice:

```bash
mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check /home/kethcode/wildcat/skills/tmp/fiat/fiat-700-proxy-model-traffic-without-giving-the-worke
```

It reported 25 of 25 source/view pairs current. The normal read mode was
therefore the verified synopsis. The authoritative root source is
`audit/AUDIT.md`, SHA-256
`c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa`;
the file actually read was `audit/AUDIT_SYNOPSIS.md`. Its in-scope Phylax
entries were:

- `Phylax TypeScript boundaries`, step 1, rounds 1 and 2: round 1 retains
  `[missing legacy field: audit-schema]`, `Covered`, `Not checked`, `Elenchus
  verdict`, and `Leads not pursued` as unknown; round 2 records zero findings
  and no leads while retaining the first four legacy fields as unknown.
- `Phylax credential argv`, step 1, round 1: `review-code`, `review-tests`, and
  `review-records` are clean. `audit-schema`, `Covered`, `Not checked`, and
  `Elenchus verdict` remain missing legacy fields. The exact lexical exclusions
  listed with PR #480 remain `Leads not pursued`.
- `Phylax unsafe deserialization`, step 1, rounds 1 through 4: findings
  `S1-R1-01`, `S1-R1-02`, `S1-R2-01`, and `S1-R3-01` are fixed and guarded;
  round 4 reports no new finding. Each entry retains the missing legacy fields
  `audit-schema`, `Covered`, `Not checked`, and `Elenchus verdict`. The exact
  exclusions listed with PR #483 remain `Leads not pursued`.

Those records neither implement nor reject a runtime inference proxy. Their
unresolved leads concern the static checker grammar, so this study leaves them
open rather than silently widening P008 or the credential-argv rule.

The Hexaemeron plugin source is `plugins/hexaemeron/audit/AUDIT.md`, SHA-256
`8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f`;
the file actually read was
`plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`. It contains two old controller
rounds: F-01 through F-09 are fixed, F-10 is accepted, and the listed
controller concurrency, symlinked-state atomicity, JSON ANSI, and Solidity
leads remain not pursued. All four legacy fields are missing. None answers the
proxy design or changes the issue ownership.

### External primary-source constraints

- Firecracker's
  [vsock documentation](https://github.com/firecracker-microvm/firecracker/blob/main/docs/vsock.md)
  maps guest AF_VSOCK connections to host Unix-domain sockets. It supports the
  assumption that #699 can furnish an ordered host/guest channel, but transport
  selection stays with #699.
- [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) defines CONNECT as a
  tunnel and describes redirect semantics. These are the reasons version 1 is
  not a general HTTP proxy, does not expose CONNECT, and refuses all redirects.
- [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html) notes the
  interoperability problem with non-unique object names. The proxy makes
  uniqueness a rejection rule rather than accepting parser-dependent meaning.
- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html) is prior art for
  deterministic JSON hashing. The policy format may use its compatible subset,
  while JobSpec canonicalisation remains a #698 decision.
- OpenAI's official
  [OpenAPI repository](https://github.com/openai/openai-openapi),
  [Responses API guide](https://github.com/openai/openai-node/blob/main/docs/responses.md),
  and [endpoint data-control documentation](https://platform.openai.com/docs/models/default-usage-policies-by-endpoint)
  show a broad request surface including tools, files, images, conversations,
  and storage-dependent retention. They support a closed adapter and explicit
  retention disclosure; they do not select OpenAI as the provider.
- Anthropic's official
  [API retention description](https://privacy.anthropic.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)
  and [zero-data-retention scope](https://privacy.anthropic.com/en/articles/8956058-i-have-a-zero-data-retention-agreement-with-anthropic-what-products-does-it-apply-to)
  likewise show that retention depends on the service and enabled features.
  They support a versioned provider profile; they do not select Anthropic.

## 3. Constraints and non-goals

The starting ref is `main` at
`7e449ba35e1519d28b33f06225c4c4137b548a23`. The repository pins Python
3.13.15 in `.python-version`, and every Python command uses
`mise exec python@3.13.15 -- python3`. The implementation should use the
standard library unless a provider-specific tokenizer or transport dependency
is justified, pinned, reviewed, and recorded before it enters a runbook.

The following constraints are unconditional for version 1:

- The guest has no provider credential, general IP path, DNS resolver, host
  mount, host socket, or provider-native API. #699 must establish the guest
  half of this constraint; #700 establishes the proxy half.
- The trusted supervisor, not the guest, supplies accepted JobSpec evidence,
  activates the policy, cancels the job, and closes the proxy.
- Policy derivation is deterministic and bound to exact accepted-JobSpec bytes
  and digest. The guest cannot submit, amend, or select a policy.
- Provider destination, endpoint family, HTTP method, model, request mapper,
  response parser, tokenizer, and retention profile are a closed, versioned
  registry. An unknown value refuses activation.
- All size, token, count, concurrency, and time fields are required positive
  integers within a documented hard ceiling. Booleans are not integers for
  this purpose; floating point and coercion are rejected.
- Parsing and accounting occur before allocation or disclosure wherever
  possible. Provider responses are bounded while reading, before JSON parsing.
- Content logging is off. Diagnostic capture requires a separate, explicit
  consent field, an approved data class, a smaller bound and retention, and an
  operator-visible disclosure. The prototype implements only the off state.
- The raw credential is read through a trusted host credential source after
  activation. It never appears in argv, the guest environment, frames,
  receipts, diagnostics, exception text, or an output artifact.
- A request rejected before disclosure still consumes a proxy-generated
  sequence and a bounded refusal receipt, preventing free floods and ambiguous
  gaps.
- Cancellation, expiry, quota exhaustion, receipt-sink failure, malformed
  upstream data, or policy mismatch fail closed. Partial upstream disclosure is
  recorded as such; it is never rewritten as “not sent.”

This prototype does not:

- implement or choose the JobSpec signature scheme, nonce store, issuer trust,
  or truth of the claims in #698;
- build, launch, network, or attest the VM in #699;
- fetch dependencies, repositories, issue content, URLs, or artifacts through
  the inference channel;
- modify Fiat delegation or controller state, which belongs to #702;
- verify or export worker artifacts, reconcile ADR-028, publish a branch or PR,
  run a public pilot, or perform independent programme review, which belong to
  #701 and #703 through #705;
- provide a generic forward proxy, CONNECT tunnel, provider SDK inside the
  guest, arbitrary model gateway, streaming API, multi-modal API, tool call,
  remote-content fetch, file upload, conversation store, or background job;
- claim confidential computing, protection from a hostile host or hypervisor,
  or non-exfiltration by the selected provider;
- retain prompts, responses, content hashes, raw provider errors, or provider
  request identifiers as receipts;
- promise exact token accounting for an unselected model. A live profile is
  unavailable until its counter and mapping are pinned; absence refuses rather
  than estimates;
- make the unprovided 60-specimen draft corpus from #706 into evidence.

A provider, deployment environment, credential source, live retention tier, or
diagnostic-capture request is an ask-first decision because it changes the
disclosure surface and operator promise. The loopback component proof does not
need those choices.

## 4. Design options

### Option A: job-scoped normalised protocol with closed provider profiles

Run one small trusted process per job. Derive and hash a closed policy from
accepted JobSpec evidence, accept only a narrow framed text operation, and map
it through a versioned provider profile. Keep lifecycle control separate from
guest data. This adds an adapter for each provider/model family, but makes the
guest grammar, secret crossing, destination, storage features, receipts, and
quotas directly testable. Cross-job memory and accounting disappear when the
process exits.

### Option B: allowlisted HTTP forward proxy

Allow the guest to send provider-shaped HTTP to an allowlisted origin. This is
quick to connect to existing SDKs, but leaves provider headers, paths, request
features, storage flags, URL-bearing fields, redirects, and schema drift under
guest influence. Preventing CONNECT and host changes does not make an
otherwise broad provider body safe. The audit surface becomes the whole
provider API and every SDK update.

### Option C: short-lived provider token inside the guest

Mint or exchange a job-limited token, give it to the guest, and permit direct
provider egress. Where a provider supports narrow ephemeral tokens this removes
the request mapper, but it directly violates #700's no-provider-credential
guest promise, makes #699's no-general-network proof harder, and still exposes
provider-native features and retention controls. Provider support is neither
uniform nor selected.

### Option D: shared multi-tenant model gateway

Place a managed multi-provider gateway outside the workers and allocate a
tenant or route per job. This may later provide fleet-level operations, but a
prototype inherits the gateway's administrative API, logging defaults,
credential store, cross-job cache and counters, provider breadth, and upgrade
cadence. A shared process also makes cross-job identity and cancellation bugs
more consequential. A future gateway can sit behind the same closed provider
profile only after equivalent evidence exists.

Option A is chosen. It is the smallest construction whose guest-visible
surface can express the one required operation while enforcing every #700
dimension. Its named trade is provider-specific adapter work and reduced API
flexibility. That cost is preferable to moving a provider API, secret, or
general network path into the untrusted guest. Option B is rejected for
unbounded semantics, option C for violating the central credential boundary,
and option D for avoidable multi-tenant and operational scope.

## 5. Risk register seed

Each id below is an audit obligation. A later round records it as reviewed or
not applicable; related prose does not merge two ids into one verdict.

```risk-register
jobspec-substitution | trusted supervisor activation into policy compilation | the proxy recomputes and binds the exact accepted JobSpec digest and refuses a substituted job or policy
policy-derivation-drift | accepted JobSpec fields into canonical policy bytes | golden vectors pin every included field compiler version canonical byte and policy digest
transport-confusion | guest byte stream into the framed operation parser | partial combined trailing and out-of-order frames cannot create a second meaning
frame-exhaustion | untrusted length prefix before allocation | declared and actual sizes are capped before allocation and truncated frames end the job
schema-smuggling | untrusted JSON into the normalised request | duplicate names unknown fields invalid UTF-8 excessive depth and unsupported scalar forms refuse
credential-crossing | trusted credential source through upstream authentication | the canary reaches only the provider fixture and never guest frames records errors argv environment or artifacts
origin-confusion | provider profile through URL construction and TLS | scheme host port path method and hostname verification are fixed by one versioned profile
dns-rebinding | fixed hostname through resolution and connection | special addresses refuse resolution is pinned for the job and egress admits only the pinned set
redirect-tunnel | upstream HTTP response before any follow-up request | every redirect and CONNECT-like path refuses without a second connection
feature-escape | normalised request into provider-native request fields | tools URLs files images storage background and unrecognised fields cannot be emitted by the adapter
quota-race | concurrent request admission against shared counters | atomic reservation prevents count byte token response and concurrency overspend
token-undercount | provider mapping and tokenizer before disclosure | the pinned profile counts the exact mapped input reserves maximum output and refuses an unknown counter
cancellation-race | trusted cancellation against admission and in-flight I/O | no request starts after cancellation and every late response is discarded before guest release
expiry-replay | signed wall expiry and elapsed-time lifetime against later frames | activation and every admission check both clocks and a restart cannot resume the job
response-flood | untrusted upstream body before parsing | the transport stops reading at the response-byte cap and never allocates or logs the excess
response-schema | upstream JSON into the normalised guest response | duplicate unknown malformed and usage-inconsistent fields stop the request without forwarding raw data
cross-job-state | job identity across process counters receipts and lifecycle | one process serves one digest and cross-job ids or second activation attempts refuse
receipt-content | request processing into retained evidence | receipts use an allowlisted schema and fixtures prove no content digest secret header raw URL or raw error survives
diagnostic-consent | any proposed content capture into logs or support output | the no-consent profile has no capture path and a future path requires a new policy and operator disclosure
provider-retention | policy profile into operator-facing disclosure | storage settings retention tier and feature exceptions are versioned and rendered before launch
provider-exfiltration | allowed content disclosure to an external provider | the claim stays limited to channel control and tests never assert provider non-retention or non-exfiltration
dependency-smuggling | guest content through the inference operation | remote references tools and retrieval forms refuse and dependency access remains a separate channel
partial-receipt | upstream disclosure and response release around receipt writes | preflight receipt failure prevents disclosure and terminal receipt failure withholds output and stops the job
secret-response-echo | provider response into guest-visible content | raw and normalised output are checked for the exact secret canary before release and the limitation against encoded leakage is documented
cleanup-gap | terminal lifecycle into process and secret destruction | cancel expiry quota failure and normal completion close connections erase references and terminate the per-job process
```

The exact-secret response check is an extra containment measure, not a proof
against arbitrary encoding or transformation by a hostile provider. The
disclosure statement and audit verdict must retain that limit.

## 6. Glossary seeds

**Accepted JobSpec.** The exact `jobspec/v1` bytes that #698 has authenticated
and accepted, plus their SHA-256 digest; the proxy does not perform that
acceptance on guest input.

**Activation.** The trusted-supervisor operation that supplies accepted
JobSpec evidence and starts one policy-bound proxy process.

**Allowed disclosure channel.** The one fixed provider operation permitted by
the policy. It is not a claim about what the provider does after receipt.

**Content-free receipt.** A bounded record containing allowlisted identifiers,
sizes, counts, timing, versions, digests, and outcome codes, but no prompt,
response, content digest, raw URL, header, credential, or raw error.

**Guest.** The credential-free, no-general-network disposable worker owned by
#699.

**Normalised request.** The closed, provider-independent text operation the
guest can frame; it has no URL, method, model, header, tool, file, or storage
field.

**Policy compiler.** Trusted, versioned code that projects the accepted
JobSpec into canonical `model-proxy-policy/v1` bytes.

**Policy digest.** SHA-256 over the exact canonical policy bytes, recorded with
the JobSpec digest in every lifecycle and request receipt.

**Provider profile.** Trusted, versioned code and data fixing one provider
origin family, operation, model, schemas, mapper, parser, token counter,
storage flags, retention statement, and credential source.

**Request sequence.** A strictly increasing number assigned by the proxy
before validation; it is not accepted from the guest or provider.

**Supervisor channel.** The separate trusted path for activation,
cancellation, expiry, and shutdown. It is not multiplexed with guest request
frames.

**Terminal outcome.** One fixed lifecycle result after which the proxy admits
no request: completed, cancelled, expired, quota-exhausted, policy-failed,
receipt-failed, upstream-failed, or killed.

## 7. Sources

Repository sources are relative to the target root unless an absolute path is
shown.

- Root contracts: `AGENTS.md`; `PROMISE_MACHINE.md` (`promise-machine/v1`);
  `.agents/skills/promise-machine/SKILL.md`; `.horos/boundary.json`;
  `plugins/hexaemeron/AGENTS.md`.
- Active Fiat contract:
  `/home/kethcode/.codex/plugins/cache/wildcat-labs/hexaemeron/1.6.5/skills/fiat/SKILL.md`,
  version 5.30.1, SHA-256
  `b133f4c438d786f4e32d6cf92fe0c7acf473a4a74d00a52928ce6ef345918611`.
- Active Protasis contract:
  `/home/kethcode/.codex/plugins/cache/wildcat-labs/hexaemeron/1.6.5/skills/protasis/SKILL.md`,
  version 4.8.0, SHA-256
  `95a5fa7f10d56d18c40939414ac8006bfc0de18ef075ee7231754aab7025dde2`.
- Active discipline contracts at the same plugin version: Phylax 1.3.0,
  SHA-256 `b8943913d56225bdf983f56cec226946168219a401516fcd795a17760f29087f`;
  Ephoros 1.2.0, SHA-256
  `2017fda2b5bbbea04a69cae4f30d16813114338ad5af47038da1ff2e98772407`;
  Metron 1.1.0, SHA-256
  `27ba8a8d3608d16264d8cacdeb4f7d46793d5ebc78a4488c763d3cb16a6c0d57`;
  Elenchus 1.3.0, SHA-256
  `33f93bd43eb63027de420e21fb312eddae46904fcdd8aefe3766b607d8f1cc2c`;
  Hypomnema 4.6.0, SHA-256
  `997b3273161cd9f55c6d1d5cc023ae289332c5cf87b81962045f8fb72cb8f3b3`.
- Active Imprimatur contract:
  `/home/kethcode/.codex/plugins/cache/wildcat-labs/hexaemeron/1.6.5/skills/imprimatur/SKILL.md`,
  version 2.3.0, SHA-256
  `39c0b5d75af6d80dcbb8322150d4825b3aa73285ce58fa96bcc85df92d62c59a`.
- Current implementation and ledgers:
  `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`;
  `plugins/hexaemeron/skills/phylax/SKILL.md`;
  `plugins/hexaemeron/skills/phylax/EVOLUTION.md`;
  `plugins/hexaemeron/skills/ephoros/SKILL.md`;
  `plugins/hexaemeron/skills/protasis/EVOLUTION.md`;
  `docs/hexaemeron-checkpoint-programme-study.md`.
- Audit read mode and sources: `audit/AUDIT_SYNOPSIS.md` for
  `audit/AUDIT.md` at source SHA-256
  `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa`;
  `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` for
  `plugins/hexaemeron/audit/AUDIT.md` at source SHA-256
  `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f`.
  The whole-set currency result was 25 of 25 current on 2026-08-28.
- Prior studies: `docs/phylax-credential-argv/study.md` and
  `docs/phylax-unsafe-deserialization/study.md`.
- GitHub issues, API bodies retrieved 2026-08-28. The following SHA-256 values
  are over each API-returned body encoded as UTF-8 without an added newline:
  [#698](https://github.com/wildcat-finance/skills/issues/698) updated
  `2026-08-28T01:05:09Z`,
  `76c2043bede85674acfec08a4326e64c203d3e540860b4faa93b2e2e89ae5d2a`;
  [#699](https://github.com/wildcat-finance/skills/issues/699) updated
  `2026-08-28T01:05:11Z`,
  `fa852d0d9e06863262ac8f8a709e51f23b5c7c0784f0cadfaca26e1440177534`;
  [#700](https://github.com/wildcat-finance/skills/issues/700) updated
  `2026-08-28T01:05:12Z`,
  `24110d3086bb418afe06cc69ca2fd4d37c9ca253c5c7e9bb9949da48b29a86da`;
  [#701](https://github.com/wildcat-finance/skills/issues/701) updated
  `2026-08-28T01:05:14Z`,
  `e388e6247f06f7184726f2f7644f111095729205cdd48b812cd2c180afff25ec`;
  [#702](https://github.com/wildcat-finance/skills/issues/702) updated
  `2026-08-28T01:05:16Z`,
  `75791e2ae4672f2be6924c565c82d004029557192d122dc1670006cf6fff34db`;
  [#703](https://github.com/wildcat-finance/skills/issues/703) updated
  `2026-08-28T01:05:17Z`,
  `fbefcb46d0b8aa2659433ba3a5abce4e910b53c46f47e02492b56d1d2d3f76e7`;
  [#704](https://github.com/wildcat-finance/skills/issues/704) updated
  `2026-08-28T01:05:19Z`,
  `e42b7af71a0baaccf244362ef9e28e1a7576e36f582d3446a4bcec15f7369344`;
  [#705](https://github.com/wildcat-finance/skills/issues/705) updated
  `2026-08-28T01:05:20Z`,
  `cd099ee5674b78f68e87860ff3c5785058f04ae2377f110d407fae9a081afe38`;
  [#706](https://github.com/wildcat-finance/skills/issues/706) updated
  `2026-08-28T02:29:09Z`,
  `5dc2e06f29747ac3268693e415bc779b64213056985023d6f63a10f4f1d87f21`.
- Merged pull requests:
  [#483](https://github.com/wildcat-finance/skills/pull/483), merge
  `4eb656e9d3f8467d7500aa74288b016fe8091b03`;
  [#480](https://github.com/wildcat-finance/skills/pull/480), merge
  `fe3008c06a0a1a605f29b81a58468a09cdb95684`;
  [#666](https://github.com/wildcat-finance/skills/pull/666), merge
  `68039a8756e60c7aae97439d1cce616c09986a24`.
- External primary sources, accessed 2026-08-28: Firecracker
  [vsock](https://github.com/firecracker-microvm/firecracker/blob/main/docs/vsock.md);
  [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html);
  [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html);
  [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html); OpenAI
  [OpenAPI](https://github.com/openai/openai-openapi),
  [Responses](https://github.com/openai/openai-node/blob/main/docs/responses.md),
  and [data controls](https://platform.openai.com/docs/models/default-usage-policies-by-endpoint);
  Anthropic [retention](https://privacy.anthropic.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)
  and [zero-data-retention scope](https://privacy.anthropic.com/en/articles/8956058-i-have-a-zero-data-retention-agreement-with-anthropic-what-products-does-it-apply-to).

## 8. Signals, and the questions behind them

This answer is governed by the active
`hexaemeron:ephoros` contract cited in section 7. It defines the signal shape;
this study fixes only the questions and source events.

1. **Why did request sequence N stop, and did any content reach the provider?**
   The policy/framing and provider-transport steps emit one fixed
   `model_proxy.request_terminal` event with job and policy digests, sequence,
   outcome code, disclosure state (`none`, `started`, or `completed`), byte and
   token counts, and duration. It contains no content or raw error.
2. **Which quota or lifecycle edge is preventing new work?** The lifecycle
   step emits bounded gauges for reserved and completed request count, bytes,
   tokens and concurrency, plus remaining wall time and one
   `model_proxy.lifecycle_terminal` event naming cancellation, expiry, quota,
   receipt failure, kill, or normal completion.
3. **Is the fixed upstream operation healthy without exposing its traffic?**
   The provider step emits bounded counters by provider-profile version,
   outcome family and latency bucket. Host, URL, headers, provider request id,
   prompt, response, and raw error are absent. A profile id is the correlation
   key.
4. **Did cleanup and evidence finish after the guest stopped?** The lifecycle
   and join steps emit one terminal record with connection-close result,
   credential-reference release, process exit, receipt count and aggregate
   receipt bytes, joined to JobSpec, launch and policy digests.

Metric labels are closed enums or version identifiers. Job id and request
sequence belong in structured events, not metric labels. Receipt and event
emission are bounded by the policy. Alerts, if later deployed, point to a
runbook that distinguishes pre-disclosure refusal, partial disclosure,
provider failure, and evidence failure; no alert contains model content.

## 9. Boundaries, per capability

This inventory is governed by the active `hexaemeron:phylax` contract cited in
section 7.

| Capability boundary | What is worth taking | Control that closes it |
| --- | --- | --- |
| Supervisor to activation | Accepted JobSpec bytes and digest, verified job identity and lifetime | Separate trusted channel; strict schema; recompute digest; deterministic projection; second activation refuses |
| Guest to frame parser | One bounded text operation | Length cap before allocation; strict UTF-8 and unique-name JSON; closed fields; nesting and collection caps; one operation per frame |
| Parser to policy | Request content only | Provider, endpoint, method, model, schemas, data class and features come only from immutable policy |
| Policy to credential source | A profile-specific authentication value | Read only after admission; no argv or serialisation; fixed header construction; zero retained references at termination |
| Proxy to name resolution and network | One fixed TLS origin family | Reject special addresses; pin resolved set; retain hostname verification; constrain process egress; no guest DNS or URL |
| HTTP response to redirect handling | Nothing from a 3xx response | Automatic redirects disabled; every redirect is a fixed refusal; CONNECT is absent |
| Request mapper to provider API | The profile's exact normalised text payload | Closed mapper; fixed storage-off fields; no tools, URLs, uploads, images, conversations, background work or unknown fields |
| Provider body to response parser | At most the configured response bytes and closed content/usage fields | Incremental byte cap before parse; strict schema; usage reconciliation; no raw pass-through |
| Provider response to guest | Normalised content and bounded usage only | Secret-canary check; policy/lifecycle recheck; terminal receipt succeeds before response release |
| Concurrent requests to counters | Reserved count, byte, token, response and concurrency allowance | One atomic reservation and release path; rejected requests consume a sequence; maximum output is reserved in advance |
| Trusted lifecycle to in-flight request | Cancel, expiry or kill | Terminal flag precedes socket close; no new admission; late response discarded; one terminal outcome |
| Request path to receipts and signals | Content-free identifiers, counts, timings, versions and outcome enums | Allowlisted schema; 4,096-byte event cap; bounded count; no content-derived hash or raw diagnostic |
| Receipt sink to guest release | Durable terminal evidence | Preflight failure prevents disclosure; terminal failure withholds result and stops job; recovery marker is bounded |
| One job to another | Nothing | One proxy process and one immutable JobSpec digest per job; guest-supplied job identities refuse |
| Inference to dependency access | Nothing | Remote references, tools and retrieval fields refuse; a separate future channel must own dependency acquisition |
| Operator to disclosure consent | Provider, data class, retention and disabled-feature acknowledgement | Disclosure rendered from policy before launch; absent or mismatched approval refuses a public pilot |

The proxy cannot close the provider's internal trust boundary. TLS, destination
pinning and request shaping prove which allowed channel was used, not what the
provider did with disclosed content. The operator text, audit, and final claim
must keep that qualification.

## 10. The budget, or its absence

This answer is governed by the active `hexaemeron:metron` contract cited in
section 7.

There is no performance-optimisation target for the prototype. External model
latency is provider-dependent and no provider has been selected, so a p95 speed
claim would be invented. Request count, bytes, tokens, concurrency, response
bytes, and total wall time are security and resource ceilings taken from the
accepted JobSpec and checked for exact refusal behaviour; they are not a claim
that the proxy is faster.

The exact command that measures the component's limit behaviour is:

```bash
mise exec python@3.13.15 -- python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_phylax_model_proxy.py' -v
```

The test record reports configured ceilings, attempted values, peak observed
concurrency, elapsed time from a process clock unaffected by wall-clock
adjustments, and the terminal outcome for deterministic
loopback cases. It must not treat a shortened or killed test as a passing
measurement. If a later step proposes a speed improvement, that step first
records a Metron baseline and a provider-independent budget using the same
fixture and machine description.

## 11. The fail-closed posture

This answer is governed by the active `hexaemeron:elenchus` contract cited in
section 7.

Activation stops before a credential read or provider connection when accepted
JobSpec evidence is absent, its digest does not match, policy projection fails,
a required field or limit is absent, an enum or provider profile is unknown,
the policy bytes do not match their digest, the job is expired, a second live
activation exists, or the preflight receipt cannot be persisted.

A request stops before disclosure on a bad frame, duplicate or unknown JSON
name, invalid UTF-8, excessive nesting or size, unsupported operation, model or
method selection, URL/header/credential smuggling, disabled feature, exhausted
or unreservable quota, cancellation, or expiry. Resolution to a disallowed
address, a connection outside the pinned set, TLS failure, redirect, unexpected
content encoding, oversized response, malformed provider schema, inconsistent
usage, secret canary in the response, or terminal-receipt failure stops the
request. Raw provider data never becomes the error returned to the guest.

Cancellation and expiry are terminal. The proxy sets the terminal state before
closing I/O, admits no new request, discards a late response, writes the fixed
outcome if possible, releases credential references, closes connections, and
exits. A terminal receipt failure preserves a small content-free recovery
marker but does not release the model response. A process crash is not called
clean completion; the supervisor must record it, and restart requires a fresh
accepted job rather than resuming counters from inference.

Every defect fix follows the Elenchus guard convention: preserve the failing
frame, policy, lifecycle schedule, or loopback-provider behaviour as the
smallest content-safe fixture; first show the focused test fail for the claimed
cause; repair the cause; then show that test and the complete model-proxy suite
pass. Secret and content fixtures use synthetic sentinels. The report records
red and green commands, exit codes, test counts, and the stable risk id. A
timeout, partial dot stream, missing receipt, or unexecuted hostile-manifest row
is not a pass.

## 12. Decisions and their homes

This answer is governed by the active `hexaemeron:hypomnema` contract cited in
section 7.

The following decisions are expensive enough to preserve:

- The cross-cutting decision to use a one-process-per-job normalised protocol,
  not a generic HTTP proxy, guest credential, or shared gateway, belongs in a
  new `docs/decisions/ADR-042-*.md`. ADR-041 is the highest existing decision
  number at the starting ref. The ADR records the trust boundary, rejected
  alternatives, digest join, provider non-exfiltration limitation, and
  replacement conditions.
- The normative wire grammar, policy schema, canonicalisation subset, provider
  profile requirements, receipt schema, fixed outcome codes, hard ceilings,
  and version-negotiation rule belong in
  `plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md`. Golden policy
  and frame bytes belong beside the test fixtures under
  `plugins/hexaemeron/tests/fixtures/model-proxy-v1/`.
- The public Phylax ownership promise and operator workflow belong in
  `plugins/hexaemeron/skills/phylax/SKILL.md`. The normal behaviour change is a
  generation update to Phylax 1.4.0 in
  `plugins/hexaemeron/skills/phylax/EVOLUTION.md`, retaining its mature frontier
  and existing frontier digest. It does not use `--frontier` and does not alter
  the unrelated held job.
- The implementation belongs under
  `plugins/hexaemeron/skills/phylax/scripts/model_proxy.py` and a small
  `model_proxy_lib/` package, with focused tests in
  `plugins/hexaemeron/tests/test_phylax_model_proxy.py`. Provider profiles are
  code-reviewed modules, not mutable guest or JobSpec URLs.
- Operator disclosure examples and the provider-profile retention inventory
  belong with the normative Phylax reference. An operational alert runbook is
  created under `docs/runbooks/` only when an actual alert is deployed; an
  unmonitored component test does not invent an on-call document.
- The #698 and #699 integration contract belongs in their implementations and
  the final hostile-conformance manifest. The join records exact JobSpec,
  launch and policy digests; this issue does not copy their signature or VM
  specifications.
- The study and future runbook are Fiat run inputs, not durable architecture
  records. The ADR, Phylax reference, public skill contract, generation row,
  executable fixtures, and terminal receipts are the durable homes.

Protasis readiness is therefore conditional but sufficient for planning: this
study fixes the component design, module order, success checks, ownership, and
dependency interface. A runbook may implement and audit the loopback component
without a live credential. The runbook must mark the #698/#699 join and any live
provider adapter as dependency-gated exits, and it must not claim full #700
end-to-end delivery while either issue is open or its named evidence is absent.
