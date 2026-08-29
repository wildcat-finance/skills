"""Bind one local ``berean-release/v1`` tree without running Berean.

The adapter copies no producer verdict into Ariadne.  It checks the closed wire
format and every byte identity it projects, then emits a grounded-agent statement
whose subjects are the exact files read.  Reads are descriptor-based, bounded and
stable; the release tree is compared before and after capture; output is checked
outside that tree and replaced atomically only after in-memory verification.
"""

import hashlib
import json
import os
import stat
import unicodedata

from .. import envelope, gates, registry, safejson, verify
from ..predicates import grounded_agent as predicate
from . import dataset, state_fixture, tree

CaptureError = tree.CaptureError

MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_COMPONENT_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_PREVIOUS_BYTES = 16 * 1024 * 1024
MAX_RELEASE_FILES = predicate.MAX_SUBJECTS
MAX_DIAGNOSTIC_FIELDS = 4
MAX_DIAGNOSTIC_FIELD_CHARS = 96

CORPUS_FORMAT = "berean-corpus/v1"
CORPUS_FIELDS = ("format", "corpus_version", "files", "corpus_digest")
CORPUS_FILE_FIELDS = ("path", "bytes", "sha256")

PROMOTION_COMMON_FIELDS = (
    "format",
    "sequence",
    "action",
    "release_digest",
    "note",
)
PROMOTION_PROMOTE_FIELDS = PROMOTION_COMMON_FIELDS + ("evals",)
PROMOTION_ROLLBACK_FIELDS = PROMOTION_COMMON_FIELDS + (
    "restored_digest",
    "reason",
)
PROMOTION_EVALS_FIELDS = (
    "report_sha256",
    "cases_sha256",
    "thresholds",
    "cases",
    "passed",
    "failed",
)
PROMOTION_THRESHOLD_FIELDS = ("failures_allowed",)


class _DuplicateKey(ValueError):
    pass


class _NonJSONNumber(ValueError):
    pass


def _duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise _DuplicateKey()
        out[key] = value
    return out


def _number(value):
    raise _NonJSONNumber(value)


def _parse_json(raw, what):
    """Parse one bounded JSON object under Berean's integer-only contract."""
    try:
        safejson.check_depth(raw, MAX_JSON_DEPTH)
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_duplicates,
            parse_float=_number,
            parse_constant=_number,
            parse_int=safejson.bounded_json_integer,
        )
    except _DuplicateKey:
        raise CaptureError(
            "%s has a duplicate key; two readers could choose different values"
            % what
        ) from None
    except _NonJSONNumber:
        raise CaptureError("%s carries a float or non-JSON number" % what) from None
    except UnicodeDecodeError as error:
        raise CaptureError("%s is not UTF-8 at byte %d" % (what, error.start)) from None
    except safejson.InputError as error:
        raise CaptureError("%s: %s" % (what, gates.one_line(str(error)))) from None
    except json.JSONDecodeError as error:
        raise CaptureError(
            "%s is not JSON at line %d column %d"
            % (what, error.lineno, error.colno)
        ) from None
    if not isinstance(value, dict):
        raise CaptureError("%s is not an object" % what)
    return value


def _closed(value, fields, what):
    if not isinstance(value, dict):
        raise CaptureError("%s is not an object" % what)
    missing = sorted(set(fields) - set(value))
    unknown = sorted(set(value) - set(fields))
    if missing:
        raise CaptureError("%s is missing %s" % (what, ", ".join(missing)))
    if unknown:
        preview = ", ".join(
            _display(field, MAX_DIAGNOSTIC_FIELD_CHARS)
            for field in unknown[:MAX_DIAGNOSTIC_FIELDS]
        )
        if len(unknown) > MAX_DIAGNOSTIC_FIELDS:
            preview += ", ..."
        raise CaptureError(
            "%s carries %d undeclared field(s): %s"
            % (what, len(unknown), preview)
        )
    return value


def _array(value, what, maximum, nonempty=False):
    if not isinstance(value, list):
        raise CaptureError("%s is not an array" % what)
    if nonempty and not value:
        raise CaptureError("%s is empty" % what)
    if len(value) > maximum:
        raise CaptureError(
            "%s has %d entries, over the %d entry ceiling"
            % (what, len(value), maximum)
        )
    return value


