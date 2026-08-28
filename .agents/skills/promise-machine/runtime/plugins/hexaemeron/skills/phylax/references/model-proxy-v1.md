# Model proxy policy version 1

## Status and scope

This reference is normative for `model-proxy-policy/v1`, its synthetic
accepted-job adapter, and the provider-independent version-1 guest framing
grammar. It also fixes the synthetic provider mapping and the standard-library
HTTPS connector used to test that mapping without a live provider. It defines
the job-scoped runtime, atomic quota ledger, cancellation and expiry rules,
content-free receipt file, and operator disclosure. The final hostile-
conformance manifest is a later boundary.

The implementation is the standard-library CLI at `../scripts/model_proxy.py`
and the library under `../scripts/model_proxy_lib/`. Golden and refusing
vectors are under
[`tests/fixtures/model-proxy-v1`](../../../tests/fixtures/model-proxy-v1/).
The architectural reason is recorded in
[ADR-042](../../../../../docs/decisions/ADR-042-use-a-job-scoped-model-proxy.md).

## Vocabulary

**Accepted-job evidence.** A closed synthetic envelope carrying exact JobSpec
bytes, their claimed SHA-256 digest, and the verified job identity and time
bounds supplied by a trusted supervisor.

**Exact JobSpec bytes.** The decoded bytes in `jobspec_b64`. Their byte order,
whitespace, and final newline are significant to `jobspec_sha256`. The
compiler does not claim that this is the canonicalisation chosen by the future
JobSpec verifier.

**Policy compiler.** `phylax-model-proxy-compiler/v1`, the deterministic
projection from accepted-job evidence and one code-owned profile into policy
bytes.

**Provider profile.** An immutable code record fixing the provider family,
origin family, path family, method, operation, model, request and response
schemas, token counter, storage setting, retention statement, allowed data
classes, and ceilings.

**Policy bytes.** The canonical JSON bytes of the projected policy, without a
trailing newline. A policy file and CLI output add one line feed after those
bytes. `policy_sha256` is computed before that line feed is added.

**Synthetic boundary.** A component adapter whose origin ends in `.invalid`
and whose transport and resolver are injected by tests. It cannot resolve or
send a live provider request in the component vectors.

**Provider credential.** A value read from the profile-owned environment name
only after the provider session has accepted the exact guest request object.
The value enters the fixed authentication header and no policy, request body,
event, diagnostic, guest response, receipt, argument, or retained snapshot.

**Pinned HTTPS connector.** The direct standard-library connector that resolves
the fixed profile hostname once, accepts one global address, opens TLS to that
address with the fixed hostname, and rejects a peer that differs from the pin.
It has no proxy, CONNECT, or redirect machinery.

**Lifecycle runtime.** One in-memory instance bound to one replayed policy,
job id, and accepted JobSpec digest. It has no loader or resume operation.

**Atomic reservation.** One lock-held decision that either reserves every
resource needed before provider disclosure or reserves none of them.

**Content-free receipt.** One bounded canonical JSON line containing only the
closed receipt vocabulary. It carries job and policy identity, fixed versions,
counts, timings, disclosure state, and an outcome code, but no model content or
provider authority.

## Accepted-job evidence

The compiler reads at most 98,304 bytes from one stable regular file without
following its final symlink. It opens the candidate nonblocking and checks its
kind before reading, so a FIFO or other special file cannot hold activation
open. The root object has exactly four fields:

| Field | JSON type | Version-1 rule |
| --- | --- | --- |
| `schema` | string | Exactly `accepted-job/v1` |
| `jobspec_b64` | string | Canonical padded base64 of no more than 32,768 decoded bytes |
| `jobspec_sha256` | string | Lowercase SHA-256 of the exact decoded bytes |
| `verified` | object | The closed acceptance object below |

`verified` has exactly `schema`, `job_id`, `accepted_at`, and `expires_at`.
Its schema is `jobspec-acceptance/v1`. Times are UTC second timestamps ending
in `Z`. The verified job id and expiry must equal the values inside the
decoded JobSpec. Expiry must be later than acceptance and no more than 3,600
seconds later.

The decoded JobSpec is strict JSON and has exactly `schema`, `job_id`,
`expires_at`, and `model_proxy`. Its schema is `jobspec/v1`. `job_id` is an
ASCII lower-case opaque identifier of at most 64 characters, using letters,
digits, dot, `_`, and hyphen.

`model_proxy` has exactly these fields:

- `schema`, fixed to `model-proxy-request/v1`;
- `provider_profile`, `model`, `operation`, `request_schema`, and
  `response_schema`, all required to match one code-owned profile;
- `data_class`, required to be admitted by that profile;
- `features`, with every name in the closed feature set present and `false`;
- `content_logging` and `diagnostic_consent`, both exactly `false`;
- `receipt_retention_seconds`, a positive integer no greater than 86,400; and
- `limits`, containing every limit in the hard-ceiling table and no other
  field.

