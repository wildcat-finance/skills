#!/usr/bin/env python3
"""Check the maintained public surface against the front-door contract.

The root README kept drifting because nothing could tell a reader it was
wrong. Its counts were typed once and aged; its capability claims outran what
the repository could actually demonstrate; the invitation to contribute sat
below three hundred lines of catalogue. This module settles the mechanical
part of that contract: order, budgets, markers, and agreement between a public
claim and the evidence behind it.

The same drift lives on every other maintained page, so the sweep covers a
named set rather than one file. The set is partly fixed and partly derived:
the root and `docs/` pages are named here, and one landing `README.md` per
discovered plugin comes from the topology reader, because a hand-typed list of
eighteen would go stale the day a nineteenth plugin lands. A named document
that is absent is a refusal and never a skip.

Each document carries the rules that apply to it. `README.md` alone carries
the front-door rules, since order, budgets and demonstration cards are
questions about a front door. Every maintained page carries the heading,
count and member-status rules. Two do not carry the heading rule:
`PROMISE_MACHINE.md`, whose section headings and promise ids `promise_machine`
pins by exact bytes, and `.agents/skills/promise-machine/SKILL.md`, which is a
normative agent contract. Restyling either would churn an operational contract
to satisfy a house style, which the study that ordered this sweep refuses.

Five kinds of rule run here.

**Structure.** The collective portrait precedes the title, the introduction
stays inside its word budget, the contribution heading and the external
contributor route begin inside the opening word boundary, the whole file stays
inside its budget, no link target appears twice, the only image is the
collective portrait, and the retained chirp plus one further
marked aside appear before the first technical section. The first Promise
Machine contract link and the first catalogue link follow both the contribution
and the demonstration sections, and the complete governed roster is not
inlined: the front door points at the catalogue rather than becoming one.

**Cards.** Each `front-door:demo` marker binds a skill id, a claim id and a
demonstration-record digest. The bound record must exist, must still be
`real-data`, and must still hash to the bound digest, and the marked cards must
be exactly the real-data records the tree holds. A card must display one
runnable command, one named preserved source, one concrete observed result and
the record's own non-claim. A marker with no record fails; a record with no
marker fails. Absence never passes.

**Counts.** Every current count claim carries a `front-door:count` marker
naming the derived quantity it asserts, and the number is compared with what
`shoggoth_topology` derives from both marketplace manifests and tree discovery
together. A number in front of a topology noun with no marker in front of it is
itself a refusal, because that is exactly how the stale literals got in. This
module holds no count of its own to compare against. A marker that begins its
line with prose after it on the same line is refused too: CommonMark reads a
line that opens with an HTML comment as an HTML block, which ends the paragraph
and renders that prose as a detached line. The front door shipped three of them.

**History.** A figure describing a dated measurement is not a claim about now,
so it is not derivable and must not be rewritten to agree with today's tree.
`INSTALL.md` records what two host installs did on one dated capture, and
those figures are evidence. A `front-door:historical` marker names the capture
and pins the figure's numeral, so the claim satisfies the marking rule
without ever being compared with the tree, and rewriting the figure fails
because the prose no longer says what the marker pinned. The two markers do
opposite jobs on purpose: a count marker binds a number to something recomputed
every run, and a historical marker binds one to something that already
happened.

That second job is an exemption, so the pages that may carry it are named here
rather than decided by whoever writes the marker. Only a page carrying the
history rule has a dated measurement to exempt; anywhere else the marker is a
refusal and the number under it stays an ordinary count claim. Naming the page
was not enough on its own: `captured` was free text, so a marker could exempt
any number on that page while naming no date, and the date it did name was
readable only in the source. It must now be a `YYYY-MM-DD` date that the page
itself records in prose, which is what a dated capture means. The marker still
pins the numeral and not the noun beside it, so it establishes that the figure
was not brought up to date and nothing about what the figure counts.

**Member status.** A sentence saying what a member's current version does or
does not do is a claim about that member's ledger. It carries a
`front-door:status` marker naming the skill and the exact `EVOLUTION.md`
version it was written against, and the claim is refused once that ledger moves
on. This is how "the version implements source admission" outlived three
anamnesis releases and "its compile path has not shipped" outlived the dokimasia
release that shipped it: both sentences were true when written, and nothing was
watching the ledger move underneath them.

On a plugin landing page the marker must also name that page's entry skill, or
a member it ships that the marked prose itself names. Shipping the skill was
too weak alone: the phase host ships ten, so any of ten ledgers vouched for any
claim on its page and the slowest-moving one held a stale sentence current
indefinitely. The marker must also agree with any release its own prose names,
because a sentence written about a superseded version passed under a marker
that was current.

Three gaps remain and are stated rather than implied. On the named pages, which
belong to no plugin, nothing narrows the marker at all. On a landing page a
sentence about another member still passes under the entry skill's marker when
it names no version. And a subject carried by a pronoun is not read: the marked
region is a paragraph, not a parse. Requiring the region to name its own skill
was measured against this tree and refused two claims that are correct --
`plugins/probitas/README.md` says "This version emits none" on probitas's own
page -- so the join is bounded rather than asserted. What a marked claim
establishes is that the named ledger stands at the declared version, not that
the sentence is about it.

Each ledger is read the first time a claim binds to it, and never before. The
sweep once resolved every governed ledger's version before it opened a page,
so one `EVOLUTION.md` with no `- Current version:` row ended the whole run at
exit 2 with no findings list, while an absent maintained page was one `FD01`
beside every other page reporting normally. A ledger that cannot be read, or
that reads cleanly and declares no current version row, is now `FD39` against
each claim that needed it, the rest of the sweep reports as it would have, and
a ledger no claim binds is never opened.

What it does not do: it never grades free-form voice, which belongs to
Imprimatur, Vulgate, Brevitas and human review. It does not decide whether a
member-status sentence is true, only whether it still describes the version its
own marker names. It reads the repository's own Markdown, ledgers and
demonstration records as bounded regular files through no-follow descriptors,
starts no subprocess, opens no socket, and writes nothing. It imports the
record-reading half of `demonstrations` and never its runner.

Word counts are taken over the rendered text: every HTML comment is blanked to
spaces of the same length before counting, so a marker costs a reader nothing
and character offsets stay aligned with the source bytes.

Headings are read from a second view with fenced code blanked the same way. A
line beginning with `#` inside a fence is a shell comment, not a section, and a
section heading quoted inside a fence is an example rather than the heading it
imitates. Everything else still reads the fence, because the `COMMAND_RE` a
card must display sits inside one.

Exit 0 when the contract holds, 1 when a rule reports, 2 when the topology or
the demonstration records cannot be read at all.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import demonstrations  # noqa: E402
from shoggoth_topology import (  # noqa: E402
    TopologyError,
    read as discover_topology,
)


FRONT_DOOR = "README.md"
MAX_DOCUMENT_BYTES = 262_144
LEDGER_NAME = "EVOLUTION.md"
PLUGIN_LANDING = "README.md"

# The rule groups a maintained document can carry.
FRONT_DOOR_RULE = "front-door"
HEADING_RULE = "headings"
COUNT_RULE = "counts"
STATUS_RULE = "status"
# The one page that records a dated measurement. A historical marker exempts a
# figure from derivation, so the pages that may carry one are named here rather
# than left to whoever writes the marker: a rule every page can grant itself is
# not a rule, and the count rules exist precisely to stop a literal being
# published unchecked.
HISTORY_RULE = "history"
HISTORY_HOME = "INSTALL.md"

# A public entry page a reader starts from. Everything the house style governs
# applies to it.
ENTRY_RULES = frozenset({HEADING_RULE, COUNT_RULE, STATUS_RULE})
# A normative contract read for its claims rather than restyled. Its headings
# are identifiers another checker pins by exact bytes, so a case rule here
# would break `promise_machine.py` rather than improve anything a reader sees.
CONTRACT_RULES = frozenset({COUNT_RULE, STATUS_RULE})


@dataclass(frozen=True)
class Maintained:
    """One swept document and the rule groups that apply to it."""

    relative: str
    rules: frozenset[str]

    def carries(self, rule: str) -> bool:
        return rule in self.rules


# The named documents this checker sweeps. A document in this tuple that is
# absent is a refusal, never a skip: a sweep that reads whatever it finds
# reports nothing when `SHOGGOTH.md` is gone, and a reader cannot tell that
# result from a clean one. One landing page per discovered
# plugin joins them in `maintained_documents`, because a hand-typed list of
# eighteen is exactly the literal this whole contract exists to remove.
MAINTAINED_DOCUMENTS = (
    Maintained(FRONT_DOOR, ENTRY_RULES | {FRONT_DOOR_RULE}),
    Maintained(HISTORY_HOME, ENTRY_RULES | {HISTORY_RULE}),
    Maintained("FUTUREPROOFING.md", ENTRY_RULES),
    Maintained("SHOGGOTH.md", ENTRY_RULES),
    Maintained("PROMISE_MACHINE.md", CONTRACT_RULES),
    Maintained("docs/how-to-help-shoggoth.md", ENTRY_RULES),
    Maintained("docs/fiat-in-plain-english.md", ENTRY_RULES),
    Maintained("docs/the-promise-machine-explained-properly.md", ENTRY_RULES),
    Maintained(".agents/skills/promise-machine/SKILL.md", CONTRACT_RULES),
)

# Budgets. Each is a contract limit measured by this checker rather than a
# performance claim, so they live here beside the rule that reads them.
INTRODUCTION_WORDS = 150
CONTRIBUTION_WORDS = 220
DOCUMENT_WORDS = 1_400
ASIDE_WORDS = 20

PORTRAIT = "./assets/characters/shoggoth.png"
TITLE_PREFIX = "# "
CONTRIBUTION_HEADING = "## SO, YOU WANT TO BUILD GOD?"
DEMONSTRATION_HEADING = "## WHAT CAN IT DO?"
CONTRIBUTOR_ROUTE = "./docs/how-to-help-shoggoth.md"
PROMISE_MACHINE_LINK = "./PROMISE_MACHINE.md"
CATALOGUE_LINK = "./FUTUREPROOFING.md"
CHIRP = "Ask the Atlas for a number. Pick your harness. Finish what you start."

# `scripts/contributors.py` owns the bytes between these markers and rewrites
# them from public history on a schedule, including its own `## Thanks`
# heading. Holding generated bytes to the house heading style would fail on the
# next regeneration rather than on anything an author did, so the region is
# named and excluded here instead of being silently tolerated.
#
# An exclusion an author can widen is not an exclusion. The region must be
# closed, must carry exactly one pair of markers, and may cover no heading
# other than the one the generator itself writes, which is the third entry
# here. Naming only a few protected headings left every other one exemptible,
# and a second opening marker widened the span the first one opened.
#
# `marketplace-context` is the landing-page arrangement, and it is not the same
# kind of region. Nothing under `scripts/` writes its bytes:
# `tests/test_marketplace_prose.py` holds every copy of a plugin's block to one
# `**Current frontier.**` line, which is presence and agreement rather than
# derivation. So an author writes this prose, and a region that exempted every
# claim inside it handed 18 landing pages the author-granted exclusion the
# paragraph above refuses -- a count or a status sentence typed between the two
# markers was read by no rule at all.
#
# Each region therefore declares what it may exempt, rather than exempting
# everything by being a region. The generator writes the `contributors` heading
# and its prose, so an author cannot mark a claim there and the next
# regeneration would delete one: that region exempts all three rules. The
# marketplace owns only the heading of `marketplace-context`, so that region
# exempts the heading rule alone, and a count or status claim inside it is
# exempt only when the skill's own `EVOLUTION.md` carries the sentence holding
# it. That is the derivation the earlier comment claimed and did not have: the
# ledger is the source these blocks quote, and a sentence the ledger does not
# carry is the author's own claim wherever it was typed.
#
# Each region also names where its generator writes. Without that, two comment
# markers around any prose on any swept page exempted every count and status
# claim between them. A region declared away from its own page is refused and
# not applied.
FRONT_DOOR_HOST = "the root front door"
LANDING_HOST = "a plugin landing page"


@dataclass(frozen=True)
class Generated:
    """One region another owner writes, and exactly what it may exempt."""

    opening: str
    closing: str
    owned: str
    host: str
    exempts: frozenset[str]
    ledger_backed: bool


GENERATED_REGIONS = (
    Generated(
        "<!-- contributors:start -->",
        "<!-- contributors:end -->",
        "## Thanks",
        FRONT_DOOR_HOST,
        frozenset({HEADING_RULE, COUNT_RULE, STATUS_RULE}),
        False,
    ),
    Generated(
        "<!-- marketplace-context:start -->",
        "<!-- marketplace-context:end -->",
        "## In one line",
        LANDING_HOST,
        frozenset({HEADING_RULE}),
        True,
    ),
)

# Which derived quantity each count key names. The values come from the
# topology reader, which already refuses when the two manifests and the tree
# disagree, so a passing count claim rests on all three agreeing.
COUNT_KEYS = {
    "plugins": "plugins",
    "governed": "governed",
    "members": "governed",
    "domain": "canonical",
    "phase": "phase",
}

# The word a claim must carry for the key its marker names. A marker binds a
# number to a derived quantity; without this the number can be right for the
# key and wrong for the sentence, so `key="plugins"` over "18 governed skills"
# would pass while telling a reader the governed count is the plugin count.
COUNT_NOUNS = {
    "plugins": "plugin",
    "governed": "governed",
    "members": "member",
    "domain": "domain",
    "phase": "phase",
}

# Source classes that carry preserved evidence. A card must name one of these,
# and never the program that reads them.
PRESERVED_CLASSES = frozenset(demonstrations.PRESERVED_CLASSES)
PROGRAM_SOURCE_ID = "program"

MARKER_RE = re.compile(
    r"<!--\s*front-door:(?P<kind>[a-z-]+)(?P<rest>[^>]*?)\s*-->"
)
ATTRIBUTE_RE = re.compile(r'(?P<name>[a-z-]+)="(?P<value>[^"<>]*)"')
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
# A fence runs from its opening row to the next row opening with the same
# marker, or to the end of the document when it is never closed. The closing
# row is part of the match so that scanning resumes after it: leaving it
# unconsumed makes the next fence's opening row the previous one's closing row,
# which masks the prose between two fences and unmasks the fences themselves.
# Either delimiter may carry up to three leading spaces, as the renderer
# allows. Requiring column zero produced that same inverted mask from an
# indented closing row, and refused a heading inside an indented block.
FENCE_RE = re.compile(
    r"(?ms)^(?P<open>[ ]{0,3}(?P<mark>`{3,}|~{3,})[^\n]*\n)"
    r"(?P<body>.*?)"
    r"(?P<close>^[ ]{0,3}(?P=mark)[^\n]*(?:\n|\Z)|\Z)"
)
HEADING_RE = re.compile(r"(?m)^(?P<hashes>#{1,6})\s+(?P<text>.+?)\s*$")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\((?P<target>[^)\s]+)[^)]*\)")
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\((?P<target>[^)\s]+)[^)]*\)")
HTML_HREF_RE = re.compile(
    r"""<a\s[^>]*?href\s*=\s*"""
    r"""(?:(?P<q>["'])(?P<quoted>[^"']+)(?P=q)|(?P<bare>[^\s"'>]+))""",
    re.IGNORECASE,
)
HTML_IMAGE_RE = re.compile(
    r"""<img\s[^>]*?src\s*=\s*"""
    r"""(?:(?P<q>["'])(?P<quoted>[^"']+)(?P=q)|(?P<bare>[^\s"'>]+))""",
    re.IGNORECASE,
)
# Reference style. A definition names a target once and every use points at the
# label, so a checker that reads only inline targets sees neither the second
# route nor the second image.
REFERENCE_DEFINITION_RE = re.compile(
    r"""(?m)^[ ]{0,3}\[(?P<label>[^\]^][^\]]*)\]:[ \t]*<?(?P<target>[^\s<>]+)>?"""
)
REFERENCE_USE_RE = re.compile(
    r"(?P<bang>!?)\[(?P<text>[^\]]*)\]\[(?P<label>[^\]]*)\]"
)
# The shortcut form carries no second bracket pair at all: `![alt]` and `[text]`
# resolve through a definition of that same name. It renders exactly as the
# other two do, so a reader sees the image or the route either way.
REFERENCE_SHORTCUT_RE = re.compile(r"(?P<bang>!?)\[(?P<label>[^\]\[]+)\](?![\[(:])")
# The command a card displays, wherever it is displayed. A fenced block is one
# a reader can copy and a code span is one they can read mid-sentence, and both
# are the same command: the delimiter is presentation, so the rule is about the
# command and the record it names.
COMMAND_RE = re.compile(
    r"python3 scripts/demonstrations\.py run"
    r" --record (?P<directory>[^`\s]+)"
    r" --report (?P<report>[^`\s]+)"
)
# Numbers a reader counts as numbers. Digits were the whole grammar once, and
# a claim spelled out escaped every rule: "thirty governed skills" asserted a
# derived quantity and nothing checked it. The table stops at ninety-nine
# because a front door that needs three digits in words has a larger problem.
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90,
}
NUMBER_WORD_RE = "|".join(sorted(NUMBER_WORDS, key=len, reverse=True))
# `one` parses as a number and is almost never used as one. English reaches for
# it as a determiner -- "one skill can have separate operations", "install one
# or more named plugins" -- and no population this checker derives has ever
# been one. Demanding a marker on every such sentence would put derivation
# markers over prose that asserts nothing about the tree, which teaches authors
# that the marker means nothing. The digit is still read, so "there is 1 domain
# here" remains a refusal and the spelled form of a real claim, from two
# upwards, is still caught.
CLAIM_WORD_RE = "|".join(
    sorted((word for word in NUMBER_WORDS if word != "one"), key=len, reverse=True)
)
# The case-insensitive flag is not decoration. Every ATX heading on this page
# must be all caps, so a case-sensitive lower-case grammar could never read a
# count claim inside one: the two rules together exempted every heading.
#
# The words between the number and the noun are free text rather than a closed
# list. A list can only hold the adjectives somebody thought of, and "42
# assorted plugins" was one word away from being a stale literal nothing read.
# Reading too much is the safe direction here: a sentence caught by mistake is
# reworded or marked, and a sentence missed is a number that ages in public.
# The lookbehind is what a version and a path cost. `Compound v3 Phase 0` and
# `plugins/lazarus` after a `v3` both put a digit in front of a topology noun
# without asserting anything, and a dotted release like `0.1.1 while the skill`
# does it again. Requiring the number to open a token leaves every real claim
# and drops all three.
#
# Two intervening words, not three. Three reaches across a verb into the next
# noun phrase: "the four workers isolate bulky phases" is a claim about
# workers, and reading it as a claim about phases reports a number nobody
# wrote. Two still covers every adjective stack the maintained set uses,
# including "25 governed first-party skills" and "42 assorted plugins".
COUNT_CLAIM_RE = re.compile(
    r"(?<![A-Za-z0-9.])"
    r"(?P<number>\d[\d,]*|(?:" + CLAIM_WORD_RE + r")(?:-(?:" + CLAIM_WORD_RE + r"))?)\s+"
    r"(?:[A-Za-z][A-Za-z-]*\s+){0,2}"
    r"(?:plugins?|skills?|members?|agents?|domains?|phases?)\b",
    re.IGNORECASE,
)
# A sentence about what one member's current version does or does not do. Both
# halves matter: the positive form goes stale the same way the negative one
# does, and the anamnesis page proved it by saying what v0.1.0 implemented for
# three releases after v3.1.0 shipped the rest.
#
# `yet` and the apostrophe are the two spellings the first grammar split on.
# "has not yet shipped" was read and "is not yet implemented" was not, because
# only one branch carried the optional word; and this repository's own voice
# mask calls contractions normal, so "hasn't shipped" was the phrasing the
# house style encourages and the rule could not see. Both are closed here
# rather than left as spellings a sentence can be rewritten into.
#
# Four families were silent because the grammar spelled one form of each and
# stopped. The predicates stay the four this rule has always named -- ship,
# implement, build, land -- and only the grammar around them widens, because a
# predicate list is open vocabulary and a conjugation is not.
#
# `been` is the passive perfect of a branch that already exists, so
# "has not shipped" was read and "has not been shipped" was not. `never` is the
# same negation as `not`, so "has never shipped" was silent. `was`, `were` and
# `had` are the past of `is`, `are` and `has`, and `remains` is the copula this
# repository's own landing pages actually use: `remain unimplemented` sat
# unmarked and unread on a maintained page while this rule was green. The
# adverb slot held exactly one word, `yet`, so "is not currently implemented"
# and "has not so far shipped" escaped a rule that reads "is not yet
# implemented"; it is now a closed list rather than one literal. The `un-`
# forms negate the same two participles morphologically.
#
# What stays out, and why. "is not available", "is still to come" and "is
# planned, not present" are different predicates, and guessing the predicate
# set is how a rule starts firing on ordinary prose across 27 documents. "No
# compile path has shipped" and "nothing has shipped" move the negation onto
# the subject, which needs a noun phrase read backwards rather than a
# conjugation. Both are recorded rather than closed.
NOT_RE = r"(?:n(?:'|’)t| not| never)"
# One adverb between the negation and the participle, from a closed list.
ADVERB_RE = r"(?:(?:yet|still|currently|as yet|so far|ever) )?"
PARTICIPLE_RE = r"(?:shipped|landed|implemented|built)"
COPULA_RE = r"(?:is|are|was|were|remains?)"
STATUS_CLAIM_RE = re.compile(
    r"(?i)(?:this version"
    r"|ha(?:s|ve|d)" + NOT_RE + r" " + ADVERB_RE + r"(?:been )?" + ADVERB_RE
    + PARTICIPLE_RE
    + r"|ha(?:s|ve|d) yet to ship"
    r"|do(?:es|)" + NOT_RE + r" " + ADVERB_RE + r"ship"
    r"|" + COPULA_RE + NOT_RE + r" " + ADVERB_RE + r"(?:been )?" + ADVERB_RE
    + PARTICIPLE_RE
    + r"|" + COPULA_RE + r" un(?:shipped|implemented|built))"
)
# A release token of the shape every governed ledger records. The status
# marker declares one and the ledger holds another; nothing read the version a
# sentence names for itself, so a marker current against its ledger vouched for
# prose about a release that ledger left behind.
VERSION_TOKEN_RE = re.compile(r"\b[a-z][a-z0-9-]*-v\d+(?:\.\d+)*\b", re.IGNORECASE)
# The date a historical marker must name. `captured` was free text, so a
# marker could assert a dated capture without naming a date at all.
CAPTURED_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# The `- Current version:` row every governed ledger opens with. The value is
# read from the ledger rather than declared here, so a release moves the whole
# set of status claims at once.
LEDGER_VERSION_RE = re.compile(r"(?m)^- Current version: `(?P<version>[^`\n]+)`\s*$")

# One stable name per refusal condition, so a case can assert on the reason
# rather than on a message. The prefix is deliberately not `Dnnn`: that
# namespace belongs to the demonstration catalogue in
# `plugins/hexaemeron/skills/DEMONSTRATIONS.md`, which a parity test counts.
REFUSALS = {
    "FD01": "maintained document present and readable",
    "FD02": "collective portrait before the title",
    "FD03": "introduction word budget",
    "FD04": "contribution heading position",
    "FD05": "external contributor route position",
    "FD06": "document word budget",
    "FD07": "unique link targets",
    "FD08": "roster not inlined",
    "FD09": "promise machine link after contribution and demonstrations",
    "FD10": "catalogue link after contribution and demonstrations",
    "FD11": "all-caps public headings",
    "FD12": "collective art only",
    "FD13": "retained chirp",
    "FD14": "one further marked aside",
    "FD15": "demonstration section present",
    "FD16": "well-formed demonstration marker",
    "FD17": "marker bound to a governed record",
    "FD18": "marker claim identity",
    "FD19": "marker record digest",
    "FD20": "bound record still real-data",
    "FD21": "cards are exactly the real-data records",
    "FD22": "card displays its command",
    "FD23": "card names a preserved source",
    "FD24": "card displays an observed result",
    "FD25": "card displays the record's non-claim",
    "FD26": "count claim agrees with the derived topology",
    "FD27": "count claim names a derived quantity",
    "FD28": "every count claim is marked",
    "FD29": "count marker agrees with the quantity its prose names",
    "FD30": "generated region is on its own page, closed, and governs no heading",
    "FD31": "historical figure still says what its marker pinned",
    "FD32": "every member-status claim is bound to a ledger",
    "FD33": "bound member status matches the ledger's current version",
    "FD34": "historical marker only where a dated capture is recorded",
    "FD35": "landing-page member status names a member that page ships",
    "FD36": "generated-region claim is carried by the skill's own ledger",
    "FD37": "marked status prose names the version its marker declares",
    "FD38": "a marker that begins its line carries no prose on that line",
    "FD39": "bound ledger is readable and declares its current version",
}


class FrontDoorError(Exception):
    """An input could not be read at all, so no rule could be decided."""


@dataclass(frozen=True)
class Finding:
    """One reported rule, named by its stable code."""

    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} {self.message}"


@dataclass(frozen=True)
class Marker:
    """One parsed `front-door:` marker and where it sits."""

    kind: str
    attributes: dict[str, str]
    start: int
    end: int


def _finding(findings: list[Finding], code: str, message: str) -> None:
    if code not in REFUSALS:
        raise RuntimeError(f"undeclared front-door refusal {code}")
    findings.append(Finding(code, message))


def read_document(root: Path, relative: str) -> str:
    """Return one bounded maintained document through no-follow descriptors."""

    try:
        payload = demonstrations._read_regular_file(
            root, relative, maximum=MAX_DOCUMENT_BYTES, label=relative
        )
    except TopologyError as exc:
        raise FrontDoorError(f"cannot read {relative}: {exc}") from exc
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FrontDoorError(f"{relative} is not UTF-8: {exc}") from exc


def maintained_documents(topology) -> tuple[Maintained, ...]:
    """The whole swept set: the named documents plus one page per plugin.

    Discovery supplies the second half. A tuple of eighteen landing pages typed
    into this module would pass on the day a nineteenth plugin arrived with no
    page at all, which is the same failure the count rules exist to stop.
    """

    return MAINTAINED_DOCUMENTS + tuple(
        Maintained(f"plugins/{plugin}/{PLUGIN_LANDING}", ENTRY_RULES)
        for plugin in topology.plugins
    )


def ledger_version(root: Path, directory: str) -> str:
    """The version one governed skill's own ledger currently records."""

    return recorded_version(
        read_document(root, f"{directory}/{LEDGER_NAME}"), directory
    )