def _whole(value, what):
    if not predicate.whole_number(value) or value < 0:
        raise CaptureError("%s is not a non-negative whole number" % what)
    return value


def _digest(value, what):
    if not predicate.sha256(value):
        raise CaptureError("%s is not 64 lowercase sha256 hex" % what)
    return value


def _stated(value, what, portable=False):
    valid = predicate.portable_name(value) if portable else predicate.stated(value)
    if valid and any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        valid = False
    if not valid:
        adjective = "portable bounded" if portable else "bounded stated"
        raise CaptureError("%s is not a %s string" % (what, adjective))
    return value


def _unique_strings(value, what):
    values = _array(value, what, predicate.MAX_POLICY_ITEMS, nonempty=True)
    seen = set()
    for index, item in enumerate(values):
        _stated(item, "%s entry %d" % (what, index + 1))
        settled = unicodedata.normalize("NFC", item)
        if settled in seen:
            raise CaptureError("%s repeats an entry after Unicode normalisation" % what)
        seen.add(settled)
    return list(values)


def _listing_digest(entries):
    lines = []
    for path, digest in sorted(entries):
        _digest(digest, "corpus digest for %s" % _display(path))
        lines.append("%s\0%s\n" % (path, digest))
    return hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def _canonical_digest(value):
    try:
        raw = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    except UnicodeEncodeError:
        raise CaptureError(
            "canonical JSON contains a non-Unicode-scalar string"
        ) from None
    return hashlib.sha256(raw).hexdigest()


def _display(value, limit=300):
    """Bound one attacker-chosen path before it reaches a one-line diagnostic."""
    cropped = isinstance(value, str) and len(value) > limit
    sample = value[:limit] if cropped else value
    shown = ascii(sample)
    if cropped or len(shown) > limit:
        return shown[: limit - 3] + "..."
    return shown


def _metadata(path):
    try:
        found = os.stat(path, follow_symlinks=False)
    except OSError:
        raise CaptureError("release entry changed while it was inventoried") from None
    return (
        found.st_dev,
        found.st_ino,
        found.st_mode,
        found.st_size,
        found.st_mtime_ns,
        found.st_ctime_ns,
    )


def _inventory(root):
    entries = tree.files(root, "Berean release")
    if len(entries) > MAX_RELEASE_FILES:
        raise CaptureError(
            "Berean release has %d files, over the %d file ceiling"
            % (len(entries), MAX_RELEASE_FILES)
        )
    out = {}
    for relative, absolute in entries:
        portable = relative.replace(os.sep, "/")
        if not predicate.usable_path(portable):
            raise CaptureError(
                "release entry %s is not a portable relative path"
                % _display(portable)
            )
        settled = unicodedata.normalize("NFC", portable)
        if settled in out:
            raise CaptureError(
                "release entries collide after Unicode normalisation: %s"
                % _display(portable)
            )
        out[settled] = (portable, absolute, _metadata(absolute))
    return out


def _same_inventory(before, after):
    if set(before) != set(after):
        return False
    return all(
        before[key][0] == after[key][0] and before[key][2] == after[key][2]
        for key in before
    )


def _release_root(path):
    if not path:
        raise CaptureError("--release is required")
    lexical = os.path.abspath(path)
    if os.path.islink(lexical):
        raise CaptureError("--release is a symlink; name the release directory itself")
    return tree.confined(path, "release")


def _output_alias(root, output, inventory):
    if not output:
        raise CaptureError("--output is required; capture never mutates the release")
    absolute = os.path.abspath(output)
    resolved = os.path.realpath(absolute)
    try:
        shared = os.path.commonpath([root, resolved])
    except ValueError:
        shared = None
    if shared == root:
        raise CaptureError("--output resolves inside the Berean release")
    if os.path.lexists(absolute):
        if os.path.islink(absolute):
            raise CaptureError("--output is a symlink")
        try:
            target = os.stat(absolute, follow_symlinks=False)
        except OSError:
            raise CaptureError("cannot inspect --output") from None
        if not stat.S_ISREG(target.st_mode):
            raise CaptureError("--output exists and is not a regular file")
        identities = {(entry[2][0], entry[2][1]) for entry in inventory.values()}
        if (target.st_dev, target.st_ino) in identities:
            raise CaptureError("--output is a hard-link alias of a release file")
    parent = os.path.realpath(os.path.dirname(absolute) or ".")
    if not os.path.isdir(parent):
        raise CaptureError("--output parent is not a directory")