There are no defaults. Missing, extra, duplicate, null, floating-point,
boolean-as-integer, negative, zero, non-NFC, format-control, surrogate, or
unknown values refuse.

## Strict JSON and canonical JSON

Both accepted-job and decoded JobSpec bytes are strict UTF-8 JSON. Parsing is
bounded at 12 object or array levels, 512 total members, 1,024 scalar values,
and 65,536 UTF-8 bytes per string. Duplicate object names and non-finite or
floating-point numbers refuse. Strings must be NFC and may not contain Unicode
control, format, surrogate, line-separator, or paragraph-separator code
points.

The canonical policy subset contains only objects, arrays, NFC strings,
booleans, null where a future schema explicitly admits it, and integers in
the interoperable range from negative 9,007,199,254,740,991 through positive
9,007,199,254,740,991. Every object name is an NFC string under the same
Unicode limits; another key type refuses rather than reaching the serializer.
Policy version 1 emits no null or negative value. Object names are sorted by
their Unicode scalar sequence. JSON is encoded as UTF-8 with no insignificant
whitespace, no ASCII escaping for ordinary Unicode, and no trailing newline.
Arrays preserve their declared order.

## Guest frame grammar

The guest sends an ordered byte stream. Each frame is a four-byte unsigned
big-endian length followed by exactly that many payload bytes. A zero length
refuses. A length above the compiled `max_request_bytes` refuses as soon as the
fourth prefix byte arrives, before the core creates a payload buffer. The
compiled policy bytes, digest, profile mapping, and every limit ceiling are
rechecked before the core accepts any stream bytes. The compiler result keeps
the exact bounded accepted-job evidence as non-rendered activation material;
framing replays the compiler from those bytes and requires every projected
policy field and digest to match. Self-consistent replacement fields in a
public compiler result therefore do not substitute for the accepted evidence.

A feed call can split any prefix or payload byte. One call can also contain
several complete frames. Chunk boundaries have no protocol meaning. Complete
frames are returned in byte-stream order. Finishing the input refuses a
partial prefix or payload, so extra bytes cannot be accepted as harmless
trailing data. A malformed request poisons the core; later input cannot resume
from an ambiguous offset.

The framing core assigns sequence numbers from 1 in admission order. It also
uses the compiled `max_requests` value as a parser and event-memory ceiling.
Step 4 adds atomic runtime accounting and lifecycle enforcement; the framing
ceiling does not claim those later controls.

## Closed text request

The payload is strict JSON under the compiled `max_json_depth`,
`max_json_members`, `max_string_bytes`, `max_request_bytes`, and
`max_input_tokens` limits. Scalar count uses `max_json_members` as its tighter
frame ceiling because version 1 has no separate scalar policy field. The
payload is one object with exactly three fields:

| Field | JSON type | Version-1 rule |
| --- | --- | --- |
| `schema` | string | Exactly `model-request/v1` |
| `operation` | string | Exactly `text.generate` |
| `input` | string | Text under the string, byte, and input-token ceilings |

The synthetic profile's `unicode-codepoint-fixture/v1` counter counts one
Python Unicode scalar per input token. This is a fixture rule, not a claim
about a live provider tokenizer.

No request field selects provider authority. Guest job or request identities,
sequence numbers, URLs, origins, paths, methods, models, headers,
authorisation, credentials, tools, uploads, files, remote references, images,
storage, expiry, retention, cancellation, or timeout fields refuse with a
fixed code. The same applies to every disabled feature name from the compiled
profile. `stream`, `streaming`, `channel`, `multiplex`, and `batch` are absent,
so version 1 offers neither streaming nor multiplexing. Another unknown field
also refuses; it does not become provider input.

## Closed text response

The trusted core accepts a normalised output string only for the exact,
unconsumed `TextRequest` object issued next by that same core. A copied,
foreign, already-consumed, or later request refuses even when it repeats an
admitted sequence. Responses therefore remain in admission order rather than
multiplexing issued requests. The core checks the compiled output-token,
string-byte, and response-byte ceilings, then emits one length-prefixed
canonical JSON object with exactly
`schema=model-response/v1`, the core-assigned `sequence`, and `output`. The
guest cannot submit a response object or choose its sequence.

Response object names are sorted by the canonical JSON rule, making equal
sequence and output values byte-identical. A response carries no provider id,
request id, model, usage claim, header, URL, raw error, or lifecycle field.
A normal terminal transition first requires an unambiguous guest EOF and
refuses while any admitted request remains unserved.

## Admission-bound provider mapping

