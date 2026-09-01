# instruction architecture corpus reconciliation

source: `a2b634d8e039af988bf30c8316defccf70071d8d`

the framework-74 corpus contains 190 physical files and
2,290,443 physical bytes. exact whole-file deduplication leaves
173 files and 1,818,999 bytes. these are
repository denominators, not prompt-size or semantic-compression claims.

## inventory

| class | files |
| --- | ---: |
| `fixed_input` | 2 |
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
| `structured_reference` | 12 |
| `worker_prompt` | 14 |

the sole exact duplicate family is the root Promise Machine contract and its
17 generated plugin copies. that family accounts for
471,444 bytes removed by exact
deduplication. similar prose is not deduplicated.

## source-directed admissions

the 70 paths below close the source-directed
Markdown census that the original issue inventory omitted. admission does not
itself imply production reachability: the profile ledger classifies six of
these Markdown paths as human evidence only. each row binds the admitted
class, condition, exact source bytes and source anchor at the frozen ref.

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

## structured references

the extension-agnostic pass adds exactly 12 unique structured inputs totalling
218,576 bytes. nine are every regular non-Markdown file under an admitted
canonical `references/` directory. the other three are Imprimatur's named
lexicons, whose canonical skill and mandatory runtime reads jointly prove
admission. scripts, templates, fixtures, examples, generated output and caller
or project input remain excluded.

| path | bytes | sha256 | owner | admission | load semantics | source anchor | runtime anchor |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| `plugins/hermes/skills/hermes/references/gas-rule-corpus.json` | 177562 | `5d1773f9a5f51e957bd769deb3b030b670fa10499e33fce4a8df3a2e221bd5ac` | `plugins/hermes/skills/hermes/SKILL.md` | `structured-reference` | `mandatory-executable` | `plugins/hermes/skills/hermes/SKILL.md:2236-2336` | `plugins/hermes/skills/hermes/scripts/hermes.py:48010-48040` |
| `plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json` | 3779 | `d2ecc41b3da60df47d5a7ce86f338dbadf7beb18080957dee21881dae4503d1d` | `plugins/hermes/skills/hermes/SKILL.md` | `structured-reference` | `mandatory-executable` | `plugins/hermes/skills/hermes/SKILL.md:5599-5633` | `plugins/hermes/skills/hermes/scripts/hermes.py:48107-48167` |
| `plugins/hexaemeron/skills/imprimatur/lexicon/gated.json` | 3716 | `e554ab6f9661d88095f285c6651983c980bd672b854287f74daa288b1dabc34c` | `plugins/hexaemeron/skills/imprimatur/SKILL.md` | `mandatory-rule-data` | `mandatory-executable` | `plugins/hexaemeron/skills/imprimatur/SKILL.md:8401-8413` | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py:2130-2193` |
| `plugins/hexaemeron/skills/imprimatur/lexicon/hard.json` | 7842 | `a6ad7adbc6c8e06512032cf460c92749a49a6c139b4f2aee101de8bdc95df844` | `plugins/hexaemeron/skills/imprimatur/SKILL.md` | `mandatory-rule-data` | `mandatory-executable` | `plugins/hexaemeron/skills/imprimatur/SKILL.md:8232-8243` | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py:2130-2193` |
| `plugins/hexaemeron/skills/imprimatur/lexicon/structural.json` | 3843 | `908e20c6319b587e95fa21de5949a10c0088ed698d546b0a1048686211826240` | `plugins/hexaemeron/skills/imprimatur/SKILL.md` | `mandatory-rule-data` | `mandatory-executable` | `plugins/hexaemeron/skills/imprimatur/SKILL.md:8549-8566` | `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py:2130-2193` |
| `plugins/homologia/references/manifest-v1.schema.json` | 3554 | `b60b46a65def47e11347fe408709c137b17accdd6fe2b39872c102c7c7db7413` | `plugins/homologia/skills/homologia/SKILL.md` | `structured-reference` | `reference-only` | `plugins/homologia/docs/checked-inputs/runbook.md:3113-3165` | - |
| `plugins/homologia/references/vectors-v1.schema.json` | 3494 | `1031838d2405c949a2ad7fcb9c693119499f1f8183286fe2019e02fa6680b056` | `plugins/homologia/skills/homologia/SKILL.md` | `structured-reference` | `reference-only` | `plugins/homologia/docs/checked-inputs/runbook.md:3169-3220` | - |
| `plugins/synkrisis/references/cohort-v1.schema.json` | 3204 | `5e71420816444af4582e0380b9d6e7ff845e4b3686126233c24a9d1ab5335b0d` | `plugins/synkrisis/skills/synkrisis/SKILL.md` | `structured-reference` | `reference-only` | `plugins/synkrisis/references/cohort-v1.schema.json:65-166` | - |
| `plugins/synkrisis/references/findings-v1.schema.json` | 4152 | `52cf6589e57a93fa82eef75520be44f10636d2469eafe2dae9c91e1d457627c8` | `plugins/synkrisis/skills/synkrisis/SKILL.md` | `structured-reference` | `reference-only` | `plugins/synkrisis/references/findings-v1.schema.json:65-168` | - |
| `plugins/synkrisis/references/policy-v1.schema.json` | 1982 | `04d440bdbd96fcff165d4b0badc029a79634bf17b1a7ac380baee85630c873bb` | `plugins/synkrisis/skills/synkrisis/SKILL.md` | `structured-reference` | `reference-only` | `plugins/synkrisis/references/policy-v1.schema.json:65-166` | - |
| `plugins/synkrisis/references/rule-v1.schema.json` | 3087 | `c8b45c1b6e2b9de010d7ce17109a6f7d49a4797d5a79b07186eabdfa1ed44698` | `plugins/synkrisis/skills/synkrisis/SKILL.md` | `structured-reference` | `reference-only` | `plugins/synkrisis/references/rule-v1.schema.json:65-164` | - |
| `plugins/synkrisis/references/rules-v1.json` | 2361 | `e754bb72235103290ec4ea58b2c71b851782573c3e27eb16a08fe762c3f3a4af` | `plugins/synkrisis/skills/synkrisis/SKILL.md` | `structured-reference` | `mandatory-executable` | `plugins/synkrisis/skills/synkrisis/SKILL.md:7131-7322` | `plugins/synkrisis/scripts/synkrisis.py:33476-33692` |