class _Paths(object):
    def __init__(self):
        self._files = {}

    def file(self, value, what):
        if not predicate.usable_path(value):
            raise CaptureError("%s is not a portable release-relative path" % what)
        settled = unicodedata.normalize("NFC", value)
        if settled in self._files:
            raise CaptureError(
                "%s repeats the file declared as %s"
                % (what, self._files[settled])
            )
        self._files[settled] = what
        return value

    @property
    def values(self):
        return set(self._files)


class _Reader(object):
    def __init__(self, root):
        self.root = root
        self.total = 0

    def read(self, relative, name, what, maximum=None):
        if maximum is None:
            maximum = MAX_COMPONENT_BYTES
        digest, size, raw = state_fixture.read_component(
            self.root, relative, what, maximum, keep_bytes=True
        )
        self.total += size
        if self.total > MAX_TOTAL_BYTES:
            raise CaptureError(
                "release components total more than the %d byte ceiling"
                % MAX_TOTAL_BYTES
            )
        return {
            "name": name,
            "path": relative,
            "sha256": digest["sha256"],
            "bytes": size,
        }, raw

    def json(self, relative, name, what):
        component, raw = self.read(relative, name, what, MAX_JSON_BYTES)
        return component, _parse_json(raw, what)


def _match(component, expected, what, expected_bytes=None):
    if component["sha256"] != expected:
        raise CaptureError("%s does not match its declared sha256" % what)
    if expected_bytes is not None and component["bytes"] != expected_bytes:
        raise CaptureError("%s does not match its declared byte count" % what)
    return component


def _release_shape(document, paths):
    _closed(document, predicate.BEREAN_RELEASE_FIELDS, "release.json")
    if document["format"] != predicate.BEREAN_FORMAT:
        raise CaptureError("release.json format is not berean-release/v1")
    _stated(document["release_version"], "release_version", portable=True)
    _digest(document["release_digest"], "release_digest")

    corpus = _closed(document["corpus"], predicate.BEREAN_CORPUS_FIELDS, "release corpus")
    if not predicate.usable_path(corpus["path"]):
        raise CaptureError("release corpus path is not portable and relative")
    paths.file(corpus["manifest"], "release corpus manifest")
    _digest(corpus["manifest_sha256"], "release corpus manifest digest")
    _stated(corpus["corpus_version"], "release corpus_version", portable=True)
    _digest(corpus["corpus_digest"], "release corpus digest")

    reads = document["reads"]
    if reads is not None:
        _closed(reads, predicate.BEREAN_READS_FIELDS, "release reads")
        paths.file(reads["path"], "release reads path")
        _digest(reads["sha256"], "release reads digest")
        _whole(reads["chain_id"], "release reads chain_id")
        _whole(reads["block_number"], "release reads block_number")
        if not predicate.hash32(reads["block_hash"]):
            raise CaptureError("release reads block_hash is not a non-zero lowercase hash")
        _stated(reads["source"], "release reads source")

    answers = _array(
        document["answers"], "release answers", predicate.MAX_COMPONENTS, nonempty=True
    )
    for index, answer in enumerate(answers):
        label = "release answer %d" % (index + 1)
        _closed(answer, predicate.BEREAN_ANSWER_FIELDS, label)
        paths.file(answer["path"], "%s path" % label)
        _digest(answer["sha256"], "%s digest" % label)

    question_families = _unique_strings(
        document["question_families"], "release question_families"
    )
    refusal_conditions = _unique_strings(
        document["refusal_conditions"], "release refusal_conditions"
    )

    rules = _closed(document["rules"], predicate.BEREAN_RULES_FIELDS, "release rules")
    if tuple(rules["source_classes"]) != predicate.BEREAN_SOURCE_CLASSES:
        raise CaptureError("release source_classes changes the closed Berean vocabulary")
    if tuple(rules["evidence_classes"]) != predicate.BEREAN_EVIDENCE_CLASSES:
        raise CaptureError("release evidence_classes changes the closed Berean vocabulary")

    allowlists = _closed(
        document["allowlists"], predicate.BEREAN_ALLOWLIST_FIELDS, "release allowlists"
    )
    chains = _array(
        allowlists["chains"], "release allowlisted chains", predicate.MAX_POLICY_ITEMS
    )
    for index, chain in enumerate(chains):
        _whole(chain, "allowlisted chain %d" % (index + 1))
    contracts = _array(
        allowlists["contracts"],
        "release allowlisted contracts",
        predicate.MAX_POLICY_ITEMS,
    )
    for index, contract in enumerate(contracts):
        if not isinstance(contract, str) or not predicate.ADDRESS.fullmatch(contract):
            raise CaptureError("allowlisted contract %d is not a lowercase address" % (index + 1))

    evals = document["evals"]
    if evals is not None:
        _closed(evals, predicate.BEREAN_EVALS_FIELDS, "release evals")
        paths.file(evals["cases"], "release eval cases path")
        paths.file(evals["report"], "release eval report path")
        _digest(evals["cases_sha256"], "release eval cases digest")
        _digest(evals["report_sha256"], "release eval report digest")

    if document["retention"] not in predicate.BEREAN_RETENTION:
        raise CaptureError("release retention is outside the closed Berean vocabulary")

    identity = {field: document[field] for field in predicate.BEREAN_IDENTITY_FIELDS}
    if _canonical_digest(identity) != document["release_digest"]:
        raise CaptureError("release_digest does not match the canonical identity fields")

    return question_families, refusal_conditions