`ProviderSession` owns one framing core. It records the exact `TextRequest`
objects that core issues and will cross the provider boundary only for the
same unconsumed object in admission order. A copied, foreign, unadmitted,
out-of-order, or already failed request refuses before the credential source
is called. A provider refusal
poisons the session rather than permitting a retry against an ambiguous
provider state. A framing refusal also poisons the session and clears every
pending provider admission before another credential read or exchange.
After validating the supplied compiled policy against its captured
accepted-job evidence, the session replays those immutable evidence bytes into
a private limit snapshot. Later mutation of the caller's policy document cannot
widen request, response, parser, token, or event bounds.

After admission, the session reads the credential from the environment name
fixed by the registered profile. The synthetic request body is canonical JSON
with exactly `schema=synthetic-provider-request/v1`, the fixed profile model,
and the normalised input. Authentication is not in that body. The connector
constructs exactly `Accept: application/json`, `Authorization: Bearer <value>`,
`Content-Encoding: identity`, and `Content-Type: application/json`. The caller
cannot supply a scheme, hostname, port, path, method, model, header, or
credential field.

The credential is a non-empty bounded ASCII bearer value. Missing, malformed,
or unreadable credential state refuses through a fixed diagnostic. Raw source
exceptions and values are not retained. Component vectors generate a fresh
in-memory canary, inject its source, and require the in-process provider
fixture to see it after admission.

## Pinned HTTPS transport

The connector re-resolves the registered profile before use, so a
self-consistent replacement dataclass cannot change its transport authority.
It fixes HTTPS, port 443, `POST`, `/v1/responses`, the profile hostname, a
30-second connector timeout, strict certificate verification, and TLS hostname
verification. A caller-supplied connector timeout must be finite and positive
and can only shorten that ceiling. Its explicit client context does not honour
`SSLKEYLOGFILE`, so ambient process state cannot select an output path for TLS
traffic secrets. It resolves that hostname on the first request, bounds the
resolver iterator, requires one unique global IP address, and reuses that pin
for every later request handled by the job connector. Empty, multiple,
malformed, private, loopback, link-local, multicast, unspecified, reserved,
documentation, and other non-global answers refuse.

The standard-library exchange connects to the selected address directly and
passes the profile hostname to TLS. It neither consults proxy environment
variables nor implements CONNECT. The response peer address must equal the
selected address, preventing a second resolver decision from changing the
target. HTTP status 300 through 399 is terminal; no redirect is followed.
Failure to close an obtained response is a transport refusal, and the
corresponding guest output is withheld.

Only status 200, `Content-Type: application/json`, absent or identity content
encoding, and absent or chunked transfer encoding are admitted. Response
header names are unique and drawn from the closed content header set. A
declared content length is checked before reading and must equal the bytes
read. Chunked and connection-delimited bodies are read in bounded chunks and
stop at the compiled response-byte ceiling. Every obtained response is closed
on success and refusal. TLS, socket, HTTP, resolver, and injected-exchange
errors become fixed value-free refusals.

## Closed provider response

The upstream body is strict JSON under the compiled response-byte, JSON depth,
member, scalar, and string limits. It has exactly `schema`, `output`, and
`usage`. The schema is `synthetic-provider-response/v1`; `output` is a string;
and `usage` has exactly non-negative integer `input_tokens` and
`output_tokens`. For the synthetic profile, both counts must equal the Python
Unicode scalar counts of the admitted input and returned output. A duplicate,
unknown, missing, malformed, mistyped, over-limit, or disagreeing field
refuses. A body or parsed field containing the current credential also
refuses. After validation, only the output string reaches the existing closed
guest response encoder.

## Content-free provider events

The session retains at most `max_requests + 1` fixed
`model-proxy-provider-event/v1` records. Each record carries only the safe
profile id, disclosure state, outcome family, fixed code, request and response
byte counts, input and output token counts, and monotonic duration in
nanoseconds. A pre-admission or credential-source refusal says `not-read`;
validation or resolution that refuses before the exchange handoff also says
`not-read`; another attempted provider exchange says `provider-only`. No event
contains a prompt, output, credential, URL, header, address, provider request
id, or raw error. Once the connector hands a mapped request to the exchange, a value-free
transport refusal preserves that request's byte count and bounded duration even
when no response object returns. If a response did return before its status,
headers, or body refused, the same refusal also preserves the body bytes read
rather than recording zero disclosure.

## Content-free frame events

The core retains at most `2 * max_requests + 2` fixed
`model-proxy-frame-event/v1` records. Each has exactly `schema`, `stage`,
`outcome`, and `code`. Stages come from the closed set `length`, `request`,
`response`, and `stream`; outcomes are `accepted` or `refused`. The event has
no payload, input, output, path, guest identity, sequence, exception text, or
free-form field name. This answers which framing stage stopped without
turning request content into telemetry.

## Atomic runtime accounting

