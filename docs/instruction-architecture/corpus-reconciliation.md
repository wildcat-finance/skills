# instruction architecture corpus reconciliation

source: `a2b634d8e039af988bf30c8316defccf70071d8d`

the framework-74 corpus contains 176 physical files and
2,071,863 physical bytes. exact whole-file deduplication leaves
159 files and 1,600,419 bytes. these are
repository denominators, not prompt-size or semantic-compression claims.

## inventory

| class | files |
| --- | ---: |
| `frontier_ledger` | 26 |
| `frontier_policy` | 1 |
| `identity_contract` | 1 |
| `identity_roster` | 1 |
| `markdown_reference` | 38 |
| `operation_reference` | 25 |
| `overlay_contract` | 1 |
| `promise_machine_contract` | 18 |
| `router_install_contract` | 1 |
| `runtime_contract` | 18 |
| `skill_contract` | 32 |
| `worker_prompt` | 14 |

the sole exact duplicate family is the root Promise Machine contract and its
17 generated plugin copies. that family accounts for
471,444 bytes removed by exact
deduplication. similar prose is not deduplicated.

## source-directed admissions

the 70 paths below close the imperative and conditional agent-load directives
that the original issue census omitted. each row binds the admitted class,
condition, exact source bytes and source anchor at the frozen ref.

