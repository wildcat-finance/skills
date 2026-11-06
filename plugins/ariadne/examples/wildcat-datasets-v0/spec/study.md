# Bind the sealed Wildcat captures to dataset statements

Assuming, unless corrected: the accepted reference remains both Wildcat estates
on Ethereum mainnet; each receives its own unsigned statement. This is the
maintainer-authorised generation run for issue 1374. Ariadne stays mature.
Existing offline Alexandria rebuilds may supply byte-identical releases with
observed producer commands. Live collection, new endpoints and signing are
outside this run. The external preserved inputs remain read-only.

## 1. Problem statement

A release consumer needs the exact bytes of both accepted Wildcat captures
joined to their producer, inputs and stated coverage. Produce a repeatable
caller-side example under `plugins/ariadne/examples/wildcat-datasets-v0/`.
It uses the existing `dataset/v1` capture and verifier without adding a predicate
or widening Ariadne's core. One statement covers V1 and one covers V2.

The accepted source revision is `104f6f82c390003fb61039d3023d07c1abe05086`,
which merged the capture handoff through PR 1838. The release identities are:

| Estate | Release ID | Manifest SHA-256 | Inclusive blocks | Components |
| --- | --- | --- | --- | --- |
| V1 | `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69` | `a8d675d23c31e44c6c6960245a2f640b4a669e58b4cec16a350ccf859b6ee591` | 18743513 to 22074622 | 109 |
| V2 | `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3` | `219d72f940b667c829b04f232bbebf7ee83020139faadc1ac88883c7241156f7` | 21866550 to 26022093 | 127 |

V1 names 16 registry subjects and 667 complete shards; V2 names 137 subjects
and 3,463 complete shards. Their intervals were fully swept. The older issue's
unswept-tail premise is superseded by these accepted bounds. Blocks outside
those bounds are excluded by the plans, not invented gaps. Within the bounds,
semantic omissions still require explicit reasons.

Success criteria, to be proved by the final demonstration and tests:

1. The example builds two unsigned statements with `capture-dataset`, binds
   every release file and the bundle, and retains every line of both CLI
   verification reports. Seven numbered gates and all three dataset checks
   pass; `inspect` reports unsigned status.
2. Producer argv comes from an observed offline Alexandria rebuild. Inputs bind
   the release manifest, plan, registry, staging manifest and archive digest,
   producer source and exact source revision. Historical collection runtime is
   recorded separately from the later rebuilding runtime.
3. The statements keep the exact intervals above and explicit reasoned gaps.
   A separate coverage inventory preserves every source capture's scope,
   evidence class, collections, selectors, record counts, unsupported collections
   and gap strings. Shard-partition descriptions are kept as partition notes;
   they do not become invented global missing blocks.
4. Mutating each statement to remove `coverage.gaps`, remove a gap reason or
   move a gap outside its bounds makes the real verifier return nonzero with
   the coverage check named. A changed release file, forged output report,
   missing input and existing destination also refuse without overwriting input.
5. A second offline run reproduces the two statement byte sequences and report
   contents. Checked metadata remains available without the external archives,
   but that operation expressly claims no rebuild or new source verification.

The source command is the example's `demo.py`; the future demonstration exposes
`build --output <fresh-directory>`, `verify <directory>` and `verify-preserved`.
The final full run uses both real external inputs. Its output contains the
statements, original gate reports, digest inventory, scope inventory and refusal
observations. `python3 -m unittest discover -s plugins/ariadne/tests -t
plugins/ariadne` exercises the committed example and its refusal cases. Fiat
controls execution and receipts; a passing example proves these bounded
observations, not completeness or the sufficiency of this specification.

## 2. Prior art

The existing `plugins/ariadne/scripts/ariadne_lib/capture/dataset.py` streams
file digests and accepts caller-supplied producer, inputs, coverage and counts.
Its published schema and `predicates/dataset.py` already enforce the required
coverage refusals. No default producer or invented count is needed. Alexandria's
individual V1 and V2 examples rebuild from preserved staging, while the combined
example demonstrates both estates offline. The organisation's original Wildcat
source/deployed-subject records remain inputs through those registries; this
run derives no new Solidity source match. The external representation is
in-toto Statement v1 with Ariadne's existing dataset predicate. No new standard
or signing mechanism is introduced.