`LifecycleController` replays the captured accepted-job bytes before it accepts
a reservation. It takes a private copy of every limit and binds itself to the
replayed job id, JobSpec digest, policy digest, profile, and token counter. A
second activation, a foreign job or digest, a duplicate sequence, or a
reservation from another controller refuses. There is no state deserialiser.

One lock covers reservation, rollback, completion, cancellation, expiry, and
the first terminal transition. Before the runtime reads a credential or calls
the connector, the lock reserves all of these values together:

- one request and the exact canonical provider-request byte count;
- the input count produced by the profile's pinned token counter;
- one concurrency slot;
- the full per-request output-token ceiling;
- the full per-request provider-response byte ceiling; and
- the smaller remaining interval from absolute expiry and elapsed lifetime.

The synthetic `unicode-codepoint-fixture/v1` counter counts the exact mapped
input string with Python's Unicode scalar count. An unrecognised counter
refuses before activation. Request count, mapped request bytes, and input
tokens are committed when disclosure begins. Output tokens and response bytes
remain reserved at their complete per-request ceilings until a closed provider
event reports actual usage. Completion requires that event to match the mapped
request bytes and input count and stay inside both response reservations.
Unused response capacity is then released. A pre-disclosure rollback releases
all seven resources and the sequence; a disclosed reservation cannot roll
back.

Terminal disclosure state is monotone across the job. Once a completed or
refusing provider event records `provider-only`, a later `not-read` refusal
cannot erase that earlier disclosure from the terminal receipt.

The aggregate checks include active reservations, so concurrent calls cannot
each observe the same remaining capacity. A count, byte, token, output,
response, or concurrency excess makes the job terminal. Later admission and
provider publication refuse. Requests may reserve concurrently, but the
runtime registers each durable request receipt in a pending-turn set and gives
the provider session one turn at a time in guest sequence order. Selection
uses the lowest pending sequence rather than the execution lock's unspecified
waiter order. It commits or refuses that turn against its own provider event
before the next turn can cross the provider boundary. When no terminal
transition has won, a successful provider event contributes its confirmed
response bytes and validated output tokens before the post-provider clock
check. A refusing event likewise contributes its confirmed response bytes,
including the one over-limit sentinel. Expiry observed by that check wins the
terminal outcome without dropping those counts. A response arriving after an
earlier terminal transition cannot rewrite that already durable snapshot.

## Cancellation, expiry, and publication

Activation records two time domains. Absolute expiry comes from the accepted
UTC `expires_at` value and is compared with `time.time_ns()`. Its
activation-time remaining interval, capped by the accepted
`absolute_lifetime_seconds`, is also added to the first
`time.monotonic_ns()` reading, so a later wall-clock rollback cannot extend the
signed absolute lifetime. Elapsed lifetime starts from Python's
`time.monotonic_ns()` and adds the compiled `total_wall_seconds`. Each admission
uses the smaller remaining interval. If `time.monotonic_ns()` fails, returns an
invalid value, or decreases, the controller sets `MP405` as the terminal outcome
at the last verified reading. The runtime checks both clocks again after the
request receipt is durable and before it marks the reservation disclosed. An
expiry during that write creates a content-free terminal record and prevents
the credential read. Otherwise, the runtime passes the shortened interval to
the connector, whose existing 30-second limit remains the upper transport
timeout.

After the credential read and pinned resolution, the connector calls a
controller-owned handoff immediately before entering the exchange adapter.
That handoff shares the lifecycle lock with cancellation and expiry, rechecks
both clocks, and shrinks the exchange timeout to the current smaller remaining
interval. The credential source and system resolver are not independently
interrupted by that callback, but an expiry observed when either returns
prevents the exchange and keeps the terminal disclosure state `not-read`. A
handoff that wins first makes the job-level state `provider-only`, even when
cancellation closes the in-flight request before a provider response returns.

`poll()` applies the first expired boundary. If both boundaries have passed,
the one whose activation-time interval was shorter supplies the fixed outcome.
Trusted cancellation checks both expiry domains under the same lock before it
can set `MP406`, so a deadline already reached remains the terminal winner.
Both transitions mark the controller terminal, erase the provider session's
credential source, connector reference, pending admissions, and content-bearing
framing buffers and issued-request references, and then invoke the trusted I/O
closer. Credential and connector references are erased in a `finally` path, and
a provider or framing cleanup exception cannot skip the trusted I/O cleanup
attempt. Admission cannot cross that linearisation point. A response that
returns after cancellation or expiry is closed by the provider component and
discarded instead of entering guest publication. Any cleanup failure refuses
with `MP407` and produces no guest response. Provider or trusted-I/O cleanup
failure occurs before the terminal write and therefore produces no successful
terminal receipt. If the terminal line was already synchronised before the
receipt descriptor's close reports failure, that line still records the first
lifecycle outcome; the close refusal cannot rewrite durable evidence. The
embedding supervisor remains responsible for terminating the per-job process.
These component checks do not prove that process exit.