| class | admission | path | bytes | source anchor |
| --- | --- | --- | ---: | --- |
| `frontier_ledger` | `frontier-gate` | `plugins/alexandria/skills/alexandria/EVOLUTION.md` | 3422 | `plugins/alexandria/skills/alexandria/SKILL.md:914-926` |
| `frontier_ledger` | `frontier-gate` | `plugins/anamnesis/skills/anamnesis/EVOLUTION.md` | 3671 | `plugins/anamnesis/skills/anamnesis/SKILL.md:1259-1271` |
| `frontier_ledger` | `frontier-gate` | `plugins/ariadne/skills/ariadne/EVOLUTION.md` | 3933 | `plugins/ariadne/skills/ariadne/SKILL.md:861-873` |
| `frontier_ledger` | `frontier-gate` | `plugins/berean/skills/berean/EVOLUTION.md` | 1905 | `plugins/berean/skills/berean/SKILL.md:2169-2181` |
| `frontier_ledger` | `frontier-gate` | `plugins/brevitas/skills/brevitas/EVOLUTION.md` | 3654 | `plugins/brevitas/skills/brevitas/SKILL.md:743-755` |
| `frontier_ledger` | `frontier-gate` | `plugins/hermes/skills/hermes/EVOLUTION.md` | 1955 | `plugins/hermes/skills/hermes/SKILL.md:948-960` |
| `frontier_ledger` | `frontier-gate` | `plugins/hexaemeron/skills/elenchus/EVOLUTION.md` | 2916 | `plugins/hexaemeron/skills/elenchus/SKILL.md:1714-1726` |
| `frontier_ledger` | `frontier-gate` | `plugins/hexaemeron/skills/ephoros/EVOLUTION.md` | 3730 | `plugins/hexaemeron/skills/ephoros/SKILL.md:1585-1597` |
| `frontier_ledger` | `frontier-gate` | `plugins/hexaemeron/skills/fiat/EVOLUTION.md` | 59332 | `plugins/hexaemeron/skills/fiat/SKILL.md:655-667` |
| `frontier_ledger` | `frontier-gate` | `plugins/hexaemeron/skills/hypomnema/EVOLUTION.md` | 11633 | `plugins/hexaemeron/skills/hypomnema/SKILL.md:1575-1587` |
| `frontier_ledger` | `frontier-gate` | `plugins/hexaemeron/skills/imprimatur/EVOLUTION.md` | 4128 | `plugins/hexaemeron/skills/imprimatur/SKILL.md:683-695` |
| `frontier_ledger` | `frontier-gate` | `plugins/hexaemeron/skills/kronos/EVOLUTION.md` | 8190 | `plugins/hexaemeron/skills/kronos/SKILL.md:1171-1183` |
| `frontier_ledger` | `frontier-gate` | `plugins/hexaemeron/skills/metron/EVOLUTION.md` | 1860 | `plugins/hexaemeron/skills/metron/SKILL.md:1430-1442` |
| `frontier_ledger` | `frontier-gate` | `plugins/hexaemeron/skills/phylax/EVOLUTION.md` | 3500 | `plugins/hexaemeron/skills/phylax/SKILL.md:1878-1890` |
| `frontier_ledger` | `frontier-gate` | `plugins/hexaemeron/skills/protasis/EVOLUTION.md` | 13575 | `plugins/hexaemeron/skills/protasis/SKILL.md:1913-1925` |
| `frontier_ledger` | `frontier-gate` | `plugins/hexaemeron/skills/vulgate/EVOLUTION.md` | 1045 | `plugins/hexaemeron/skills/vulgate/SKILL.md:601-613` |
| `frontier_ledger` | `frontier-gate` | `plugins/homologia/skills/homologia/EVOLUTION.md` | 2710 | `plugins/homologia/skills/homologia/SKILL.md:709-721` |
| `frontier_ledger` | `frontier-gate` | `plugins/horos/skills/horos/EVOLUTION.md` | 11541 | `plugins/horos/skills/horos/SKILL.md:1173-1185` |
| `frontier_ledger` | `frontier-gate` | `plugins/janus/skills/janus/EVOLUTION.md` | 3208 | `plugins/janus/skills/janus/SKILL.md:945-957` |
| `frontier_ledger` | `frontier-gate` | `plugins/lazarus/skills/lazarus/EVOLUTION.md` | 4072 | `plugins/lazarus/skills/lazarus/SKILL.md:762-774` |
| `frontier_ledger` | `frontier-gate` | `plugins/lemma/skills/lemma/EVOLUTION.md` | 1723 | `plugins/lemma/skills/lemma/SKILL.md:722-734` |
| `frontier_ledger` | `frontier-gate` | `plugins/pandects/skills/pandects/EVOLUTION.md` | 2297 | `plugins/pandects/skills/pandects/SKILL.md:843-855` |
| `frontier_ledger` | `frontier-gate` | `plugins/probitas/skills/probitas/EVOLUTION.md` | 2595 | `plugins/probitas/skills/probitas/SKILL.md:856-868` |
| `frontier_ledger` | `frontier-gate` | `plugins/sapheneia/skills/sapheneia/EVOLUTION.md` | 1404 | `plugins/sapheneia/skills/sapheneia/SKILL.md:696-708` |
| `frontier_ledger` | `frontier-gate` | `plugins/synkrisis/skills/synkrisis/EVOLUTION.md` | 6715 | `plugins/synkrisis/skills/synkrisis/SKILL.md:800-812` |
| `frontier_ledger` | `frontier-gate` | `plugins/tabularium/skills/tabularium/EVOLUTION.md` | 1248 | `plugins/tabularium/skills/tabularium/SKILL.md:955-967` |
| `frontier_policy` | `frontier-gate` | `plugins/hexaemeron/skills/VERSIONING.md` | 4450 | `plugins/hexaemeron/AGENTS.md:4368-4390` |
| `identity_contract` | `identity-contract` | `SHOGGOTH.md` | 5165 | `AGENTS.md:879-922` |
| `identity_roster` | `credential-identity` | `CONTRIBUTORS.md` | 1485 | `SHOGGOTH.md:2112-2179` |
| `operation_reference` | `operation-branch` | `docs/fiat-run-observation-binding-v1.md` | 3247 | `plugins/hexaemeron/skills/fiat/SKILL.md:47744-47795` |
| `operation_reference` | `operation-branch` | `plugins/alexandria/docs/runbook.md` | 10440 | `plugins/alexandria/skills/alexandria/SKILL.md:12097-12118` |
| `operation_reference` | `operation-branch` | `plugins/alexandria/docs/study.md` | 36040 | `plugins/alexandria/skills/alexandria/SKILL.md:12028-12047` |
| `operation_reference` | `operation-branch` | `plugins/alexandria/docs/usdc-interval-collector.md` | 9008 | `plugins/alexandria/skills/alexandria/SKILL.md:11397-11434` |
| `operation_reference` | `operation-branch` | `plugins/anamnesis/docs/demo.md` | 2605 | `plugins/anamnesis/skills/anamnesis/SKILL.md:7636-7654` |
| `operation_reference` | `operation-branch` | `plugins/ariadne/docs/capturing-a-dataset.md` | 6549 | `plugins/ariadne/skills/ariadne/SKILL.md:6506-6539` |
| `operation_reference` | `operation-branch` | `plugins/ariadne/docs/capturing-a-grounded-agent.md` | 5457 | `plugins/ariadne/skills/ariadne/SKILL.md:7865-7905` |
| `operation_reference` | `operation-branch` | `plugins/ariadne/docs/capturing-a-release.md` | 5122 | `plugins/ariadne/skills/ariadne/SKILL.md:5707-5740` |
| `operation_reference` | `operation-branch` | `plugins/ariadne/docs/capturing-a-state-fixture.md` | 9129 | `plugins/ariadne/skills/ariadne/SKILL.md:7486-7525` |
| `operation_reference` | `operation-branch` | `plugins/ariadne/docs/conformance.md` | 20229 | `plugins/ariadne/skills/ariadne/SKILL.md:12375-12400` |
| `operation_reference` | `operation-branch` | `plugins/ariadne/docs/dataset.md` | 5393 | `plugins/ariadne/skills/ariadne/SKILL.md:14765-14786` |
| `operation_reference` | `operation-branch` | `plugins/ariadne/docs/grounded-agent.md` | 7872 | `plugins/ariadne/skills/ariadne/SKILL.md:17238-17266` |
| `operation_reference` | `operation-branch` | `plugins/ariadne/docs/solidity-release.md` | 5536 | `plugins/ariadne/skills/ariadne/SKILL.md:13763-13793` |
| `operation_reference` | `operation-branch` | `plugins/ariadne/docs/state-fixture.md` | 11442 | `plugins/ariadne/skills/ariadne/SKILL.md:16437-16464` |
| `operation_reference` | `operation-branch` | `plugins/lazarus/docs/chain-anchors.md` | 4079 | `plugins/lazarus/skills/lazarus/SKILL.md:6905-6932` |
| `operation_reference` | `operation-branch` | `plugins/lazarus/docs/preservation-release.md` | 7886 | `plugins/lazarus/skills/lazarus/SKILL.md:5474-5508` |
| `operation_reference` | `operation-branch` | `plugins/lazarus/docs/runbook.md` | 8985 | `plugins/lazarus/skills/lazarus/SKILL.md:5603-5624` |
| `operation_reference` | `operation-branch` | `plugins/lazarus/docs/study.md` | 31691 | `plugins/lazarus/skills/lazarus/SKILL.md:5540-5559` |
| `operation_reference` | `operation-branch` | `plugins/lemma/INVARIANTS.md` | 14936 | `plugins/lemma/skills/lemma/SKILL.md:4440-4459` |
| `operation_reference` | `operation-branch` | `plugins/pandects/docs/applicability.md` | 4434 | `plugins/pandects/skills/pandects/SKILL.md:11720-11741` |
| `operation_reference` | `operation-branch` | `plugins/pandects/docs/writing-a-law.md` | 5137 | `plugins/pandects/skills/pandects/SKILL.md:11631-11652` |
| `operation_reference` | `operation-branch` | `plugins/pandects/integrations/wildcat/APPLICABILITY.md` | 9005 | `plugins/pandects/skills/pandects/SKILL.md:11327-11364` |
| `operation_reference` | `operation-branch` | `plugins/probitas/docs/adding-a-venue.md` | 17029 | `plugins/probitas/skills/probitas/references/venues.md:838-869` |
| `operation_reference` | `operation-branch` | `plugins/tabularium/docs/adding-an-adapter.md` | 2728 | `plugins/tabularium/skills/tabularium/SKILL.md:7864-7895` |
| `operation_reference` | `operation-branch` | `plugins/tabularium/docs/release-policy.md` | 1955 | `plugins/tabularium/skills/tabularium/SKILL.md:8151-8179` |
| `overlay_contract` | `vendored-overlay` | `plugins/hexaemeron/PROMISES.md` | 8781 | `plugins/hexaemeron/AGENTS.md:3543-3569` |
| `router_install_contract` | `installed-route` | `.agents/skills/promise-machine/PORTABLE.md` | 2476 | `.agents/skills/promise-machine/SKILL.md:846-864` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/agents/mason.md` | 4026 | `plugins/hexaemeron/skills/fiat/SKILL.md:43406-43413` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/agents/scribe.md` | 3968 | `plugins/hexaemeron/skills/fiat/SKILL.md:43428-43436` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/agents/surveyor.md` | 4546 | `plugins/hexaemeron/skills/fiat/SKILL.md:43394-43404` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/agents/warden.md` | 7418 | `plugins/hexaemeron/skills/fiat/SKILL.md:43415-43423` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/skills/fizz/agents/implementers/global-property-implementer.md` | 4096 | `plugins/hexaemeron/skills/fizz/SKILL.md:34938-34988` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/skills/fizz/agents/implementers/specific-property-implementer.md` | 5447 | `plugins/hexaemeron/skills/fizz/SKILL.md:35155-35207` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/skills/fizz/agents/invariant-discovery/adversarial-profit-maximizer.md` | 6618 | `plugins/hexaemeron/skills/fizz/SKILL.md:32149-32207` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/skills/fizz/agents/invariant-discovery/conservation-auditor.md` | 5052 | `plugins/hexaemeron/skills/fizz/SKILL.md:31660-31710` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/skills/fizz/agents/invariant-discovery/protocol-type-specialist.md` | 8492 | `plugins/hexaemeron/skills/fizz/SKILL.md:32316-32370` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/skills/fizz/agents/invariant-discovery/roundtrip-rounding-analyst.md` | 7634 | `plugins/hexaemeron/skills/fizz/SKILL.md:31825-31881` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/skills/fizz/agents/invariant-discovery/state-transition-mapper.md` | 4658 | `plugins/hexaemeron/skills/fizz/SKILL.md:31981-32034` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/skills/fizz/agents/invariant-discovery/synthesizer.md` | 15737 | `plugins/hexaemeron/skills/fizz/SKILL.md:32766-32807` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/skills/fizz/agents/protocol-analyzer.md` | 5600 | `plugins/hexaemeron/skills/fizz/SKILL.md:13158-13185` |
| `worker_prompt` | `worker-dispatch` | `plugins/hexaemeron/skills/fizz/agents/report-writer.md` | 8781 | `plugins/hexaemeron/skills/fizz/SKILL.md:42958-42981` |

an independent second pass parses 298 existing local
inline Markdown-link occurrences from every admitted source. after classifying
127 historical-ledger, decision, example, evidence,
reader-background and delivery-provenance occurrences, it adds
0 paths. the admitted Anamnesis demo's only local
descendant is specimen evidence, so the operative closure stops there.

## excluded links

these representative links do not create loader edges. the classification is
source-bound rather than inferred from a file's presence.

| excluded class | path | source anchor |
| --- | --- | --- |
| `human_or_background` | `README.md` | `AGENTS.md:115-173` |
| `generated_reader` | `plugins/pandects/docs/catalogue.md` | `plugins/pandects/skills/pandects/SKILL.md:11499-11526` |
| `historical_record` | `audit/AUDIT.md` | `plugins/hexaemeron/skills/fiat/references/audit-loop.md:2560-2574` |
| `dynamic_target` | `.hexaemeron/study.md` | `plugins/hexaemeron/agents/surveyor.md:2356-2376` |
| `example_or_evidence` | `plugins/probitas/docs/example-dossier.md` | `plugins/probitas/docs/adding-a-venue.md:15708-15726` |
| `unavailable_operation` | `plugins/alexandria/docs/compound-v3-harvest.md` | `plugins/alexandria/skills/alexandria/SKILL.md:11890-11921` |

## loader evidence

`loader-graph.json` records 19 roots and 206
host edges, plus 231 scenario roots and
245 scenario edges. the scenarios cover the exact 93
base combinations of 31 selectable canonical skills and the repository,
isolated Agent Skills and standalone-plugin host routes. 87 bases admit a
zero-condition invocation; Ariadne and Kronos instead require an operation or
target-plus-Fiat vector on all three routes. conditional roots carry one closed,
sorted invocation vector. each starts at its real host entry, loads
only the selected plugin runtime and skill, and includes only descendants whose
conditions fire. no scenario edge uses a wildcard, every potential edge has a
realizable witness, and sibling Kronos targets or Ariadne operations do not
co-occur. every edge cites a source path, exact byte range,
source digest and span digest. unconditional runtime loads, installed routes,
identity checks, overlays, frontier gates, worker dispatches and operation
branches remain distinct. manifest reachability is recomputed from those
edges. a file's presence creates no edge. fixtures and
`distribution/skills-runtime/` are outside this corpus.

## byte classes

the partition is gapless over every physical source byte. generated Promise
Machine copies are `generated_duplicate`; fenced command and data blocks are
`exact_literal_or_evidence`; all remaining canonical Markdown stays in the
conservative `governed_operative_semantics` class. no prose is discarded as
human-only and no byte is treated as a saving through uncertainty.

## cohorts

the development cohort holds 27
logical skills and 1,280,333 exact-unique
bytes (0.799999). the sealed holdout holds
five logical skills and 320,086 exact-unique
bytes (0.200001). memberships are disjoint.
the development set covers every shared root and runtime contract, all ten
file-size deciles, authority tier, admitted document class and construct class
recorded in `cohorts.json`.

`holdout-seal.json` commits the selection method, seed, membership and 16-slot
case envelope. it contains no prompt, expected answer, scorer key or model
output. later work may open that envelope once; Step 1 does not score it.

## refusal boundary

all four verification commands rebuild from the fixed Git ref and compare the
live source bytes before accepting an artefact. Git runs by one absolute
system-owned executable with lazy fetch, global and system configuration,
prompts and ambient environment disabled. a path, byte, digest, loader span,
partition range, cohort member or commitment that drifts refuses with the
failed predicate. paths are canonical printable-ASCII POSIX relatives no longer
than 1,024 bytes; aliases, traversal, empty segments, backslashes, controls and
non-ASCII input refuse in both runtime and schema. current prompt and
scenario-reachable denominators remain
unmeasured until the later arm and case builders exist.