def _corpus(reader, document, paths):
    block = document["corpus"]
    manifest_component, manifest = reader.json(
        block["manifest"], "corpus manifest", "corpus manifest"
    )
    _match(manifest_component, block["manifest_sha256"], "corpus manifest")
    _closed(manifest, CORPUS_FIELDS, "corpus manifest")
    if manifest["format"] != CORPUS_FORMAT:
        raise CaptureError("corpus manifest format is not berean-corpus/v1")
    _stated(manifest["corpus_version"], "corpus manifest version", portable=True)
    if manifest["corpus_version"] != block["corpus_version"]:
        raise CaptureError("corpus manifest version is not the release version")
    _digest(manifest["corpus_digest"], "corpus manifest digest")
    if manifest["corpus_digest"] != block["corpus_digest"]:
        raise CaptureError("corpus manifest digest is not the release corpus digest")

    files = _array(
        manifest["files"], "corpus manifest files", predicate.MAX_COMPONENTS, nonempty=True
    )
    listed = []
    components = []
    previous_path = None
    for index, entry in enumerate(files):
        label = "corpus file %d" % (index + 1)
        _closed(entry, CORPUS_FILE_FIELDS, label)
        relative = entry["path"]
        if not predicate.usable_path(relative):
            raise CaptureError("%s path is not portable and relative" % label)
        if previous_path is not None and relative <= previous_path:
            raise CaptureError("corpus manifest file paths are not strictly sorted")
        previous_path = relative
        _whole(entry["bytes"], "%s bytes" % label)
        if entry["bytes"] > MAX_COMPONENT_BYTES:
            raise CaptureError("%s is over the per-file byte ceiling" % label)
        _digest(entry["sha256"], "%s digest" % label)
        full = "%s/%s" % (block["path"], relative)
        paths.file(full, "%s release path" % label)
        component, _ = reader.read(full, "corpus component %d" % (index + 1), label)
        _match(component, entry["sha256"], label, entry["bytes"])
        components.append(component)
        listed.append((relative, entry["sha256"]))
    if _listing_digest(listed) != manifest["corpus_digest"]:
        raise CaptureError("corpus_digest does not match the manifest file listing")
    return manifest_component, components


def _close_corpus_subtree(corpus_path, components, inventory):
    """Require the manifest to own every file beneath ``corpus.path``."""
    prefix = unicodedata.normalize("NFC", corpus_path) + "/"
    expected = {
        unicodedata.normalize("NFC", component["path"])
        for component in components
    }
    actual = {path for path in inventory if path.startswith(prefix)}
    if actual == expected:
        return
    extra = sorted(actual - expected)
    if extra:
        raise CaptureError(
            "corpus subtree holds file(s) absent from its manifest: %s"
            % ", ".join(_display(path) for path in extra[:8])
        )
    missing = sorted(expected - actual)
    raise CaptureError(
        "corpus subtree is missing manifest file(s): %s"
        % ", ".join(_display(path) for path in missing[:8])
    )