def recorded_version(text: str, directory: str) -> str:
    """The `- Current version:` row of one ledger, refusing one without it."""

    match = LEDGER_VERSION_RE.search(text)
    if match is None:
        raise FrontDoorError(
            f"{directory}/{LEDGER_NAME} declares no current version row"
        )
    return match.group("version")


class Ledgers:
    """Every governed ledger, each read the first time a claim binds to it.

    The sweep once resolved all of these before it opened a page, so one
    ledger with no version row raised out of the whole run at exit 2 with no
    findings list, on a tree where no page said anything about that skill.
    Reading at the point of use gives the condition the shape of every other
    declared one: `FD39` against the claim that needed the ledger, with the
    rest of the sweep reporting as it would have.

    Each ledger is opened at most once. The outcome is kept whether it was the
    text or the error that stopped the read, so a ledger bound by several
    claims is read once and an unreadable one is reported at each claim
    without being opened again.
    """

    def __init__(self, root: Path, by_skill: dict[str, str]) -> None:
        self.root = root
        self.by_skill = by_skill
        self._read: dict[str, str | FrontDoorError] = {}

    def governed(self, skill: str) -> bool:
        return skill in self.by_skill

    def text(self, skill: str) -> str:
        """The ledger as text, or the error that stopped its read."""

        if skill not in self._read:
            try:
                self._read[skill] = read_document(
                    self.root, f"{self.by_skill[skill]}/{LEDGER_NAME}"
                )
            except FrontDoorError as exc:
                self._read[skill] = exc
        outcome = self._read[skill]
        if isinstance(outcome, FrontDoorError):
            raise outcome
        return outcome

    def version(self, skill: str) -> str:
        """The version the ledger currently records."""

        return recorded_version(self.text(skill), self.by_skill[skill])

    def carries(self, skill: str, display: str, offset: int) -> bool:
        """Whether the ledger holds the sentence making the claim at `offset`.

        Normalised the same way `claim_sentence` normalises the page, so the
        two sides of the comparison differ only where the prose does.
        """

        return ledger_carries(
            display, offset, flat(self.text(skill).replace("*", " "))
        )


