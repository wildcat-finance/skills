# Hexaemeron Promise Machine overlays

This first-party file declares the promises Hexaemeron makes around vendored
instructions. Each declaration binds the local bytes to an immutable upstream
commit, path and digest. The overlay is unavailable when the local digest
changes or the separately verified upstream bytes no longer match. These
records do not establish who controlled the upstream publisher identity.

### hexaemeron-fizz-harness-campaign

- Path: `plugins/hexaemeron/skills/fizz/SKILL.md`
- Repository: `https://github.com/pashov/skills.git`
- Commit: `aadee2ca49cae20246af378ef791d2d4f941e237`
- Upstream path: `fizz/SKILL.md`
- Upstream SHA-256: `fa706e94e9ec3456528985548f46461d44442d9223e26b2a0dbbb8b5f522172a`
- Local SHA-256: `62a60df4cec160511b8ef36433eef7c8805d0b4a398491293eb4542ab73539bd`
- Verification status: upstream-bytes-verified, local-bytes-modified, publisher-authentication-unknown
- Promise: A completed Fizz run establishes that the generated Echidna or Medusa harness builds and that the named campaign actually ran against it with its preserved configuration and results.
- Evidence: The digest-matched instruction, source snapshot, generated harness and manifest, build result, named engine command, campaign configuration, bounded raw output and machine-readable result where the engine supplies one.
- Evidence classes: checked, recorded
- Boundary: The result covers the generated harness and campaign that ran; it does not establish exhaustive property discovery, semantic adequacy of every property, absence of vulnerabilities or a security sign-off.
- Authorises: Using the generated harness and recorded campaign result as evidence for the properties and target boundary explicitly exercised.
- Consequence: 3
- Refuses: A stale overlay digest, a harness that does not build, a campaign inferred from generated files but never run, missing configuration, narrowed bounds used to hide a failure or a claim broader than the exercised properties.
- Recovery: Reconcile the upstream instruction digest, regenerate the harness from the named source, restore the campaign configuration, run the selected engine and retain its actual result.
- Exceptions: none

### hexaemeron-fizz-convert-properties

- Path: `plugins/hexaemeron/skills/fizz/skills/fizz-convert/SKILL.md`
- Repository: `https://github.com/pashov/skills.git`
- Commit: `aadee2ca49cae20246af378ef791d2d4f941e237`
- Upstream path: `fizz/skills/fizz-convert/SKILL.md`
- Upstream SHA-256: `59cd4b4ef5dc56315782a7d25222afb286a24e63e438530cbd0044293ea54af7`
- Local SHA-256: `59cd4b4ef5dc56315782a7d25222afb286a24e63e438530cbd0044293ea54af7`
- Verification status: upstream-bytes-verified, local-bytes-identical, publisher-authentication-unknown
- Promise: A completed Fizz Convert run establishes that the selected pending property was translated into wired Solidity assertion code, the harness builds and the corresponding source checklist entry was updated.
- Evidence: The digest-matched instruction, selected property text and identifier, generated assertion and handler wiring, build output, changed checkbox and bounded diff.
- Evidence classes: checked, recorded
- Boundary: The result proves mechanical conversion and buildability of the selected property; it does not establish that the property is semantically correct, reachable, complete or adequate for security review.
- Authorises: Treating the selected checklist entry as implemented in the named harness and passing it to a real fuzz campaign.
- Consequence: 2
- Refuses: A stale overlay digest, an ambiguous property, unwired assertion, failed build, unchecked source update or a semantic-completeness claim unsupported by execution.
- Recovery: Reconcile the upstream instruction digest, clarify one property, repair its assertion and wiring, rebuild the harness and update only the matching checklist entry.
- Exceptions: none

### hexaemeron-fizz-sync-drift

- Path: `plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md`
- Repository: `https://github.com/pashov/skills.git`
- Commit: `aadee2ca49cae20246af378ef791d2d4f941e237`
- Upstream path: `fizz/skills/fizz-sync/SKILL.md`
- Upstream SHA-256: `e969cd8a447941989715840e24aa6a915c0fd795effabd912b3c627598a95e16`
- Local SHA-256: `e969cd8a447941989715840e24aa6a915c0fd795effabd912b3c627598a95e16`
- Verification status: upstream-bytes-verified, local-bytes-identical, publisher-authentication-unknown
- Promise: A completed Fizz Sync run establishes that bounded source-interface drift was reconciled into the existing harness, stale properties were quarantined, generated stubs were refreshed and the updated harness builds.
- Evidence: The digest-matched instruction, prior and current source snapshots, ABI drift report, quarantined-property record, regenerated stubs, refreshed snapshot, bounded diff and build result.
- Evidence classes: checked, recorded
- Boundary: The result covers syntactic and declared interface reconciliation within the inspected source boundary; it does not prove semantic equivalence, preserve unstated assumptions or validate property adequacy.
- Authorises: Running the reconciled harness against the current named source while treating quarantined properties as unresolved.
- Consequence: 2
- Refuses: A stale overlay digest, unbounded or unidentified source drift, silently deleted properties, a failed build, an unrefreshed snapshot or any claim that ABI agreement proves semantic agreement.
- Recovery: Reconcile the upstream instruction digest, restore the before and after snapshots, classify every drift item, quarantine rather than erase stale properties, regenerate the affected stubs and rebuild.
- Exceptions: none