Completion, cancellation, and expiry share one publication lock in
`ModelProxyRuntime`. Completion either commits before the terminal transition,
or sees that transition and withholds the response. A transport refusal that
arrives after cancellation or expiry reports the earlier terminal winner. The
controller retains one terminal snapshot; another terminal call does not
create another receipt. A final-response completion that finds another active
reservation still finalises the resulting refusal before returning it; cleanup
and terminal evidence do not depend on that other caller running afterwards.
Every final waiter and direct completion reports an already durable terminal
outcome instead of replacing it with the closed provider session's refusal.
The final-response path validates the guest EOF before provider disclosure and
withholds its already normalised response if a later admitted request remains
unserved. Direct completion applies the same EOF and pending-admission checks.

## Content-free receipt file

`ReceiptSink` creates one new file with exclusive creation and mode `0600`.
If that initial creation or the activation-record write refuses, runtime
construction erases the provider session's credential and connector references,
attempts any available sink close, and invokes the trusted I/O closer before
propagating the original refusal. A provider cleanup exception cannot skip the
remaining cleanup attempts. A path-encoding or descriptor-close failure while
walking the parent chain or refusing target setup cannot replace the fixed
`MP407` result or skip those runtime cleanup attempts; every other descriptor
already acquired for that failed construction is still given one close attempt.
It walks every parent directory and opens the final target with no-follow
flags. A symbolic link, directory, existing path, missing parent, replacement,
or changed inode refuses. Keeping the descriptor open is not enough. The sink
retains the absolute named path and original parent identity, reopens the whole
no-follow parent chain, and compares both file and parent identities before and
after every write. Renaming or replacing an ancestor therefore poisons the
sink instead of diverting later records to an unnamed file.

Each canonical UTF-8 JSON record is at most the smaller of compiled
`max_receipt_bytes` and 4,096 bytes, excluding its line feed. One `os.write`
must write the whole line. A zero, short, partial, failed, or replaced-target
write poisons the sink; it is never retried as an append. Nanosecond timings
are decimal strings so an absolute Unix value remains exact without exceeding
the canonical JSON safe-integer range. The activation write synchronises both
the file and its parent directory before guest input can be accepted, making
the new directory entry part of the pre-disclosure durability boundary.

The file has exactly these record kinds in order:

1. one `activation` record before guest input;
2. at most one `request` record for each consumed sequence, written after all
   resources are reserved and before credential access; and
3. one `terminal` record with the first terminal outcome and bounded totals.

Every root record has exactly `schema`, `event`, `job_id`,
`jobspec_sha256`, `policy_sha256`, `profile`, `sequence`, `versions`, `counts`,
`timings`, `disclosure_state`, and `outcome_code`. Nested version, count, and
timing sets are closed by record kind. The schema is
`model-proxy-receipt/v1`. No record accepts a prompt, response, content digest,
credential, raw URL, header, provider request id, provider name, or exception
text.

A request-receipt failure occurs before `mark_disclosed`, rolls the reservation
back, marks the runtime terminal, and prevents the credential read and provider
call. A terminal-receipt failure closes the sink, keeps the runtime terminal,
and refuses guest publication of the response being completed. Because a
receipt path must be absent at activation and no resume reader exists, a new
process cannot resume a prior job from its receipt file.

## Operator disclosure

`render_operator_text` replays the exact accepted-job evidence and refuses a
caller-mutated policy. Its output names what leaves the machine, the provider
family, origin and path family, profile and model, provider storage and
retention rule, local content-free receipt retention, every disabled feature,
and every compiled limit. It also states the boundary directly: restricting
the destination and withholding the credential from the guest does not prove
that the provider will not retain or exfiltrate disclosed model content.

## Policy vocabulary

The policy root has exactly `schema`, `compiler`, `job`, `provider`,
`disclosure`, `limits`, and `receipt`.

| Object | Fields | Authority |
| --- | --- | --- |
| Root | `schema=model-proxy-policy/v1`; `compiler=phylax-model-proxy-compiler/v1` | Compiler code |
| `job` | `id`, `jobspec_sha256`, `activated_at`, `expires_at`, `absolute_lifetime_seconds` | Accepted bytes and verified evidence |
| `provider` | `id`, `provider`, `origin_family`, `path_family`, `method`, `operation`, `model`, `request_schema`, `response_schema`, `token_counter`, `storage`, `retention` | Code-owned profile |
| `disclosure` | `data_class`, `content_logging=false`, `diagnostic_consent=false`, and the ordered `disabled_features` list | Accepted bytes constrained by profile |
| `limits` | Every row of the hard-ceiling table, using the accepted positive value | Accepted bytes constrained by code ceilings |
| `receipt` | `content=none` and `retention_seconds` | Compiler constant and accepted retention |

