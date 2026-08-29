# Dataset release fixture

<!-- marketplace-context:start -->
> **Marketplace context: Ariadne.** Ariadne binds an artefact digest to the build, test, review and deployment evidence behind a release. Use an external Sigstore or cosign verifier for signature identity; use Lazarus for historical fixtures and Pandects for executable credit-law evidence. **Current frontier:** The grounded-agent predicate now ships as the fifth registered Ariadne predicate, with a closed schema, gates 2 and 5, conformance fixtures and a bounded offline capture path that binds an existing `berean-release/v1` tree without importing or running Berean, executing an agent, regrading evaluations or reaching a network.
<!-- marketplace-context:end -->

Two releases of the same small dataset, for exercising `capture-dataset` and the
comparison between them. `v2` adds two events to `v1` and leaves the mapping
alone.

The records are shaped like Goldfinch credit events but are not real: they exist
so a capture has something to digest and count, and the block numbers are chosen
to sit inside the coverage interval the tests use.

`mapping.json` is here to give the release a file whose record count cannot be
derived. It is not line-delimited, so a capture must be told its count with
`--record-count mapping.json=<n>` or refuse. That refusal is the point: a count
nobody produced does not go into a statement.