def rendered(text: str) -> str:
    """Blank every HTML comment, keeping every character offset unchanged.

    A marker is not a word a reader sees, and shifting offsets to remove one
    would make every position this checker reports refer to a document nobody
    has. Replacing each comment with spaces of its own length keeps both true.
    """

    return COMMENT_RE.sub(lambda match: " " * len(match.group(0)), text)


def unfenced(display: str) -> str:
    """Blank the inside of every fenced block, keeping offsets and line breaks.

    Only heading discovery reads this view. A `# comment` inside a shell block
    is not a section, and a heading quoted inside a fence is an example of one;
    reading either as structure let a front door satisfy its order contract
    with text that renders as code. Every other rule keeps the fenced view,
    because the `COMMAND_RE` a card must display sits inside a fence.
    """

    def blank(match: re.Match) -> str:
        body = match.group("body")
        return (
            match.group("open")
            + "".join(
                character if character == "\n" else " " for character in body
            )
            + match.group("close")
        )

    return FENCE_RE.sub(blank, display)


def claim_number(text: str) -> int:
    """The integer a count claim asserts, in digits or in words."""

    stripped = text.replace(",", "")
    if stripped.isdigit():
        return int(stripped)
    return sum(NUMBER_WORDS[part] for part in stripped.lower().split("-"))


