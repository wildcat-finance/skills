# Protasis study: Anamnesis

**Date:** 31 August 2026
**Study target:** `audit-findings-corpus/README.md` at
`wildcat-finance/skills-braintrust@ba5e5b565a2e6e948604e1bd3fda6d8b5671854f`
**Implementation base:**
`wildcat-finance/skills@1c1137898bce9086c34310bd29b5cf8a889f800c`

This study turns the decision memo into a buildable prototype specification.
It does not start a Fiat run or claim that the pending pilot evidence exists.

## 1. Problem statement

Build a new Promise Machine member, with the working id `anamnesis`, for
Shoggoth contributors who need a durable corpus of audit findings, remediation
attempts, verification evidence, and bounded lessons. Elenchus must be able to
retrieve a historical analogue without inheriting its conclusion. Synkrisis
must be able to compare a checked projection without taking custody of the
source material.

A working prototype admits 25–50 adjudicated Warden findings from several runs
and skills, including zero-finding rounds, duplicates, rejected or accepted
findings, multi-finding fixes, non-guarded fixes, and inconclusive Elenchus
results. It emits a deterministic release whose original source identity,
rights basis, native status, normalised assertions, many-to-many remediation
edges, verification state, exclusions, and unknowns remain inspectable.

The eventual demo path is:

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo \
  --specimen plugins/anamnesis/specimens/pilot
