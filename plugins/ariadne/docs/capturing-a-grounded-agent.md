# Capturing a grounded-agent release

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The grounded-agent predicate now ships as the fifth registered Ariadne predicate, with a closed schema, gates 2 and 5, conformance fixtures and a bounded offline capture path that binds an existing `berean-release/v1` tree without importing or running Berean, executing an agent, regrading evaluations or reaching a network.
<!-- marketplace-context:end -->

`capture-grounded-agent` binds an existing `berean-release/v1` directory to a
grounded-agent/v1 statement. It does not import or run Berean, execute an agent,
grade answers, reach a network, or mutate the release.

```bash
python3 scripts/ariadne.py capture-grounded-agent \
  --release ../berean/examples/aave-v4-demo-v0/release \
  --name aave-v4-demo-v0 \
  --producer-tool berean \
  --producer-version 0.2.0 \
  --producer-command python3 \
  --producer-command plugins/berean/examples/aave-v4-demo-v0/rebuild.py \
  --first-capture-reason 'first Ariadne capture of this Berean release' \
  --output grounded-agent.intoto.json

python3 scripts/ariadne.py verify grounded-agent.intoto.json
```

The producer fields have no defaults. `release.json` does not say which tool or
argv produced the tree, and Ariadne will not invent them. One
`--producer-command` flag records one argv word. The adapter parameters digest
is the canonical digest of the empty parameter object because this command has
no separate producer-parameter input.

## What is checked

The capture independently checks the closed release fields and recomputes the
semantic `release_digest` from Berean's named identity fields. That digest is
not the sha-256 of `release.json`; the exact document bytes are a separate
component and subject.

The corpus manifest is closed and bounded. Its version and digest must match the
release, its paths must be strictly sorted and unique, and its listing digest is
recomputed as sorted `path`, NUL, sha-256, newline records. Every corpus file is
then read through a no-follow descriptor and checked against its declared byte
count and digest.

Reads, answers, evaluation cases and the evaluation report are likewise bound to
their declared bytes. Ariadne does not interpret those answers or regrade the
evaluation report. A present `promotions.jsonl` is parsed as a closed, ordered,
1,000-record chain: every record must name this release, and each promotion must
name the release's declared case and report digests. The statement projects only
the chain bytes and terminal sequence, action and target. Thresholds, result
counts and the producer's substantive verdict remain in the digested file, not
in the Ariadne predicate.

The release inventory is exact. `release.json`, the corpus manifest and files,
optional reads, every answer, optional evaluations, and optional promotion chain
are the complete allowed set. A missing declared file or an undeclared file is a
refusal.

## Filesystem boundary

Paths are portable release-relative paths. Absolute POSIX paths, Windows drive
paths, backslashes, empty segments, dot segments, parent traversal, symlinks and
special files are refused. The release is inventoried before and after capture,
and each regular file is checked for size or metadata changes around its bounded
read. JSON files are UTF-8, integer-only, duplicate-key-free, at most 4 MiB and
at most 32 levels deep. Components are at most 4 MiB each, the release carries at
most the grounded-agent subject ceiling, and aggregate reads stop at 2 GiB.

`--output` is mandatory and must resolve outside the release. A symlink, special
file, or hard-link alias of a release component is refused. Ariadne constructs
and verifies the complete statement in memory, checks the release boundary
again, stages the output beside its destination, flushes it, and replaces the
destination with one rename. A failed check or interrupted replacement exposes
no partial new statement and leaves an existing destination intact.

## Comparison and absence

Without `--previous`, supply `--first-capture-reason`. Reads, evaluations and
promotion evidence that the release does not declare remain JSON `null` with a
bounded reason; absence is never inferred as success.

`--previous` names a bounded bare or DSSE-wrapped grounded-agent/v1 statement.
All its Ariadne gates and predicate checks must pass. The new statement uses the
previous statement's current name and semantic release digest as its baseline.
Comparing a release with itself is refused, and
`--first-capture-reason` is invalid when a previous statement exists. Ariadne
does not verify a DSSE signature in this path; the baseline comes from the
locally supplied, structurally verified statement bytes, not an authorship
claim.

## Authority boundary

A clean capture proves that the projected identity agrees with the local bytes
and that the result satisfies Ariadne's gates. It does not prove Berean's full
release policy, answer quality, chain canonicality, provider independence,
promotion merit, or signer identity. Run Berean's own verifier for its release
claims and an external Sigstore or cosign verifier for signature identity.
