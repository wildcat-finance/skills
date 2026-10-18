# Decision: Admit Wildcat V2 wrapper instances as plan-declared subjects

## Status

Accepted, 2026-10-18. Numberless until the integration composer assigns it. It supersedes nothing.

## Context

Alexandria's Wildcat V2 venue cannot hold a `Wildcat4626Wrapper` instance as a capture subject. The pinned V2 registry has no role for one, and the venue refuses a plan subject the registry does not list, so no release carries a wrapper's epoch or native logs and Tabularium's three wrapper rules have nothing to read. Issue #2092 asked for wrapper instances as capture subjects. The V2 registry document and its digest, the pre-#1880 digest and the V1 digest must stay byte-identical, no real wrapper data may be collected for this change, and every plan without the new field must build the bytes it builds today.

A preserved `WrapperDeployed(address,address)` log from the registry's one `wrapper-factory` entry names a market in its first indexed topic and a wrapper in its second. Whether every wrapper comes from that factory, and whether a wrapper's code is immutable, are not established.

## Decision

A Wildcat V2 interval plan declares its wrappers in the optional field `wildcat_v2_wrappers`, `{"rule": "wrapper-deployed/v1", "subjects": [...]}`, and each declared address is admitted only when a preserved `WrapperDeployed` log from the registry's wrapper factory names it and names a market the registry lists; the release binds the derived wrapper set as the `wrapper-subjects` component, format `alexandria-wildcat-v2-wrapper-subjects/v1`.

The field is valid only on an `alexandria-interval-plan/v2` plan for venue `wildcat-v2` whose `evidence_classes` include `logs` and whose `subjects` include the wrapper factory. Its list is non-empty, sorted, lowercase and unique, disjoint from `subjects` and from every registry entry, and stays under `MAX_SUBJECTS` (4,096) together with `subjects`.

A `WrapperDeployed` naming a market the registry does not list refuses build and `check`; it never becomes a gap. A declared wrapper that no preserved `WrapperDeployed` names, a wrapper with no runtime code at its first block and a wrapper log before its epoch's first block refuse too. Each refusal names the wrapper and the market or block at fault. A discovered wrapper the plan does not declare is listed in the component as undeclared, with a bounded gap sentence saying its native logs were not requested.

Each wrapper's epoch opens at its `WrapperDeployed` block under the venue's `immutable-code` model, naming the wrapper as proxy and implementation. Its logs join the existing `logs` journal through the address filter. The component lists the factory, the `WrapperDeployed` topic, the discovery window and every discovered wrapper with its market, deployment log identity (block, transaction hash, transaction index, log index) and declared flag, and `check` re-derives it byte for byte. `check` requires the component exactly when the plan carries the field. No receipt format changes, and a plan without the field reaches none of this code.

## Alternatives

- **`discovered-wrapper-journal`.** The plan opts in with a rule alone, and after the shards the collector walks a new `wrapper-logs` journal from each staged `WrapperDeployed` block. It needs no operator list and leaves no undeclared-wrapper gap, but it adds a journal class, a checkpoint field and reconcile and split handling, and its request ranges derive from collected bytes rather than the plan. Rejected because it fails `plan-derived-requests`.
- **`registry-wrapper-role`.** A `wrapper` role in the pinned V2 registry makes wrappers ordinary registry subjects. The registry bytes and `WILDCAT_V2_REGISTRY_SHA256` would move, the five Tabularium files that pin the current digest would be affected, and the merged record would list real wrapper data this change may not collect. Rejected because it fails `registry-bytes-unchanged` and `constructed-proof-suffices`.
- **`separate-wrapper-venue`.** A `wildcat-v2-wrappers` venue takes its wrapper set from an earlier V2 release and leaves the V2 path untouched. Wrapper logs would then sit in a release apart from the market logs, so no one `release_id` binds both and a consumer joins two releases. Rejected because it fails `one-release-binds-wrapper-logs`.

## Consequences

The operator must know the wrapper set before collecting. A wrapper the factory deploys inside the interval but the plan omits gets a gap and no native logs; every declared address is still checked against preserved evidence, so no unverified operator assertion reaches a release. In exchange every shard-class request still derives from the plan, the checkpoint format does not change and the registry stays as it is. Each declared wrapper adds one code read and at most one header read to the never-split `epoch-evidence` journal, inside the existing caps.

A wrapper release states as gaps that wrapper immutability and single-factory provenance are not established. Tabularium's wrapper contexts stay with the issue's `tabularium-wrapper-context` carryover. The constructed V1 and V2 release identifiers frozen at Step 1 and the three registry digests hold at every step.
