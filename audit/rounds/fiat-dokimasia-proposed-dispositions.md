## Step 1, round 1 -- 2026-09-01T21:10:14Z

Audit schema: fiat-audit-round/v2

Covered: proposal-covered-path=reviewed; emitted-set-unvalidated=reviewed; reason-overclaim=reviewed; evidence-digest-binding=reviewed; path-traversal=reviewed; partial-write=reviewed; subprocess-and-network=reviewed; target-repository-write=reviewed; cap-exhaustion=reviewed; regeneration-clobber=not-applicable; confirmation-forgery=not-applicable; disposition-closure=not-applicable

Not checked: the step ships no runtime behaviour, so nothing was audited against a real inventory, workbook or disposition set; no proposal code exists, which is why the three concerns naming the generator's runtime are recorded as not applicable rather than reviewed; the Pashov pair did not run under the recorded security-suite waiver, since the step ships no Solidity; whether the drafted reason templates read well to a reviewer is a judgement no check here makes.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | plugins/dokimasia/schemas/dispositions-v1.json | The entry object required `reason` and `oracle` on every disposition. The reconciler treats both as optional, reading an absent value as the empty string through `entry.get`, and then refuses `manual` and `excluded` for carrying no reason, which is the stronger check because it also catches a reason that is present and blank. Requiring them here would have refused every set written before this run: probed against the committed `closed.json` fixture, which produced 30 findings, 15 of them for these two keys on entries the reconciler accepts. The schema would have failed closed on valid input the moment `propose` began emitting through it. Fixed by requiring `item`, `disposition` and `confirmed` only, and by stating in each field's description that the reconciler holds the stronger condition. | fixed in 63307fa1 |
| S1-R1-02 | low | plugins/dokimasia/docs/design/build_proposal_design_evidence.py | Every selection report records `command` as the bare generator path, and the generator's `--record` default pointed at `.hexaemeron/design-evidence.json`, the controller's own gitignored state directory. A reader running exactly the command the evidence names would therefore write a record somewhere other than the artefact the evidence describes, and would not reproduce the committed bytes. This is the other half of the previous run's S1-R1-01, which recorded a command path that did not resolve at all; a path that resolves and produces the wrong file is the same defect one step later. Fixed by defaulting to the committed record. Verified by running the bare recorded command and comparing digests before and after: both `a27b3d090ab1f6e3d50627d3b38509f64949fc70d693a778637354825b6afdff`. | fixed in 63307fa1 |

Leads not pursued: the committed disposition fixtures do not yet carry `confirmed`, so 15 findings remain when `closed.json` is validated against the new schema. This is ADR-002's required field arriving one step before the reconciler that reads it, and step 2's Files clause owns those fixtures; nothing validates an input set against this schema until `propose` emits one in step 3, so the gap is bounded to the interval between two steps of this run and is recorded here rather than closed by editing fixtures the next step is about to rewrite. The generator writes each report with a plain `write_bytes` rather than staging and renaming, so a killed run can leave a record whose digests do not match its reports; the design checker refuses exactly that state, so the failure is detected rather than silent, and adding a staged write to a build-time generator whose output is digest-bound buys nothing the checker does not already provide. The `--record` argument is operator-supplied and its parent is not walked for symlinks, which is the same reading the previous run accepted for `read_json` and is stated rather than repaired. The reason templates quote only fields the record holds and name no status, but nothing mechanically prevents a later template from quoting one; the rule is stated in `proposal-rules.md` and the enforcement, if it is ever worth having, belongs to the step that writes the templates.

## Step 1, round 2 -- 2026-09-01T21:12:05Z

Audit schema: fiat-audit-round/v2

Covered: proposal-covered-path=reviewed; emitted-set-unvalidated=reviewed; reason-overclaim=reviewed; evidence-digest-binding=reviewed; path-traversal=reviewed; partial-write=reviewed; subprocess-and-network=reviewed; target-repository-write=reviewed; cap-exhaustion=reviewed; regeneration-clobber=not-applicable; confirmation-forgery=not-applicable; disposition-closure=not-applicable

