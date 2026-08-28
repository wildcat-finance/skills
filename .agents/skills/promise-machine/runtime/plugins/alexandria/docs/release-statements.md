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
Canonical statement bytes above Ariadne's default 8 MiB bounded-input limit are
refused before the output path is prepared, so an existing target remains
unchanged and every successful output stays directly readable by Ariadne.

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

## Evidence boundary

The command emits no DSSE envelope, invokes no cosign operation and checks no
signature. It names no publisher and makes no claim of publisher
authentication, provider completeness, consensus finality or canonical-chain
membership. The passed claim means only that Alexandria completed offline
verification for the logical release digest before emitting these bytes.

Ariadne accepts the output as Statement v1 and applies its core gates. The
Alexandria predicate is not registered there, so predicate-owned gates 2 and 5
remain visibly unchecked. Ariadne also reports the bare statement as unsigned.
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