def _promotion_record(record, line, document):
    if record.get("format") != predicate.BEREAN_PROMOTION_FORMAT:
        raise CaptureError("promotion record %d has another format" % line)
    action = record.get("action")
    if action not in predicate.BEREAN_PROMOTION_ACTIONS:
        raise CaptureError("promotion record %d has an unknown action" % line)
    fields = (
        PROMOTION_PROMOTE_FIELDS if action == "promote" else PROMOTION_ROLLBACK_FIELDS
    )
    _closed(record, fields, "promotion record %d" % line)
    if _whole(record["sequence"], "promotion sequence") != line:
        raise CaptureError("promotion sequence is gapped or reordered at line %d" % line)
    if record["sequence"] < 1:
        raise CaptureError("promotion sequence starts below one")
    _digest(record["release_digest"], "promotion release digest")
    if record["release_digest"] != document["release_digest"]:
        raise CaptureError("promotion record %d names another release" % line)
    _stated(record["note"], "promotion note")

    if action == "promote":
        if document["evals"] is None:
            raise CaptureError("a promotion requires release evaluation files")
        evals = _closed(record["evals"], PROMOTION_EVALS_FIELDS, "promotion evals")
        _digest(evals["report_sha256"], "promotion report digest")
        _digest(evals["cases_sha256"], "promotion cases digest")
        if evals["report_sha256"] != document["evals"]["report_sha256"]:
            raise CaptureError("promotion report digest is not the release report")
        if evals["cases_sha256"] != document["evals"]["cases_sha256"]:
            raise CaptureError("promotion cases digest is not the release cases")
        thresholds = _closed(
            evals["thresholds"], PROMOTION_THRESHOLD_FIELDS, "promotion thresholds"
        )
        allowed = _whole(thresholds["failures_allowed"], "promotion failures_allowed")
        cases = _whole(evals["cases"], "promotion cases")
        passed = _whole(evals["passed"], "promotion passed")
        failed = _whole(evals["failed"], "promotion failed")
        if cases == 0 or passed + failed != cases or failed > allowed:
            raise CaptureError("promotion evaluation counts or threshold do not permit promotion")
        return document["release_digest"]

    _digest(record["restored_digest"], "rollback restored digest")
    _stated(record["reason"], "rollback reason")
    if line == 1:
        raise CaptureError("a rollback cannot be the first promotion record")
    if record["restored_digest"] == document["release_digest"]:
        raise CaptureError("rollback restores the release it supersedes")
    return record["restored_digest"]


def _promotions(reader, document, paths, present):
    if not present:
        return None
    paths.file(predicate.BEREAN_PROMOTIONS_FILE, "promotion chain")
    component, raw = reader.read(
        predicate.BEREAN_PROMOTIONS_FILE,
        "promotion chain",
        "promotion chain",
        MAX_JSON_BYTES,
    )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CaptureError("promotion chain is not UTF-8 at byte %d" % error.start) from None
    # JSONL uses literal LF records. ``str.splitlines`` also treats U+2028,
    # U+2029 and several control characters as boundaries, which would accept
    # two records where Berean's line reader sees one invalid JSON document.
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines:
        raise CaptureError("promotion chain is empty")
    if len(lines) > predicate.BEREAN_MAX_PROMOTION_RECORDS:
        raise CaptureError("promotion chain is over the record ceiling")
    terminal = None
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            raise CaptureError("promotion chain has a blank line at %d" % number)
        record = _parse_json(line.encode("utf-8"), "promotion record %d" % number)
        target = _promotion_record(record, number, document)
        terminal = {
            "sequence": number,
            "action": record["action"],
            "target_release_digest": target,
        }
    return {
        "component": component,
        "format": predicate.BEREAN_PROMOTION_FORMAT,
        "terminal": terminal,
    }