Read the two latest merged PRs that changed the dataset capture implementation:
[PR 756](https://github.com/wildcat-finance/skills/pull/756) and
[PR 219](https://github.com/wildcat-finance/skills/pull/219). PR 756 retained
bounded local reads, shared path guards and explicit UTF-8 writes; its deferred
example and version work belonged to that completed run. PR 219 fixed the
first-release gate-5 hole, FIFO handling, traversal and schema disagreements.
Its Forge/environment and Lazarus-frontier observations remain historical;
they are not new failures reproduced here. Current Ariadne frontier status was
read directly from its ledger and remains mature.

Audit reading used the verified synopsis view after the whole-set
`audit_synopsis.py --check .` command exited 0. The complete report is
`.hexaemeron/design-reports/audit-synopsis-check.txt`. Authoritative sources and
the actual in-scope reading views are:

| Authoritative source | View and scope read |
| --- | --- |
| `plugins/ariadne/audit/AUDIT.md` | `plugins/ariadne/audit/AUDIT_SYNOPSIS.md`, all 21 rounds |
| `audit/AUDIT.md` | `audit/AUDIT_SYNOPSIS.md`, Ariadne dataset and state-fixture sections, lines 92 to 106 and 123 to 146 |
| `audit/rounds/fiat-402-implement-the-grounded-agent-predicate.md` | sibling synopsis, Step 3 capture rounds and final closure |
| `audit/rounds/fiat-1731-venue-agnostic-interval-capture-for-both-wi.md` | sibling synopsis, final Step 9 round and Steps 10 and 11 handoff records |

The source files remain authoritative; synopsis use does not claim their full
source text was read. Legacy missing `Covered`, `Not checked`, `Elenchus
verdict` and `Leads not pursued` fields remain unknown. Finding IDs and statuses
are preserved in those checked source views. The dataset's fixed producer,
count, path, comparison and gap findings stay fixed history. `S4-R6-06` and
`S4-R8-09` were later answered by PR 219. `S4-R8-08`'s wider core-name policy
is outside this example, which emits nonblank names and no executable command
records. No unresolved historical defect requires changing product code here;
there is no claim that audit-history review found every possible defect.

Retained leads: no general total-release-byte budget; recursive robustness
sweeps and exhaustive schema equivalence remain outside scope; invisible-string
and homoglyph policy, short secret formats, replay sandboxing and automated
docstring truth checking are not reopened. The example must refuse its own
wrong digests and paths and keep output separate from source. Grounded-capture
concurrency limits are not promoted into a guarantee for dataset capture.

The handoff retains targeted-trace exclusion of logless transactions, missing
deployment blocks, the V1 five-commit checkout ambiguity, private V2 source
references, unproved provider completeness/finality and the unchanged
transaction-index-reconciliation frontier. V1 opening-edge parity,
deploy-log-free market derivation, and Fiat-1350 finality-boundary,
opening-header-by-hash and undeclared-journal leads remain open. Unclosed
`compound_phase0.py` HTTPError handling and contributor-fixture warnings were
not reproduced. Earlier Step 9 Elenchus verdicts remain inconclusive;
W8-R1-01's prose correction is the dated delivery-proof erratum.

## 3. Constraints and non-goals

Start from `main` at `104f6f82c390003fb61039d3023d07c1abe05086` in verified
worktree `issue/16777231-893567831`. Use CPython 3.14.6 from `.python-version`,
stdlib unittest and existing checked-runner ownership. No new dependency,
service, signing key, RPC request or frontend is needed.

The coordinator verified both original releases with Alexandria `verify` and
interval `check`, then rebuilt both offline. Evidence is under
`.hexaemeron/input-evidence/`. V2's old staging lacked
`reconciliation/errors.jsonl`; two refusal observations remain preserved. The
verified archive was extracted into a fresh directory and its build exited 0.
This is repaired input availability, not a code fix or a guarded verdict.
Use the rebuilt releases named by `rebuild-recovery.json`; the old mutable V2
staging path is not an accepted rebuild input.

Always preserve source bytes, public/private access labels, explicit absences,
source digests, first-release reason and unsigned status. Ask first for a new
collection, changed target/interval, signing or publication outside the
existing delivery authority. Never substitute Compound, invent historical V2
argv, interpret registry checkout ambiguity as a unique source checkout,
execute commands copied from a statement, or turn provider agreement into
canonical-chain proof. Exclude credit-event derivation, source-review completion,
frontier reopening, dataset schema changes and general collector repairs.

Only Ariadne receives a generation increase at integration, relative to the
then-current accepted version. The starting ledger reads `ariadne-v3.4.0`.
Its frontier revision, digest, status, sentence and held job stay unchanged.
Refresh generated installation copies and Horos artefacts through their owners.

## 4. Design options

`full-release` binds every file of each sealed release through the current
capture interface. An example-owned adapter supplies verified record counts,
producer and coverage. This costs reading all release bytes and produces a
larger statement; it directly exposes each component digest to a consumer.

`manifest-only` binds only each manifest, leaving component bytes referenced
transitively. It is smaller and faster, but fails the required exact release
subject inventory: its one file per estate omits 109 and 127 component subjects.
The existing capture core needs no new generic adapter for either construction.

`.hexaemeron/design-evidence.json` selects `full-release` by `unique-frontier`.
Its 10 resolved reports cover correctness, time, space, compatibility and
recovery. The executed probe read both releases: 110 and 128 subjects for the
full option, versus 1 and 1 for the manifest option. Combined subject listing
work took 149 ms versus a rounded 1 ms; serialized listings totalled 71,128
versus 322 bytes. These are one local probe's wall time and listing size,
not memory peaks, final statement size or a production timing guarantee.
Both options retain the existing interface and its stray-count refusal.
Manifest-only fails the all-files gate, so its speed cannot select it.

Implementation mapping for the selected option:

- Resolve each manifest component to its exact digest-named regular file.
  Count the declared JSON selector (`/records`, `/epochs`, `/shards` or
  `/entries`) and cross-check its manifest count; `manifest.json` is one
  metadata record. Never count a JSON object as one event or a byte string as
  records. Every file and every manifest component must be accounted for.
- Supply the actual offline rebuild command and pinned runtime as producer.
  Keep original collection commands, capture source versions and observed
  timestamps as separate provenance. Bind plan, registry, archive/staging
  manifest, rebuild evidence and producer source through exact input digests.
- Use the declared block interval. Where semantic exclusions cannot be
  represented as disjoint temporal holes, emit one reasoned gap over the whole
  interval explaining the conservative limitation, and bind the full source
  gap inventory. This does not claim every block was unread. It prevents a
  clean temporal sweep from becoming a completeness assertion.
- Bind both outputs to their exact manifests and source inventories. Each has
  a null baseline and an explicit first-statement reason; V1 and V2 are separate
  estates, not previous/current versions of one dataset.

Two steps suffice. Step 1 commits the specification, design reports, example
layout, decision record and metadata checks without claiming a completed
statement. Step 2 implements the adapter, creates both statements and gate
reports, adds meaningful refusal tests, and executes the full demonstration.
Keep full external release trees and archives outside Git; commit the smaller
statements, exact input metadata and complete gate reports.

## 5. Risk register seed

```risk-register
subject-substitution | accepted V1 and V2 releases | release IDs, manifest hashes, exact file inventory and registry subjects match the handoff
producer-confusion | capture runtime and rebuild runtime | only observed rebuild argv is producer and historical collection provenance stays separate
record-count-confusion | content-addressed JSON components | selector lengths agree with manifest counts and metadata is not counted as events
gap-erasure | temporal bounds and semantic omissions | every source gap and unsupported collection survives with a reasoned interval projection
partition-as-missing | sharded journals | component partition notes cannot create invented global unswept blocks
input-digest-drift | caller-supplied inputs | plan, registry, archive, manifest and producer source digests match exact bytes
signature-promotion | statement and report | unsigned stays unsigned and publisher identity stays unchecked
partial-output | example destination | existing output refuses and failure installs no incomplete accepted bundle
path-alias | input and output filesystem boundary | links, special files, escapes and output aliases cannot mutate release inputs
forged-report | published reports and statements | verify reruns gates and compares exact subjects and report bytes
coverage-refusal | coverage mutation specimens | missing gaps, missing reason and outside bounds fail the named check
historical-overclaim | handoff limitations | deployment gaps, trace selection and source ambiguity remain visible
frontier-drift | mature Ariadne ledger | only generation changes and every frontier field remains unchanged
```

## 6. Glossary seeds

Sealed release: Alexandria's manifest and every digest-named component verified
as one release. Dataset statement: an unsigned in-toto record binding those
bytes to supplied evidence. Temporal tail: blocks inside the declared interval
that were not swept. Semantic gap: an evidence limitation that may persist
through a fully swept interval. Producer: the observed process that created
these byte-identical rebuilt release files. Coverage inventory: the retained
source scopes and gap statements, without strengthened evidence classes.

## 7. Sources

Repository pointers below are fixed to the starting commit; paths mentioned
elsewhere are lookup identifiers. Live issue and PR bodies were read during
this study, not inferred from closed status.

- [Issue 1374](https://github.com/wildcat-finance/skills/issues/1374), its accepted scope and comments; [capture integration PR 1838](https://github.com/wildcat-finance/skills/pull/1838).
- [Accepted capture record](https://github.com/wildcat-finance/skills/blob/104f6f82c390003fb61039d3023d07c1abe05086/docs/kickoff/1374/capture.md), with its dated observations preserved.
- [Dataset capture](https://github.com/wildcat-finance/skills/blob/104f6f82c390003fb61039d3023d07c1abe05086/plugins/ariadne/scripts/ariadne_lib/capture/dataset.py) and [dataset guide](https://github.com/wildcat-finance/skills/blob/104f6f82c390003fb61039d3023d07c1abe05086/plugins/ariadne/docs/capturing-a-dataset.md).
- [Wildcat delivery proof](https://github.com/wildcat-finance/skills/blob/104f6f82c390003fb61039d3023d07c1abe05086/plugins/alexandria/docs/wildcat-interval/proof.md) and [combined offline example](https://github.com/wildcat-finance/skills/blob/104f6f82c390003fb61039d3023d07c1abe05086/plugins/alexandria/examples/wildcat-estates-interval-v0/README.md).
- [Ariadne ledger](https://github.com/wildcat-finance/skills/blob/104f6f82c390003fb61039d3023d07c1abe05086/plugins/ariadne/skills/ariadne/EVOLUTION.md); the audit sources and exact view ranges are listed in section 2.

## 8. Signals and questions

[Ephoros](https://github.com/wildcat-finance/skills/blob/104f6f82c390003fb61039d3023d07c1abe05086/plugins/hexaemeron/skills/ephoros/SKILL.md)
governs the reports. Which exact release was bound? Record estate, release ID,
manifest and statement digests. Which check failed? Keep the entire verifier
output, command and exit status. Was the archive actually used? Distinguish
full rebuild from metadata-only verification. Step 2 emits these local records;
there is no unattended service or new alerting system.

## 9. Trust boundaries and controls

[Phylax](https://github.com/wildcat-finance/skills/blob/104f6f82c390003fb61039d3023d07c1abe05086/plugins/hexaemeron/skills/phylax/SKILL.md)
governs filesystem inputs, caller metadata and subprocess boundaries. Treat
manifest paths, selectors and historical commands as data. Confine reads,
refuse special files and aliases, use argv execution for owned commands only,
and retain named digest refusals. Input recovery uses the verified archive in a
fresh directory. Keep credentials and endpoint secrets out of examples; source
provider-class labels grant no network authority. The local no-socket test is
an observed Python boundary, not an operating-system sandbox or protection
against a hostile concurrent filesystem writer.

## 10. Performance and resources

[Metron](https://github.com/wildcat-finance/skills/blob/104f6f82c390003fb61039d3023d07c1abe05086/plugins/hexaemeron/skills/metron/SKILL.md)
governs performance claims. There is no speedup target for this binding task.
The design reports retain the executed probe command and its limited wall-time
and listing-size observations. The accepted release inputs total 20,496,046
bytes for V1 and 242,722,051 bytes for V2. Stream hashes and inspect one bounded
component at a time; keep the input owner's 67,108,864-byte component ceiling.
No throughput, whole-collection duration or peak-memory claim follows from the
probe. Final tests must not silently skip the real-input demonstration.

## 11. Fail-closed posture

[Elenchus](https://github.com/wildcat-finance/skills/blob/104f6f82c390003fb61039d3023d07c1abe05086/plugins/hexaemeron/skills/elenchus/SKILL.md)
governs any reproduced failure and guard. Missing or changed source bytes,
wrong release, unsupported count selector, conflicting counts, absent gap
reason, incomplete gate output or source/output alias stops acceptance. Keep
the failure and repair the named input before rerunning. A fixture test that
expects a refusal proves the refusal; it is not a product-fix claim. Any actual
fix must carry the source-owned reporter, parent-red and fixed-green evidence
required by the controller. The current V2 staging recovery introduced no code
change and earns no Elenchus guard verdict.

## 12. Decisions and homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/104f6f82c390003fb61039d3023d07c1abe05086/plugins/hexaemeron/skills/hypomnema/SKILL.md)
governs the durable decision. Record the full-release choice and conservative
semantic-gap projection in Ariadne's existing `EVOLUTION.md`, with its evidence
link when delivery lands. The example README explains how to reproduce the
statements, what inputs are external, how counts were supplied, and why a
whole-interval semantic gap is not an unread temporal interval. The study and
runbook live with the example's specification; no cross-cutting ADR is needed.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | full-release
record | plugins/ariadne/skills/ariadne/EVOLUTION.md
```