Not checked: the same negative space as round 1; the step still ships no runtime behaviour, no proposal code exists to audit, and the Pashov pair still did not run under the recorded security-suite waiver.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the four items from round 1 stand unchanged. Confirmed sound this round against the fixed tree, each with its output read rather than discarded: the three lints exit zero over the step's full changed path set; `run_checks --scope dokimasia` is green across all four checks; the amended step 1 exit command runs end to end at exit zero; the bare command every selection report names reproduces the committed record byte for byte; the committed synopsis matches a fresh render; the working tree is clean at the recorded head; and validating the committed `closed.json` against the new schema now yields 15 findings, all of them the absent `confirmed` field that ADR-002 requires and step 2 supplies, and none of them the `reason` or `oracle` keys round 1 removed from the required set.

## Step 2, round 1 -- 2026-09-01T21:26:36Z

Audit schema: fiat-audit-round/v2

Covered: disposition-closure=reviewed; confirmation-forgery=reviewed; emitted-set-unvalidated=reviewed; cap-exhaustion=reviewed; evidence-digest-binding=reviewed; path-traversal=reviewed; partial-write=reviewed; subprocess-and-network=reviewed; target-repository-write=reviewed; proposal-covered-path=not-applicable; regeneration-clobber=not-applicable; reason-overclaim=not-applicable

Not checked: no proposal code exists yet, so nothing was audited against a generated set and the three concerns naming the generator stay not applicable; whether a reviewer confirming an entry made the right judgement is outside what any of this establishes; the reconciler was exercised against the committed fixtures and the one pinned release, and nothing establishes it behaves correctly against a set some other tool writes; the Pashov pair did not run under the recorded security-suite waiver, since the step ships no Solidity.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/dokimasia/scripts/dokimasia_lib/reconcile.py | Splitting entries into a confirmed dict and an unconfirmed list turned the duplicate check into a dict lookup followed by a walk of that list, once per entry. The check was constant time before, and `MAX_DISPOSITIONS` admits 40,000 entries, so a set near the cap would have cost on the order of hundreds of millions of comparisons on a path that exists to refuse in one. The cap bounds the input and therefore bounds the damage, which is why this is recorded as medium rather than high, but a declared cap that is reachable and quadratic is a cap that stops bounding anything useful. Fixed by keeping every answered item in a set beside the two lists. Guarded by a test driving the duplicate across both lists, a confirmed entry against a drafted one for the same item and two drafts for one item, since splitting the entries is what opened the second path. | fixed in d8258e73 |

Leads not pursued: the committed pinned evidence was regenerated rather than migrated, from the application at its recorded `bb9685fb` commit and the workbook at its recorded `9da2f2e8` digest, both of which happened to be present on this machine; the inventory and workbook digests come back unchanged and the scoped and disposed figures are identical, so the two new fields and the digests binding them are the whole diff, and the byte-for-byte regeneration test passes with both inputs supplied. That test still skips in a checkout without them, which is unchanged and stated rather than repaired. The canonical digest covers the `unconfirmed` list, so a set whose confirmations move produces a different coverage digest even when every disposition is otherwise identical; that is the intended reading, since the confirmations are part of what was decided. `by_disposition` counts confirmed entries only, so a drafted `excluded` does not appear there; the `unconfirmed` list carries the drafted states instead, and nothing sums the two, which is deliberate because adding them would produce a figure that is neither drafted nor decided. The status and source vocabularies the workbook uses remain unpinned, as the previous run recorded three times; this step does not pin them and the proposal rules commit to reading a status only into drafted prose.

## Step 2, round 2 -- 2026-09-01T21:27:23Z

Audit schema: fiat-audit-round/v2

Covered: disposition-closure=reviewed; confirmation-forgery=reviewed; emitted-set-unvalidated=reviewed; cap-exhaustion=reviewed; evidence-digest-binding=reviewed; path-traversal=reviewed; partial-write=reviewed; subprocess-and-network=reviewed; target-repository-write=reviewed; proposal-covered-path=not-applicable; regeneration-clobber=not-applicable; reason-overclaim=not-applicable