The policy contains the accepted JobSpec digest but not its bytes. It contains
no prompt, response, content digest, raw URL, arbitrary header, credential,
credential source, provider request identifier, or raw error.

## Closed synthetic provider profile

Version 1 has one profile, `loopback-text/v1`:

| Property | Fixed value | Purpose |
| --- | --- | --- |
| Provider | `synthetic-loopback` | Names non-production ownership |
| Origin family | `https://model-proxy.loopback.invalid` | Makes live resolution impossible |
| Path family and method | `/v1/responses`, `POST` | Pins request routing |
| Operation and model | `text.generate`, `fixture-text-1` | Pins inference semantics |
| Schemas | `model-request/v1`, `model-response/v1` | Pins both mapping boundaries |
| Provider schemas | `synthetic-provider-request/v1`, `synthetic-provider-response/v1` | Pins the internal adapter boundary |
| Token counter | `unicode-codepoint-fixture/v1` | Pins synthetic counting |
| Storage and retention | `false`, `process-memory-only` | Forbids provider-side state |
| Allowed data class | `synthetic-public` | Excludes private input |
| HTTPS authority | `model-proxy.loopback.invalid`, port 443, `/v1/responses`, `POST` | Pins transport authority |
| Credential source | `WILDCAT_MODEL_PROXY_CREDENTIAL`, `Bearer` | Keeps source and header construction in code |

The origin remains a non-connectable component endpoint. The reserved
`.invalid` name cannot resolve through the default resolver, while provider
vectors inject both the resolver and an in-process exchange. No live call is
part of the command or test suite. A later live profile must choose its own
origin, retention tier, token counter, and credential source in reviewed code;
none can come from the guest or accepted JobSpec as an arbitrary URL or header.

The complete disabled feature set is `audio`, `background`, `conversations`,
`files`, `images`, `remote_urls`, `storage`, `streaming`, `tools`, and
`uploads`. Every field is required and must be `false` in accepted evidence.

## Hard implementation ceilings

Every value is a positive JSON integer. A boolean is not an integer. Values
above these ceilings refuse rather than clamp:

| Limit | Ceiling | Scope |
| --- | ---: | --- |
| `max_requests` | 32 | Job aggregate |
| `max_request_bytes` | 65,536 | One request |
| `max_response_bytes` | 131,072 | One response |
| `max_input_tokens` | 8,192 | One request |
| `max_output_tokens` | 4,096 | One response |
| `max_total_request_bytes` | 1,048,576 | Job aggregate |
| `max_total_response_bytes` | 2,097,152 | Job aggregate |
| `max_total_input_tokens` | 65,536 | Job aggregate |
| `max_total_output_tokens` | 32,768 | Job aggregate |
| `max_concurrency` | 4 | Job process |
| `max_json_depth` | 12 | Frame parser |
| `max_json_members` | 256 | Frame parser |
| `max_string_bytes` | 32,768 | Frame parser |
| `max_receipt_bytes` | 4,096 | One receipt |
| `max_receipts` | 34 | Job aggregate |
| `total_wall_seconds` | 900 | Job lifetime |

Each aggregate byte or token limit must be at least its matching per-request
limit. `max_requests` must be at least `max_concurrency`.
`max_receipts` may not exceed `max_requests + 2`. These are security and
resource ceilings, not a performance claim.

## Version rule

All schema and profile versions are exact. The compiler accepts no
negotiation, range, fallback, alias, or absent version. A recognised family
with an old or future version refuses with `MP121`. An unknown schema family
refuses with `MP111`; an unknown profile family refuses with `MP112`. A new
version requires new normative bytes, code, fixtures, and tests while version
1 remains readable.

## Outcomes and diagnostics

Successful compilation emits the canonical policy line on standard output and
one `model-proxy-diagnostic/v1` line on standard error. The diagnostic has only
`schema`, `outcome`, `policy_schema`, `profile`, `jobspec_sha256`, and
`policy_sha256`.

Successful `check-frames` emits one `model-proxy-diagnostic/v1` line with only
`outcome=frames_checked`, the fixed manifest schema, case and request counts,
and the policy digest. The checked manifest is bounded, has a closed shape,
uses lowercase hexadecimal chunks, resolves only its sibling
`accepted-job.json`, and carries exact response bytes. A manifest path with the
wrong scalar type refuses through the same content-free diagnostic boundary.
The command is component-vector evidence rather than a live guest transport.

Successful `provider-demo` emits one line of the same diagnostic schema with
only `outcome=provider_checked`, the fixed manifest schema, case and request
counts, and the policy digest. The bounded closed manifest carries exact guest
frames, provider request objects, synthetic provider responses, and guest
response bytes, but no credential. Each case generates its canary in memory,
injects a resolver and in-process exchange, requires one post-admission
credential read, and closes the response. The command makes no network call.

