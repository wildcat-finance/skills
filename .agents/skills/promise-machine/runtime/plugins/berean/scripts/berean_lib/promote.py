"""Promotion and rollback as records, never as edits.

The promotion chain is an append-only JSONL file beside the release. A
promotion names the evaluation report that earned it and repeats its
counts; a rollback names the release it restores and the reason. The chain
is replayed from the start on every read, so a reordered, gapped or forged
record is a refusal rather than a different history.
"""

import os

from . import BereanError
from . import canonical
from . import digests
from . import jsonio
from . import release as release_lib

FORMAT = "berean-promotion/v1"
ACTIONS = ("promote", "rollback")
COMMON_FIELDS = ("format", "sequence", "action", "release_digest", "note")
PROMOTE_FIELDS = COMMON_FIELDS + ("evals",)
ROLLBACK_FIELDS = COMMON_FIELDS + ("restored_digest", "reason")
EVALS_FIELDS = ("report_sha256", "cases_sha256", "thresholds", "cases", "passed", "failed")
THRESHOLD_FIELDS = ("failures_allowed",)
REPORT_FORMAT = "berean-eval-report/v1"
# The report names the corpus, the cases and the answers it graded, never
# the release digest: the release pins the report's bytes, so a report
# naming the release digest would be a cycle neither side could close.
REPORT_FIELDS = (
    "format",
    "corpus_digest",
    "cases_sha256",
    "answers_digest",
    "cases",
    "passed",
    "failed",
    "failures",
)
MAX_RECORDS = 1000


def validate_report(report):
    """The minimal evaluation report a promotion may rest on."""
    jsonio.require(report, REPORT_FIELDS, "eval report")
    if report["format"] != REPORT_FORMAT:
        raise BereanError(f"eval report format is {report['format']!r}, not {REPORT_FORMAT!r}")
    digests.check_hex(report["corpus_digest"], "report corpus digest")
    digests.check_hex(report["cases_sha256"], "report cases digest")
    digests.check_hex(report["answers_digest"], "report answers digest")
    cases = jsonio.whole_number(report["cases"], "report cases")
    passed = jsonio.whole_number(report["passed"], "report passed")
    failed = jsonio.whole_number(report["failed"], "report failed")
    if passed + failed != cases:
        raise BereanError(f"report counts disagree: {passed} passed + {failed} failed != {cases}")
    if not isinstance(report["failures"], list):
        raise BereanError("report failures is not a list")
    if len(report["failures"]) != failed:
        raise BereanError("report failures list does not carry one entry per failure")
    if cases == 0:
        raise BereanError("a report over zero cases proves nothing")
    return report


def answers_digest(document):
    """The listing digest over the release's pinned answers."""
    return digests.of_listing(
        (entry["path"], entry["sha256"]) for entry in document["answers"]
    )


def validate_record(record):
    if not isinstance(record, dict) or record.get("format") != FORMAT:
        raise BereanError("promotion record format is not berean-promotion/v1")
    action = record.get("action")
    if action not in ACTIONS:
        raise BereanError(f"unknown promotion action: {action!r}")
    fields = PROMOTE_FIELDS if action == "promote" else ROLLBACK_FIELDS
    jsonio.require(record, fields, f"{action} record")
    jsonio.whole_number(record["sequence"], "promotion sequence")
    digests.check_hex(record["release_digest"], "promotion release digest")
    jsonio.stated(record["note"], "promotion note")
    if action == "promote":
        evals = record["evals"]
        jsonio.require(evals, EVALS_FIELDS, "promotion evals")
        digests.check_hex(evals["report_sha256"], "promotion report digest")
        digests.check_hex(evals["cases_sha256"], "promotion cases digest")
        jsonio.require(evals["thresholds"], THRESHOLD_FIELDS, "promotion thresholds")
        allowed = jsonio.whole_number(evals["thresholds"]["failures_allowed"], "failures_allowed")
        cases = jsonio.whole_number(evals["cases"], "promotion cases")
        passed = jsonio.whole_number(evals["passed"], "promotion passed")
        failed = jsonio.whole_number(evals["failed"], "promotion failed")
        if passed + failed != cases or cases == 0:
            raise BereanError("promotion counts disagree or cover zero cases")
        if failed > allowed:
            raise BereanError(
                f"a promotion recording {failed} failure(s) over the allowed {allowed} is not a promotion"
            )
    else:
        digests.check_hex(record["restored_digest"], "restored release digest")
        jsonio.stated(record["reason"], "rollback reason")
        if record["restored_digest"] == record["release_digest"]:
            raise BereanError("a rollback that restores the release it supersedes says nothing")
    return record


