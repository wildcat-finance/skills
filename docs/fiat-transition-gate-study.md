# Study: checkpoint-bound Fiat audit-loop continuation

Assuming, unless corrected:

1. Issue [#871](https://github.com/wildcat-finance/skills/issues/871) is the complete protected scope. Its six enforcement responsibilities and ten acceptance cases are requirements, not optional design suggestions.
2. The immediate operator need is to restore a different Fiat run from its pre-verdict checkpoint and begin audit loop 2. This study may design that path but does not read, score, or mutate that run's task, holdout, model, controller, or audit evidence.
3. A restored checkpoint may have a new absolute worktree path. "Same worktree" therefore means the one active worktree identity proved by the current preimage, with at most one controller-receipted relocation from the supplied checkpoint. Literal equality with the checkpoint's former absolute path would contradict #871's fresh-operator restore acceptance case.
4. A two-file state and ledger update cannot be one POSIX namespace operation. "Atomic" therefore means the stronger recoverable condition #871 states in acceptance case 6: exact preimage or one durable, labelled transaction from which the exact postimage can be completed; never an unlabelled mixed state.
5. The repository's pinned Python is used with the standard library. No package, service, operating-system profile, model call, or provider credential is added.
6. Existing `steps[*].audit.rounds` values are historical loop 1. Their ordered entries and the corresponding audit-log prefix are immutable.

## 1. Problem statement

Fiat currently verifies a hash-chained ledger and emits one canonical next directive, but those facts are not joined to a closed Promise-to-command decision before every effect. The failure in #871 made the gap concrete: an exhausted eight-round audit was treated as permission to raise `audit.max_rounds`, clear a halt, and describe rounds 9 through 16 in public prose. None of those transitions belonged to the active `fiat-receipted-delivery` Promise.

This run must add two connected capabilities without conflating them:

- a closed transition kernel that makes every Fiat effect prove its exact preimage, active directive, Promise, command evidence, and permitted consequence before a writer runs; and
- a separate checkpoint-bound Promise and `start-audit-loop` transition that appends loop `N + 1`, begins its round 1 on the same ledger, and preserves every earlier loop.

A working prototype is the repository implementation, not a deployment into another live run. It is proved by a disposable end-to-end demo that creates an exhausted loop, exports and restores its checkpoint, obtains one controller-generated handover, starts loop 2 with recorded authority, records loop 2 round 1, and verifies all of these together:

1. the imported ledger remains one valid chain;
2. the canonical bytes for loop 1 and its audit-log prefix are unchanged;
3. every inherited final-round finding id and the unresolved-leads digest is present in the loop 2 carryover;
4. `next`, state, log headings, filenames, and handover output name loop 2 round 1 and never round 9;
5. hostile variants in #871 refuse before an effect, or leave one recoverable transaction; and
6. the current valid study, runbook, implementation, audit, prose, push, merge, halt, checkpoint, restore, and reset fixtures still reach only their declared transitions.

The final named demo is `verify_transition_gate.py conformance --case full-acceptance --report <path>`. The runbook must also name the exact focused and repository suites that exercise it. No success claim may depend on applying the prototype to the separate live run mentioned in assumption 2.

## 2. Prior art

### Promise and checkpoint contracts already present

`PROMISE_MACHINE.md` defines a Promise as a single evidence-bounded transition. `plugins/hexaemeron/skills/fiat/SKILL.md` declares `fiat-receipted-delivery`; it authorises only the canonical next controller transition and already refuses model interpretation as authority. It has no audit-loop continuation Promise.

[ADR-028](../docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md) replaced the earlier fresh-run continuation idea with cumulative portable checkpoints and explicitly leaves a later same-ledger audit-loop transition open. `docs/fiat-controller-checkpoint-study.md` and `plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md` define the current capsule, restore marker, clone-loss recovery, and exact-prefix rules. `plugins/hexaemeron/skills/fiat/references/checkpoint-identity.md` supplies a stable semantic identity over state, ledger, refs, sources, policy, and selected observations. The new transition should consume those proofs instead of defining a second checkpoint format.

[ADR-047](../docs/decisions/ADR-047-freeze-fiat-configuration-after-init.md) records why audit policy cannot be widened to escape a controller refusal. The new loop is a new bounded object, not an edit to the old loop's ceiling.

### Current implementation surface

At the pinned base `01a17bed45058a1fc20875bb19765fdf91cb293a`:

- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py:2065` declares twelve names in `MUTATING`, and `hexctl.py:16242` chooses locking from `args.fn.__name__`. This is an open list rather than discovery of every writer.
- `hexctl.py:2243` appends the ledger and then replaces state. The existing general commit path has no durable transaction marker across those two writes.
- `hexctl.py:1642` validates the version-1 container spine but treats audit-round leaves as heterogeneous dictionaries. It has no loop identity or prior-loop immutability rule.
- `hexctl.py:6425` initialises each step with `audit.rounds`; `hexctl.py:6866` numbers the next receipt as `len(rounds) + 1`; and `hexctl.py:15457` returns `audit-verdict` after the one flat list reaches its configured ceiling. This representation cannot express loop 2 round 1 without either rewriting history or inventing round 9.
- `hexctl.py:2444` accepts an integer ceiling greater than or equal to 1, while checkpoint identity at `hexctl.py:13033` admits values as high as 1,000,000. Both must converge on 1 through 8.
- `hexctl.py:6065` keeps `config get` and `config set` in one handler. The write allowlist admits the whole `git` object and every `git.*` leaf, so its shape is not yet field- and phase-specific.
- `hexctl.py:15711` records a generic halt and `hexctl.py:15720` clears any halt from a free-form note. There is no stored pre-halt directive grant.
- `cmd_checkpoint_restore` writes a worktree, refs, controller files, state, ledger, marker, and breadcrumb but is not in `MUTATING`. `cmd_next --brief-out` writes a delegation file while being described as read-only. `cmd_checkpoint_export` and `cmd_reset` write outside the ordinary state/ledger pair. Writer discovery must cover these effect classes rather than trusting the current set's name.
- The audit-record v2 parser verifies row count and receipt-safe digests but discards finding ids and `Leads not pursued` content. A continuation cannot claim complete carryover from the stored integer alone.

The verified plugin synopsis `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` records F-01 through F-09 fixed and F-10 accepted. Its legacy round lacks `Audit schema`, `Covered`, `Not checked`, and `Elenchus verdict`, which remain unknown. Its retained leads include a symlinked state-directory boundary and single-driver concurrency. Current code has since added a run lock and hostile checkpoint handling, but the synopsis does not retroactively prove those newer paths.

### Last two merged controller changes

[PR #1158](https://github.com/wildcat-finance/skills/pull/1158) added source-bound delegation contract paths and the plugin root to worker briefs. Its carryover keeps #1122's third acceptance item blocked on #1098. This run must preserve the brief fields and must not claim that unrelated item.

[PR #1156](https://github.com/wildcat-finance/skills/pull/1156) added Warden continuity as `new` or `same-agent`, derived from the flat audit-round list. Loop-aware delegation must add the active loop and round while keeping continuity truthful: loop 2 is still audit work on the same step, so it is not automatically a new Warden context.

### Incidents and adjacent proposals

Issue #871 preserves the #622 incident's 43-entry, exhausted-round-8 preimage identity and the rejected 45-entry mutation. The remote #622 and #681 records were unavailable to the authenticated GitHub API on 2026-09-03, so this study does not pretend to have reread them. It relies on #871's preserved statement, ADR-028, the controller-checkpoint study, and the repository's verified audit views. The implementation must turn the preserved #622 input into a committed bounded fixture or state explicitly why the exact public bytes cannot be recovered; a lookalike fixture cannot be labelled the #622 preimage.

[Issue #508](https://github.com/wildcat-finance/skills/issues/508) concerns exhausted-audit carryover, absolute delegated writes, and executable runbook commands. This run answers the first lane only where #871 requires it. It does not claim the other two. [Issue #857](https://github.com/wildcat-finance/skills/issues/857) and the Shoggoth Interceptor supply integrity-first wrapper precedent. [Issue #859](https://github.com/wildcat-finance/skills/issues/859) is the checkpoint programme, not authority to build a service or broker.

## 3. Constraints and non-goals

- The implementation starts from `main` at `01a17bed45058a1fc20875bb19765fdf91cb293a`. Repository Python commands use `.python-version` through `mise`; JavaScript-dependent repository checks use the declared Node version.
- `transition_gate.py`, `handover.py`, `verify_transition_gate.py`, the publication wrapper, and the transaction machinery are standard-library Python or the required small `set -eu` shell wrapper. No dependency is added.
- The gate is pure: no filesystem, process, network, clock, environment, prose interpretation, or write access. Callers capture and validate evidence before passing closed values to it.
- Existing state version 1 and `audit.rounds` are accepted. Legacy entries remain loop 1 in place. No migration may nest, reorder, renumber, or rewrite them.
- Every loop has an immutable integer maximum from 1 through 8. Loop 1 uses its receipted configuration. A later loop receives its own maximum in the continuation grant. Raising an active or completed loop's maximum is never a recovery path.
- `config get` remains read-only. `config set` accepts only individually declared leaves in individually declared phases. Whole-object replacement is refused. `audit.max_rounds` can be selected only before the first audit receipt and only in the range 1 through 8.
- A generic halt note is evidence of why work stopped, not permission to clear it. A resumable halt must preserve the exact pre-halt directive and its specific resume rule. An exhausted `audit-verdict` halt has no generic resume rule.
- A continuation is accepted only from an active `audit-verdict` whose current loop is exhausted and whose last round has findings. A halted legacy run is restored to its verified pre-verdict checkpoint; it is not edited or generically resumed.
- Checkpoint restore may relocate once through its existing receipted transaction. After restore, the active preimage worktree identity is fixed. Unreceipted ref, tree, state, ledger, audit-log, controller, or path movement refuses.
- The claim is deterministic refusal, exact evidence binding, and tamper evidence under the repository's checked execution path. It is not privilege isolation from a process that can rewrite and execute every file under the same operating-system account.
- The bootstrap run that creates the gate cannot claim the new gate governed its own creation. The final integration installs and pins it. Later gate changes require a separate human-maintainer review and a new manifest/controller digest.
- This run does not close or waive inherited audit findings, select an `audit-verdict` outcome, mutate #622, inspect or mutate the separate live run, implement a general delegation-write sandbox, or build an Interceptor-owned broker.
- Publication checking is limited to live Fiat mutation recipes in ADR, handover, issue-comment, and pull-request bodies. It does not establish the surrounding prose true or make arbitrary manual `gh` use impossible.
- No step may publish, deploy, or expose a partially wired transition. The first functional continuation slice remains disabled outside its tests until all #871 gates integrate.

Success is testable by the demo in item 1, the two progressive conformance reports declared in `.hexaemeron/design-evidence.json`, the repository's affected checked runner, portable Promise Machine synchronisation, exact controller-pin reconciliation, and hostile byte-equality tests. A missing exact #622 fixture blocks only claims about acceptance cases 1 and 2; it does not permit substituting a synthetic fixture under that name.

## 4. Design options

### Candidate `append-only-loop-kernel` (selected)

Keep `steps[*].audit.rounds` as the physical record of loop 1 and add one optional `audit.continuations` array. Each continuation is a closed object containing its loop number, its own maximum, an empty-then-append-only `rounds` list, the predecessor-loop canonical digest, the verified checkpoint and active-preimage identities, the exact recorded authority, and a carryover object derived from the predecessor's final audit record. A helper presents loop 1 and later continuations through one read interface; writers never migrate loop 1.

The first implementation slice after the required record/scaffold step adds the smallest safe continuation path:

1. `transition_gate.py` with closed `fiat-transition-grant/v1` and refusal envelopes;
2. a separate `fiat-checkpoint-audit-loop-continuation` Promise in the canonical Fiat contract;
3. the effect registry and verified preimage capture needed by `start-audit-loop`;
4. a general write-ahead transaction primitive that stages exact postimage state and ledger bytes before publishing either; and
5. loop-aware state validation, directives, audit receipt v3, Warden brief fields, and hostile continuation fixtures.

The command shape is:

`hexctl start-audit-loop --checkpoint <capsule-directory> --manifest-sha256 <sha256> --authority-file <bounded-utf8-file> --max-rounds <1..8>`

The dispatcher verifies gate integrity, the exact state and ledger bytes, the canonical `audit-verdict`, the checkpoint or its unique restore lineage, current controller and worktree evidence, the final audit-log suffix, Git cleanliness and refs, and the typed arguments. It then calls the pure gate. The grant binds the Promise id, consequence, normalised command, preimage digests, directive digest, evidence digest, and one transition id. Only the transaction writer consumes the grant.

The current audit v2 row grammar is extended, not reinterpreted. For a legacy final round the evidence builder parses the already digest-bound raw suffix, validates unique finding ids and exact row count, preserves each row's identity-bearing cells, and hashes the exact `Leads not pursued` value. Audit v3 adds loop identity and a carryover digest. The first loop 2 directive and Warden brief carry every inherited id and the leads digest. No free-form integer count can stand in for those identities.

The transaction stages `state.next`, `ledger.next`, the grant, and a closed manifest in one private transaction directory, fsyncs them, and publishes a durable pending marker before replacing either live file. Recovery accepts only exact preimage, exact postimage, or the two named mixed windows whose staged bytes match. It completes the recorded postimage or refuses; it never guesses or silently rolls back an append-only ledger. The marker is retired only after both live bytes and their directory entry are durable.

The remaining slices route every effect through a closed registry, add controller-derived handover JSON and rendering, install integrity-first verification and wrapper paths, gate publication recipes, reconcile portable copies and pins, and run the full acceptance demo. Read-only commands have no writer capability. Derived-output commands such as `next --brief-out`, checkpoint export, restore, and reset are distinct effect classes with exact grants; they are not hidden under the state/ledger commit label.

Trade: the physical state has a legacy loop-1 list beside later continuation objects, so readers need one audited projection helper instead of a visually uniform nested array. That complexity buys byte-preserved history, a direct same-ledger append, and no migration of receipted states.

### Candidate `nested-loop-state-v2`

Introduce a new state version in which every step has `audit.loops`, migrate `audit.rounds` into `loops[0].rounds`, then build the same pure gate, transaction writer, handover, integrity path, and publication gate over the uniform structure.

Trade: downstream code becomes simpler after migration, but the first safe continuation requires a state migration, loop-aware verifier, and transition kernel before it can exist. More importantly, migrating the #622 or another legacy preimage rewrites the physical loop-1 subtree. A digest saying the values are equivalent is not the byte-identity #871 requires. This candidate therefore fails the compatibility gate.

### Candidate `continuation-sidecar`

Leave `hexctl`'s current commit and handler dispatch intact. Add a checked sidecar that maps an exhausted checkpoint to a second list of rounds and teach handover output to mention it.

Trade: it reaches a loop-2-shaped display quickly and leaves legacy state untouched, but it has two authorities for one audit, no single state/ledger transaction, no complete writer discovery, no integrity-first dispatcher, and no publication grant. It recreates the judgement gap #871 was filed to remove and therefore fails the protected-scope and recovery gates.

### Checked design comparison

The closed report matrix uses these pre-build facts. A "safe continuation slice" is an implementation slice after the mandatory record/scaffold step; it is not a wall-clock estimate. A "legacy round record rewritten" is one existing physical record class that the design requires a loader or writer to relocate.

| candidate | all six #871 responsibilities | safe continuation slices | legacy record classes rewritten | legacy loop 1 exact | labelled transaction recovery |
| --- | --- | ---: | ---: | --- | --- |
| `append-only-loop-kernel` | yes | 1 | 0 | yes | yes |
| `nested-loop-state-v2` | yes | 3 | 1 | no | yes |
| `continuation-sidecar` | no | 1 | 0 | yes | no |

`append-only-loop-kernel` is the unique surviving frontier: `nested-loop-state-v2` fails legacy compatibility, and `continuation-sidecar` fails correctness and recovery. Among the surviving designs it also minimises both declared comparative counts. Implementation conformance remains pending at the explicit step and integration boundaries in the design record; the study does not predict those test results.

## 5. Risk register seed

```risk-register
grant-preimage-binding | the join from verified state and ledger to a transition grant | stale state ledger directive checkpoint or evidence digests refuse before any effect
writer-discovery-drift | the parser handler registry and low-level write call graph | every effectful handler has one rule hostile specimen and guarded writer path
transaction-crash-window | the staged state ledger pair and pending marker | each injected interruption yields exact preimage exact postimage or one recoverable labelled transaction
transaction-concurrency | one run lock around preimage capture gate evaluation and publication | a second writer refuses and cannot consume or replace the first writer's grant
same-account-tamper | the integrity manifest verifier wrapper and writable checkout | claims stop at deterministic refusal and tamper evidence rather than operating-system isolation
legacy-loop-preservation | legacy audit rounds and their audit-log prefix | starting a later loop leaves both canonical round bytes and raw log prefix unchanged
round-nine-alias | state directives logs filenames status briefs handovers and receipts | no accepted output can encode round 9 and every loop-local round stays between 1 and 8
loop-number-continuity | the append-only continuation array | the next loop is exactly predecessor plus one and every prior loop digest remains fixed
finding-carryover-omission | the predecessor final audit table and continuation evidence | unique finding ids and exact unresolved-leads digest are derived from the checked suffix with no caller-selected omission
audit-log-schema | legacy v1 and v2 records beside loop-aware v3 | legacy records remain loop 1 and later loops require explicit loop identity and carryover binding
checkpoint-lineage | an exported capsule or its unique restored descendant | source manifest restore receipt active preimage and ledger prefix agree before continuation
worktree-and-ref-movement | the active restored worktree Git refs and working tree | unreceipted relocation ref movement commit movement or dirty content refuses
generic-resume-overreach | halt and resume state | resume requires a stored pre-halt grant and cannot clear an exhausted audit-verdict halt
config-container-bypass | config get set parsing and policy | whole-object writes unknown leaves wrong phases booleans and maxima outside 1 through 8 refuse byte-identically
derived-output-writers | brief export restore reset archive and breadcrumb paths | each non-ledger effect has its own grant containment cap no-follow checks and recovery rule
handover-prose-divergence | accepted handover JSON and rendered paste block | human bytes derive only from the checked envelope and unsupported continuation or round 9 cannot render
publication-command-smuggling | Markdown recipe extraction and the four allowed GitHub actions | only closed read-only or fixture-accepted controller commands reach fixed-argv GitHub invocation
gate-integrity-bootstrap | gate verifier manifest wrapper portable copy and workflow references | bootstrap is named and every post-install mutation verifies regular files modes pins call order and required tests first
current-brief-compatibility | plugin-root contract-path and Warden continuity fields from PRs 1158 and 1156 | loop fields are additive and continuity does not assert fresh context merely because a new bounded loop began
fixture-provenance | the preserved #622 identity and any synthetic exhausted-loop fixture | unavailable public bytes stay unavailable and a synthetic fixture is never labelled as the incident preimage
```

The audit loop should also retain the plugin synopsis's older unknown fields and accepted F-10 boundary when it cites that source. A new clean round cannot rewrite those historical observations.

## 6. Glossary seeds

- **Active preimage:** the stable, verified state bytes, ledger bytes, controller identity, worktree, refs, and directive captured under the run lock before a grant is evaluated.
- **Audit loop:** one bounded sequence of local rounds numbered 1 through its immutable maximum of at most 8.
- **Continuation:** one append-only loop object authorised from an exhausted predecessor checkpoint; it is not an increase to the predecessor's limit.
- **Effect:** any state, ledger, filesystem, Git, archive, capsule, breadcrumb, derived-output, or publication write initiated by the Fiat command surface.
- **Effect registry:** the closed mapping from parsed command and effect class to Promise, evidence builder, grant rule, and sole writer API.
- **Exhausted loop:** the active loop has exactly its immutable maximum of receipts, its final finding count is non-zero, and the canonical directive is `audit-verdict`.
- **Finding carryover:** the complete identity-bearing final-round finding rows plus the exact unresolved-leads digest derived from the checked audit suffix.
- **Grant:** the pure gate's closed, digest-bound authority for one normalised command against one preimage and consequence.
- **Legacy loop 1:** the unchanged `steps[*].audit.rounds` list and its corresponding raw audit-log prefix in a pre-loop-aware run.
- **Projection effect:** a bounded write of bytes derived from a verified preimage, such as `next --brief-out`, which does not advance state or ledger but still needs a grant.
- **Restore lineage:** the exact checkpoint identity plus the unique controller-receipted relocation event that relates it to the current worktree preimage.
- **Transition transaction:** the durable staged postimage, grant, manifest, and pending marker that make a state/ledger crash recoverable.

## 7. Sources

- `AGENTS.md`, `SHOGGOTH.md`, `PROMISE_MACHINE.md`, `.agents/skills/promise-machine/SKILL.md`, and `plugins/hexaemeron/AGENTS.md`: repository identity, routing, authority, and root Promise contract.
- `plugins/hexaemeron/skills/fiat/SKILL.md` version 5.49.1, `EVOLUTION.md`, `references/audit-loop.md`, `references/controller-checkpoint.md`, `references/checkpoint-identity.md`, and the Surveyor worker brief: delivery, audit, checkpoint, and worker contracts.
- `plugins/hexaemeron/skills/protasis/SKILL.md` version 5.10.0 and `EVOLUTION.md`: study, design-record, and runbook content contracts.
- `plugins/hexaemeron/skills/{ephoros,phylax,metron,elenchus,hypomnema}/SKILL.md`: the five discipline questions cited below.
- `plugins/hexaemeron/skills/imprimatur/SKILL.md`: study prose gate.
- [Issue #871](https://github.com/wildcat-finance/skills/issues/871), refreshed with no comments on 2026-09-03: protected scope, incident identities, responsibilities, acceptance cases, and boundary.
- [Issue #508](https://github.com/wildcat-finance/skills/issues/508), [issue #857](https://github.com/wildcat-finance/skills/issues/857), and [issue #859](https://github.com/wildcat-finance/skills/issues/859): adjacent scope and programme context.
- [PR #1158](https://github.com/wildcat-finance/skills/pull/1158) and [PR #1156](https://github.com/wildcat-finance/skills/pull/1156): the last two merged changes read before design.
- `docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md`, `docs/fiat-controller-checkpoint-study.md`, `docs/decisions/ADR-047-freeze-fiat-configuration-after-init.md`, and `docs/decisions/ADR-061-lock-designs-with-progressive-checked-evidence.md`: checkpoint, configuration, and design-lock decisions.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and focused tests under `plugins/hexaemeron/tests/`: current handler, writer, config, audit-log, checkpoint, restore, delegation, and verification behavior.
- `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`, after `audit_synopsis.py --check .` exited 0 under the pinned toolchain on 2026-09-03: verified reading view of the plugin audit. Relevant verified per-run synopsis views for the checkpoint and controller lineage were consulted under `audit/rounds/`; their authoritative sources remain the sibling `.md` files.
- The remote #622 and #681 records returned unavailable through the authenticated GitHub API on 2026-09-03. They are not claimed as read; #871 and the local records above preserve the facts used here.

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) governs the signal review. This is an interactive controller rather than an unattended service, so it adds no metric, trace, alert, or page. It does add bounded structured records that answer four recovery questions:

1. **What authorised this effect?** Every state/ledger event and external-effect receipt carries the stable Promise id, transition id, consequence, directive digest, preimage state and ledger identities, normalised-command digest, evidence digest, and grant digest.
2. **Where did an interrupted mutation stop?** The pending transaction manifest and `status` or `verify` response name preimage, staged postimage, observed live pair, permitted recovery, and one correlation id.
3. **Why did a command refuse, and did it write?** The closed refusal envelope names the failed Promise, consequence, blocked transition, stable refusal code, and recovery. Hostile tests compare all in-scope bytes before and after.
4. **Did a published recipe use the same grant?** The publication receipt binds action, repository target, body digest, fixture preimage, accepted command set, and grant digest.

No credential, authority-file path, arbitrary prose, finding text, or high-cardinality path becomes a metric or log key. Human diagnostics render from those structured records and make no stronger claim.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) governs these off-chain boundaries.

- **State, ledger, pending marker, and audit log:** hostile local bytes could forge authority or exhaust parsing. Stable no-follow reads, strict closed JSON where applicable, exact UTF-8 grammar for logs, duplicate-key refusal, size and depth caps, digest joins, and before/after identity checks close the boundary.
- **Checkpoint and restore lineage:** a supplied directory, manifest, sidecar, refs, and paths could traverse, link, change mid-read, or name another run. Existing checkpoint descriptor pinning and identity logic is reused; continuation adds exact source-to-active lineage and refuses an unrelated or multiply advanced restore.
- **Command and authority input:** argv and the authority file are untrusted. `argparse` produces a typed command, fields are allowlisted and normalised without a shell, the authority file is bounded regular UTF-8 read without links, and the receipt records its exact statement and digest without asserting who authored it.
- **Gate output:** a grant is data, not executable authority by itself. Only the sole writer API accepts its closed schema, verifies its digest and unused correlation id, and checks it against the still-current preimage immediately before publication.
- **Filesystem and Git effects:** output paths, worktree paths, refs, and subprocess output are untrusted. Paths remain within their declared roots through descriptor-based no-follow checks; subprocesses receive fixed argument lists, bounded output, time limits, and recomputed Git object identities.
- **Handover and model-authored prose:** prose can omit findings or smuggle a command. The controller emits closed JSON first, renders the paste block from it, and publication checks exact controller command syntax against a named fixture. Prose never enters the pure transition decision.
- **GitHub publication:** body bytes and destination identifiers cross into `gh`. The wrapper admits only four named actions, uses fixed argv without a shell, verifies the same grant first, and refuses before spawning on any unknown or unsupported recipe.
- **Integrity files:** the repository and installed plugin are writable by the same account. The verifier checks ordinary files, links, caps, modes, exact pins, required call sites, source order, tests, portable copies, and workflow references. This detects drift in the checked path but cannot stop a deliberately replaced verifier and launcher under the same account.

No new secret or dependency boundary is opened. Any future move to an external broker or separate operating-system identity requires a new study and authority.

## 10. The budget, or its absence

[Metron](../plugins/hexaemeron/skills/metron/SKILL.md) governs performance claims. There is no latency, throughput, memory, or token budget and no performance optimisation in this run. The design counts in item 4 compare implementation structure, not runtime speed.

All new readers inherit or tighten explicit file, JSON-depth, entry-count, path, subprocess-output, and timeout ceilings. The transaction may stage complete bounded state and ledger postimages to make recovery exact; that is an accepted space trade, not an unmeasured speed claim. If implementation changes performance or proposes an optimisation, the step must add a Metron baseline and same-method result before keeping it. Otherwise the affected repository suites and hostile cap cases are the required checks.

## 11. The fail-closed posture

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) governs failure diagnosis and guards.

Integrity failure, unverifiable preimage, stale directive, unknown Promise or command, malformed evidence, absent exact checkpoint fixture, incomplete carryover, wrong phase, wrong worktree or ref, dirty tree, loop ceiling outside 1 through 8, prior-loop digest drift, unsupported handover, publication recipe drift, or a writer outside the registry stops before the effect. A pending transaction stops every ordinary transition and exposes only verify, inspection, and its exact recovery command.

An observed implementation failure stops the step. Its reproducer preserves exact command, output, tree, state/ledger bytes, and transaction marker. A fix must address the causal mechanism and add a source-bound regression that is observed red on the unfixed parent and green on the fix before the audit records `guarded`. Crash-window tests inject after every durable boundary. Refusal tests assert exit, stable code, and byte equality; accepting a different error is not a guard.

The #622 acceptance cases stop if the exact 43-entry source fixture cannot be established from preserved bytes. A separately labelled synthetic exhausted-loop fixture may prove general behavior but cannot close the incident-specific criterion.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) governs placement.

The expensive-to-reverse decision is to use a pure closed transition gate, a central effect registry, recoverable staged state/ledger publication, and an append-only dual audit layout whose legacy list is loop 1. Its standing home will be `docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md`, with the rejected nested migration and sidecar alternatives and the same-account limitation. The runbook's record/scaffold step must create that ADR before implementation.

The new Promise and command interface live beside their executable contract in `plugins/hexaemeron/skills/fiat/SKILL.md`. The resulting governed version and frontier evidence receive one row in `plugins/hexaemeron/skills/fiat/EVOLUTION.md`; that row points to the ADR rather than duplicating the design. `references/audit-loop.md`, `references/controller-checkpoint.md`, and `references/checkpoint-identity.md` change only where their public operator contracts change. Existing ADR-028 remains historical and is linked, not rewritten or deleted.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | append-only-loop-kernel
record | docs/decisions/ADR-069-gate-fiat-mutations-and-continue-audit-loops.md
```
