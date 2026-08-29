# Promise Machine run-observation capture v1

`promise-machine-run-observation-capture/v1` is the narrow gate before a run
observation becomes durable. It accepts a closed structured candidate and
returns exactly one of: an accepted event, a visible observation gap, or a
refusal. It is neither a transcript store nor a generic text scrubber.

## Durable boundary

Only direct descriptors may survive: small identities, event type and time,
status, declared names or selectors, non-negative counts and sizes, a checked
repository-relative path, and an eligible correlation fingerprint. Candidate
payloads, headers, environment maps, instructions, arguments, URLs, exception
text, traces, source text, and credentials never become a durable object.

The writer accepts only a runtime-issued accepted `CaptureResult`, revalidates
its closed event and redaction shape, and creates a new file through no-follow
directory descriptors beneath the supplied or current repository root. It rejects a
caller-supplied dictionary, an unissued or mutated result, a gap, a refusal,
and a target outside that root or below a symlinked parent. A gap says what
class was withheld without storing the source key, value, byte length, or
location. It carries a closed redaction object:

```json
{"field_class":"content","reason_code":"forbidden_content","method":"omitted"}
```

The available methods are `omitted`, `fingerprinted`, and `path_dehosted`.
The stable reason codes are `forbidden_content`, `ineligible_fingerprint`,
`invalid_path`, `over_limit`, `unknown_field`, and `unsafe_shape`.

## Confinement and correlation

A repository path is resolved beneath the supplied repository root before it
is stored as a portable relative path. Traversal, a symlink escape, an
out-of-root source, non-NFC spelling, and an unreadable path produce a gap;
the source path is not repeated in diagnostics.

Correlation is opt-in. The source input must be bounded bytes supplied as
base64, carry a declared scope, and have at least 128 declared entropy bits
that do not exceed a conservative byte-distribution estimate. The runtime
stores only a domain-separated SHA-256 result with its scope and algorithm.
Predictable or credential-like material must be omitted, not fingerprinted;
equal fingerprints do not prove identity.

## Bounds and signals

The candidate JSON, string values, collections, redaction list, path, and
fingerprint source have fixed ceilings in the runtime. Unknown or malformed
shapes fail closed. CLI output carries an outcome and a stable code but does
not echo candidate text. This makes the answer to three operational questions
visible without retaining sensitive material: whether capture accepted, gapped
or refused; which closed policy class acted; and whether an eligible scoped
correlation was recorded.

```bash
python3 scripts/run_observation_capture.py check \
  tests/fixtures/run-observation-capture/valid/accepted.json
```

The command demonstrates the gate only. It does not establish complete secret
detection, source truth, outside-host retention, Fiat receipt binding, or the
#436/#437/#508 work that remains outside this contract.