the six `reference-only` schema rows have no loader edge, loader root or
scenario reachability. Hermes's corpus and schema and Imprimatur's three
lexicons load whenever their owner is selected. Synkrisis's rule catalogue has
separate, mutually exclusive `diagnose` and `verify` source and runtime spans.

## fixed agent inputs

X-Ray and Solidity Auditor each direct the agent to read the local two-byte
`VERSION` file. these files are prompt context with `agent-or-prompt`
semantics, not executable or parsed structured data.

| path | bytes | sha256 | owner | source anchor |
| --- | ---: | --- | --- | --- |
| `plugins/hexaemeron/skills/solidity-auditor/VERSION` | 2 | `1121cfccd5913f0a63fec40a6ffd44ea64f9dc135c66634ba001d10bcf4302a2` | `plugins/hexaemeron/skills/solidity-auditor/SKILL.md` | `plugins/hexaemeron/skills/solidity-auditor/SKILL.md:1179-1246` |
| `plugins/hexaemeron/skills/x-ray/VERSION` | 2 | `53c234e5e8472b6ac51c1ae1cab3fe06fad053beb8ebfd8977b010655bfdd3c3` | `plugins/hexaemeron/skills/x-ray/SKILL.md` | `plugins/hexaemeron/skills/x-ray/SKILL.md:2289-2344` |

## reference-only evidence

the graph keeps exactly 12 authority or human-evidence records with zero host
or scenario reachability: six immutable schemas, three Imprimatur documents
listed only under `References`, and three descriptive Pandects documents.

