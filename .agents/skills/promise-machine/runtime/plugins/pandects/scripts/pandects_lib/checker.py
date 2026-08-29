"""The six parts, enforced.

A law that has never failed may be a tautology or an unreachable check. That is
the specification's gate 2, and it is not rhetoric: a property asserting
`seen() >= 0` survived five hundred and twelve calls of a stateful campaign
without complaint. Nothing in a passing run distinguishes a law that holds from
a law that cannot fail, so the specimen is not documentation. It is the only
evidence that a law is a law.

These checks cannot tell whether a law is true either. They refuse the shapes
that let something which is not a law be filed as one:

1. It executes. A component exists, and its `id()` is this law's id.
2. It catches something. A specimen exists and says it is deliberately broken.
3. It has been reduced. A counterexample exists, replayable without a fuzzer.
4. It says where it applies. Accounting model, assumptions, requirements.
5. Its bounds are justified. Exact, or a tolerance naming the arithmetic that
   produces it.
6. It judges rather than reverts. A component that reverts to signal a failure
   reports nothing under `fail_on_revert = false`.
"""

import os
import re

from .catalogue import EXACT, REQUIRED_APPLICABILITY

ID_IN_SOLIDITY = re.compile(
    r"function\s+id\s*\(\s*\)[^{]*\{[^}]*return\s+\"([^\"]+)\"", re.DOTALL
)

BROKEN_MARKER = "deliberately broken"

REVERTS = re.compile(
    r"(?<![\w.$])(require|assert|revert)\s*\(|(?<![\w.$])(revert)\s+[A-Z]"
)
"""`assert` belongs here with the other two. It reverts with a panic, which
under `fail_on_revert = false` is as silent as any other revert, and a law
reaching for it to mean "violated" is making the same mistake in a different
word.

The two alternatives are the two spellings and nothing else. `revert` followed
by whitespace and a capital is a custom error; `revert(` is the plain form. A
function called `revertHelper` is neither, and an earlier pattern that accepted
any uppercase letter after the word flagged it."""

STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
LINE_COMMENT = re.compile(r"//[^\n]*")
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


class Finding(object):
    def __init__(self, law, part, detail):
        self.law = law
        self.part = part
        self.detail = detail

    def line(self):
        return "%s: %s -- %s" % (self.law, self.part, self.detail)


def read(path):
    """Read a component's source, or None when it is not text.

    A component that is not UTF-8 is not a component. Returning rather than
    raising keeps it a finding the reader is told about instead of a traceback
    out of the checker.
    """
    try:
        with open(path, "rb") as handle:
            return handle.read().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def scannable(source):
    """Source with string literals and comments removed.

    Both are places a law legitimately writes the word `require` without doing
    it: a comment saying what the law does not do, and a `statement()` whose
    sentence describes a system that requires something. Strings go first, so a
    `//` inside one is removed with the string rather than truncating the line.

    A double quote inside a comment can confuse the string pass. The cost is a
    comment being over-removed, which loses nothing, because comments are being
    removed anyway.
    """
    return LINE_COMMENT.sub("", BLOCK_COMMENT.sub("", STRING.sub('""', source)))


def resolve(root, relative):
    """A catalogue path, resolved and confined to the plugin."""
    if not isinstance(relative, str) or not relative.strip():
        return None
    try:
        root = os.path.realpath(root)
        target = os.path.realpath(os.path.join(root, relative))
        shared = os.path.commonpath([root, target])
    except (ValueError, OSError):
        # A path the filesystem will not even look at: an embedded null byte,
        # a name too long, or two paths that cannot be compared. Each is a
        # containment this cannot establish, so it is not established.
        return None
    if shared != root:
        return None
    return target


def check_component(root, law, findings):
    path = resolve(root, law.get("component"))
    if path is None or not os.path.isfile(path):
        findings.append(
            Finding(law.label, "executes", "no component at %r" % law.get("component"))
        )
        return
    source = read(path)
    if source is None:
        findings.append(
            Finding(
                law.label, "executes", "%s is not readable text" % law.get("component")
            )
        )
        return
    declared = ID_IN_SOLIDITY.search(source)
    if declared is None:
        findings.append(
            Finding(law.label, "executes", "%s declares no id()" % law.get("component"))
        )
        return
    if declared.group(1) != law.id:
        findings.append(
            Finding(
                law.label,
                "executes",
                "%s declares id %r, the catalogue says %r"
                % (law.get("component"), declared.group(1), law.id),
            )
        )
    # Scanned over the whole component rather than a parsed `check` body. A
    # law component holds `id`, `statement` and `check` and nothing else, so
    # there is no legitimate revert anywhere in it, and a regex that had to
    # find the body first would stop checking whenever a law was formatted in
    # a way the regex did not expect. A check that silently stops checking is
    # worse than no check.
    reverting = REVERTS.search(scannable(source))
    if reverting:
        findings.append(
            Finding(
                law.label,
                "judges rather than reverts",
                "uses %s; under fail_on_revert = false a revert carries no "
                "verdict, so this reports nothing rather than a violation"
                % (reverting.group(1) or reverting.group(2)),
            )
        )