Successful `lifecycle-demo` emits one line of the same diagnostic schema with
`outcome=lifecycle_checked`, the fixed lifecycle-manifest schema, case,
request, and receipt counts, and the policy digest. Its closed manifest uses
injected wall-clock and monotonic-clock start values, an injected global
address, an in-process exchange, and a fresh in-memory credential. Each case
writes a fresh receipt file, completes one request, verifies activation/request/terminal order and
record bounds, scans retained bytes for the credential and model content, and
checks the operator disclosure. The command makes no network call and claims
no provider retention behaviour.

Refusal diagnostics have exactly `schema`, `outcome=refused`, `code`, and
`field`. `field` is a code-owned schema location, never an input value. CLI
argument errors use the same value-free shape and accept no abbreviated option
names. The compiler never prints an input path, unknown argument or field name,
JobSpec bytes, job id, or exception text.

| Code | Fixed outcome | Stage |
| --- | --- | --- |
| `MP000` | Accepted content-free frame event | Request, response, or stream |
| `MP100` | Input path or stability refusal | File read |
| `MP101` | Size, count, or collection ceiling refusal | Read or parse |
| `MP102` | Input is not strict UTF-8 | Parse |
| `MP103` | Malformed JSON | Parse |
| `MP104` | Excessive JSON depth | Pre-parse scan |
| `MP105` | Duplicate JSON field | Parse |
| `MP106` | Unsupported Unicode | Tree validation |
| `MP107` | Wrong JSON shape | Schema validation |
| `MP108` | Missing or extra field | Schema validation |
| `MP109` | Wrong scalar type, encoding, sign, or zero value | Value validation |
| `MP110` | JobSpec digest, identity, or expiry join mismatch | Evidence join |
| `MP111` | Unknown schema family | Version gate |
| `MP112` | Unknown provider profile family | Profile resolution |
| `MP113` | Profile/model/operation/schema disagreement | Profile projection |
| `MP114` | Provider feature enabled | Feature gate |
| `MP115` | Content logging enabled | Disclosure gate |
| `MP116` | Diagnostic consent requested in the no-consent profile | Disclosure gate |
| `MP117` | Data class not admitted by the profile | Disclosure gate |
| `MP118` | Invalid or excessive absolute lifetime | Lifetime gate |
| `MP119` | Hard ceiling or aggregate relation exceeded | Limit gate |
| `MP120` | Golden policy bytes or digest disagree | Golden check |
| `MP121` | Old or future version of a recognised family | Version gate |
| `MP122` | Missing, unknown, or abbreviated CLI argument | CLI boundary |
| `MP199` | Unexpected internal exception, with no exception text retained | CLI boundary |
| `MP200` | Zero frame length | Frame length |
| `MP201` | Frame length exceeds the compiled byte ceiling | Frame length |
| `MP202` | Incomplete trailing length prefix | Stream finish |
| `MP203` | Incomplete trailing payload | Stream finish |
| `MP204` | Accepted evidence replay, compiled policy identity, mapping, or ceiling mismatch | Frame activation |
| `MP205` | Request is not an object | Request shape |
| `MP206` | Required request field is absent | Request shape |
| `MP207` | Guest supplied an authority, feature, or lifecycle field | Request authority |
| `MP208` | Request has another unknown field | Request shape |
| `MP209` | Request field or stream chunk has the wrong scalar type | Request value |
| `MP210` | Request schema is not exactly version 1 | Request version |
| `MP211` | Operation is not exactly `text.generate` | Request operation |
| `MP212` | Input exceeds the compiled token ceiling | Request input |
| `MP213` | Response request was not the exact unconsumed issue from this core | Response authority |
| `MP214` | Response output has the wrong type or encoding | Response value |
| `MP215` | Response output exceeds a compiled ceiling | Response value |
| `MP216` | Input resumed after finish or refusal | Stream state |
| `MP217` | Request count exceeds the compiled safety ceiling | Request count |
| `MP218` | Framing manifest path, shape, or expected bytes disagree | Manifest check |
| `MP300` | Profile, connector, or internally mapped request authority disagrees | Provider activation |
| `MP301` | Name resolution failed or returned no bounded answer | Provider resolution |
| `MP302` | Resolved address is malformed or not globally routable | Provider resolution |
| `MP303` | Resolution returned more than one distinct address | Provider resolution |
| `MP304` | Connected peer differs from the pinned resolved address | Provider connection |
| `MP305` | Strict TLS context, certificate, or hostname verification failed | Provider TLS |
| `MP306` | Socket, HTTP, timeout, exchange, or duration failed | Provider transport |
| `MP307` | Redirect status is terminal | Provider response |
| `MP308` | Status is mistyped or not 200 | Provider response |
| `MP309` | Response headers are malformed, repeated, unknown, or inconsistent | Provider response |
| `MP310` | Declared, streamed, or actual response bytes exceed or disagree with the bound | Provider response |
| `MP311` | Content type, content encoding, or transfer encoding is not admitted | Provider response |
| `MP320` | Request is not the exact admitted object or session is poisoned | Provider admission |
| `MP321` | Credential source or bounded bearer value is unavailable | Provider credential |
| `MP322` | Mapped provider request exceeds its compiled bound | Provider mapping |
| `MP323` | Provider response JSON or closed field set is malformed | Provider normalisation |
| `MP324` | Provider response schema is not exactly version 1 | Provider normalisation |
| `MP325` | Provider output or usage has the wrong type or exceeds a bound | Provider normalisation |
| `MP326` | Provider usage disagrees with the synthetic token counter | Provider normalisation |
| `MP327` | Provider response contains the current credential | Provider disclosure |
| `MP328` | Provider manifest path, shape, mapping, or expected bytes disagree | Manifest check |
| `MP400` | Runtime policy, connector, or I/O closer disagrees | Lifecycle activation |
| `MP401` | Job, digest, sequence, reservation, activation, or state disagrees | Lifecycle identity |
| `MP402` | Request count, mapped bytes, or input-token reservation exceeds a limit | Lifecycle admission |
| `MP403` | Concurrency, output-token, or response-byte reservation exceeds a limit | Lifecycle admission |
| `MP404` | Accepted absolute expiry has arrived | Lifecycle expiry |
| `MP405` | Monotonic deadline or clock value refuses | Lifecycle expiry |
| `MP406` | Trusted cancellation made the job terminal | Lifecycle cancellation |
| `MP407` | Receipt path, count, state, identity, complete write, or close refuses | Receipt sink |
| `MP408` | Receipt limit, closed shape, or byte ceiling refuses | Receipt schema |
| `MP409` | Token counter or provider usage disagrees with the reservation | Lifecycle accounting |
| `MP410` | Lifecycle manifest path, shape, execution, or expected result disagrees | Manifest check |

