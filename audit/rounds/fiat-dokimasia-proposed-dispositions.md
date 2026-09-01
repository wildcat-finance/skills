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