def check_specimen(root, law, findings):
    path = resolve(root, law.get("specimen"))
    if path is None or not os.path.isfile(path):
        findings.append(
            Finding(law.label, "catches", "no specimen at %r" % law.get("specimen"))
        )
        return
    source = read(path)
    if source is None:
        findings.append(
            Finding(
                law.label, "catches", "%s is not readable text" % law.get("specimen")
            )
        )
        return
    if BROKEN_MARKER not in source.lower():
        findings.append(
            Finding(
                law.label,
                "catches",
                "%s does not say it is %s; a broken credit contract that does "
                "not say so gets copied" % (law.get("specimen"), BROKEN_MARKER),
            )
        )


def check_counterexample(root, law, findings):
    path = resolve(root, law.get("counterexample"))
    if path is None or not os.path.isfile(path):
        findings.append(
            Finding(
                law.label,
                "has been reduced",
                "no counterexample at %r" % law.get("counterexample"),
            )
        )


def check_applicability(law, findings):
    found = law.get("applicability")
    if not isinstance(found, dict):
        findings.append(
            Finding(law.label, "says where it applies", "applicability is not an object")
        )
        return
    missing = [f for f in REQUIRED_APPLICABILITY if f not in found]
    if missing:
        findings.append(
            Finding(
                law.label,
                "says where it applies",
                "applicability has no %s" % ", ".join(missing),
            )
        )
        return
    if not isinstance(found["accounting_model"], str) or not found["accounting_model"].strip():
        findings.append(
            Finding(law.label, "says where it applies", "accounting_model is empty")
        )
    for field in ("assumes", "requires"):
        if not isinstance(found[field], list):
            findings.append(
                Finding(law.label, "says where it applies", "%s must be a list" % field)
            )


def check_bounds(law, findings):
    found = law.get("bounds")
    if found == EXACT:
        return
    if not isinstance(found, dict):
        findings.append(
            Finding(
                law.label,
                "bounds are justified",
                'bounds must be "%s" or an object naming its arithmetic' % EXACT,
            )
        )
        return
    for field in ("tolerance", "arithmetic"):
        value = found.get(field)
        if not isinstance(value, str) or not value.strip():
            findings.append(
                Finding(
                    law.label,
                    "bounds are justified",
                    "bounds has no %s; an epsilon chosen because it made a test "
                    "pass is the thing being refused" % field,
                )
            )


def check_family(catalogue, law, findings):
    if law.get("family") not in catalogue.families:
        findings.append(
            Finding(
                law.label,
                "is filed",
                "family %r is not one the catalogue declares" % law.get("family"),
            )
        )


def check_statement(law, findings):
    statement = law.get("statement")
    if not isinstance(statement, str) or not statement.strip():
        findings.append(Finding(law.label, "states itself", "statement is empty"))


def orphans(root, catalogue, findings):
    """Components on disk that no catalogue entry claims.

    The reverse of a missing component, and the easier mistake to make: a law
    written, compiled and never filed is a law nobody can find the applicability
    of.
    """
    laws_dir = os.path.join(root, "src", "laws")
    if not os.path.isdir(laws_dir):
        return
    claimed = {law.get("component") for law in catalogue.laws}
    for name in sorted(os.listdir(laws_dir)):
        if not name.endswith(".sol"):
            continue
        relative = os.path.join("src", "laws", name)
        if relative not in claimed:
            findings.append(
                Finding(relative, "is filed", "on disk and in no catalogue entry")
            )


def check(root, catalogue):
    """Every law, every part. Returns findings; an empty list is a pass."""
    findings = []
    for law in catalogue.laws:
        check_statement(law, findings)
        check_family(catalogue, law, findings)
        check_component(root, law, findings)
        check_specimen(root, law, findings)
        check_counterexample(root, law, findings)
        check_applicability(law, findings)
        check_bounds(law, findings)
    orphans(root, catalogue, findings)
    return findings