def words(text: str) -> list[str]:
    return text.split()


def flat(text: str) -> str:
    """Collapse every run of whitespace, the way a renderer does.

    A card's evidence is checked against what a reader sees, not against how
    the source happens to be wrapped. Requiring a 40-word non-claim to sit on
    one physical line would be a formatting rule wearing an evidence rule's
    clothes, and the first person to rewrap the paragraph would delete the
    claim to make the checker quiet.
    """

    return " ".join(text.split())


def word_index(display: str, offset: int) -> int:
    """How many words precede `offset` in the rendered text."""

    return len(display[:offset].split())


def hosted(host: str, relative: str) -> bool:
    """Whether the page named by `relative` is where this generator writes."""

    if host == FRONT_DOOR_HOST:
        return relative == FRONT_DOOR
    return relative.startswith("plugins/") and relative.endswith(f"/{PLUGIN_LANDING}")


def generated_spans(
    text: str, relative: str | None = None
) -> tuple[list[tuple[int, int, frozenset[str], bool]], list[str]]:
    """The half-open ranges another generator owns, and why any was refused.

    An unclosed region used to run to the end of the file, so deleting one
    marker exempted every heading below it from the heading rule. A region that
    reaches a heading this contract governs does the same thing with both
    markers in place. A region opened on a page its generator never writes did
    it a third way, on any swept page and over any claim. None of the three is
    an exclusion an author may grant themselves, so each is refused and none is
    applied.
    """

    # A marker written inside a fenced block is a quoted example, not a region
    # boundary, so the markers are located in the fence-blanked view.
    outline = unfenced(text)
    spans: list[tuple[int, int, frozenset[str], bool]] = []
    refusals: list[str] = []
    for region_rule in GENERATED_REGIONS:
        opening, closing = region_rule.opening, region_rule.closing
        owned, host = region_rule.owned, region_rule.host
        start = outline.find(opening)
        if start < 0:
            continue
        # `relative` names the page under test. Omitting it reads the regions
        # a page declares without deciding whether it is entitled to them,
        # which is what an agreement check over the live tree wants; the sweep
        # always supplies it.
        if relative is not None and not hosted(host, relative):
            refusals.append(
                f"{opening} is written on {host} and this is not one, so the "
                "region governs nothing here"
            )
            continue
        for marker in (opening, closing):
            if outline.count(marker) > 1:
                refusals.append(
                    f"{marker} appears {outline.count(marker)} times; a region "
                    "with more than one boundary is not one region"
                )
        end = outline.find(closing, start)
        if end < 0:
            refusals.append(f"the {opening} region is never closed by {closing}")
            continue
        if outline.count(opening) > 1 or outline.count(closing) > 1:
            continue
        span = (start, end + len(closing))
        region = outline[span[0]: span[1]]
        # The exclusion exists for the headings the generator writes. Every
        # other heading inside the region is an exemption the author granted
        # themselves, which is the whole failure this rule refuses.
        reached = [
            match.group(0).strip()
            for match in HEADING_RE.finditer(region)
            if match.group(0).strip() != owned
        ]
        if reached:
            refusals.append(
                f"the {opening} region reaches {reached[0]!r}; it may cover no "
                f"heading other than {owned!r}"
            )
            continue
        spans.append(
            (span[0], span[1], region_rule.exempts, region_rule.ledger_backed)
        )
    return spans, refusals