def load_chain(path):
    """Replay the promotion chain; sequence gaps and reorders are refusals."""
    if os.path.islink(path):
        raise BereanError(f"refusing symlink: {path}")
    if not os.path.isfile(path):
        raise BereanError(f"not a regular file: {path}")
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                raise BereanError(f"blank line in promotion chain at line {number}")
            record = validate_record(jsonio.loads(line, f"promotion record at line {number}"))
            if record["sequence"] != number:
                raise BereanError(
                    f"promotion sequence {record['sequence']} at line {number}; the chain replays in order"
                )
            records.append(record)
    if len(records) > MAX_RECORDS:
        raise BereanError(f"promotion chain over the {MAX_RECORDS} record ceiling")
    return records


def state(chain, document):
    """What the chain says about this release document."""
    digest = document["release_digest"]
    current = None
    for record in chain:
        if record["action"] == "promote":
            if record["release_digest"] != digest:
                raise BereanError(
                    "a promotion in this release's chain names another release"
                )
            evals = document["evals"]
            if evals is None:
                raise BereanError("a promoted release declares its evaluation files")
            if record["evals"]["report_sha256"] != evals["report_sha256"]:
                raise BereanError("the promotion's report digest is not the release's")
            if record["evals"]["cases_sha256"] != evals["cases_sha256"]:
                raise BereanError("the promotion's cases digest is not the release's")
            current = digest
        else:
            if record["release_digest"] != digest:
                raise BereanError("a rollback in this release's chain supersedes another release")
            current = record["restored_digest"]
    if not chain:
        return "never promoted"
    if current == digest:
        return "active"
    return f"rolled back to {current}"


def append(path, record):
    """Land the whole chain again with the new record, staged and renamed."""
    validate_record(record)
    existing = load_chain(path) if os.path.exists(path) else []
    if record["sequence"] != len(existing) + 1:
        raise BereanError(
            f"next sequence is {len(existing) + 1}, not {record['sequence']}"
        )
    lines = [canonical.dumps(item) for item in existing + [record]]
    staging = path + ".staging"
    with open(staging, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    os.replace(staging, path)


def promote(directory, note):
    """Promote the release in `directory` on the evidence of its own report."""
    document = release_lib.load(directory)
    evals = document["evals"]
    if evals is None:
        raise BereanError("the release declares no evaluation files; nothing to promote on")
    report_path = os.path.join(directory, evals["report"])
    report_bytes = digests.read_file(report_path)
    if digests.of_bytes(report_bytes) != evals["report_sha256"]:
        raise BereanError("the eval report does not match the release's pinned digest")
    try:
        report_text = report_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise BereanError(f"eval report is not UTF-8: {error}") from error
    report = validate_report(jsonio.loads(report_text, "eval report"))
    if report["corpus_digest"] != document["corpus"]["corpus_digest"]:
        raise BereanError("the eval report grades another corpus")
    if report["cases_sha256"] != evals["cases_sha256"]:
        raise BereanError("the eval report grades other cases than the release declares")
    if report["answers_digest"] != answers_digest(document):
        raise BereanError("the eval report grades other answers than the release pins")
    # Promotion re-earns its evidence: the cases are graded again now, and
    # the fresh report must agree with the pinned one field for field. A
    # pinned report is a claim; the grading is the check. Imported here
    # because evals imports this module's report contract.
    from . import evals as evals_lib

    fresh, _ = evals_lib.run(directory)
    if fresh != report:
        raise BereanError(
            "grading the cases now does not reproduce the pinned report; refusing to promote"
        )
    chain_path = os.path.join(directory, release_lib.PROMOTIONS_FILE)
    existing = load_chain(chain_path) if os.path.exists(chain_path) else []
    record = {
        "format": FORMAT,
        "sequence": len(existing) + 1,
        "action": "promote",
        "release_digest": document["release_digest"],
        "note": note,
        "evals": {
            "report_sha256": evals["report_sha256"],
            "cases_sha256": evals["cases_sha256"],
            "thresholds": {"failures_allowed": 0},
            "cases": report["cases"],
            "passed": report["passed"],
            "failed": report["failed"],
        },
    }
    append(chain_path, record)
    return record


def rollback(directory, restored_digest, reason, note):
    """Record that this release stands down in favour of `restored_digest`."""
    document = release_lib.load(directory)
    digests.check_hex(restored_digest, "restored release digest")
    chain_path = os.path.join(directory, release_lib.PROMOTIONS_FILE)
    existing = load_chain(chain_path) if os.path.exists(chain_path) else []
    if state(existing, document) != "active":
        raise BereanError("only an active release rolls back; the chain says this one is not")
    record = {
        "format": FORMAT,
        "sequence": len(existing) + 1,
        "action": "rollback",
        "release_digest": document["release_digest"],
        "restored_digest": restored_digest,
        "reason": reason,
        "note": note,
    }
    append(chain_path, record)
    return record