```

That command must rebuild the release twice, compare its digests, validate an
Elenchus analogue response and a Synkrisis cohort projection, and write the
closed integration report named by the design-evidence record. It proves only
the bounded specimen and adapters, not ecosystem prevalence or causal fix
efficacy.

## 2. Prior art

The starting point is the [audit findings corpus decision](../README.md), added
by direct commit `1572bf7`. No merged pull request changed this idea stream.
The last two pull requests merged to the repository's `main` before it were
[skills-braintrust #6](https://github.com/wildcat-finance/skills-braintrust/pull/6)
and [skills-braintrust #4](https://github.com/wildcat-finance/skills-braintrust/pull/4).
Both concern commercial-credit-sidecar history migration and its audit loop;
neither supplies a corpus schema or member boundary.

Those pull requests referenced `audit/rounds/` records and migration-only
machinery. The cleanup at `ba5e5b565a2e6e948604e1bd3fda6d8b5671854f`
removed them on the user's instruction. There is now no `audit/AUDIT.md`,
`AUDIT_SYNOPSIS.md`, or `audit/rounds/` source in the target tree. No synopsis
was substituted for a source, and this study does not treat the removed paths
as a runtime dependency. Git history is still available as historical context;
actual pilot source admission remains a checked Step 2 precondition.

Current Shoggoth contracts leave the corpus promise unowned:

- [Warden](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/plugins/hexaemeron/agents/warden.md#L74)
  emits one source-bound audit-round record and its synopsis.
- [Elenchus](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/plugins/hexaemeron/skills/elenchus/SKILL.md#L27)
  starts from one failure in hand and proves a current causal repair and guard.
- [Synkrisis](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/plugins/synkrisis/skills/synkrisis/SKILL.md#L30)
  builds checked cohorts from admitted run observations and refuses capture,
  redaction, causal triage, and autonomous action.

Protasis's current evidence model came from
[framework-70](https://github.com/wildcat-finance/skills/issues/1000),
[ADR-061](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/docs/decisions/ADR-061-lock-designs-with-progressive-checked-evidence.md),
and [PR #1002](https://github.com/wildcat-finance/skills/pull/1002). The next
merged change, [PR #1003](https://github.com/wildcat-finance/skills/pull/1003),
rewrote public descriptions but did not change the evidence semantics. This
study uses `protasis-design-evidence/v1` exactly as delivered there.

External prior art supplies parts of the record model, not a complete answer:

- [OSV](https://ossf.github.io/osv-schema/) separates aliases, upstream and
  related records, source ranges, and browser-oriented fix links.
- [SARIF 2.1.0 plus Errata 01](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
  binds rules, locations, runs, source revisions, and proposed edits.
- [CSAF 2.1](https://docs.oasis-open.org/csaf/csaf/v2.1/csaf-v2.1.html)
  separates workaround, mitigation, planned fix, vendor fix, and no-fix states.
- [MITRE's root-cause mapping guidance](https://cwe.mitre.org/documents/cwe_usage/guidance.html)
  requires mapping precision and respects entries that must not be used.
- [DAppSCAN](https://arxiv.org/abs/2305.08456) shows the value and labour cost
  of curating 1,199 real-world audit reports into 9,154 weakness observations.
- [Vul4J](https://bqcuong.github.io/papers/msr22.pdf) retained 79 reproducible
  cases after examining 1,803 fix commits for 912 Java vulnerabilities.
- [Croft, Babar, and Kholoosi](https://conf.researchr.org/details/icse-2023/icse-2023-technical-track/45/Data-Quality-for-Software-Vulnerability-Datasets)
  show that label error and duplication can materially distort downstream work.
- [Code4rena](https://docs.code4rena.com/awarding/awarding-process) and
  [Sherlock](https://docs.sherlock.xyz/audits/judging/guidelines) distinguish
  submissions, adjudication, duplicate groups, and fix verification in their
  current workflows.

## 3. Constraints and non-goals

- The human deliverables are Markdown only. The JSON files under
  `protasis/.hexaemeron/` exist solely because the requested evidence-model test
  has a closed machine interface. No PDF is produced.
- The study is valid against the exact bases named above. A future Fiat run on
  a different `wildcat-finance/skills` base must recheck the two latest merged
  changes, the Promise Machine boundaries, and all in-scope audit sources.
- Python is pinned to `3.14.6`. The implementation uses the standard library
  unless a dependency earns an explicit, pinned addition.
- The member is one plugin and one canonical skill. It may expose several
  operations, but they share one source, assertion, policy, and release model.
- The source unit is immutable bytes or a digest-bound private locator. A
  normalised record never replaces the native record.
- The graph preserves engagement, submission, duplicate cluster, canonical
  finding, occurrence, remediation attempt, verification, residual or
  regression, and derived pattern as separate entities or relations.
- The prototype does not train a model, rank auditors, estimate ecosystem
  prevalence, import embargoed material, scrape arbitrary URLs, deploy a
  service, mutate a consumer repository, or assert that merged means fixed.
- Public visibility is not a rights basis. GitHub's
  [licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
  and Sherlock's statement that report links have protocol-team permission
  make admission and redistribution separate decisions.
- Naming is fixed only for this design as `anamnesis`; visual identity,
  marketplace copy, and a general training interface are deferred.

## 4. Design options

The normative matrix is
the run's `.hexaemeron/design-evidence.json` record. Its selection facts
are bound to `wildcat-finance/skills@1c1137898bce9086c34310bd29b5cf8a889f800c`
and the decision memo by
`.hexaemeron/selection-observations.json`.

| Candidate | Construction | Trade |
| --- | --- | --- |
| `anamnesis-member` | Add a dedicated plugin that owns admission, curation, release, and typed projections | More visible scaffolding; no existing member promise is broadened |
| `elenchus-library` | Put the corpus beside Elenchus and make Elenchus own its lifecycle | Cheap reading-list pilot; merges one-failure causal proof with long-lived custody and release |
| `synkrisis-extension` | Make Synkrisis ingest sources before comparing them | Reuses cohort machinery; merges source custody and normalisation with downstream inference |

`anamnesis-member` is the unique eligible frontier. The other two candidates
fail the closed-corpus and preserved-consumer gates, and each broadens one
existing promise. The count is a design-coordination surface, not a delivery
duration estimate. Release size, rights admission, and rebuild behaviour remain
conformance evidence because no implementation exists from which to measure
them.

Anamnesis exposes three bounded promises:

1. `anamnesis-ingest` validates source identity, acquisition, scope,
   disclosure, and rights without asserting that the source is true.
2. `anamnesis-curate` emits source-linked finding, remediation, verification,
   and relationship assertions without upgrading their evidence state.
3. `anamnesis-release` rebuilds a declared cohort and projections from named
   inputs while preserving exclusions, unknowns, policy versions, and digests.

## 5. Risk register seed

```risk-register
source-rights | the boundary between a visible report and a redistributable corpus object | every admitted byte has an explicit permission basis or stays private or digest-only
source-byte-drift | the boundary between a cited source and later fetched bytes | acquisition records bind exact bytes and refuse a digest mismatch
evidence-strengthening | the boundary between native assertions and normalised assertions | mappings retain source state and never promote reported or merged to verified
duplicate-collapse | the boundary between submissions and canonical findings | duplicate edges preserve every submission and the policy version that joined them
fix-state-collapse | the boundary between a remediation proposal and its lifecycle | proposed applied released deployed reverted and verified remain independent states
many-to-many-loss | the boundary joining findings remediation attempts and verification | validation preserves clusters where one change addresses several findings or one finding needs several changes
private-egress | the boundary between restricted sources and release or adapter output | release policy fails closed before writing excerpts locations or derived text
partial-release | the staging boundary of a killed build | verification refuses any release not atomically completed with a closed manifest and digest
taxonomy-drift | the boundary between native labels and a versioned taxonomy | mappings name taxonomy version mapper rationale confidence and counterevidence
cohort-leakage | the boundary between a checked cohort and an aggregate claim | every aggregate names its denominator unit era inclusion policy missingness and exclusions
adapter-overreach | the boundary between Anamnesis and Elenchus or Synkrisis | adapters validate a closed projection and cannot import the consumer's stronger verdict into source records
```

The audit loop must cite every id as reviewed or not applicable. A rights gap,
digest mismatch, strengthened evidence state, invalid relation, or incomplete
release is a refusal, not a warning.

## 6. Glossary seeds

- **Native record:** the producer's source bytes and identifiers, unchanged.
- **Assertion:** a curator's source-linked claim with method, version, and state.
- **Submission:** one reporter's candidate issue before duplicate handling.
- **Canonical finding:** an adjudicated finding identity; never a replacement
  for its submissions.
- **Occurrence:** one scoped manifestation of a canonical finding.
- **Remediation attempt:** one proposal, change, release, configuration, or
  mitigation linked many-to-many with findings.
- **Verification:** a review, test, invariant, specimen, or Elenchus result with
  its exact environment and evidence.
- **Guarded:** the narrow Elenchus state supported by an old-fails/new-passes
  specimen and bound runner; not general correctness.
- **Projection:** a closed read-only view admitted by a named consumer adapter.
- **Cohort:** the exact included records under one versioned policy.
- **Rights basis:** the licence, permission, contract, or digest-only rule that
  controls preservation and release.
- **Unknown:** evidence not established; distinct from none or not applicable.

## 7. Sources

Project sources:

- [Decision memo](../README.md) and direct commit `1572bf7`.
- [Promise Machine at the implementation base](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/PROMISE_MACHINE.md).
- [Protasis evidence delivery](https://github.com/wildcat-finance/skills/pull/1002),
  [ADR-061](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/docs/decisions/ADR-061-lock-designs-with-progressive-checked-evidence.md),
  and [framework-70](https://github.com/wildcat-finance/skills/issues/1000).
- [Public prose follow-up](https://github.com/wildcat-finance/skills/pull/1003).
- [Warden](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/plugins/hexaemeron/agents/warden.md),
  [Elenchus](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/plugins/hexaemeron/skills/elenchus/SKILL.md),
  and [Synkrisis](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/plugins/synkrisis/skills/synkrisis/SKILL.md).
- Historical target [PR #6](https://github.com/wildcat-finance/skills-braintrust/pull/6)
  and [PR #4](https://github.com/wildcat-finance/skills-braintrust/pull/4).

External sources:

- [OSV schema](https://ossf.github.io/osv-schema/),
  [SARIF 2.1.0 plus Errata 01](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html),
  [CSAF 2.1](https://docs.oasis-open.org/csaf/csaf/v2.1/csaf-v2.1.html), and
  [MITRE CWE mapping guidance](https://cwe.mitre.org/documents/cwe_usage/guidance.html).
- [DAppSCAN](https://arxiv.org/abs/2305.08456),
  [Vul4J](https://bqcuong.github.io/papers/msr22.pdf), and
  [Data Quality for Software Vulnerability Datasets](https://conf.researchr.org/details/icse-2023/icse-2023-technical-track/45/Data-Quality-for-Software-Vulnerability-Datasets).
- [Code4rena awarding](https://docs.code4rena.com/awarding/awarding-process),
  [Sherlock judging](https://docs.sherlock.xyz/audits/judging/guidelines),
  [Sherlock public reports](https://github.com/sherlock-protocol/sherlock-reports),
  and [GitHub licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

## 8. Signals, and the questions behind them

[Ephoros](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/plugins/hexaemeron/skills/ephoros/SKILL.md)
owns the signal contract. The prototype must answer four operator questions:

1. Why was a source refused, and which source, policy version, field, and rule
   produced that decision? Steps 1 and 2 emit `anamnesis.source.refused`.
2. Which input or policy changed a release digest? Steps 2 and 3 emit
   `anamnesis.release.built` and `anamnesis.rebuild.mismatch` with correlation
   ids, input manifest digest, policy digest, and output digest.
3. Did any restricted source reach a release or projection? Steps 2 and 3 emit
   admission counts by disclosure class and `anamnesis.projection.refused`.
4. Which adapter rejected a record and what narrow recovery command applies?
   Step 3 emits the adapter id, record id, schema version, refusal code, and
   retry-safe command.

No remote telemetry is added in the prototype. Closed JSONL events and the
release manifest are the durable operator view.

## 9. Boundaries, per capability

[Phylax](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/plugins/hexaemeron/skills/phylax/SKILL.md)
owns the boundary and control rules.

| Capability boundary | Worth taking | Closing control |
| --- | --- | --- |
| Local source path or private locator | Source bytes, provenance, scope, and rights metadata | No network by default; regular-file and no-symlink reads; size cap; digest before parse; explicit locator policy |
| Native prose to normalised assertion | Finding identity, mappings, relationships, and counterevidence | Source locator on every assertion; closed enums; versioned mapper; unknown preserved; no generated authority |
| Remediation and verification link | Before and after identities, runner, outcome, and residuals | Many-to-many relation validation; proposed, applied, released, deployed, and verified states cannot imply one another |
| Build subprocess | Deterministic validators and bounded specimen runners | Fixed argv without a shell, pinned interpreter, timeout, exit capture, bounded output, no inherited secret dump |
| Release filesystem | Manifest, entities, relations, evidence, policy, projections | Staging directory, content digests, closed manifest, atomic promotion, refusal on collision or partial write |
| Restricted data to output | Digest, disclosure class, and permitted derived fields | Default deny; field-level release policy; pre-write egress scan; no raw excerpt without permission |
| Anamnesis to Elenchus | Historical analogue ids and source-bound context | Read-only adapter; no causal or guarded verdict imported from similarity |
| Anamnesis to Synkrisis | Checked cohort observations | Explicit admitted-producer schema; cohort and denominator retained; no custody or action authority transferred |

## 10. The budget, or its absence

[Metron](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/plugins/hexaemeron/skills/metron/SKILL.md)
owns the measurement contract. The pilot release, including manifests and both
projections but excluding immutable source bytes held outside it, must be at
most 50,000,000 bytes. Step 2 measures it with:

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py measure-release \
  --release plugins/anamnesis/specimens/pilot/release \
  --report .hexaemeron/reports/anamnesis-member-seed-release-byte-cap.json
```

