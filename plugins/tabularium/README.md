# Tabularium

<!-- marketplace-context:start -->
## In one line

Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning.

**Try something else when.** Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay.

**Current frontier.** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.

**Next Fiat job.** Use /hexaemeron:fiat to ship Compound v3 Phase 1 from Alexandria raw evidence with a new canonical and coverage schema version, supply, withdraw, base-transfer and absorb mappings, a mined borrower-to-borrower transfer witness, hostile fixtures and a byte-identical offline Ethereum USDC specimen. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

A public record of on-chain credit events that keeps the venue's source record
beside every common row.

The checked-in releases preserve three narrow credit records: Goldfinch's
borrower-side index, one Euler v1 canonical-proxy block and one Euler V2 owner
activity response from the Euler V3 API. Each can be rebuilt after its source
endpoint changes or disappears.

Tabularium also ships a non-canonical Compound v3 Phase 0 execution witness.
It consumes a verified Alexandria raw release and rebuilds ordered calls,
relevant proxy-storage writes and one signed-principal transition. These facts
prove the recorded method for one transaction; they are not canonical credit
events or a market history.

The common event families do not flatten the venue. A row says
`goldfinch.borrow`, `euler-v1.borrow` or `euler-v2.interest-accrued`, keeps the
complete native entity, and names the mapping rule and adapter version that
produced it. A repayment row records the venue event; it does not say that the
borrower's whole debt was settled. Euler interest remains accrual rather than
being flattened into a fresh draw.

Three rules hold the release together:

1. Raw evidence and interpretation stay separate. The source bytes are never
   rewritten to make the canonical output tidier.
2. Coverage is a file, not an assurance. Mapped and unsupported entity counts,
   interpretation versions and known gaps sit in `coverage.json`.
3. Verification rebuilds. Matching a declared digest is not enough; `verify`
   maps the preserved source again and requires the bytes, order and source
   selectors to agree.

## Run it

From this directory, `plugins/tabularium`:

```bash
python3 scripts/tabularium.py build \
  --adapter <goldfinch|euler-v1|euler-v2> \
  --source <release-dir>/source.json \
  --capture-manifest <release-dir>/capture.json \
  --out <release-dir>/events.jsonl \
  --manifest <release-dir>/coverage.json \
  --release <release-id>

python3 scripts/tabularium.py verify <release-dir>/coverage.json

python3 scripts/tabularium.py compound-witness \
  --alexandria-release <alexandria-release> \
  --out facts.jsonl --manifest witness.json
python3 scripts/tabularium.py verify-compound-witness \
  --alexandria-release <alexandria-release> \
  --facts facts.jsonl --manifest witness.json
```

`build` refuses a capture whose source digest, byte count, adapter, scope or
source metadata disagrees with the preserved bytes. Goldfinch remains the
default adapter for backward compatibility. It writes canonical JSONL and a
coverage manifest only inside the release directory.

`verify` reaches no network and writes nothing. It refuses absolute paths,
parent traversal, symlinks, aliased files, unsupported versions, malformed
JSON, count drift, duplicate selectors, reordered rows and canonical bytes
that do not match a fresh source rebuild.

## The checked-in releases

[`examples/goldfinch-v0`](examples/goldfinch-v0/README.md) contains the
unchanged source and capture manifest, the 511-row ledger, its coverage
manifest, a data dictionary and a rebuild demonstration.

[`examples/euler-v1-v0`](examples/euler-v1-v0/README.md) preserves one real
borrow log from the canonical Euler v1 proxy in block 14,531,589.
[`examples/euler-v2-v0`](examples/euler-v2-v0/README.md) preserves one real,
fixed owner/second response from the Euler V3 API. Its manifest calls the
protocol generation `euler-v2` and the source API `euler-v3`; these are not the
same version axis.

[`examples/compound-v3-phase0-v0`](examples/compound-v3-phase0-v0/README.md)
rebuilds 11 non-canonical facts from Alexandria's checked-in release: two
ordered calls, eight relevant storage writes and one signed-principal
transition.

From the repository root:

```bash
python3 plugins/tabularium/examples/goldfinch-v0/rebuild.py
python3 plugins/tabularium/examples/euler-v1-v0/rebuild.py
python3 plugins/tabularium/examples/euler-v2-v0/rebuild.py
python3 plugins/tabularium/examples/compound-v3-phase0-v0/rebuild.py
```

The demonstration copies the preserved inputs to a new temporary directory,
builds there, makes all four release files read-only, verifies them offline and
compares the canonical and coverage bytes with the committed release. It never
rewrites the example.

The Goldfinch source also contains `_meta`, `callableLoans`, `creditLines` and
`tranchedPools`. Their counts remain visible in the coverage manifest, but this
adapter does not turn them into canonical events.

## What it never proves

Each boundary is what its hosted indexer or public RPC reported. The Euler v1
release retains its log's block hash; the Euler V2 API rows omit block hashes
and transaction indexes. None of the releases independently proves a chain
boundary.

The release is unsigned. Offline verification proves that the four local files
agree with one another and with the implemented mapping. It does not establish
publisher identity or authenticity.

No address-to-person inference and no counterparty score enter the ledger.
Those are different claims, with different evidence, and do not belong inside
an event record.

## Adding a venue or correcting a release

[`docs/adding-an-adapter.md`](docs/adding-an-adapter.md) sets out the source
validation, mapping, provenance, coverage and fixture work a new venue needs.
[`docs/release-policy.md`](docs/release-policy.md) makes published
interpretations immutable: a corrected mapping gets a new version and a new
release directory rather than replacing old bytes.

[`docs/compound-v3-preservation.md`](docs/compound-v3-preservation.md) specifies
the Compound III mapping and preservation requirements. Alexandria's linked
harvest specification owns raw collection; this document explains why logs
alone miss or misclassify debt transitions, what Phase 0 now proves and what
the Phase 1 canonical mapping still needs.

## Tests

From the repository root:

```bash
python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium
```

Python 3.9 or later, standard library only. The tests make no network request.

## Reading further

- [`examples/goldfinch-v0/DATA-DICTIONARY.md`](examples/goldfinch-v0/DATA-DICTIONARY.md)
  -- every canonical field and the limits of its meaning.
- [`examples/euler-v1-v0/DATA-DICTIONARY.md`](examples/euler-v1-v0/DATA-DICTIONARY.md)
  and [`examples/euler-v2-v0/DATA-DICTIONARY.md`](examples/euler-v2-v0/DATA-DICTIONARY.md)
  -- Euler schema v2 provenance, amount legs and source limits.
- [`examples/compound-v3-phase0-v0/DATA-DICTIONARY.md`](examples/compound-v3-phase0-v0/DATA-DICTIONARY.md)
  -- the non-canonical execution facts and their refusal boundaries.
- [`docs/adding-an-adapter.md`](docs/adding-an-adapter.md) -- how a second venue
  earns a release.
- [`docs/release-policy.md`](docs/release-policy.md) -- how a later
  interpretation supersedes an earlier one without rewriting it.
- [`docs/compound-v3-preservation.md`](docs/compound-v3-preservation.md) -- the
  Compound III mapping and preservation requirements.
- [`docs/euler-preservation-study.md`](docs/euler-preservation-study.md) and
  [`docs/euler-preservation-runbook.md`](docs/euler-preservation-runbook.md) --
  the evidence decisions and atomic delivery boundary for the Euler releases.
- [`audit/AUDIT.md`](audit/AUDIT.md) -- every audit round and the fixes it
  required.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
