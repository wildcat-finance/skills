# Runbook: portable Hexaemeron checkpoint archive design package

This run ships documentation and executable document checks only. It records
the common contract for `run-anchor`, `archive-core`, `checkpoint-store`, and
`resume-routing`; each module still requires its own later Fiat study and
runbook before code is written. Nothing here adds controller commands, deploys
a service, changes the Atlas, regenerates the contributor PDF, or makes remote
checkpoint handover live.

The run uses the repository's existing Apache-2.0 licence, Python 3.11 standard
library test style, and root unittest discovery. No dependency, CI workflow, or
licence file changes. Every step starts from the reviewed exit of the preceding
step, stays green under the targeted document tests and the root suite, and
gets one stacked pull request and its own Fiat audit loop. Imprimatur runs before
Brevitas on every prose file changed by a step. The final step derives Horos's
whole boundary twice, updates `.horos/boundary.json` only when that exact
comparison proves it stale, and then runs both Horos currency checks.

## Step 1: Scaffold the design-package contract

**Goal.** Establish the tracked design-package layout and test entry point,
including committed copies of the receipted study and runbook that remain
byte-identical to their controller artefacts.

**Modules.** `run-anchor`, `archive-core`, `checkpoint-store`, and
`resume-routing`: this scaffold is the common design boundary and implements
none of them.

**Entry.** Run branch
`fiat/portable-hexaemeron-checkpoint-archives-and-hand` at
`346c1223e86d07635ebbdfc4d09850c6b865b136`, with a clean tracked tree, the
study receipted at state
`624d9b7a06b4b967693037baaaf914d0094bfba167fb24bdd44b76e8f4a2f6d1`, and
this runbook receipted before the controller opens Step 1.

**Exit.** The repository tracks the study, runbook, and a root-suite document
test stub; the two tracked documents match the receipted bytes; existing root
licence and unittest discovery cover the new first-party files; all of the
following exit 0 after the step commit:

```bash
cmp .hexaemeron/study.md docs/hexaemeron-checkpoint-archive-study.md
cmp .hexaemeron/runbook.md docs/hexaemeron-checkpoint-archive-runbook.md
git ls-files --error-unmatch \
  docs/hexaemeron-checkpoint-archive-study.md \
  docs/hexaemeron-checkpoint-archive-runbook.md \
  tests/test_checkpoint_archive_spec.py LICENSE
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study docs/hexaemeron-checkpoint-archive-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  docs/hexaemeron-checkpoint-archive-runbook.md
python3 -m unittest tests.test_checkpoint_archive_spec
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  docs/hexaemeron-checkpoint-archive-study.md \
  docs/hexaemeron-checkpoint-archive-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/hexaemeron-checkpoint-archive-study.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/hexaemeron-checkpoint-archive-runbook.md
test -z "$(git status --porcelain)"
```

**Files.** Create
`docs/hexaemeron-checkpoint-archive-study.md`,
`docs/hexaemeron-checkpoint-archive-runbook.md`, and
`tests/test_checkpoint_archive_spec.py`. Read and reuse `LICENSE` and the root
test discovery; do not edit `.github/` or licence files.

**Tests.** Start `tests.test_checkpoint_archive_spec` with at least two checks:
the tracked design paths and the existing root licence/test context. The local
`cmp` commands separately prove byte identity with ignored controller
artefacts; CI must not depend on `.hexaemeron/` being present.

**Disciplines.** phylax: none, this step adds no executable or external-input
boundary; ephoros: none, no unattended path runs; metron: none, no performance
claim or change; elenchus: none, this scaffold addresses no reproduced runtime
failure; hypomnema: file placement and resolvable references apply because the
study and runbook become tracked sources for later records.

## Step 2: Specify run anchors and cumulative archives

**Goal.** Record the immutable-base, package, manifest, export, import, and
lineage decisions for `run-anchor` and `archive-core`, with tests that reject
the known prior-art gaps.

**Modules.** `run-anchor` followed by `archive-core`; the documents fix their
interface and #439 dependency but add no controller implementation.

**Entry.** Step 1's reviewed exit state, with byte-identical tracked study and
runbook copies, passing scaffold tests, and no change to the run's original
base SHA.

**Exit.** ADR-014 holds the chosen cumulative design, alternatives, Wildcat
Labs provenance, and Proposed status. The standing specification fixes the
immutable initial base, issue and run identity, exact archive members,
canonical manifest, content digests, read-only export, accepted-parent stage,
and isolated import/refusal semantics. It states that #439 must land before
import or controller integration and does not describe either as live. The
following exit 0:

