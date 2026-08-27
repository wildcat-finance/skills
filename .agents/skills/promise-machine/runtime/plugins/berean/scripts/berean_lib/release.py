"""Release manifests: one digested unit binding corpus, reads, answers,
rules and evaluation references.

A release directory holds exactly what its `release.json` declares: the
corpus manifest and tree, the preserved reads, the answer documents, the
evaluation files and the promotion chain beside them. `verify` runs the
specification's gates by name from bytes on disk. The release digest is
built from named fields rather than by deleting a key, so a field added to
the format without joining the identity is a test failure instead of a
silently uncovered digest.
"""

import os
import re

from . import BereanError
from . import answers as answers_lib
from . import canonical
from . import corpus as corpus_lib
from . import digests
from . import jsonio
from . import paths
from . import reads as reads_lib
from .corpus import Check

FORMAT = "berean-release/v1"
FIELDS = (
    "format",
    "release_version",
    "corpus",
    "reads",
    "answers",
    "question_families",
    "refusal_conditions",
    "rules",
    "allowlists",
    "evals",
    "retention",
    "release_digest",
)
IDENTITY_FIELDS = tuple(field for field in FIELDS if field != "release_digest")
CORPUS_FIELDS = ("path", "manifest", "manifest_sha256", "corpus_version", "corpus_digest")
READS_FIELDS = ("path", "sha256", "chain_id", "block_number", "block_hash", "source")
ANSWER_FIELDS = ("path", "sha256")
RULES_FIELDS = ("source_classes", "evidence_classes")
ALLOWLIST_FIELDS = ("chains", "contracts")
EVALS_FIELDS = ("cases", "cases_sha256", "report", "report_sha256")
RETENTION = ("none", "answers-only")
HASH32 = re.compile(r"^0x[0-9a-f]{64}$")
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")
ZERO_HASH = "0x" + "0" * 64
RELEASE_DOCUMENT = "release.json"
PROMOTIONS_FILE = "promotions.jsonl"


def release_digest(document):
    """The digest over the named identity fields, in canonical spelling."""
    identity = {field: document[field] for field in IDENTITY_FIELDS}
    return digests.of_bytes(canonical.encode(identity))


def validate(document):
    """Hold a release document to its closed tables and vocabularies."""
    jsonio.require(document, FIELDS, "release")
    if document["format"] != FORMAT:
        raise BereanError(f"release format is {document['format']!r}, not {FORMAT!r}")
    jsonio.stated(document["release_version"], "release_version")

    block = document["corpus"]
    jsonio.require(block, CORPUS_FIELDS, "release corpus")
    paths.usable(block["path"], "corpus path")
    paths.usable(block["manifest"], "corpus manifest path")
    digests.check_hex(block["manifest_sha256"], "corpus manifest digest")
    digests.check_hex(block["corpus_digest"], "corpus digest")
    jsonio.stated(block["corpus_version"], "corpus_version")

    reads = document["reads"]
    if reads is not None:
        jsonio.require(reads, READS_FIELDS, "release reads")
        paths.usable(reads["path"], "reads path")
        digests.check_hex(reads["sha256"], "reads digest")
        jsonio.whole_number(reads["chain_id"], "reads chain_id")
        jsonio.whole_number(reads["block_number"], "reads block_number")
        if not isinstance(reads["block_hash"], str) or not HASH32.match(reads["block_hash"]):
            raise BereanError(f"block_hash is not 0x-prefixed lowercase hex: {reads['block_hash']!r}")
        if reads["block_hash"] == ZERO_HASH:
            raise BereanError("block_hash is the zero hash")
        jsonio.stated(reads["source"], "reads source")

    if not isinstance(document["answers"], list) or not document["answers"]:
        raise BereanError("a release carries at least one answer")
    seen = set()
    for index, entry in enumerate(document["answers"]):
        jsonio.require(entry, ANSWER_FIELDS, f"answer entry {index}")
        paths.usable(entry["path"], f"answer path {index}")
        digests.check_hex(entry["sha256"], f"answer digest {index}")
        if entry["path"] in seen:
            raise BereanError(f"answer listed twice: {entry['path']}")
        seen.add(entry["path"])

    for name in ("question_families", "refusal_conditions"):
        values = document[name]
        if not isinstance(values, list) or not values:
            raise BereanError(f"{name} is empty; a release states its boundary")
        for value in values:
            jsonio.stated(value, name)

    rules = document["rules"]
    jsonio.require(rules, RULES_FIELDS, "release rules")
    if tuple(rules["source_classes"]) != answers_lib.SOURCE_CLASSES:
        raise BereanError("rules.source_classes is not the closed source-class vocabulary")
    if tuple(rules["evidence_classes"]) != reads_lib.EVIDENCE_CLASSES:
        raise BereanError("rules.evidence_classes is not the closed evidence-class vocabulary")

    allowlists = document["allowlists"]
    jsonio.require(allowlists, ALLOWLIST_FIELDS, "release allowlists")
    if not isinstance(allowlists["chains"], list):
        raise BereanError("allowlists.chains is not a list")
    for chain in allowlists["chains"]:
        jsonio.whole_number(chain, "allowlisted chain")
    if not isinstance(allowlists["contracts"], list):
        raise BereanError("allowlists.contracts is not a list")
    for contract in allowlists["contracts"]:
        if not isinstance(contract, str) or not ADDRESS.match(contract):
            raise BereanError(f"allowlisted contract is not a lowercase address: {contract!r}")

    evals = document["evals"]
    if evals is not None:
        jsonio.require(evals, EVALS_FIELDS, "release evals")
        paths.usable(evals["cases"], "eval cases path")
        paths.usable(evals["report"], "eval report path")
        digests.check_hex(evals["cases_sha256"], "eval cases digest")
        digests.check_hex(evals["report_sha256"], "eval report digest")

    if document["retention"] not in RETENTION:
        raise BereanError(f"undeclared retention: {document['retention']!r}")

    digests.check_hex(document["release_digest"], "release digest")
    if document["release_digest"] != release_digest(document):
        raise BereanError("release_digest does not match the identity fields")
    return document