### hexaemeron-x-ray-preaudit

- Path: `plugins/hexaemeron/skills/x-ray/SKILL.md`
- Repository: `https://github.com/pashov/skills.git`
- Commit: `aadee2ca49cae20246af378ef791d2d4f941e237`
- Upstream path: `x-ray/SKILL.md`
- Upstream SHA-256: `b23bb94517805c1b8ce717d0e1e0282b0b5c14c7b16f4c32e73940292d3d4a41`
- Local SHA-256: `b23bb94517805c1b8ce717d0e1e0282b0b5c14c7b16f4c32e73940292d3d4a41`
- Verification status: upstream-bytes-verified, local-bytes-identical, publisher-authentication-unknown
- Promise: A completed X-Ray run establishes that the required pre-audit views were produced for the named repository snapshot and complete current logical scope, with their source boundary and unresolved gaps visible; when source reuse is selected, it applies only to closed, complete, validated per-source preparation entries after every current source was read and digested.
- Evidence: The digest-matched vendored instruction; the first-party adapter `plugins/hexaemeron/lib/xray_reuse.py` at SHA-256 `23e628b7ffc963000ace6b081c57de267267c37108527ef7d3a092dbf0fcab10`; the repository commit, complete current scope, every current source read and digest, current source and dependency digests, validated plan, exact current union and exact current fact union, fresh coverage, history, integration and cross-source analysis, fresh global synthesis, and output manifest; and current-run `architecture.json`, `x-ray.md`, `entry-points.md`, and `invariants.md` with their cited inputs and digests.
- Evidence classes: checked, recorded, inferred
- Boundary: The adapter is a preparation layer only. Cache validity does not establish that a reused fact was originally correct, and no global synthesis, final output, finding, or security conclusion is reusable. The four artefacts remain analysis aids, not an audit or evidence of exploitability or absence of defects, and inherit every omission in the inspected repository boundary.
- Authorises: Beginning a human or agent audit with the four named pre-audit views as scoped orientation material.
- Consequence: 1
- Refuses: A stale X-Ray or adapter digest, an unnamed repository snapshot, a skipped current-source read or digest, an unsafe or incomplete current scope, a prior/current scope mismatch or other cache uncertainty that does not produce named full recomputation, a stale or incomplete preparation entry, a fact union that differs from the exact current inventory, missing fresh global synthesis, a missing or unbound required artefact, uncited conclusions, hidden exclusions, or language that presents pre-audit analysis as security sign-off.
- Recovery: Reconcile both instruction digests, repair and reread the complete source boundary, discard uncertain cache material and run the named full recomputation, then regenerate fresh coverage, history, integration and cross-source analysis, fresh global synthesis, and all four views while leaving every unresolved gap explicit.
- Exceptions: none

### hexaemeron-solidity-audit-report

- Path: `plugins/hexaemeron/skills/solidity-auditor/SKILL.md`
- Repository: `https://github.com/pashov/skills.git`
- Commit: `aadee2ca49cae20246af378ef791d2d4f941e237`
- Upstream path: `solidity-auditor/SKILL.md`
- Upstream SHA-256: `1c1cf4e99d042e7aadc56b622d97a07d3286f4786838a05510697c814d1e983f`
- Local SHA-256: `1c1cf4e99d042e7aadc56b622d97a07d3286f4786838a05510697c814d1e983f`
- Verification status: upstream-bytes-verified, local-bytes-identical, publisher-authentication-unknown
- Promise: A completed Solidity Auditor run establishes that all twelve prescribed audit roles inspected the named Solidity scope, their raw results crossed the required wait barrier and the final report deduplicated, completeness-checked and judged the submitted findings.
- Evidence: The digest-matched instruction, repository commit and Solidity scope, twelve role prompts and raw outputs, completion barrier, deduplication record, completeness pass, judgement record and final report.
- Evidence classes: checked, recorded, inferred
- Boundary: The report establishes performance of the prescribed review process over the named scope; findings remain judgements and a clean report does not prove the absence of vulnerabilities or replace independent review.
- Authorises: Using the scoped report as one security-review input and advancing only according to its explicit findings, uncertainties and unresolved coverage.
- Consequence: 3
- Refuses: A stale overlay digest, fewer than twelve isolated role results, synthesis before the wait barrier, missing raw outputs, hidden scope exclusions, undeduplicated findings or a claim of defect absence.
- Recovery: Reconcile the upstream instruction digest, restore the exact scope, rerun every missing or compromised role independently, wait for all raw results and repeat deduplication, completeness checking and judgement.
- Exceptions: none