The corresponding conformance result is pending and blocks Step 3. There is no
latency threshold yet because no executable path exists to baseline; Step 3
must record build duration and peak resident memory without presenting either
as a pass criterion. The 25–50 finding range is a curation scope, not a
performance claim.

## 11. The fail-closed posture

[Elenchus](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns triage and the guard rule. Ingestion stops on missing rights, a source
digest mismatch, an unsupported schema or policy, a duplicate stable id, an
invalid relation, a strengthened evidence state, an unexpected network or
subprocess request, or a source that exceeds its bound. Release stops on a
quarantined required record, a partial staging tree, output collision, egress
failure, manifest mismatch, or non-deterministic rebuild. An adapter refusal
does not mutate the corpus or weaken its schema.

Step 2 remains closed until `seed-source-rights-admitted` passes. Step 3 remains
closed until `seed-release-byte-cap` passes. Integration remains closed until
`deterministic-rebuild` passes. A defect fix gets one bounded regression that
fails against the exact parent, passes against the fixed tree, and emits the
closed Elenchus report named by the runbook's audit runner contract.

## 12. Decisions and their homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/1c1137898bce9086c34310bd29b5cf8a889f800c/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns durable decision placement.

| Decision | Home |
| --- | --- |
| Why Anamnesis is a separate member and why its three promises stop where they do | `plugins/anamnesis/docs/decisions/ADR-001-member-boundary.md` |
| Why the graph keeps submissions, findings, occurrences, remediation attempts, and verifications separate | `plugins/anamnesis/docs/decisions/ADR-002-corpus-graph.md` |
| Which disclosure and rights states admit preservation, curation, and release | `plugins/anamnesis/docs/decisions/ADR-003-source-rights.md` |
| Why Elenchus and Synkrisis receive projections rather than ownership | `plugins/anamnesis/docs/decisions/ADR-004-consumer-projections.md` |
| Immutable candidate selection and later evidence obligations | `.hexaemeron/design-evidence.json`, copied byte-for-byte from this review before a Fiat study receipt |
| Step dependency order and exact proof commands | `.hexaemeron/runbook.md`, copied from [runbook.md](runbook.md) |

Changing the selected candidate, criteria, thresholds, or blocking transitions
after design lock requires a new run until Protasis gains a design-amendment
transition. Changing a schema after release requires a new version and an
explicit migration; old releases remain verifiable under their original bytes.
