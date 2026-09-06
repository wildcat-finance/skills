# Decision: Derive topology counts from the tree

## Status

Accepted, 2026-09-06.

## Context

Public prose repeatedly carried plugin and skill counts that a person typed
once and nobody updated. The failure is not carelessness; it is that a number
written into prose has no owner, and the person landing the change that makes
it wrong has no way to find it.

Commit `67a01a6c` is the worked example. It landed the eighteenth plugin and
did the maintenance honestly: it moved `README.md` and
`.agents/skills/promise-machine/SKILL.md` from twenty-five members and sixteen
domain agents to twenty-six and seventeen. It missed `SHOGGOTH.md`, which went
on saying "The current roster has 25 members: 16 domain agents and 9 phase
agents" while the tree held twenty-six. Every check in the repository was
green. Nothing in that commit was wrong except that a fourth place existed and
the author did not know it.

The same shape had already produced two other stale claims that this delivery
found: a member described by the version it shipped three releases earlier, and
a capability described as not yet built after the release that built it. In
each case the sentence was true when written and nothing was watching the
thing underneath it move.

The tree can answer these questions. Both marketplace manifests declare a
plugin set, and walking `plugins/<id>/skills/<skill>/EVOLUTION.md` derives one
independently. A count that all three agree on is checkable; a count typed into
a paragraph is not.

## Decision

No shipped first-party document states a topology count as a literal. Every
current count claim carries a `front-door:count` marker naming the derived
quantity it asserts, and `scripts/check_public_front_door.py` compares the
number with what `scripts/shoggoth_topology.py` derives from both manifests and
tree discovery together.

The derivation refuses rather than guesses. A duplicate id, a disagreement
between the two manifests, a manifest and tree that derive different plugin
sets, a governed directory with no regular `SKILL.md`, a symlinked entry, and a
phase skill outside the phase host each raise a refusal with a stable code, so
a passing count rests on all three sources agreeing rather than on one of them
being read.

The rule is symmetrical, and that half is what makes it hold. A number in front
of a topology noun with no marker in front of it is itself a refusal, because
an unmarked literal is exactly how the stale numbers got in. The checker holds
no count of its own to compare against.

Two exemptions exist, and each is named rather than granted by whoever writes
the marker.

**A dated measurement.** A figure describing what happened on a named capture
is evidence, not a claim about now, so it must not be rewritten to agree with
today's tree. A `front-door:historical` marker pins the numeral and names a
`YYYY-MM-DD` date the page itself records in prose. It is admitted only on a
page the checker names as carrying a dated capture; anywhere else the marker is
a refusal and the number under it stays an ordinary count claim.

**A pinned specimen.** A test specimen declares its own counts as literals, and
that is correct. A specimen plants a synthetic tree with arbitrary identities
and asserts what the reader derives from it, so its numbers describe that tree
and are measurement input rather than a public claim. The boundary is that no
assertion compares a specimen identity set or count with a live one: the
predecessor run froze `specimen.plugin_ids == live.plugin_ids` and the next
plugin to land broke a test that had nothing to do with it.

## Alternatives

- **Keep the literals and add a checklist to the contribution guide.** Rejected
  for the reason `67a01a6c` demonstrates: the author was following the
  convention and still missed a place. A checklist scales with the number of
  documents somebody remembers.
- **Delete the counts from public prose.** It removes the failure completely.
  Rejected because the numbers are the answer to the first question a reader
  asks, and a page that will not say how large the collective is has traded a
  maintenance problem for a worse page.
- **Generate the count sentences from the ledgers at build time.** Rejected
  because it puts generated prose on the front door and needs a build step
  before anybody can read the repository. The marker achieves the same
  guarantee by checking rather than by writing, and the sentence stays the
  author's.
- **Compare only the numbers somebody marked.** This was the first form of the
  rule and it is the one that fails silently: an author who does not know the
  marker exists writes a bare literal, no rule reads it, and the count ages in
  public exactly as before. Requiring a marker on every count claim is what
  turns an aid into a contract.

## Consequences

Adding or removing a plugin or a governed skill moves every published count at
once, and the author edits no document to make that happen. A landing page for
the new member joins the swept set from discovery, so forgetting to write one
is a refusal rather than a silence.

Authors have a new obligation. A sentence with a number and a topology noun in
it now needs a marker or a rewording, including sentences that assert nothing
about the tree; the checker reads two words between the number and the noun and
will catch some prose that was never a claim. That direction is deliberate: a
sentence caught by mistake is reworded, and a sentence missed is a number that
ages in public.

The two exemptions are the weak points, and they are stated rather than
implied. A historical marker takes a figure out of derivation permanently, so
the pages that may carry one are named in the checker; a specimen's literals
are unchecked against anything, so the specimen must never be compared with the
live tree.

What this does not establish: that a count is meaningful, that the tree is the
right thing to count, or that a marked sentence is about the quantity its
marker names beyond the noun the checker requires it to carry.