def inside(
    spans: Sequence[tuple[int, int, frozenset[str], bool]], offset: int, rule: str
) -> bool:
    """Whether `offset` sits in a region whose owner exempts `rule`.

    Being inside a region is no longer the whole answer. A region exempts the
    rules its owner actually writes, so a heading the marketplace supplies is
    excused while a count claim typed beside it is not.
    """

    return any(
        start <= offset < end and rule in exempts
        for start, end, exempts, _ in spans
    )


def ledger_backed(
    spans: Sequence[tuple[int, int, frozenset[str], bool]], offset: int
) -> bool:
    """Whether `offset` sits in a region that quotes the skill's own ledger."""

    return any(
        start <= offset < end and backed for start, end, _, backed in spans
    )


def claim_sentence(display: str, offset: int) -> str:
    """The flattened sentence carrying `offset`, with emphasis markers dropped.

    A landing block writes its claims as `**Current frontier.** ...`, and the
    label's own full stop is not a sentence boundary a reader sees. Blanking
    the asterisks before splitting keeps the label out of the sentence and
    leaves the claim itself byte-for-byte comparable with the ledger row it
    was quoted from.
    """

    body = display.replace("*", " ")
    starts = [body.rfind(mark, 0, offset) for mark in (". ", "; ", ".\n", ";\n")]
    start = max(starts)
    start = 0 if start < 0 else start + 1
    ends = [body.find(mark, offset) for mark in (". ", "; ", ".\n", ";\n")]
    end = min([found for found in ends if found >= 0], default=-1)
    end = len(body) if end < 0 else end + 1
    return flat(body[start:end])


def ledger_carries(display: str, offset: int, ledger: str) -> bool:
    """Whether the skill's own ledger holds the sentence making this claim."""

    sentence = claim_sentence(display, offset)
    return bool(sentence) and bool(ledger) and sentence in ledger


def check_region_claim(
    where: str,
    kind: str,
    claim: re.Match,
    display: str,
    entry: str | None,
    ledgers: Ledgers | None,
    findings: list[Finding],
) -> None:
    """Decide one claim inside a region that quotes the page's own ledger.

    The region exempts the claim only when the entry skill's ledger carries
    the sentence making it. The ledger is read here, at the first claim that
    needs it, and not before; one that cannot be read shows nothing, so the
    claim is refused against that ledger rather than against the sentence.
    """

    word = word_index(display, claim.start())
    carried = False
    if entry is not None and ledgers is not None and ledgers.governed(entry):
        try:
            carried = ledgers.carries(entry, display, claim.start())
        except FrontDoorError as exc:
            _finding(
                findings,
                "FD39",
                f"{where}: the {kind} claim {claim.group(0)!r} at word {word} "
                f"sits in a generated region quoting {entry}'s ledger, and "
                f"{exc}; a ledger that cannot be read exempts nothing",
            )
            return
    if carried:
        return
    _finding(
        findings,
        "FD36",
        f"{where}: the {kind} claim {claim.group(0)!r} at word {word} sits in "
        "a generated region and no sentence in this skill's own EVOLUTION.md "
        "carries it, so the region exempts nothing here",
    )


def markers(text: str) -> list[Marker]:
    """Parse every `front-door:` marker in document order."""

    found = []
    for match in MARKER_RE.finditer(text):
        rest = match.group("rest")
        attributes = {
            item.group("name"): item.group("value")
            for item in ATTRIBUTE_RE.finditer(rest)
        }
        found.append(
            Marker(match.group("kind"), attributes, match.start(), match.end())
        )
    return found


def headings(display: str) -> list[tuple[int, int, str]]:
    """Every ATX heading as (offset, level, text) over the rendered document."""

    return [
        (match.start(), len(match.group("hashes")), match.group("text"))
        for match in HEADING_RE.finditer(display)
    ]


def html_target(match: re.Match) -> str:
    """The target of one HTML attribute, quoted either way or not at all."""

    return match.group("quoted") or match.group("bare")


def reference_definitions(display: str) -> dict[str, str]:
    """Every `[label]: target` definition, keyed the way Markdown folds them."""

    return {
        match.group("label").strip().lower(): match.group("target")
        for match in REFERENCE_DEFINITION_RE.finditer(display)
    }


def reference_uses(display: str, *, images: bool) -> list[tuple[int, str]]:
    """Reference-style uses resolved through their definitions.

    `![alt][label]` renders an image and `[text][label]` renders a link, and
    the collapsed forms `![alt][]` and `[text][]` take the label from the text.
    A checker blind to these reads a page with a second portrait on it, or a
    route linked twice, as a page with neither.
    """

    definitions = reference_definitions(display)
    found = []
    seen: set[int] = set()
    for match in REFERENCE_USE_RE.finditer(display):
        if bool(match.group("bang")) != images:
            continue
        seen.update(range(match.start(), match.end()))
        label = (match.group("label") or match.group("text")).strip().lower()
        target = definitions.get(label)
        if target is not None:
            found.append((match.start(), target))
    for match in REFERENCE_SHORTCUT_RE.finditer(display):
        if bool(match.group("bang")) != images or match.start() in seen:
            continue
        target = definitions.get(match.group("label").strip().lower())
        if target is not None:
            found.append((match.start(), target))
    return found


def link_targets(display: str) -> list[tuple[int, str]]:
    found = [
        (match.start(), match.group("target"))
        for match in MARKDOWN_LINK_RE.finditer(display)
    ]
    found += [
        (match.start(), html_target(match)) for match in HTML_HREF_RE.finditer(display)
    ]
    found += reference_uses(display, images=False)
    return sorted(found)


def image_targets(display: str) -> list[tuple[int, str]]:
    found = [
        (match.start(), match.group("target"))
        for match in MARKDOWN_IMAGE_RE.finditer(display)
    ]
    found += [
        (match.start(), html_target(match)) for match in HTML_IMAGE_RE.finditer(display)
    ]
    found += reference_uses(display, images=True)
    return sorted(found)


def find_heading(display: str, heading: str) -> int | None:
    """The offset of one exact ATX heading line, or None."""

    for match in HEADING_RE.finditer(display):
        if match.group(0).strip() == heading:
            return match.start()
    return None


def governed_home(directory: str) -> str:
    """The link a reader follows to reach one governed skill's own page."""

    parts = directory.split("/")
    plugin, skill = parts[1], parts[3]
    if plugin == skill:
        return f"./plugins/{plugin}"
    return f"./{directory.rsplit('/skills/', 1)[0]}/skills/{skill}"


def observation_display(observation: demonstrations.Observation) -> str:
    """The exact text a card must carry to show this observed result."""

    if observation.kind == "line":
        return observation.line or ""
    return f"{'.'.join(observation.path)} {json.dumps(observation.value)}"


def preserved_sources(record: dict) -> list[str]:
    """Every preserved input a card may name, excluding the program itself."""

    named = []
    for source in record["sources"]:
        if source["id"] == PROGRAM_SOURCE_ID:
            continue
        if source["class"] not in PRESERVED_CLASSES:
            continue
        named.append(source.get("path") or source.get("anchor") or "")
    return [item for item in named if item]


def emit_event(event: str, **fields: object) -> None:
    """Emit one bounded, stable event as canonical JSON on one line."""

    print(json.dumps({"event": event, **fields}, sort_keys=True, separators=(",", ":")))


def check_regions(
    where: str, text: str, findings: list[Finding]
) -> list[tuple[int, int, frozenset[str], bool]]:
    """The ranges another generator owns on one page, checked once.

    Every set-wide rule reads past a generated region, so every set-wide rule
    depends on this being sound. Computing it inside each rule left the refusal
    reported by whichever rule happened to run: a page carrying counts but not
    headings could open a region and never close it, and every count and status
    claim below would be exempt with nothing said. It is decided here, once per
    page, and the spans are handed to the rules that read them.
    """

    spans, refused = generated_spans(text, where)
    for reason in refused:
        _finding(findings, "FD30", f"{where}: {reason}")
    return spans


def check_headings(
    where: str,
    display: str,
    spans: Sequence[tuple[int, int, frozenset[str], bool]],
    findings: list[Finding],
) -> None:
    """The house all-caps style, over one maintained page.

    The generated regions are the one exemption, and it is not one an author
    grants: `check_regions` refuses a region that is unclosed or that reaches a
    heading its owner does not write, and a refused region is not applied.
    """

    outline = unfenced(display)
    for offset, _, heading in headings(outline):
        if inside(spans, offset, HEADING_RULE):
            continue
        # A heading with no letter in it is upper case only because there is
        # nothing to lower, so `## 2026` used to satisfy the house style by
        # holding none of it.
        if heading != heading.upper() or not any(
            character.isalpha() for character in heading
        ):
            _finding(findings, "FD11", f"{where}: heading {heading!r} is not all caps")