def load(directory):
    document = jsonio.load(os.path.join(directory, RELEASE_DOCUMENT), RELEASE_DOCUMENT)
    return validate(document)


def declared_files(document):
    """Every path the release document claims, relative to its directory."""
    claimed = {RELEASE_DOCUMENT, document["corpus"]["manifest"]}
    if document["reads"] is not None:
        claimed.add(document["reads"]["path"])
    for entry in document["answers"]:
        claimed.add(entry["path"])
    if document["evals"] is not None:
        claimed.add(document["evals"]["cases"])
        claimed.add(document["evals"]["report"])
    return claimed


def _file_digest_matches(directory, relative, expected):
    data = digests.read_file(paths.resolve(directory, relative, relative))
    return digests.of_bytes(data) == expected


def _address_shaped(value):
    """Every address-shaped string anywhere in a params tree.

    Walked rather than scanned at the top level, because a filter object
    carries its address one level down and an allowlist that misses it is
    not an allowlist.
    """
    if isinstance(value, str):
        if ADDRESS.match(value):
            yield value
    elif isinstance(value, list):
        for item in value:
            yield from _address_shaped(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _address_shaped(item)


def verify(directory):
    """Run the release gates by name from bytes on disk; no repair."""
    checks = []
    try:
        document = load(directory)
        checks.append(Check("release-shape", True))
    except BereanError as error:
        return [Check("release-shape", False, str(error))]

    corpus_block = document["corpus"]
    detail = []
    manifest = None
    try:
        if not _file_digest_matches(directory, corpus_block["manifest"], corpus_block["manifest_sha256"]):
            detail.append("the corpus manifest does not match its pinned digest")
        manifest = corpus_lib.validate(
            jsonio.load(os.path.join(directory, corpus_block["manifest"]), "corpus manifest")
        )
        if manifest["corpus_digest"] != corpus_block["corpus_digest"]:
            detail.append("the manifest's corpus digest is not the release's")
        if manifest["corpus_version"] != corpus_block["corpus_version"]:
            detail.append("the manifest's corpus version is not the release's")
        corpus_root = paths.resolve(directory, corpus_block["path"], "corpus path")
        for result in corpus_lib.verify(manifest, corpus_root):
            if not result.passed:
                detail.append(f"{result.name}: {result.detail}")
    except BereanError as error:
        detail.append(str(error))
    checks.append(Check("release-corpus", not detail, "; ".join(detail)))

    records = {}
    reads_block = document["reads"]
    detail = []
    if reads_block is not None:
        try:
            if not _file_digest_matches(directory, reads_block["path"], reads_block["sha256"]):
                detail.append("the reads file does not match its pinned digest")
            records = reads_lib.load(paths.resolve(directory, reads_block["path"], "reads path"))
            if reads_block["chain_id"] not in document["allowlists"]["chains"]:
                detail.append(f"chain {reads_block['chain_id']} is not allowlisted")
        except BereanError as error:
            detail.append(str(error))
    checks.append(Check("release-reads", not detail, "; ".join(detail)))

    strays = []
    contracts = set(document["allowlists"]["contracts"])
    for key, record in sorted(records.items()):
        for param in _address_shaped(record["params"]):
            if param not in contracts:
                strays.append(f"{key[:12]}: {param}")
    checks.append(
        Check("release-allowlists", not strays, "; ".join(strays))
    )

    detail = []
    user_supplied = 0
    if manifest is not None:
        corpus_root = os.path.join(directory, corpus_block["path"])
        chain_id = reads_block["chain_id"] if reads_block else 0
        block_number = reads_block["block_number"] if reads_block else 0
        for entry in document["answers"]:
            try:
                if not _file_digest_matches(directory, entry["path"], entry["sha256"]):
                    detail.append(f"{entry['path']}: does not match its pinned digest")
                    continue
                answer = jsonio.load(os.path.join(directory, entry["path"]), entry["path"])
                results = answers_lib.check(
                    answer, manifest, corpus_root, records, chain_id, block_number
                )
                for result in results:
                    if not result.passed:
                        detail.append(f"{entry['path']}: {result.name} ({result.detail})")
                if answer["kind"] == "answer":
                    user_supplied += sum(
                        1
                        for sentence in answer["sentences"]
                        if sentence["source_class"] == "user_supplied"
                    )
            except BereanError as error:
                detail.append(f"{entry['path']}: {error}")
    else:
        detail.append("not checked; the corpus gate failed first")
    checks.append(Check("release-answers", not detail, "; ".join(detail)))

    retention_ok = not (document["retention"] == "none" and user_supplied)
    checks.append(
        Check(
            "release-retention",
            retention_ok,
            ""
            if retention_ok
            else f"retention is none but {user_supplied} user-supplied sentence(s) are retained in answers",
        )
    )

    detail = []
    evals_block = document["evals"]
    if evals_block is not None:
        try:
            if not _file_digest_matches(directory, evals_block["cases"], evals_block["cases_sha256"]):
                detail.append("the eval cases do not match their pinned digest")
            if not _file_digest_matches(directory, evals_block["report"], evals_block["report_sha256"]):
                detail.append("the eval report does not match its pinned digest")
        except BereanError as error:
            detail.append(str(error))
    checks.append(Check("release-evals", not detail, "; ".join(detail)))

    claimed = declared_files(document)
    strays = []
    for current, directories, files in os.walk(directory):
        directories.sort()
        for name in sorted(files):
            relative = os.path.relpath(os.path.join(current, name), directory).replace(os.sep, "/")
            if relative == PROMOTIONS_FILE:
                continue
            if relative.startswith(corpus_block["path"] + "/"):
                continue
            if relative not in claimed:
                strays.append(relative)
    checks.append(
        Check("release-components", not strays, f"undeclared: {', '.join(strays)}" if strays else "")
    )

    from . import promote as promote_lib

    detail = []
    state = "never promoted"
    chain_path = os.path.join(directory, PROMOTIONS_FILE)
    if os.path.exists(chain_path):
        try:
            chain = promote_lib.load_chain(chain_path)
            state = promote_lib.state(chain, document)
        except BereanError as error:
            detail.append(str(error))
    checks.append(Check("release-promotions", not detail, "; ".join(detail) or state))
    return checks


def build(directory, release_version, question_families, refusal_conditions,
          allowlists, retention, reads_context=None, evals_paths=None,
          corpus_path="corpus", manifest_path="corpus-manifest.json",
          reads_path="reads.jsonl", answers_path="answers"):
    """Assemble release.json over artefacts already in the directory.

    The corpus manifest, reads file, answer documents and eval files are
    read from disk and pinned as found; the document is validated and
    landed with one rename. Nothing here creates evidence, it only binds
    what exists.
    """
    manifest = corpus_lib.validate(
        jsonio.load(os.path.join(directory, manifest_path), "corpus manifest")
    )
    corpus_block = {
        "path": corpus_path,
        "manifest": manifest_path,
        "manifest_sha256": digests.of_file(os.path.join(directory, manifest_path)),
        "corpus_version": manifest["corpus_version"],
        "corpus_digest": manifest["corpus_digest"],
    }
    reads_block = None
    if reads_context is not None:
        reads_block = {
            "path": reads_path,
            "sha256": digests.of_file(os.path.join(directory, reads_path)),
            "chain_id": reads_context["chain_id"],
            "block_number": reads_context["block_number"],
            "block_hash": reads_context["block_hash"],
            "source": reads_context["source"],
        }
    answers_dir = os.path.join(directory, answers_path)
    entries = []
    if os.path.isdir(answers_dir):
        for name in sorted(os.listdir(answers_dir)):
            relative = f"{answers_path}/{name}"
            entries.append(
                {"path": relative, "sha256": digests.of_file(os.path.join(directory, relative))}
            )
    evals_block = None
    if evals_paths is not None:
        evals_block = {
            "cases": evals_paths["cases"],
            "cases_sha256": digests.of_file(os.path.join(directory, evals_paths["cases"])),
            "report": evals_paths["report"],
            "report_sha256": digests.of_file(os.path.join(directory, evals_paths["report"])),
        }
    document = {
        "format": FORMAT,
        "release_version": release_version,
        "corpus": corpus_block,
        "reads": reads_block,
        "answers": entries,
        "question_families": list(question_families),
        "refusal_conditions": list(refusal_conditions),
        "rules": {
            "source_classes": list(answers_lib.SOURCE_CLASSES),
            "evidence_classes": list(reads_lib.EVIDENCE_CLASSES),
        },
        "allowlists": {
            "chains": list(allowlists["chains"]),
            "contracts": list(allowlists["contracts"]),
        },
        "evals": evals_block,
        "retention": retention,
    }
    document["release_digest"] = release_digest(document)
    validate(document)
    jsonio.write_canonical(os.path.join(directory, RELEASE_DOCUMENT), document, canonical.dumps)
    return document