```bash
python3 -m unittest tests.test_checkpoint_archive_spec
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study docs/hexaemeron-checkpoint-archive-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  docs/hexaemeron-checkpoint-archive-runbook.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py \
  tests/test_checkpoint_archive_spec.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  docs/hexaemeron-checkpoint-archive-study.md \
  docs/hexaemeron-checkpoint-archive-runbook.md \
  docs/hexaemeron-checkpoint-archive-spec.md \
  docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/hexaemeron-checkpoint-archive-study.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/hexaemeron-checkpoint-archive-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/hexaemeron-checkpoint-archive-spec.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  docs/hexaemeron-checkpoint-archive-study.md \
  docs/hexaemeron-checkpoint-archive-runbook.md \
  docs/hexaemeron-checkpoint-archive-spec.md \
  docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md
```

**Files.** Create
`docs/hexaemeron-checkpoint-archive-spec.md` and
`docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md`;
extend `tests/test_checkpoint_archive_spec.py`.

**Tests.** Extend the document suite with named checks for Wildcat Labs design
provenance and not-live status; full immutable initial-base SHA and #439
dependency; exact bundle, cumulative, index, worktree, and controller-state
members; manifest member digests and exclusions; stage derived from accepted
parent-chain depth rather than caller input; read-only export without a digest
cycle; isolated import and unchanged caller checkout; and ADR shape and rejected
alternatives. Each assertion must be absent or fail on Step 1's tree before it
passes here.

**Disciplines.** phylax: the specification opens hostile ZIP, Git-object,
filesystem, controller-state, and secret boundaries and must pair each with a
control; ephoros: none, this step defines no running service or new signal;
metron: none, the byte ceilings are security limits rather than performance
claims; elenchus: the known caller-supplied-stage and mutable-base failures get
red-before-green document guards; hypomnema: ADR-014 records the
expensive-to-reverse cumulative format and the alternatives it rejects.

## Step 3: Specify checkpoint-store operations

**Goal.** Complete the `checkpoint-store` service and operator contract without
choosing or deploying infrastructure.

**Modules.** `checkpoint-store`, consuming the fixed `archive-core` package
interface from Step 2.

**Entry.** Step 2's reviewed exit state, with ADR-014 Proposed, the package
contract fixed, document tests green, and #439 still treated as a prerequisite
rather than accepted behaviour.

**Exit.** The specification fixes routes, request integrity, authentication
boundary, response codes, RFC 9457 problems, immutable metadata/object records,
idempotency, lineage conflicts, validator caps, and signal fields. The operator
runbook answers what fired, the first check, and who to wake for every named
service failure, while saying that no service exists yet. The following exit 0:

```bash
python3 -m unittest tests.test_checkpoint_archive_spec
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study docs/hexaemeron-checkpoint-archive-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  docs/hexaemeron-checkpoint-archive-runbook.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py \
  tests/test_checkpoint_archive_spec.py
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  docs/hexaemeron-checkpoint-archive-spec.md \
  docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md \
  docs/runbooks/hexaemeron-checkpoint-store.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/hexaemeron-checkpoint-archive-spec.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/runbooks/hexaemeron-checkpoint-store.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  docs/hexaemeron-checkpoint-archive-spec.md \
  docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md \
  docs/runbooks/hexaemeron-checkpoint-store.md
```

**Files.** Extend `docs/hexaemeron-checkpoint-archive-spec.md`; create
`docs/runbooks/hexaemeron-checkpoint-store.md`; extend
`tests/test_checkpoint_archive_spec.py`.

**Tests.** Add named document guards for every route and status; RFC 9530
content digest and RFC 9457 refusal shape; the four logical metadata records;
immutable object identity and idempotent repeats; parent validation and a `409`
fork instead of timestamp choice; bounded ZIP and member limits; stable refusal
codes; private archive access; operator dependency and restore checks; bounded
signals and metric labels; and the three required operational-runbook answers.
Each new guard must fail against Step 2 before passing here.

**Disciplines.** phylax: the planned API, bearer identity, archive validator,
metadata store, object store, and importer are explicit trust boundaries with
refusal controls; ephoros: the service runs unattended, so the operator
questions, bounded events and alert paths belong in its runbook; metron: none,
no service is measured or optimised and later objectives require a recorded
archive corpus; elenchus: service refusal and partial-publication cases receive
red-before-green document guards; hypomnema: the operator runbook and service
interface live in the repository's established documentation locations.

## Step 4: Correct contributor routing and demonstrate the package

**Goal.** Make the contributor guide match the live random Atlas route and the
not-yet-live checkpoint boundary, then run the complete design-package demo.

**Modules.** `resume-routing`, consuming the design contracts from Steps 2 and
3 while leaving the Atlas and checkpoint service unchanged.