def check_structure(text: str, display: str, findings: list[Finding]) -> None:
    """Order, budgets, links and images on the front door."""

    outline = unfenced(display)
    title = next(
        (
            match.start()
            for match in HEADING_RE.finditer(outline)
            if match.group(0).startswith(TITLE_PREFIX)
        ),
        None,
    )

    images = image_targets(display)
    portrait = next((offset for offset, src in images if src == PORTRAIT), None)
    if portrait is None:
        _finding(findings, "FD02", f"{FRONT_DOOR} carries no {PORTRAIT}")
    elif title is None:
        _finding(findings, "FD02", f"{FRONT_DOOR} has no level-one title")
    elif portrait > title:
        _finding(findings, "FD02", "the collective portrait follows the title")
    for offset, src in images:
        if src != PORTRAIT:
            _finding(
                findings,
                "FD12",
                f"{FRONT_DOOR} carries a second image {src!r} at word "
                f"{word_index(display, offset)}",
            )

    contribution = find_heading(outline, CONTRIBUTION_HEADING)
    demonstration = find_heading(outline, DEMONSTRATION_HEADING)
    if demonstration is None:
        _finding(findings, "FD15", f"{FRONT_DOOR} has no {DEMONSTRATION_HEADING!r}")

    first_section = None
    for offset, level, _ in headings(outline):
        if level != 2:
            continue
        if contribution is not None and offset <= contribution:
            continue
        if demonstration is not None and offset <= demonstration:
            continue
        first_section = offset
        break

    if title is not None:
        # The introduction runs from the title to whichever section opens
        # first, not to the contribution heading: a section wedged in between
        # would otherwise be counted as introduction and report the wrong rule.
        opening = next(
            (offset for offset, level, _ in headings(outline) if level == 2), None
        )
        introduction = display[title: len(display) if opening is None else opening]
        # The title line itself is not the introduction.
        introduction = introduction.split("\n", 1)[-1]
        counted = len(words(introduction))
        if counted > INTRODUCTION_WORDS:
            _finding(
                findings,
                "FD03",
                f"the introduction is {counted} words, over {INTRODUCTION_WORDS}",
            )

    if contribution is None:
        _finding(findings, "FD04", f"{FRONT_DOOR} has no {CONTRIBUTION_HEADING!r}")
    else:
        at = word_index(display, contribution)
        if at > CONTRIBUTION_WORDS:
            _finding(
                findings,
                "FD04",
                f"{CONTRIBUTION_HEADING!r} begins at word {at}, over "
                f"{CONTRIBUTION_WORDS}",
            )

    route = next(
        (offset for offset, target in link_targets(display) if target == CONTRIBUTOR_ROUTE),
        None,
    )
    if route is None:
        _finding(findings, "FD05", f"{FRONT_DOOR} does not link {CONTRIBUTOR_ROUTE}")
    else:
        at = word_index(display, route)
        if at > CONTRIBUTION_WORDS:
            _finding(
                findings,
                "FD05",
                f"the contributor route begins at word {at}, over "
                f"{CONTRIBUTION_WORDS}",
            )

    total = len(words(display))
    if total > DOCUMENT_WORDS:
        _finding(
            findings, "FD06", f"{FRONT_DOOR} is {total} words, over {DOCUMENT_WORDS}"
        )

    seen: dict[str, int] = {}
    for offset, target in link_targets(display):
        if target in seen:
            _finding(
                findings,
                "FD07",
                f"link target {target!r} appears again at word "
                f"{word_index(display, offset)}",
            )
        seen.setdefault(target, offset)

    boundary = max(
        offset for offset in (contribution, demonstration, 0) if offset is not None
    )
    for code, target in (
        ("FD09", PROMISE_MACHINE_LINK),
        ("FD10", CATALOGUE_LINK),
    ):
        first = next(
            (offset for offset, item in link_targets(display) if item == target), None
        )
        if first is None:
            _finding(findings, code, f"{FRONT_DOOR} does not link {target}")
        elif first < boundary:
            _finding(
                findings,
                code,
                f"the first {target} link is at word {word_index(display, first)}, "
                "before contribution and demonstrations",
            )

    chirp = display.find(CHIRP)
    if chirp < 0:
        _finding(findings, "FD13", "the retained chirp is absent")
    elif first_section is not None and chirp > first_section:
        _finding(findings, "FD13", "the retained chirp follows the first section")


def check_asides(text: str, display: str, findings: list[Finding]) -> None:
    """One further short, marked, self-aware line before the technical part."""

    outline = unfenced(display)
    contribution = find_heading(outline, CONTRIBUTION_HEADING)
    demonstration = find_heading(outline, DEMONSTRATION_HEADING)
    first_section = None
    for offset, level, _ in headings(outline):
        if level != 2:
            continue
        if contribution is not None and offset <= contribution:
            continue
        if demonstration is not None and offset <= demonstration:
            continue
        first_section = offset
        break

    limit = len(display) if first_section is None else first_section
    for marker in markers(text):
        if marker.kind != "aside":
            continue
        if marker.start >= limit:
            continue
        line = display[marker.end:].lstrip("\n").split("\n", 1)[0].strip()
        if not line or line == CHIRP:
            continue
        if len(words(line)) > ASIDE_WORDS:
            continue
        return
    _finding(
        findings,
        "FD14",
        "no marked aside of at most "
        f"{ASIDE_WORDS} words, other than the chirp, precedes the first section",
    )


def claim_after(display: str, marker: Marker) -> tuple[re.Match | None, int]:
    """The count claim a marker sits immediately in front of, and its offset."""

    tail = display[marker.end:]
    offset = marker.end + (len(tail) - len(tail.lstrip()))
    return COUNT_CLAIM_RE.match(tail.lstrip()), offset