Not checked: the same negative space as round 1; no proposal code exists, the reconciler was exercised against the committed fixtures and one pinned release only, whether a confirmation was the right judgement stays outside this, and the Pashov pair still did not run under the recorded security-suite waiver.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the items from round 1 stand unchanged. Confirmed sound this round against the fixed tree, each with its output read rather than discarded: the three lints exit zero over the step's 27 changed paths; `run_checks --scope dokimasia` is green; all five check verbs exit zero when invoked from the repository root; the suite passes 237/237 with both pinned inputs supplied and 237 with the regeneration test skipped; the committed synopsis matches a fresh render; and the working tree is clean at the recorded head. One apparent finding this round was the auditor's error rather than the code's: a sweep reported every check verb refusing, and the cause was running it from the plugin directory rather than the repository root, so the script path did not resolve. That is the same class of mistake the previous run recorded at step 5 round 5, arrived at by a different route, and it is written down here because a sweep that reports five refusals and is believed is worse than one that reports none.

## Step 3, round 1 -- 2026-09-01T21:44:35Z

Audit schema: fiat-audit-round/v2

Covered: proposal-covered-path=reviewed; regeneration-clobber=reviewed; confirmation-forgery=reviewed; reason-overclaim=reviewed; emitted-set-unvalidated=reviewed; partial-write=reviewed; path-traversal=reviewed; cap-exhaustion=reviewed; evidence-digest-binding=reviewed; disposition-closure=reviewed; subprocess-and-network=reviewed; target-repository-write=reviewed

Not checked: the generator was exercised against the committed fixtures and not against the pinned release, which step 4 owes; whether a drafted state is the right one for a given item, and whether a drafted reason reads well to a reviewer, are judgements no check here makes; nothing establishes that a reviewer will read a draft rather than confirming it wholesale, which is the risk the design accepts and ADR-002 states; the Pashov pair did not run under the recorded security-suite waiver, since the step ships no Solidity.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | plugins/dokimasia/scripts/dokimasia_lib/propose.py | Deciding whether a scoped item counted as replaced or added walked the existing disposition list once per scoped item. Both sides admit 40,000 entries under the declared cap, so a regeneration near it would have cost on the order of a billion comparisons on a path whose only output is three counters. This is the shape recorded as S2-R1-01 in the reconciler one step earlier, reintroduced in new code by the same reflex, which is why it is named rather than quietly corrected: the first one was a slip, and a second in the same run says the pattern needs stating. Fixed by deciding against the `seen` set the loop above already builds. | fixed in 04773842 |
| S3-R1-02 | low | plugins/dokimasia/scripts/dokimasia_lib/propose.py | `_reason_for` took a `case_fields` argument that its only caller passed empty and its body never read. A parameter shaped like a dependency that is not one costs a reader the same as a docstring describing work a helper does not do, which the previous run recorded as S4-R4-01; both invite a check that the code does not reward. Fixed by removing it. | fixed in 04773842 |

Leads not pursued: an entry's `proposed_sha256` is the reviewer's own file, so somebody who edits a reason and recomputes that digest by hand makes the entry read as untouched and lose the edit on the next regeneration. The cost falls on whoever did it and the field is documented as the generator's, so this is accepted rather than defended against; a tamper-evident version would need a key this skill deliberately does not hold. `entry_digest` excludes `confirmed`, so confirming an entry does not move its digest and the confirmation check runs first in `_touched`; that ordering is what makes a confirmed entry survive whether or not its text also changed. The regeneration counters are reported to stderr rather than recorded in the set, so a reviewer reading only the file cannot tell what the last run replaced; the runbook asks for the counts to be reported and the coverage record carries the three figures that matter for the ratio, so widening the set's own schema for run history is out of this step's scope. A drafted `excluded` reason states that no reviewed case cites the item, which is true of the workbook as imported and would stop being true if a later import changed; the reason is a draft a person is expected to correct, and the reconciler never reads it.

## Step 3, round 2 -- 2026-09-01T21:45:26Z

Audit schema: fiat-audit-round/v2

