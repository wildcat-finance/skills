# Model proxy policy version 1

## Status and scope

This reference is normative for `model-proxy-policy/v1` and its synthetic
accepted-job adapter. It fixes policy compilation only. Guest framing,
provider transport, runtime accounting, receipts, cancellation, and the final
hostile-conformance manifest are later boundaries.

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
and whose future transport is injected by tests. It cannot resolve or send a
live provider request.

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
| Token counter | `unicode-codepoint-fixture/v1` | Pins synthetic counting |
| Storage and retention | `false`, `process-memory-only` | Forbids provider-side state |
| Allowed data class | `synthetic-public` | Excludes private input |

The origin is descriptive policy data, not a connectable endpoint. The
reserved `.invalid` name and absent transport make a network call impossible
in this step. A later live profile must choose its own origin, retention tier,
token counter, and credential source in reviewed code; none can come from the
guest or accepted JobSpec as an arbitrary URL or header.

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

Refusal diagnostics have exactly `schema`, `outcome=refused`, `code`, and
`field`. `field` is a code-owned schema location, never an input value. CLI
argument errors use the same value-free shape and accept no abbreviated option
names. The compiler never prints an input path, unknown argument or field name,
JobSpec bytes, job id, or exception text.

| Code | Fixed outcome | Stage |
| --- | --- | --- |
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