def _external_document(path):
    absolute = os.path.abspath(path)
    root, name = os.path.split(absolute)
    if not name:
        raise CaptureError("--previous does not name a file")
    _, _, raw = state_fixture.read_component(
        root or ".", name, "previous statement", MAX_PREVIOUS_BYTES, keep_bytes=True
    )
    try:
        document = envelope.read(
            raw, safejson.loader(MAX_PREVIOUS_BYTES, MAX_JSON_DEPTH)
        )
    except (envelope.EnvelopeError, safejson.InputError, ValueError) as error:
        raise CaptureError(
            "--previous is not a bounded Ariadne statement: %s"
            % gates.one_line(str(error))
        ) from None
    if document.statement.predicate_type != predicate.TYPE:
        raise CaptureError("--previous is not a grounded-agent/v1 statement")
    report = verify.report(document, registry.DEFAULT)
    if not report.ok or not report.predicate_gates_checked:
        failed = next((gate for gate in report.ordered if not gate.passed), None)
        label = failed.name if failed is not None else "predicate checks"
        raise CaptureError("--previous does not verify at %s" % label)
    return document


def _comparison(name, release_digest, previous, first_capture_reason):
    current = {
        "name": unicodedata.normalize("NFC", _stated(name, "--name", portable=True)),
        "release_digest": release_digest,
    }
    if previous:
        if first_capture_reason is not None:
            raise CaptureError(
                "--first-capture-reason is only for a capture without --previous"
            )
        document = _external_document(previous)
        baseline = document.statement.predicate["comparison"]["current"]
        if baseline["release_digest"] == release_digest:
            raise CaptureError("--previous and current name the same semantic release")
        return {
            "baseline": dict(baseline),
            "current": current,
            "first_capture_reason": None,
        }
    _stated(first_capture_reason, "--first-capture-reason")
    return {
        "baseline": None,
        "current": current,
        "first_capture_reason": first_capture_reason,
    }


def _self_verify(statement):
    try:
        raw = (json.dumps(statement, indent=2, ensure_ascii=False) + "\n").encode(
            "utf-8"
        )
    except UnicodeEncodeError:
        raise CaptureError(
            "constructed statement contains a non-Unicode-scalar string"
        ) from None
    try:
        document = envelope.read(raw, safejson.loader(len(raw) + 1, MAX_JSON_DEPTH))
        report = verify.report(document, registry.DEFAULT)
    except (envelope.EnvelopeError, safejson.InputError, ValueError) as error:
        raise CaptureError(
            "constructed statement could not be read back: %s"
            % gates.one_line(str(error))
        ) from None
    if not report.ok or not report.predicate_gates_checked or report.unchecked:
        failed = next((gate for gate in report.ordered if not gate.passed), None)
        if failed is not None:
            raise CaptureError(
                "constructed statement failed self-verification at %s: %s"
                % (failed.name, gates.one_line(failed.detail))
            )
        raise CaptureError("constructed statement left predicate checks unchecked")
    return statement