| path | owner | reason |
| --- | --- | --- |
| `plugins/hexaemeron/skills/imprimatur/references/agent-replies.md` | `plugins/hexaemeron/skills/imprimatur/SKILL.md` | the link occurs only in the human References section |
| `plugins/hexaemeron/skills/imprimatur/references/lexicon-rationale.md` | `plugins/hexaemeron/skills/imprimatur/SKILL.md` | the link occurs only in the human References section |
| `plugins/hexaemeron/skills/imprimatur/references/rewriting.md` | `plugins/hexaemeron/skills/imprimatur/SKILL.md` | the link occurs only in the human References section |
| `plugins/homologia/references/manifest-v1.schema.json` | `plugins/homologia/skills/homologia/SKILL.md` | the schema is authority but no production invocation reads it |
| `plugins/homologia/references/vectors-v1.schema.json` | `plugins/homologia/skills/homologia/SKILL.md` | the schema is authority but no production invocation reads it |
| `plugins/pandects/docs/applicability.md` | `plugins/pandects/skills/pandects/SKILL.md` | the source describes the document but never directs an agent to read it |
| `plugins/pandects/docs/writing-a-law.md` | `plugins/pandects/skills/pandects/SKILL.md` | the source describes the document but never directs an agent to read it |
| `plugins/pandects/integrations/wildcat/APPLICABILITY.md` | `plugins/pandects/skills/pandects/SKILL.md` | the source describes the document but never directs an agent to read it |
| `plugins/synkrisis/references/cohort-v1.schema.json` | `plugins/synkrisis/skills/synkrisis/SKILL.md` | the schema is authority but no production invocation reads it |
| `plugins/synkrisis/references/findings-v1.schema.json` | `plugins/synkrisis/skills/synkrisis/SKILL.md` | the schema is authority but no production invocation reads it |
| `plugins/synkrisis/references/policy-v1.schema.json` | `plugins/synkrisis/skills/synkrisis/SKILL.md` | the schema is authority but no production invocation reads it |
| `plugins/synkrisis/references/rule-v1.schema.json` | `plugins/synkrisis/skills/synkrisis/SKILL.md` | the schema is authority but no production invocation reads it |

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

`loader-graph.json` records 19 roots and 324
host edges, plus 2595 scenario roots and
329 scenario edges and 12
reference-only records. `invocation-profiles.json` contains exactly
519 normalized, source-owned bounded
operation profiles across all 31 selectable skills. each profile expands to
two repository roots, two Agent Skills roots and one standalone root:
1,038 +
1,038 +
519 =
2,595. those scenarios retain the exact 93
route/skill bases while preserving every source-required worker, nested skill,
fixed input and executable input in the applicable phase. each reached union
must equal the profile ledger plus its route contract; no shortest-path or
singleton-edge witness can satisfy that oracle. every required-document
obligation has an explicit identity and its own frozen source path, exact byte
range, source digest and span digest. no scenario edge uses a wildcard, every
edge has a realizable witness, and exclusive profiles cannot co-occur. every
edge carries the corresponding obligation witness. unconditional runtime
loads, installed routes,
identity checks, overlays, frontier gates, worker dispatches, operation
branches and mandatory executable reads remain distinct. every mandatory read
also cites a runtime span. manifest reachability is recomputed from those
edges. a file's presence creates no edge. fixtures and
`distribution/skills-runtime/` are outside this corpus.

## byte classes

the partition is gapless over every physical source byte. generated Promise
Machine copies are `generated_duplicate`; fenced command and data blocks are
`exact_literal_or_evidence`; every structured input is one whole-file exact
range; all remaining canonical Markdown stays in the
conservative `governed_operative_semantics` class. no prose is discarded as
human-only and no byte is treated as a saving through uncertainty.

## cohorts

the development cohort holds 27
logical skills and 1,455,195 exact-unique
bytes (0.799998). the sealed holdout holds
five logical skills and 363,804 exact-unique
bytes (0.200002). memberships are disjoint.
the development set covers every shared root and runtime contract, all ten
file-size deciles, authority tier, admitted document class and construct class
recorded in `cohorts.json`.

`holdout-seal.json` commits the selection method, seed, membership, 16-slot
case envelope, invocation-profile identity
`8bfb56c6aa0b440ed6f072f6468844b750f176b0ad24b68be3b5e1134afb1501` and loader-graph identity
`e28717bb28bb50630369ca2dc9fe161d603e0b33f32b1bf2e37a3c5af2409f9c`. it contains no prompt, expected answer, scorer key
or model output. later work may open that envelope once; Step 1 does not score
it.

## refusal boundary

all five verification commands rebuild from the fixed Git ref and compare the
live source bytes before accepting an artefact. Git runs by one absolute
system-owned executable with lazy fetch, global and system configuration,
prompts and ambient environment disabled. a path, byte, digest, loader span,
partition range, cohort member or commitment that drifts refuses with the
failed predicate. the six JSON records and this reconciliation are payloads;
`artifact-inventory.json` binds all seven byte identities and is published last
as their logical commit point. a verifier reads that inventory, snapshots and
checks every bound payload, then rereads the same inventory before consuming
the cached bytes. an interrupted or concurrent build therefore leaves either
one intact generation or a refusal, never an accepted mixture. paths are
canonical printable-ASCII POSIX relatives no longer than 1,024 bytes; aliases,
traversal, empty segments, backslashes, controls and non-ASCII input refuse in
both runtime and schema. current prompt and scenario-reachable denominators
remain unmeasured until the later arm and case builders exist.
