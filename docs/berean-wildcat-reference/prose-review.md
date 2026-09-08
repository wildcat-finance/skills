# Marketplace prose reconciliation

The review covered 207 source surfaces. The parent reader covered 126 sibling
files; Mason covered root, Hexaemeron, Berean and the two Berean example READMEs.
The initial 209-path Markdown survey contributed 205 reads: CONTRIBUTORS.md
and SOURCES.md are generated inventories, while docs/ledger-declared-inputs-demo.md
and docs/test-scoping-dedup-playbook.md are completed historical records. These
four paths are retained in the exclusions inventory. Adding both Berean example
READMEs gives 207 reads; no surveyed path was silently dropped.

Files were read sequentially in complete bounded chunks. Immutable ledger rows
were excluded after their current headers. Search supported subsequent lookup;
it did not substitute for reading.

`cold-read-inventory.json` records each baseline digest, byte count, reader and
actual line spans, separately from the final digest and candidate review.
`parent-cold-read-baseline.json` and `mason-cold-read-baseline.json` preserve the
original reader inventories without changing their bytes. Changed candidates
received complete diff review; unchanged context retained its baseline review.

`cold-read-exclusions.json` names 864 excluded paths with baseline identities and
reasons: preserved records and specimens, upstream material, owner-generated
copies, and completed historical records. The supplied Horos maintainer request
and the Pandects design study were read as historical rationale and preserved.
Rolling marketplace context in example READMEs remains mutable. Captured corpus
documents remain under their fixtures/docs boundaries.

The review reconciled current capabilities, counts, reference commands and
qualification language. Berean alone earns an evolution: v0.2.0 to v1.2.0,
retaining generation 2 and epoch 0. Its completed release frontier is mature.
The demonstration remains mixed because its answers are authored records;
no model execution was supplied. Its existing actual-agent-answer job remains
open. Sibling skill frontiers, versions and held jobs remain unchanged.
Installed package patch counters advance for changed shipped sources.

All 18 Codex manifest description and interface summaries also received a
structured-field prose review. Anamnesis now distinguishes its separately
readable Synkrisis projection from admission to Synkrisis; this review does not
claim that the other JSON fields were prose cold reads.

Prospective durable records received Sapheneia shaping, Imprimatur, Vulgate
surface review with frozen candidate parity, and final Imprimatur. Fixed owner
reports and the receipted runbook were copied without rewriting their bytes.

`preserved-release-inventory.json` proves that 47 tracked example files equal
those in signed Step 2 commit
`f05365a5980dcbe5bab9ebad789dad5ad5a3c89e`. This includes the Aave release and
executable example, Wildcat inputs, release, rebuild and unsigned statement.
Rolling README context is excluded from that fixed inventory. Existing Aave
consumer files received no changes.

The registered Wildcat demonstration passed all five declared observations,
including 18 component bindings, ten evaluation cases, mixed status, no model
execution, and citation, block and missing-read refusals. The selected-docs
probe and integration design-evidence checker both exited zero. The fixed
matrix and original reports remain unchanged; the final selected-docs report
is retained under `design-reports/selected-docs-final-release.json`.

Horos CLI help at `plugins/horos/skills/horos/scripts/horos.py:10` still
describes every read as prefix-bounded. The README now states the whole-file
content-addressed hashing exception. The runtime source remains unchanged;
this stale help description changes no classification behavior and warrants
no standalone issue.

This record covers local implementation evidence. It does not authorise a
controller transition, publication, or resumption of #1144.
