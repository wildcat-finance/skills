# Homologia checked-input schema compatibility

`homologia.py check` admits version-1 manifests and JSONL vector records. The
published JSON Schemas describe the closed structural surface. The standard-
library validator is authoritative because it also checks relationships that a
schema cannot settle: unique ids and paths, exact scale equality, tolerance
equality, filesystem containment, source identity and input caps.

## Version-1 files

- A manifest has `schema`, `pair` and `vector_sets`, with no other top-level
  fields. `schema` is exactly `homologia-manifest/v1`.
- A pair names one chain id, contract address and function, plus one mirror id,
  SHA-256 revision and scale.
- Each vector-set descriptor names one repository-relative JSONL path, a scale
  exactly equal to the mirror scale, and optionally one absolute tolerance.
- Each JSONL record names one vector id, a non-empty object of canonical
  decimal-integer strings, one expected decimal-integer string, one provenance
  object, and optionally the declared set tolerance.

Objects are closed. Unknown fields refuse; they are not ignored for forward
compatibility. A future additive field therefore needs a new schema identity
and a validator that understands its meaning. Existing version-1 bytes keep
their meaning.

## Expected-answer provenance

The three accepted forms are deliberately separate:

- `proved` requires `lazarus_artifact`, a repository-relative reference. This
  step checks the reference's syntax and does not open it or repeat Lazarus's
  proof work.
- `recorded` requires canonical chain id and block number strings plus a
  32-byte block hash.
- `asserted` requires a bounded, non-empty author name.

The class is evidence attached to the supplied expected integer. Admission
does not establish that the answer is correct, and the checked record is not an
agreement verdict.

## Integer and path forms

Integers are base-10 strings. Zero is `0`; other values have no leading zero;
negative zero, fractions, exponents and locale separators refuse. Chain ids,
block numbers and absolute tolerances are unsigned.

Input paths use `/`, have no absolute, empty, dot or parent components, and
remain under their declared directory. Manifest and output paths remain under
the repository root. Existing symlinks refuse. Each input is opened once with
no-follow where the platform provides it, read through that descriptor, and
checked against the named file again before output.

## Fixed safety caps

| Boundary | Version-1 cap |
| --- | ---: |
| Vector sets per manifest | 16 |
| Vectors per set | 100,000 |
| Bytes per manifest or vector file | 8 MiB |
| Bytes across one manifest and its vector files | 64 MiB |

The file cap is checked before decoding. Set and vector counts and aggregate
bytes are checked before any output is installed. Raising a cap requires a new
study decision; it is not a compatibility edit.

## Checked record and output

Success writes `homologia-checked-inputs/v1` as sorted, compact UTF-8 JSON with
one trailing newline. It contains the pair, every admitted vector, manifest and
vector source paths and SHA-256 digests, scale and tolerance declarations, and
set and vector counts. It contains no timestamp or host path, so the same input
bytes at the same repository-relative paths produce the same output bytes.

Validation finishes before the destination is touched. The command writes a
same-directory temporary file, flushes it, then replaces the destination. A
refusal leaves an existing destination byte-identical.

## Command signals

Success and refusal are one-line JSON events on standard error. Success uses
`homologia_check_ok` and reports the manifest digest, output digest and bounded
counts. Refusal uses `homologia_check_refused`, a stable code, a subject capped
at 256 characters and one recovery action. Standard output stays empty.

| Code | Boundary |
| --- | --- |
| `HOM-CHECK-PATH` | lexical containment, symlink or changed file identity |
| `HOM-CHECK-READ` | stable descriptor read |
| `HOM-CHECK-FILE-CAP` | one input file |
| `HOM-CHECK-AGGREGATE-CAP` | all declared input bytes |
| `HOM-CHECK-SET-CAP` | vector-set count |
| `HOM-CHECK-VECTOR-CAP` | vectors in one set |
| `HOM-CHECK-JSON` | UTF-8, JSON, JSONL or duplicate-key decoding |
| `HOM-CHECK-SHAPE` | closed version-1 object shape and identities |
| `HOM-CHECK-INTEGER` | canonical decimal-integer form |
| `HOM-CHECK-SCALE` | exact mirror and set scale equality |
| `HOM-CHECK-PROVENANCE` | closed expected-answer evidence form |
| `HOM-CHECK-TOLERANCE` | undeclared or unequal tolerance use |
| `HOM-CHECK-DUPLICATE` | repeated set id, path or vector id |
| `HOM-CHECK-OUTPUT` | atomic destination installation |

Bad command syntax is argparse exit 2. A governed but unavailable verb exits
3. A refused input exits 4, an output-install refusal exits 5, and successful
admission exits 0.
