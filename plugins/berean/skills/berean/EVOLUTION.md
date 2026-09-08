# Berean evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `berean-v1.2.0`
- Frontier status: `mature`
- Frontier revision: `wildcat-reference-complete`
- Current frontier: The Wildcat reference release pins three captured official documents and five recorded market calls at Ethereum block 25907928, with an unsigned Ariadne statement binding all 18 release components. The release frontier is mature; authored answers keep its demonstration status mixed.
- Next Fiat job: None -- mature
- Sources: [../../../../SOURCES.md](../../../../SOURCES.md)

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `berean-v0.1.0` | baseline | `wildcat-reference-release` | `961c0fcb214b50ec3ada19cb8cec8e8c4557e229f72e3eaf9b4f43b325d8cca0` | [README marketplace-context](../../README.md) | Versioning starts here. The plugin is built from its Wildcat Commons specification and the held frontier is the first grounded Wildcat deployment. |
| `berean-v0.2.0` | generation | `wildcat-reference-release` | `961c0fcb214b50ec3ada19cb8cec8e8c4557e229f72e3eaf9b4f43b325d8cca0` | [question-span guards](../../tests/test_answers.py), [study](../../../../docs/berean-question-spans/study.md) | A `user_supplied` sentence names at least one `question:<start>-<end>` span over the UTF-8 byte offsets of `question`, and each span must re-slice to whole, non-blank bytes. An empty list is refused, citation and read ids stay refused on that class, and no citation or read id may begin with `question:`. A per-sentence field and a top-level span artefact were rejected as format changes. The held frontier and Next Fiat job stay unchanged. |
| `berean-v1.2.0` | evolution | `wildcat-reference-complete` | `3636f088014a4a0ff75ba24026e4d2762ceea98fd2165319b13512b5c7e2eb16` | [offline demo](../../examples/wildcat-mainnet-v0/demo.py), [release handoff](../../../../docs/berean-wildcat-reference/handoff.md) | The first Wildcat reference pins three official documents and five fixed-block calls, reproduces all 18 components, grades ten authored cases and binds an unsigned Ariadne statement. Full mutable marketplace prose was reconciled. No concrete successor to this release frontier was established, so it is mature; live model demonstration remains a separate open lane. |

## Wildcat reference packaging decision

On 2026-09-08, the [selected design](../../../../docs/berean-wildcat-reference/design-evidence.json)
chose `selected-docs`: three unchanged official document blobs totalling
40,001 bytes. The rejected `whole-markdown` option retained 86 files and
496,297 bytes, including deprecated and other-chain material outside the
finite market read set. Both passed the source, schema, time and recovery
gates; retained corpus bytes selected the smaller corpus. Linked pages remain
uncaptured, so questions requiring them must be refused. The [study](../../../../docs/berean-wildcat-reference/study.md)
holds the measurements and scope. This records a packaging choice only;
release conformance remains pending and no evolution is earned here.