def check_counts(
    where: str,
    text: str,
    display: str,
    counts: dict[str, int],
    spans: Sequence[tuple[int, int, frozenset[str], bool]],
    findings: list[Finding],
    *,
    history: bool = False,
    entry: str | None = None,
    ledgers: Ledgers | None = None,
) -> None:
    """Every current count claim names a derived quantity and agrees with it."""

    marked: set[int] = set()

    for marker in markers(text):
        # Rendering, not derivation. A line that opens with `<!--` is an HTML
        # block to CommonMark, which interrupts the paragraph and leaves
        # whatever follows the comment on that line as bare text outside it.
        # GitHub showed "27 governed skills in" on a line of its own that way.
        # Only the source shows this; the rendered form the count rules read
        # has already lost the line break.
        line_start = text.rfind("\n", 0, marker.start) + 1
        if text[line_start : marker.start].strip():
            continue
        line_end = text.find("\n", marker.end)
        if line_end == -1:
            line_end = len(text)
        if text[marker.end : line_end].strip():
            _finding(
                findings,
                "FD38",
                f"{where}: the front-door:{marker.kind} marker on line "
                f"{text.count(chr(10), 0, marker.start) + 1} begins its line "
                "and prose follows it there; a line opening with an HTML "
                "comment is an HTML block, so that prose renders outside the "
                "paragraph. Move the marker mid-line",
            )

    for marker in markers(text):
        if marker.kind != "historical":
            continue
        # The exemption is the whole risk in this marker: it takes a number out
        # of derivation for good. A page that records no dated measurement has
        # nothing to exempt, so the marker is refused there and the number it
        # sits over stays an ordinary count claim rather than becoming a
        # literal nothing reads.
        if not history:
            _finding(
                findings,
                "FD34",
                f"{where}: a front-door:historical marker sits on a page that "
                f"records no dated capture; only {HISTORY_HOME} exempts a "
                "figure from derivation",
            )
            continue
        claim, offset = claim_after(display, marker)
        missing = sorted({"captured", "figure"} - set(marker.attributes))
        if missing:
            _finding(
                findings,
                "FD31",
                f"{where}: the historical marker at word "
                f"{word_index(display, marker.start)} is missing {missing}",
            )
            continue
        if claim is None:
            _finding(
                findings,
                "FD31",
                f"{where}: the historical marker at word "
                f"{word_index(display, marker.start)} is not followed by a figure",
            )
            continue
        # Naming the page was half the rule. `captured` was free text, so the
        # marker could assert a dated capture while naming no date, and the
        # date it named appeared nowhere a reader could check. Both halves are
        # required now: the attribute is a date, and the page records it in
        # prose. The exemption then rests on evidence the reader can see
        # rather than on an attribute the renderer hides.
        captured = marker.attributes["captured"]
        if not CAPTURED_RE.match(captured):
            _finding(
                findings,
                "FD34",
                f"{where}: the historical marker at word "
                f"{word_index(display, marker.start)} declares captured="
                f"{captured!r}, which is not a YYYY-MM-DD date",
            )
            continue
        if captured not in display:
            _finding(
                findings,
                "FD34",
                f"{where}: the historical marker at word "
                f"{word_index(display, marker.start)} names the {captured} "
                "capture, and no prose on this page records that date",
            )
            continue
        marked.add(offset)
        figure = marker.attributes["figure"]
        # Byte-for-byte, and deliberately so. A dated measurement is evidence
        # about one past install, and the only useful question a checker can
        # ask of it is whether the prose still says what was measured.
        if claim.group("number") != figure:
            _finding(
                findings,
                "FD31",
                f"{where}: the {marker.attributes['captured']} capture pinned "
                f"{figure!r} and the prose now says {claim.group('number')!r}; a "
                "historical figure is evidence, not a number to bring up to date",
            )

    for marker in markers(text):
        if marker.kind != "count":
            continue
        key = marker.attributes.get("key", "")
        claim, offset = claim_after(display, marker)
        if claim is None:
            _finding(
                findings,
                "FD27",
                f"{where}: the count marker {key!r} at word "
                f"{word_index(display, marker.start)} is not followed by a count claim",
            )
            continue
        marked.add(offset)
        if key not in COUNT_KEYS:
            _finding(
                findings,
                "FD27",
                f"{where}: count key {key!r} names no derived quantity; "
                f"declared keys are {sorted(COUNT_KEYS)}",
            )
            continue
        # The marker binds the number to a quantity; the sentence tells the
        # reader which quantity it is. When the two disagree the number can be
        # right for the key and wrong for every reader.
        if COUNT_NOUNS[key] not in claim.group(0).lower():
            _finding(
                findings,
                "FD29",
                f"{where}: the count marker {key!r} sits over {claim.group(0)!r}, "
                f"which names no {COUNT_NOUNS[key]!r} quantity",
            )
            continue
        derived = counts[COUNT_KEYS[key]]
        claimed = claim_number(claim.group("number"))
        if claimed != derived:
            _finding(
                findings,
                "FD26",
                f"{where}: the prose claims {claimed} for {key!r}; both manifests "
                f"and tree discovery derive {derived}",
            )

    for claim in COUNT_CLAIM_RE.finditer(display):
        if claim.start() in marked or inside(spans, claim.start(), COUNT_RULE):
            continue
        if ledger_backed(spans, claim.start()):
            check_region_claim(
                where, "count", claim, display, entry, ledgers, findings
            )
            continue
        _finding(
            findings,
            "FD28",
            f"{where}: the count claim {claim.group(0)!r} at word "
            f"{word_index(display, claim.start())} carries no front-door:count "
            "or front-door:historical marker",
        )


def check_status(
    where: str,
    text: str,
    display: str,
    ledgers: Ledgers,
    spans: Sequence[tuple[int, int, frozenset[str], bool]],
    findings: list[Finding],
    *,
    plugin: str | None = None,
    by_plugin: dict[str, str] | None = None,
    entry: str | None = None,
) -> None:
    """Every member-status claim names the ledger version it describes.

    The claim's region runs from its marker to the end of the paragraph, which
    is where a reader stops reading one statement about a member and starts the
    next. Anchoring on the marker's own line instead would have refused
    "Its compile path has not shipped", which is the second half of a sentence
    that opens somewhere else.

    Like the count rules, this reads the fenced view. A status sentence inside
    a code block is read as one, which is the safe direction: a fenced example
    caught by mistake is reworded or marked, and one missed is a member status
    that ages in public.
    """

    covered: set[int] = set()

    for marker in markers(text):
        if marker.kind != "status":
            continue
        missing = sorted({"skill", "version"} - set(marker.attributes))
        if missing:
            _finding(
                findings,
                "FD32",
                f"{where}: the status marker at word "
                f"{word_index(display, marker.start)} is missing {missing}",
            )
            continue
        end = display.find("\n\n", marker.end)
        region = (marker.end, len(display) if end < 0 else end)
        claims = [
            claim.start()
            for claim in STATUS_CLAIM_RE.finditer(display[region[0]: region[1]])
        ]
        if not claims:
            _finding(
                findings,
                "FD32",
                f"{where}: the status marker at word "
                f"{word_index(display, marker.start)} governs no member-status claim",
            )
            continue
        covered.update(region[0] + start for start in claims)
        skill = marker.attributes["skill"]
        declared = marker.attributes["version"]
        if not ledgers.governed(skill):
            _finding(
                findings,
                "FD32",
                f"{where}: the status marker binds skill {skill!r}, which is not "
                "a governed skill",
            )
            continue
        # A marker binds a version; the sentence is about a member. Nothing
        # joined the two, so a claim about one member sat under a marker naming
        # another whose ledger happened to be current, and the rule reported
        # nothing. A landing page knows which plugin it belongs to, so that
        # much of the join is free.
        if plugin is not None and (by_plugin or {}).get(skill) != plugin:
            _finding(
                findings,
                "FD35",
                f"{where}: the status marker binds {skill!r}, which {plugin} "
                "does not ship; a landing page states its own members' status",
            )
            continue
        # Shipping the skill was too weak on its own. The phase host ships ten,
        # so any of ten ledgers could vouch for any claim on its page, and the
        # slowest-moving one holds a stale sentence current for ever. The page's
        # own entry skill is the member a landing page is about; any other
        # member it ships has to be named in the prose it vouches for.
        text_region = display[region[0]: region[1]]
        if (
            plugin is not None
            and entry is not None
            and skill != entry
            and not re.search(rf"\b{re.escape(skill)}\b", text_region, re.IGNORECASE)
        ):
            _finding(
                findings,
                "FD35",
                f"{where}: the status marker binds {skill!r}, which is neither "
                f"{plugin}'s entry skill {entry!r} nor named in the claim it "
                "governs; a sibling ledger is not evidence about this member",
            )
            continue
        # The marker declares a version and the ledger holds one; nothing read
        # the version the sentence itself names. A claim written about a
        # superseded release passed under a marker that was current, which is
        # the failure this whole rule exists for wearing a version number.
        stale = [
            token
            for token in VERSION_TOKEN_RE.findall(text_region)
            if token.lower().startswith(f"{skill.lower()}-v")
            and token != declared
        ]
        if stale:
            _finding(
                findings,
                "FD37",
                f"{where}: the marked prose names {stale[0]!r} and its marker "
                f"declares {declared!r}; a marker vouches for the release it "
                "names and for no other",
            )
            continue
        # The ledger is read here, at the comparison that needs it, and not
        # before. The three rules above are decided from the page alone, so a
        # ledger that cannot be read refuses this marker and hides nothing else.
        try:
            current = ledgers.version(skill)
        except FrontDoorError as exc:
            _finding(
                findings,
                "FD39",
                f"{where}: the status marker at word "
                f"{word_index(display, marker.start)} binds {skill!r}, and "
                f"{exc}, so nothing decides whether {declared} is current",
            )
            continue
        if declared != current:
            _finding(
                findings,
                "FD33",
                f"{where}: the prose describes {declared}; {skill}'s ledger now "
                f"records {current}, so the claim is about a release that has "
                "been superseded",
            )

    for claim in STATUS_CLAIM_RE.finditer(display):
        if claim.start() in covered or inside(spans, claim.start(), STATUS_RULE):
            continue
        if ledger_backed(spans, claim.start()):
            check_region_claim(
                where, "member-status", claim, display, entry, ledgers, findings
            )
            continue
        _finding(
            findings,
            "FD32",
            f"{where}: the member-status claim {claim.group(0)!r} at word "
            f"{word_index(display, claim.start())} carries no front-door:status marker",
        )


