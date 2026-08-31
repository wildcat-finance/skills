# Raw releases

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
<!-- marketplace-context:end -->

Alexandria ingests local source files into a self-contained release directory.
It does not fetch, interpret or rewrite them.

## Capture plan

A capture plan uses `alexandria-capture-plan/v1`. Paths are relative POSIX
paths below the plan's directory. Absolute paths, traversal and symlinks are
refused. Each component declares a stable name, media type, role, `public`,
`restricted` or `private` access class, and `permitted`, `restricted`,
`prohibited` or `unknown` redistribution class. Each capture points to one
component and declares:

- its venue and canonical `eip155` chain;
- a source kind, locator class and non-secret reference;
- an evidence class from the capture-plan schema;
- either a full-dataset scope or lowercase CAIP-10 subject accounts;
- a finality class and a snapshot or inclusive block range, with block
  identifiers when known; and
- complete, partial, failed or unsupported coverage.

Coverage collections use absolute JSON Pointers. Each pointer must resolve to
a list in the unchanged source object, and its declared count must match the
list length. The total must equal the sum of the distinct collection counts.
Complete coverage needs at least one counted collection and cannot carry an
unsupported collection or gap. Partial coverage names an unsupported
collection or gap. Failed and unsupported captures carry no counted rows and
state why in `gaps`. These checks say that the retained response agrees with
the declaration; they do not prove that a provider returned everything it
should have returned.

The fixture at `../tests/fixtures/capture-plan.json` shows one full-dataset
hosted-indexer capture and one subject-scoped archive-log capture.

Source references are provenance labels, not fetch instructions. Do not put
credentials or private URLs in them. Use the `undisclosed` locator class and a
non-secret reference when a locator cannot safely appear in the manifest.
Block identifiers are optional for `unknown` and `provider-reported` finality.
They are required when finality is declared `safe` or `finalized`.

## Ingest

Run from any directory:

```bash
python3 plugins/alexandria/scripts/alexandria.py ingest \
  --plan capture-plan.json --output release
```

The command copies exact source bytes under
`objects/sha256/<first-two-hex>/<digest>` and writes `manifest.json`. It builds
in a temporary sibling directory, verifies the result and installs the output
atomically. A different release at the output path is never replaced. An
identical release is accepted without rewriting it.

The manifest is compact UTF-8 JSON with sorted object keys and one trailing
newline. Duplicate keys, floats, non-finite numbers, integers longer than 78
digits, more than 64 nested levels and oversized control documents are
refused. The release ID is the SHA-256 digest of the canonical manifest object
before its `release_id` field is added. Object identities are SHA-256 digests
of the raw bytes. A raw component is limited to 64 MiB; larger corpora must be
split into separately declared components.

Those numeric restrictions apply to the capture plan and manifest, not the
raw component. Coverage recounting accepts valid JSON floats and large numeric
literals without interpreting them.

A correction supplies a non-empty reason and one or more immutable release IDs
under `release.correction.supersedes`. It creates a new release; it does not
change the prior one.

## Verify

```bash
python3 plugins/alexandria/scripts/alexandria.py verify release
```

Verification reads only the named local directory. It checks canonical
manifest bytes, release identity, component order, digest-derived paths, exact
sizes and digests, component access and redistribution classes,
capture-to-component links, capture source, scope and finality, collection
counts, declared gaps, correction links and exact release-tree membership. An
undeclared file or directory makes verification fail. The command prints the
release ID on success and changes nothing, so it also works against a read-only
release tree.

The command does not establish publisher identity, completeness outside the
declared boundary or canonical-chain finality. It makes no network request and
has no live fallback.