Covered: proposal-covered-path=reviewed; regeneration-clobber=reviewed; confirmation-forgery=reviewed; reason-overclaim=reviewed; emitted-set-unvalidated=reviewed; partial-write=reviewed; path-traversal=reviewed; cap-exhaustion=reviewed; evidence-digest-binding=reviewed; disposition-closure=reviewed; subprocess-and-network=reviewed; target-repository-write=reviewed

Not checked: the same negative space as round 1; the generator was exercised against the committed fixtures and not the pinned release, whether a drafted state or reason is right stays a human judgement, nothing establishes a reviewer will read a draft rather than confirm it wholesale, and the Pashov pair still did not run under the recorded security-suite waiver.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the items from round 1 stand unchanged. Confirmed sound this round against the fixed tree, each with its output read: the three lints exit zero over the step's five changed paths; `run_checks --scope dokimasia` is green; all six check verbs exit zero from the repository root; the suite passes 264/264 with both pinned inputs supplied; the committed synopsis matches a fresh render; and the working tree is clean at the recorded head. Four properties were driven rather than read and are recorded so a later round need not rediscover them: a label carrying a separator or a parent reference refuses with exit 2 and writes nothing outside the declared evidence root, checked against `/tmp` afterwards; the executable source of the proposal module carries no `covered` literal once docstrings and comments are stripped, and `DRAFTABLE` holds exactly the two draftable states; a real write followed by two hand edits and a regeneration preserved both edited entries byte for byte and replaced the other thirteen; and two drafts of the same records serialise identically.

## Step 4, round 1 -- 2026-09-01T23:00:51Z

Audit schema: fiat-audit-round/v2

Covered: disposition-closure=reviewed; proposal-covered-path=reviewed; confirmation-forgery=reviewed; regeneration-clobber=reviewed; evidence-digest-binding=reviewed; reason-overclaim=reviewed; emitted-set-unvalidated=reviewed; partial-write=reviewed; path-traversal=reviewed; cap-exhaustion=reviewed; subprocess-and-network=reviewed; target-repository-write=reviewed

Not checked: whether the 202 confirmations are correct judgements about wildcat-app-v2 is the reviewer's claim and nothing here establishes it; the 59 compiled items carry drafted exclusions nobody has decided on, so the record states they are undecided and not that they are out of scope; the 288ms class of timing observation remains one run on one machine; the scrutiny establishes what the declared rules recognised at one commit and nothing about the application's behaviour; the RS-40 router-selection regrade is still owed and needs an isolated context this session cannot open; the Pashov pair did not run under the recorded security-suite waiver, since the step ships no Solidity.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S4-R1-01 | medium | plugins/dokimasia/docs/evidence/wildcat-app-v2.dispositions.json | The committed set recorded `generated_by: 1.1.0`. The draft was written before the ledger moved, and version 1.1.0 has no `propose` verb, so the field named a version that could not have produced the file. Provenance that is merely stale reads the same as provenance that is wrong, and this is committed evidence a later comparison reads. Fixed by regenerating against the same two records, which also exercised the preservation rule against the real release rather than a fixture: 202 preserved, 59 replaced, 0 added, 0 dropped, every confirmed entry byte-identical and the ratio unchanged at 202 over 261. | fixed in 8758fafa |

Leads not pursued: the committed set carries workbook sheet names, row numbers and case identifiers such as `1 Admin:6, identifier ADM-01`. That is metadata about the reviewed workbook rather than its content, and the coverage record and scrutiny prose already commit the same identifiers, so this ships no more than the previous release did; the workbook's bytes remain uncommitted as the phylax boundary requires. The 202 confirmations were applied mechanically under a rule a person stated rather than entry by entry, and the record cannot distinguish the two, which is exactly the gap the next frontier job names and the reason this run halted to ask rather than deciding on its own. `generated_by` is an operator-supplied provenance field with no signature behind it, so it records what the writing process claimed and not what a reader can verify; making it checkable needs a key this skill deliberately does not hold. The step's receipted exit named `run_checks --full`, which cannot pass from this branch because `tabularium-suite` fails on the base commit over the `VENUES.json` ownership question pull request #1094 raised; the amendment replaces it with the scope-selected form and the failure is carried into the integration pull request rather than fixed here, because moving that file is a reviewer's decision about another plugin.
