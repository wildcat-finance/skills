# Alexandria release statements

Alexandria can project a verified raw or derived release into a deterministic
unsigned in-toto Statement v1:

```bash
python3 plugins/alexandria/scripts/alexandria.py statement <release> \
  --output <statement.json>
```

The command performs the complete existing offline verification before it
builds the statement. It then writes canonical UTF-8 JSON with a trailing
newline through a fresh sibling temporary regular file and atomically replaces
the target. The target must be outside and must not alias the release. A failed
verification, projection or write installs no new result; an existing regular
target remains unchanged unless the final replacement succeeds.

A single statement must stay within two bounds of Ariadne's default reader:
8,388,608 canonical bytes, its bounded-input limit, and 262,144 key characters,
the budget its gates 4 and 7 scan. Key characters are counted over every object
key under `predicate` and every key of each subject's `digest` object. A
release past either bound is refused before the output path is prepared, so an
existing target remains unchanged. The refusal is the line naming the bound
the release passed, the byte bound checked first:

```text
alexandria: release statement encodes to N bytes, above Ariadne's 8388608-byte input limit
alexandria: release statement carries N key characters, above Ariadne's 262144-character scan budget
```

and a second line, `alexandria: write this release as an index and parts with
--parts <directory>`, points to the [part form](#part-sets). Every successful
`--output` file stays directly readable by Ariadne.

## Wire contract

The output uses `https://in-toto.io/Statement/v1` and predicate type
`https://ariadne.wildcat.finance/alexandria-release/v1`. Its subjects are
exactly:

1. `release/<release-name>` with the logical Alexandria `release_id`; and
2. `component/<component-name>` for every manifest component in manifest
   order.

Each Alexandria `sha256:<64 lowercase hexadecimal characters>` identity becomes
an in-toto `{"sha256":"<64 lowercase hexadecimal characters>"}` digest. The
release digest is the logical manifest-content identity defined by
`alexandria-release/v1`, not a claim about the bytes of `manifest.json`.

The closed predicate carries:

- `release` with the Alexandria format and logical release digest;
- `components` with each name, confined object path, media type, byte count
  and digest;
- `captures` with each capture id, component and digest, venue, chain,
  evidence class, exact scope, coverage status and counts, unsupported
  collections and declared gaps;
- one passed `alexandria release offline verification` claim bound to the
  logical release digest; and
- an explicit empty `commands` list.

The [closed JSON Schema](../schemas/release-statement-v1.schema.json) and
fixture drift tests bind those fields and type identifiers. The statement is a
projection, not another Alexandria manifest: it does not copy source locators,
component access classes or redistribution classes.

## Part sets

A release whose single statement passes either bound is written as a part set:

```bash
python3 plugins/alexandria/scripts/alexandria.py statement <release> \
  --parts <directory>
```

`--output` and `--parts` are mutually exclusive. `--parts` refuses a release
within both single bounds with `alexandria: release statement fits Ariadne's
8388608-byte input limit and 262144-character scan budget; emit it with
--output <file>`, so each release has exactly one statement form. The
statements of releases within both bounds keep the bytes they had before part
sets existed.

The set is one directory:

```text
<directory>/index.json
<directory>/part/part-00000.json
<directory>/part/part-00001.json
...
```

Every file is an in-toto Statement v1 in Alexandria's canonical encoding:
sorted keys, compact separators, UTF-8 and one trailing newline.

A part, `part/part-<k>.json` with `k` zero-padded to five digits, has
predicate type `https://ariadne.wildcat.finance/alexandria-release-part/v1`.

- `subject` is `release/<release-name>` with the release digest, then
  `component/<name>` for each component in the part, in manifest order.
- `predicate.release` carries the format and release digest, as in the single
  statement.
- `predicate.part` carries `index` (`k`), `first_component` (the manifest
  position of the part's first component), and the part's `components` and
  `captures` counts.
- `predicate.components` and `predicate.captures` are the single statement's
  objects, unchanged, for the part's components and every capture that names
  one of them, in manifest order.
- `predicate.claims` is the one passed offline-verification claim on the
  release digest, and `predicate.commands` is `[]`.

The index, `index.json`, has predicate type
`https://ariadne.wildcat.finance/alexandria-release-parts/v1`.

- `subject` is the release, then `part/part-<k>.json` with the SHA-256 of that
  part's bytes, in part order.
- `predicate.release`, `predicate.claims` and `predicate.commands` are as in a
  part.
- `predicate.parts` carries `count` and the release's total `components` and
  `captures`.

The [part schema](../schemas/release-statement-part-v1.schema.json) and the
[index schema](../schemas/release-statement-parts-v1.schema.json) close both
shapes and reuse the single statement's component, capture and claim
definitions.

Packing is greedy in manifest order. A part closes before the component whose
subject, component object and captures would carry it past either part bound.
A component whose own part would pass a bound is refused by name, naming the
component and the bound, and nothing is written.

### The part bound

Every part and the index stay within 6,225,920 bytes and 262,144 key
characters. The key budget is Ariadne's own. The byte bound is 6 MiB less
64 KiB. Its base64 encoding is 8,301,228 bytes, which leaves 87,380 bytes of
Ariadne's 8,388,608-byte input limit for a DSSE envelope's own fields and its
signatures. A part that Ariadne reads bare therefore stays readable with the
default bounds inside an envelope whose fields and signatures fit those
87,380 bytes. An index is largest when every part holds one component: its
16,385 subjects then measure 1,950,336 bytes and 98,405 key characters for a
release named `limits`, and a longer name adds its bytes once.

### The write

`--parts` completes the same offline verification, then writes the set into a
fresh hidden sibling directory, `.<name>.tmp-<16 hexadecimal characters>`,
through owner-only, exclusive, no-follow creates. It fsyncs every file and
both directories, verifies the release again, checks that the output parent
and the temporary directory are still the ones it opened, and renames the
directory into place. The target must be absent, outside the release and
reached without a symlink. A failed verification, projection or write removes
what the command created and installs nothing. On success its canonical JSON
receipt reports `release_id`, `part_count`, `component_count`,
`capture_count`, `index_predicate_type`, `part_predicate_type` and the
absolute `output` path.

### A stranger's check

A holder of the set alone makes three checks, each with Ariadne's default
bounds:

1. `verify` on the index;
2. `verify` on each part; and
3. each part's SHA-256 against its subject in the index, with the index's
   `count` equal to the number of part files.

```bash
parts=<directory>
python3 plugins/ariadne/scripts/ariadne.py verify "$parts/index.json"
for part in "$parts"/part/part-*.json; do
  python3 plugins/ariadne/scripts/ariadne.py verify "$part"
done
python3 - "$parts" <<'EOF'
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
index = json.loads((root / "index.json").read_bytes())
named = {item["name"]: item["digest"]["sha256"] for item in index["subject"][1:]}
found = {f"part/{path.name}": hashlib.sha256(path.read_bytes()).hexdigest()
         for path in (root / "part").iterdir()}
assert named == found and len(found) == index["predicate"]["parts"]["count"]
EOF
```

A holder of the release can also run `--parts` again into a fresh directory
and compare the bytes. No separate set-checker command exists. The
[proof](statement-parts/proof.md) records these checks on a
16,384-component release.

### Limits

- A process killed during a `--parts` write, before its rename, leaves its
  hidden `.<name>.tmp-*` directory beside the target, because no cleanup runs
  after a kill. The target stays absent, so no partial set is ever installed.
  Remove the leftover directory by hand before relying on the parent's
  contents.
- A single statement between 6,225,920 and 8,388,608 bytes takes the single
  path and verifies bare, but its DSSE envelope passes Ariadne's default
  8,388,608-byte read. A signing step must read that envelope with a larger
  `--max-bytes`. No pinned release is that large: the largest single
  statement the tree pins, Wildcat V1's, is 510,772 bytes.

## Evidence boundary

Neither form emits a DSSE envelope, invokes a cosign operation or checks a
signature. It names no publisher and makes no claim of publisher
authentication, provider completeness, consensus finality or canonical-chain
membership. The passed claim means only that Alexandria completed offline
verification for the logical release digest before emitting these bytes.

Ariadne accepts each output file as Statement v1 and applies its core gates.
None of the three Alexandria predicates is registered there, so
predicate-owned gates 2 and 5 remain visibly unchecked. Ariadne also reports
each bare statement as unsigned.
A downstream signing step owns the envelope, key, signer identity and
signature-verification evidence; it must not upgrade Alexandria's capture or
chain claims.

## Deterministic demonstration

From the repository root:

```bash
workspace="$(mktemp -d)"
workspace="$(cd "$workspace" && pwd -P)"
python3 plugins/alexandria/examples/credit-history-v0/demo.py build \
  --output "$workspace/credit-history-v0"
python3 plugins/alexandria/scripts/alexandria.py statement \
  "$workspace/credit-history-v0/derived-release" \
  --output "$workspace/alexandria-statement.json"
python3 plugins/ariadne/scripts/ariadne.py inspect \
  "$workspace/alexandria-statement.json"
python3 plugins/ariadne/scripts/ariadne.py verify \
  "$workspace/alexandria-statement.json"
```

Run `statement` again with unchanged input and the same output to obtain the
same bytes. On success its canonical JSON receipt reports `release_id`,
`component_count`, `capture_count`, `predicate_type` and the absolute `output`
path.
