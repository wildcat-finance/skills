# Anamnesis

<!-- marketplace-context:start -->
## In one line

Anamnesis keeps audit findings and the changes that answered them as a source-bound corpus, admitted against an explicit rights basis and released as read-only projections.

**Current frontier.** Source admission ships as the member's first promise: a closed pilot policy, no-follow regular-file reads under a declared byte cap, exact digest checks, and a closed rights and disclosure enumeration in which public visibility is not a rights basis. Curation and release are declared boundaries that refuse by name and say which runbook step owes them.

**Next Fiat job.** Use /hexaemeron:fiat to ship the curation graph runbook step 2 owes: closed engagement, assertion, relation and policy schemas that keep submissions, adjudicated findings, occurrences, remediation attempts and verifications as separate records. Accepted when the admitted pilot produces that graph, a one-fix-to-many-findings cluster and a many-fixes-to-one-finding cluster both survive a round trip with their edges intact, no mapper promotes a native state, and the seed release byte report exists at the path the design record names. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose. Change a skill's Next Fiat job only when that exact frontier job completed; otherwise leave it unchanged.
<!-- marketplace-context:end -->

## Why it exists

An audit finding and the change that answered it are usually recorded once, in
one report, and then left where they fell. Hundreds of rounds later nobody can
say which weaknesses keep coming back, which fixes held, or which were quietly
reverted, because the records were never kept in a form that answers those
questions.

Anamnesis keeps them. It admits a source only against an explicit rights basis,
preserves the producer's own bytes and identifiers unchanged, and curates a
graph in which submissions, adjudicated findings, occurrences, remediation
attempts and verifications stay separate records joined by many-to-many edges.

## What it is careful about

A corpus is easy to build and easy to make useless. Three things break one:

- **Collapsing a fix into a finding.** One change can answer several findings
  and one finding can need several changes. Both stay representable.
- **Strengthening evidence.** A proposed mitigation is not an applied patch,
  and an applied patch is not a guarded fix. Proposed, applied, released,
  deployed, reverted and verified never imply one another.
- **Losing what was never established.** Unknown is not none and not
  applicable. A field the source never settled stays unknown.

Every release rebuilds to the same digest from the same inputs, or refuses.

## Where it stops

Anamnesis does not produce audit rounds, decide whether a finding was real,
prove a fix correct, or compare runs. Warden produces a round's record.
Elenchus proves one present cause and guard, and may read a historical
analogue from here as a hypothesis rather than a verdict. Synkrisis compares
declared runs, and may read a checked cohort projection from here without
taking custody of the source.

It does not train a model, rank auditors, estimate how common a weakness is
beyond the records it holds, or treat public visibility as permission to
redistribute.

## Using it

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py admit \
  --policy plugins/anamnesis/specimens/pilot/policy.json
```

Read [skills/anamnesis/SKILL.md](skills/anamnesis/SKILL.md) before running it.
The design behind the member is in [docs/study.md](docs/study.md), the build
order in [docs/runbook.md](docs/runbook.md), and the decisions that were
expensive to reverse in [docs/decisions/](docs/decisions/).

This version implements source admission. Curation and release are declared
boundaries that refuse by name and say which runbook step owes them.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