def capture(
    release,
    name,
    producer_tool,
    producer_version,
    producer_command,
    output,
    previous=None,
    first_capture_reason=None,
):
    """Read one closed Berean release into a self-verifying statement."""
    _stated(producer_tool, "--producer-tool", portable=True)
    _stated(producer_version, "--producer-version", portable=True)
    if (
        not isinstance(producer_command, (list, tuple))
        or not producer_command
        or len(producer_command) > predicate.MAX_COMMAND_WORDS
    ):
        raise CaptureError(
            "--producer-command needs 1 to %d bounded argv words"
            % predicate.MAX_COMMAND_WORDS
        )
    for index, word in enumerate(producer_command):
        _stated(word, "--producer-command word %d" % (index + 1))

    root = _release_root(release)
    before = _inventory(root)
    _output_alias(root, output, before)
    reader = _Reader(root)
    declared = _Paths()
    declared.file(predicate.BEREAN_RELEASE_DOCUMENT, "release document")

    release_component, document = reader.json(
        predicate.BEREAN_RELEASE_DOCUMENT,
        "Berean release document",
        "release.json",
    )
    question_families, refusal_conditions = _release_shape(document, declared)
    manifest_component, corpus_components = _corpus(reader, document, declared)
    _close_corpus_subtree(document["corpus"]["path"], corpus_components, before)

    reads_component = None
    if document["reads"] is not None:
        reads_component, _ = reader.read(
            document["reads"]["path"], "block-bound reads", "release reads"
        )
        _match(reads_component, document["reads"]["sha256"], "release reads")

    answer_components = []
    for index, answer in enumerate(document["answers"]):
        component, _ = reader.read(
            answer["path"], "answer %d" % (index + 1), "release answer %d" % (index + 1)
        )
        _match(component, answer["sha256"], "release answer %d" % (index + 1))
        answer_components.append(component)

    evaluation_components = None
    if document["evals"] is not None:
        cases, _ = reader.read(
            document["evals"]["cases"], "evaluation cases", "evaluation cases"
        )
        report, _ = reader.read(
            document["evals"]["report"], "evaluation report", "evaluation report"
        )
        _match(cases, document["evals"]["cases_sha256"], "evaluation cases")
        _match(report, document["evals"]["report_sha256"], "evaluation report")
        evaluation_components = {"cases": cases, "report": report}

    promotion_key = unicodedata.normalize("NFC", predicate.BEREAN_PROMOTIONS_FILE)
    promotion = _promotions(reader, document, declared, promotion_key in before)

    expected = declared.values
    actual = set(before)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing:
            raise CaptureError(
                "release is missing declared file(s): %s"
                % ", ".join(_display(path) for path in missing[:8])
            )
        raise CaptureError(
            "release holds undeclared file(s): %s"
            % ", ".join(_display(path) for path in extra[:8])
        )

    after = _inventory(root)
    if not _same_inventory(before, after):
        raise CaptureError("Berean release changed while it was captured")
    _output_alias(root, output, after)

    given_reads = None
    if reads_component is not None:
        reads = document["reads"]
        given_reads = {
            "component": reads_component,
            "chain_id": reads["chain_id"],
            "block_number": reads["block_number"],
            "block_hash": reads["block_hash"],
            "source": reads["source"],
        }

    body = {
        "release": {
            "format": document["format"],
            "release_version": document["release_version"],
            "release_digest": document["release_digest"],
            "document": release_component,
        },
        "given": {
            "corpus": {
                "path": document["corpus"]["path"],
                "corpus_version": document["corpus"]["corpus_version"],
                "corpus_digest": document["corpus"]["corpus_digest"],
                "manifest": manifest_component,
                "components": corpus_components,
            },
            "reads": given_reads,
            "reads_absence_reason": (
                None
                if given_reads is not None
                else "the Berean release declares no preserved reads"
            ),
        },
        "produced": {
            "answers": answer_components,
            "evaluations": evaluation_components,
            "evaluations_absence_reason": (
                None
                if evaluation_components is not None
                else "the Berean release declares no evaluation files"
            ),
            "promotion": promotion,
            "promotion_absence_reason": (
                None
                if promotion is not None
                else "the Berean release has no promotion chain and was never promoted"
            ),
        },
        "policy": {
            "question_families": question_families,
            "refusal_conditions": refusal_conditions,
            "rules": dict(document["rules"]),
            "allowlists": dict(document["allowlists"]),
            "retention": document["retention"],
        },
        "adapter": {
            "tool": producer_tool,
            "tool_version": producer_version,
            "command": list(producer_command),
            "parameters_digest": {"sha256": _canonical_digest({})},
        },
        "comparison": _comparison(
            name, document["release_digest"], previous, first_capture_reason
        ),
        "claims": [],
        "commands": [],
    }

    components = [release_component, manifest_component]
    components.extend(corpus_components)
    if reads_component is not None:
        components.append(reads_component)
    components.extend(answer_components)
    if evaluation_components is not None:
        components.extend(
            [evaluation_components["cases"], evaluation_components["report"]]
        )
    if promotion is not None:
        components.append(promotion["component"])

    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {"name": entry["name"], "digest": {"sha256": entry["sha256"]}}
            for entry in components
        ],
        "predicateType": predicate.TYPE,
        "predicate": body,
    }
    return _self_verify(statement)


def write(path, statement, release):
    """Self-verify and atomically replace one output outside the release."""
    _self_verify(statement)
    root = _release_root(release)
    inventory = _inventory(root)
    _output_alias(root, path, inventory)
    body = json.dumps(statement, indent=2, ensure_ascii=False) + "\n"
    dataset.write(path, body)