## Golden command

Run from the repository root using the interpreter named by
`.python-version`:

```bash
mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/phylax/scripts/model_proxy.py compile-policy --accepted-job plugins/hexaemeron/tests/fixtures/model-proxy-v1/accepted-job.json --expect plugins/hexaemeron/tests/fixtures/model-proxy-v1/policy.json
```

`--expect` requires exact policy bytes followed by one line feed and the
sibling `policy.sha256` file. A match establishes the checked component vector
only. It does not establish a live credential boundary, provider behaviour,
provider non-retention, or provider non-exfiltration.

Check the framing vectors with:

```bash
mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/phylax/scripts/model_proxy.py check-frames --manifest plugins/hexaemeron/tests/fixtures/model-proxy-v1/framing-cases.json
```

The two cases exercise a one-byte-fragmented request and two concatenated
requests with exact closed responses. The unittest surface carries the
hostile, incomplete, oversized, duplicate, forbidden-authority, and
content-free diagnostic cases.

Check the provider vectors with:

```bash
mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/phylax/scripts/model_proxy.py provider-demo --manifest plugins/hexaemeron/tests/fixtures/model-proxy-v1/provider-cases.json
```

The two cases exercise exact ASCII and Unicode mappings through an injected
resolver and in-process exchange. Hostile unittests cover admission ordering,
credential-source failure and absence from retained surfaces, endpoint and
header authority, resolution and peer pinning, TLS, all 3xx statuses, response
headers and byte floods, closed response JSON, usage disagreement, secret
echo, raw-error sanitisation, connection close, and the absence of a live
socket call. They also show that a framing refusal blocks every pending
provider call, one job connector keeps its first address pin across requests,
that post-activation caller mutation cannot widen the captured policy limits,
that an out-of-order request stops before credential or provider disclosure,
that ambient `SSLKEYLOGFILE` cannot enable TLS traffic-secret output, and a
response refusal retains confirmed content-free disclosure counts.

Check the lifecycle, quota, receipt, and operator vectors with:

```bash
mise exec python@3.13.15 -- python3 plugins/hexaemeron/skills/phylax/scripts/model_proxy.py lifecycle-demo --manifest plugins/hexaemeron/tests/fixtures/model-proxy-v1/lifecycle-cases.json
```

The two cases exercise ASCII and Unicode input under injected clocks and an
in-process exchange. The unittest surface covers exact and excessive quota
reservations, concurrent admission, rollback, request floods, identity and
restart refusals, both expiry domains, cancellation and late responses,
ordered concurrent provider turns, quota and active-completion terminalisation,
provider-usage disagreement, receipt schema and filesystem failures including
ancestor replacement and parent-directory synchronisation, content absence,
constructor cleanup, response-close and terminal publication failure,
truncated terminal input, unserved admission refusal, and operator-text parity.