**Entry.** Step 3's reviewed exit state, with the complete package/store design
and operator runbook green, and the checked-in contributor guide still carrying
the stale finish-the-issue and proposed earliest-Wave wording identified by the
study.

**Exit.** The guide sends a contributor to the existing random Atlas, says the
assistant rechecks the selected issue, assignment, issue-number branches, pull
requests, dependencies, and checkpoint discovery before new work, and lets the
contributor stop at a named Fiat checkpoint. It distinguishes an accepted
future checkpoint from today's pushed-branch fallback and does not claim an API,
archive, importer, deployment, or PDF update exists. The exact study demo and
all added repository gates exit 0:

```bash
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  --study docs/hexaemeron-checkpoint-archive-study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py \
  docs/hexaemeron-checkpoint-archive-runbook.md
python3 -m unittest tests.test_checkpoint_archive_spec
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py \
  docs/hexaemeron-checkpoint-archive-study.md \
  docs/hexaemeron-checkpoint-archive-runbook.md \
  docs/hexaemeron-checkpoint-archive-spec.md \
  docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md \
  docs/runbooks/hexaemeron-checkpoint-store.md \
  docs/how-to-help-shoggoth.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/hexaemeron-checkpoint-archive-study.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/hexaemeron-checkpoint-archive-runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/hexaemeron-checkpoint-archive-spec.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/runbooks/hexaemeron-checkpoint-store.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py \
  docs/how-to-help-shoggoth.md
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py \
  tests/test_checkpoint_archive_spec.py
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py \
  docs/hexaemeron-checkpoint-archive-study.md \
  docs/hexaemeron-checkpoint-archive-runbook.md \
  docs/hexaemeron-checkpoint-archive-spec.md \
  docs/decisions/ADR-014-use-cumulative-portable-checkpoints-for-fiat-handover.md \
  docs/runbooks/hexaemeron-checkpoint-store.md \
  docs/how-to-help-shoggoth.md
```

Then prove the whole Horos document is deterministic and current without
weakening the unchanged-path boundary:

```bash
horos_evidence_dir="$(mktemp -d)"
python3 plugins/horos/skills/horos/scripts/horos.py scan . --json \
  > "$horos_evidence_dir/fresh-one.json"
python3 plugins/horos/skills/horos/scripts/horos.py scan . --json \
  > "$horos_evidence_dir/fresh-two.json"
cmp -s "$horos_evidence_dir/fresh-one.json" \
  "$horos_evidence_dir/fresh-two.json"
if ! cmp -s "$horos_evidence_dir/fresh-one.json" .horos/boundary.json; then
  python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
fi
cmp -s "$horos_evidence_dir/fresh-one.json" .horos/boundary.json
python3 -c 'import shutil, sys; shutil.rmtree(sys.argv[1])' \
  "$horos_evidence_dir"
python3 plugins/horos/skills/horos/scripts/horos.py check .
python3 -m unittest tests.test_boundary_currency
git diff --exit-code \
  346c1223e86d07635ebbdfc4d09850c6b865b136..HEAD -- \
  README.md docs/pdf plugins .github LICENSE
```

**Files.** Update `docs/how-to-help-shoggoth.md` and extend
`tests/test_checkpoint_archive_spec.py`. Update `.horos/boundary.json` only when
the first fresh whole document differs; Horos may rewrite
`.horos/candidates.json` byte-identically in that conditional write. Do not
change `README.md`, `docs/pdf/how-to-help-shoggoth.pdf`, `plugins/`, `.github/`,
or `LICENSE`.

**Tests.** Add named guards for random selection across all eligible Waves;
live issue, assignment, dependency, branch, pull-request, and checkpoint
rechecks; resume, redraw, or start outcomes; stop-at-checkpoint wording; the
pushed-branch fallback; explicit not-live archive/service/importer wording;
and removal of the stale earliest-Wave selector and finish-the-issue advice.
The full design-package test module and root suite are the final demonstration.
Two fresh Horos documents must match, the committed whole document must match
them after the conditional write, and both `horos check .` and
`tests.test_boundary_currency` must pass.

**Disciplines.** phylax: the guide treats Atlas and future checkpoint responses
as candidates rather than authority and names the live rechecks; ephoros: none,
this step changes guidance rather than an unattended path; metron: none, no
performance claim or change; elenchus: stale-route claims receive guards that
fail on the entry guide and pass after correction, while a stale Horos whole
document is repaired only after direct comparison; hypomnema: the contributor
truth belongs in the existing guide, while the implementation decision remains
in ADR-014 and the PDF stays explicitly deferred.
