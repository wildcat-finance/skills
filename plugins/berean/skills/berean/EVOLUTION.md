# Berean evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `berean-v0.2.0`
- Frontier status: `open`
- Frontier revision: `wildcat-reference-release`
- Current frontier: The reference release answers against a frozen demonstration corpus and preserved Aave v4 mainnet reads; no release yet cites live Wildcat documentation or a captured Wildcat market read, and no Ariadne statement binds a berean release.
- Next Fiat job: Ship the first berean release grounded in captured Wildcat documentation and Wildcat market reads, replacing the demonstration corpus in the reference deployment. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.
- Sources: [../../../../SOURCES.md](../../../../SOURCES.md)

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `berean-v0.1.0` | baseline | `wildcat-reference-release` | `961c0fcb214b50ec3ada19cb8cec8e8c4557e229f72e3eaf9b4f43b325d8cca0` | [README marketplace-context](../../README.md) | Versioning starts here. The plugin is built from its Wildcat Commons specification and the held frontier is the first grounded Wildcat deployment. |
| `berean-v0.2.0` | generation | `wildcat-reference-release` | `961c0fcb214b50ec3ada19cb8cec8e8c4557e229f72e3eaf9b4f43b325d8cca0` | [question-span guards](../../tests/test_answers.py), [study](../../../../docs/berean-question-spans/study.md) | A `user_supplied` sentence names at least one `question:<start>-<end>` span over the UTF-8 byte offsets of `question`, and each span must re-slice to whole, non-blank bytes. An empty list is refused, citation and read ids stay refused on that class, and no citation or read id may begin with `question:`. A per-sentence field and a top-level span artefact were rejected as format changes. The held frontier and Next Fiat job stay unchanged. |