def check_cards(
    text: str,
    display: str,
    records: dict[str, dict],
    by_skill: dict[str, str],
    findings: list[Finding],
) -> list[dict]:
    """Every card binds a live real-data record and displays its evidence."""

    outline = unfenced(display)
    demonstration = find_heading(outline, DEMONSTRATION_HEADING)
    if demonstration is None:
        return []
    end = len(display)
    for offset, level, _ in headings(outline):
        if level <= 2 and offset > demonstration:
            end = offset
            break

    cards = [
        marker
        for marker in markers(text)
        if marker.kind == "demo" and demonstration <= marker.start < end
    ]
    stray = [
        marker
        for marker in markers(text)
        if marker.kind == "demo" and not (demonstration <= marker.start < end)
    ]
    for marker in stray:
        _finding(
            findings,
            "FD16",
            f"a demonstration marker sits outside {DEMONSTRATION_HEADING!r} at word "
            f"{word_index(display, marker.start)}",
        )

    events: list[dict] = []
    bound: set[str] = set()
    for index, marker in enumerate(cards):
        where = f"card {index + 1}"
        missing = sorted({"skill", "claim", "digest"} - set(marker.attributes))
        if missing:
            _finding(findings, "FD16", f"{where} marker is missing {missing}")
            continue
        skill = marker.attributes["skill"]
        claim = marker.attributes["claim"]
        digest = marker.attributes["digest"]
        directory = by_skill.get(skill)
        if directory is None:
            _finding(
                findings,
                "FD17",
                f"{where} binds skill {skill!r}, which is not a governed skill",
            )
            continue
        record = records.get(directory)
        if record is None:
            _finding(
                findings,
                "FD17",
                f"{where} binds {directory!r}, which holds no demonstration record",
            )
            continue
        # Set membership answers "is every record carded" and not "is every
        # card a different record", so a fifth card repeating the first passed
        # while the section claimed one more demonstration than the tree holds.
        if directory in bound:
            _finding(
                findings,
                "FD21",
                f"{where} binds {directory}, which another card already binds",
            )
        bound.add(directory)
        body = flat(
            display[
                marker.end: cards[index + 1].start if index + 1 < len(cards) else end
            ]
        )

        if record["claim_id"] != claim:
            _finding(
                findings,
                "FD18",
                f"{where} binds claim {claim!r}; {directory} records "
                f"{record['claim_id']!r}",
            )
        actual = demonstrations.record_digest(record)
        if actual != digest:
            _finding(
                findings,
                "FD19",
                f"{where} binds digest {digest}; {directory} now hashes to {actual}",
            )
        if record["status"] != "real-data":
            _finding(
                findings,
                "FD20",
                f"{where} claims real data; {directory} is {record['status']!r}",
            )

        commands = list(COMMAND_RE.finditer(body))
        if len(commands) != 1 or commands[0].group("directory") != directory:
            _finding(
                findings,
                "FD22",
                f"{where} must display exactly one "
                f"`python3 scripts/demonstrations.py run --record {directory} "
                "--report <new path>` command",
            )
        named = preserved_sources(record)
        if not any(source in body for source in named):
            _finding(
                findings,
                "FD23",
                f"{where} names none of {directory}'s preserved sources {named}",
            )
        # A record may carry prose alongside its checkable observations. Prose
        # is not an observed result, so it is passed over here rather than
        # raising: the card still has to show one result the runner decides.
        observed = []
        for item in record["observations"]:
            try:
                parsed = demonstrations.parse_observation(item, where=directory)
            except demonstrations.DemonstrationError:
                continue
            observed.append(observation_display(parsed))
        shown = [item for item in observed if item and flat(item) in body]
        if not shown:
            _finding(
                findings,
                "FD24",
                f"{where} displays none of {directory}'s recorded results",
            )
        if flat(record["non_claim"]) not in body:
            _finding(
                findings,
                "FD25",
                f"{where} does not display {directory}'s non-claim",
            )
        events.append(
            {
                "claim_id": record["claim_id"],
                "digest": actual,
                "directory": directory,
                "observed": shown[0] if shown else "",
                "skill": skill,
                "status": record["status"],
            }
        )

    expected = {
        directory
        for directory, record in records.items()
        if record["status"] == "real-data"
    }
    for directory in sorted(expected - bound):
        _finding(
            findings,
            "FD21",
            f"{directory} is real-data and no card binds it",
        )
    for directory in sorted(bound - expected):
        _finding(
            findings,
            "FD21",
            f"{directory} carries a card and is not real-data",
        )
    return events


def check_roster(display: str, governed: Sequence[str], findings: list[Finding]) -> None:
    """The front door points at the catalogue rather than becoming one."""

    targets = {target for _, target in link_targets(display)}
    linked = [
        directory for directory in governed if governed_home(directory) in targets
    ]
    if len(linked) >= len(governed):
        _finding(
            findings,
            "FD08",
            f"{FRONT_DOOR} links all {len(governed)} governed skills; the complete "
            f"roster belongs in {CATALOGUE_LINK}",
        )


def check(root: Path) -> tuple[list[Finding], list[dict]]:
    """Run every rule against the repository rooted at `root`."""

    findings: list[Finding] = []
    topology = discover_topology(root)
    documents = maintained_documents(topology)

    sources: dict[str, str] = {}
    for item in documents:
        try:
            body = read_document(root, item.relative)
        except FrontDoorError as exc:
            _finding(findings, "FD01", str(exc))
            continue
        # Present is not the same as readable content. A page holding nothing
        # satisfies every rule below by carrying none of them, and the sweep
        # then counts it among the documents that hold the contract, which is
        # the reading a reader cannot tell from a clean one.
        if not body.strip():
            _finding(
                findings,
                "FD01",
                f"{item.relative} is present and holds nothing; an empty page "
                "passes every rule by carrying none of them",
            )
            continue
        sources[item.relative] = body
    # A rule read against a set that is already incomplete reports on whatever
    # happened to be there, and a reader cannot tell that from a clean sweep.
    if findings:
        return findings, []

    by_skill = {
        directory.rsplit("/", 1)[-1]: directory for directory in topology.governed
    }
    by_plugin = {
        skill: directory.split("/")[1] for skill, directory in by_skill.items()
    }
    # No ledger is read here. Each is opened by the first claim that binds to
    # it, so a ledger no page describes is never read, and one that cannot be
    # read is a refusal against that claim rather than the end of the sweep.
    ledgers = Ledgers(root, by_skill)
    # The entry skill one landing page is about, and the ledger its generated
    # region quotes. A landing block is the skill's own frontier prose copied
    # out of `EVOLUTION.md`, so the ledger is what decides whether a claim
    # inside the region was derived or typed.
    entries = {
        directory.split("/")[1]: directory.rsplit("/", 1)[-1]
        for directory in topology.canonical
    }
    counts = topology.counts()

    events: list[dict] = []
    for item in documents:
        text = sources[item.relative]
        display = rendered(text)
        spans = check_regions(item.relative, text, findings)
        owner = (
            item.relative.split("/")[1]
            if hosted(LANDING_HOST, item.relative)
            else None
        )
        if item.carries(HEADING_RULE):
            check_headings(item.relative, display, spans, findings)
        if item.carries(COUNT_RULE):
            check_counts(
                item.relative,
                text,
                display,
                counts,
                spans,
                findings,
                history=item.carries(HISTORY_RULE),
                entry=entries.get(owner or ""),
                ledgers=ledgers,
            )
        if item.carries(STATUS_RULE):
            check_status(
                item.relative,
                text,
                display,
                ledgers,
                spans,
                findings,
                plugin=owner,
                by_plugin=by_plugin,
                entry=entries.get(owner or ""),
            )
        if item.carries(FRONT_DOOR_RULE):
            records = demonstrations.load_records(root)
            check_structure(text, display, findings)
            check_asides(text, display, findings)
            check_roster(display, topology.governed, findings)
            events = check_cards(text, display, records, by_skill, findings)
    return findings, events


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Check the maintained public surface against its contract."
    )
    parser.add_argument(
        "--root", type=Path, default=Path("."), help="repository root to read"
    )
    args = parser.parse_args(argv)

    try:
        topology = discover_topology(args.root)
        swept = len(maintained_documents(topology))
        findings, events = check(args.root)
    except (FrontDoorError, TopologyError, demonstrations.DemonstrationError) as exc:
        print(f"check_public_front_door.py: {exc}", file=sys.stderr)
        return 2

    for event in events:
        emit_event("demonstration.public_claim.checked", **event)
    for finding in findings:
        print(str(finding), file=sys.stderr)
    if findings:
        print(
            f"maintained surface: {len(findings)} finding(s) across "
            f"{swept} document(s)",
            file=sys.stderr,
        )
        return 1
    print(
        f"maintained surface: {swept} document(s) hold the contract, with "
        f"{len(events)} checked card(s) on {FRONT_DOOR}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
