# ADR-076: Generate the harness roster from one probed manifest

## Status

Accepted, 2026-09-04. Taken in the Fiat run for issue
[#856](https://github.com/wildcat-finance/skills/issues/856), whose study and
runbook are at [docs/atlas-harness-handoff/](../atlas-harness-handoff/study.md).
The design record that selected the construction is
`protasis-design-evidence/v1` at sha256
`dc945d47bd56ee1ef71051fb86fd93d8a63242806bf9a8a41d1bbc5d193552fe`, candidate
`probe-manifest`.

## Context

Three surfaces state which agent harnesses can pick up a Wildcat job and how:
the badge block in `README.md`, the harness table in
`docs/how-to-help-shoggoth.md`, and the harness page the PDF builder emits from
`scripts/build_contributor_guide.py`. All three are written and edited by hand.
Nothing holds them in agreement with each other, and nothing holds any of them
to a run that actually happened. A contributor who reads that a harness is
tested has no way to tell whether anyone ever tested it.

Issue #856 asks for the remaining hand-offs to be tested before more launch
buttons are added to the README. Probing this host answered that question in a
way the issue did not anticipate: not one of the six clients is installed here,
and not one is authenticated. Copilot has no seat and an unconfigured
organisation policy; Cursor, Gemini CLI and Cline are absent from `PATH` and
unauthenticated; Windsurf is absent and is now published as Cascade inside Devin
Desktop; Roo Code is sunset and archived. The `~/.cursor`, `~/.gemini` and
`~/.copilot` directories that do exist are residue of an earlier probe and hold
no client and no credential.

That turns the deliverable from six test results into a record that can carry
five named blockers honestly, and machinery that keeps carrying them. Three
constructions were drawn for it and graded against checked gates. `hand-record`
failed `credential-free`, because completing it needs six authenticated client
runs this host cannot perform. `contract-manifest` failed
`per-harness-evidence`, because reading published client contracts never
observes client presence, version or authentication state.

Two of the decisions below are expensive to reverse once public prose is
generated from them, which is why they are here rather than only in the study.
The third resolves a direct conflict between the issue's own wording and a live
test, and a later reader who does not know it was decided will reopen it.

## Decision

**One schema, one manifest, one generator.** The roster's single source is
`docs/harness-classification.json`, validated by
[`schemas/harness-classification-v1.json`](../../schemas/harness-classification-v1.json)
under the identifier `harness-classification/v1`. A manifest carries a
`recorded` block naming the host, the date and the base ref it was written
against, and a `harnesses` array. Each harness entry carries `name`,
`classification`, the five observation fields `client_present`,
`client_version`, `auth_configured`, `launcher_contract` and `blocker`, and the
derived field `version_read`. Exactly two fields are optional, `testable_here`
and `probe`; every other field named here is required. Objects are closed: an
undeclared field is refused rather than ignored. `client_version` may be null
only where `client_present` is false, so an absent client cannot be recorded as
a version nobody read.

`client_present` and `auth_configured` are separate fields on purpose. A client
that is missing and a client that is installed but unauthenticated are different
facts, and a single verdict field would collapse them into one.

**A present client that did not answer is fielded, not spelled.** Such a client
is present with its version unread, so `client_present` stays true and
`client_version` carries the sentinel `unread`. A sentinel is prose where a
reader wants a field, so `version_read` carries the same fact as a boolean and
is required: false both where no client was present and where a present client
did not answer, true only where `client_version` holds a version a client
reported. Nothing downstream may recognise the sentinel to tell a version from
the absence of one, and the schema refuses a document whose two fields
disagree. `version_read` is required rather than optional for the reason the
closed object exists: a field a conforming producer may omit is one a consumer
cannot rely on, which leaves it string-matching the sentinel after all.

`testable_here` stays optional, and is `client_present` and `auth_configured`
together rather than a claim that a run succeeded: a present client that never
answered is `testable_here` with `version_read` false. Read `classification`
for what the run earned.

**Four classification names, and no fifth.** A harness is exactly one of
`Atlas launcher`, `tested local route`, `manual route` or `unsupported`. The
first two are earned classes and require a recorded client run; the schema
declares the four as a closed enumeration so an unknown name is refused rather
than published. These four names become the vocabulary of the roster, the tests
and every later harness discussion, so renaming one rewrites text readers have
already seen.

**Acceptance condition 2 means "preserve `job.prompt` byte for byte".** The
condition asks the hand-off to retain a list of items including "the link to PR
#479". That link was removed from the contributor prose by commit `daa64e5f`,
and `tests/test_marketplace_prose.py` lines 331 and 332 now assert that
`pull/479` and `PR #479` are absent from both `README.md` and
`docs/how-to-help-shoggoth.md`. The issue and the suite cannot both be satisfied
literally. The reading taken is that condition 2 requires the launcher to
preserve `job.prompt` byte for byte, and that its enumerated items are checked
against the prompt's current content rather than against the August wording. The
current prompt carries the issue number and the checkpoint sentence and carries
no reference to pull request 479, so the condition is met and the two test lines
stand unchanged.

Which harness got which class in this run is deliberately not recorded here. It
belongs in the manifest, where it is regenerated from observation, not in a
decision record that would freeze it.

## Alternatives

- **`hand-record`: write the test record by hand and edit the three surfaces to
  agree.** The cheapest start and the only construction needing no new code.
  Rejected on `credential-free`: it can only be completed by someone able to run
  all six clients, and it gives away every guarantee that the surfaces still
  agree a month later.
- **`contract-manifest`: one hand-maintained manifest read from the published
  client contracts, with no machine probe.** Keeps the single source and the
  generated surfaces, and is simpler than a probe. Rejected on
  `per-harness-evidence`: it never looks at the host, so it cannot record a
  client version or an authentication state, and cannot satisfy acceptance
  condition 1.
- **Leave the three surfaces hand-edited and add a review checklist.** No new
  code and no schema. Rejected because a checklist is not a check: the drift
  this record exists to stop is exactly what review has already missed.
- **A free-form classification string instead of a closed enumeration.**
  Flexible, and no schema change when a new kind of hand-off appears. Rejected
  because it admits `tested`, `Tested`, `Atlas Launcher` and anything else a
  future writer reaches for, and the earned-class rule then has nothing to bind
  to.
- **Read acceptance condition 2 literally and restore the PR #479 link.**
  Follows the issue's words. Rejected because it requires deleting or weakening
  two passing assertions to satisfy a clause that a later, deliberate change
  already superseded.
- **Ask the issue author to amend condition 2 and wait.** Cleanest on paper.
  Rejected as a blocker: the reading costs nothing to reverse in prose, and this
  record makes it visible to whoever wants to argue with it.

## Consequences

The roster gains a build step and a schema. Publishing a harness change now
means running the probe and regenerating three surfaces, rather than editing
whichever one the writer was looking at. That is the cost bought deliberately:
a roster that cannot outrun its evidence.

Field names in `harness-classification/v1` are now read by the schema, the
manifest, the renderer, three wording surfaces and the suite. Renaming one is a
change to all seven at once, and needs a successor record rather than an edit.

Five harnesses ship classified `manual route` or `unsupported` with a named
blocker rather than as untested blanks. A reader learns what was tried and why
it stopped, and any of the five can move to an earned class later by a probe run
on a host that has the client, with no prose edit.

The acceptance-condition-2 reading is recorded with the test lines it conflicts
with. If a later reader decides the PR #479 clause should be honoured after all,
the change is to those two assertions and to this record, in that order, and not
a silent edit to either.

## Numbering, and one stale pointer this leaves behind

This record was written as ADR-074, which was free when the run checked. Pull
request 1181 merged `ADR-074-shape-every-written-record-through-sapheneia.md`
into `main` fifty-five minutes later, at 2026-09-04T01:40:30Z against this
record's own commit at 00:45:16Z. `tests/test_decision_records.py`
compares numbers against the default branch, so the collision turned the step's
own exit gate red. ADR-075 was already claimed by open pull request 1185, so
this record took 076. Issue 888 is rebuilding ADR numbering to assign at merge
instead of at authoring, which is the general answer to the race; renumbering
here is the local one.

One pointer did not survive the renumber. Between the two events the run's study
gained a `hypomnema-design-bridge/v1` block naming
`docs/decisions/ADR-074-generate-the-harness-roster-from-one-probed-manifest.md`.
Study amendments are append-only, and Hypomnema refuses a study that declares
more than one design bridge home, so the block cannot be repointed and cannot be
removed. The study at `docs/atlas-harness-handoff/study.md` therefore names a
file that does not exist, and `hypomnema --study` reports H008 against it. The
repository suite exercises study mode only against its own fixtures and never
against this study, so nothing here goes red on it.

The decision the bridge was meant to reach is this file. Anyone following that
block should read it here.
