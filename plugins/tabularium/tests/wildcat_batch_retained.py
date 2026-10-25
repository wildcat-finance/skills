"""Retained-conformance resolver for the Wildcat withdrawal-batch join (#2087).

The resolver reads the two staging trees named by `ALEXANDRIA_WILDCAT_V1_STAGING`
and `ALEXANDRIA_WILDCAT_V2_STAGING`, checks each against the public example's
staging manifest, rebuilds each raw release through that example's builder,
builds and verifies a canonical release in a private temporary directory
outside the repository, and answers one boolean per generation. A generation
whose canonical release maps no `WithdrawalBatchPayment` row refuses by
generation name instead of passing, so the join is exercised on every
generation a `true` report covers. The observations it hands back carry raw
release identifiers, canonical and coverage digests and the generations that
passed: no path, count, address, transaction, block or amount from the
retained releases. The temporary directory is removed on success, on a false
result and on refusal.

`wildcat_batch_reports.py` may not import `os`, so the environment and
directory checks live here and that module imports only `retained_resolver`.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PLUGIN / "scripts"))

from tabularium_lib import verifier
from tabularium_lib.core import TabulariumError
from tabularium_lib.keccak import keccak256
from tabularium_lib.wildcat_release import build_wildcat_canonical
from tabularium_lib.wildcat_rules import BURN_JOIN_RULE
from wildcat_batch_fixtures import BATCH_SIGNATURES, PAYMENT
from wildcat_v3_reports import EvidenceUnavailable

BATCH_TOPICS = frozenset("0x" + keccak256(signature.encode()).hex() for signature in BATCH_SIGNATURES)
BURN_GAP = "attribution:withdrawal-batch-payment:burn"
UNCLAIMED_GAP = "attribution:transfer:unclaimed-burn"
SCRATCH_PREFIX = "tabularium-retained-conformance-"
RELEASE_SUFFIX = "-retained-conformance"
# The generated-artefact cap the release owner already enforces.
MAX_DOCUMENT_BYTES = 256 * 1024 * 1024
DIGEST_FILES = (("canonical_sha256", "events.jsonl"), ("coverage_sha256", "coverage.json"))


class RetainedGeneration:
    """One preserved generation: the variable naming its staging tree and the builder that rebuilds it."""

    def __init__(self, generation: str, variable: str, example: str) -> None:
        self.generation = generation
        self.variable = variable
        self.example = example

    def custody(self, environ) -> Path:
        """The named staging root, refused by variable name and never followed through a link."""
        value = environ.get(self.variable)
        if not value:
            raise EvidenceUnavailable(self.variable + " is not set")
        root = Path(value)
        if not root.is_absolute():
            raise EvidenceUnavailable(self.variable + " must name an absolute path")
        try:
            status = os.lstat(root)
        except OSError:
            raise EvidenceUnavailable(self.variable + " names an unreadable path") from None
        if stat.S_ISLNK(status.st_mode):
            raise EvidenceUnavailable(self.variable + " names a symlink")
        if not stat.S_ISDIR(status.st_mode):
            raise EvidenceUnavailable(self.variable + " names no directory")
        if not os.access(root, os.R_OK | os.X_OK):
            raise EvidenceUnavailable(self.variable + " names an unreadable directory")
        return root

    def rebuild(self, root: Path, output: Path) -> Path:
        """Check the tree against its manifest, rebuild the raw release and compare it with the pin."""
        module = example_module(self.example)
        if module.STAGING_ENV_VAR != self.variable:
            raise EvidenceUnavailable("public example names another staging variable")
        manifest = module.verify_preserved()["manifest"]
        module.verify_staging_tree(root, manifest)
        module.build(output)
        module.verify(output)
        return output / "release"


GENERATIONS = (
    RetainedGeneration("wildcat-v1", "ALEXANDRIA_WILDCAT_V1_STAGING", "wildcat-v1-interval-v0"),
    RetainedGeneration("wildcat-v2", "ALEXANDRIA_WILDCAT_V2_STAGING", "wildcat-v2-interval-v0"),
)


def example_module(example: str):
    """Load one public Alexandria example builder under a name of its own."""
    path = PLUGIN.parent / "alexandria" / "examples" / example / "demo.py"
    if path.is_symlink() or not path.is_file():
        raise EvidenceUnavailable("public example builder unavailable: " + example)
    name = "alexandria_example_" + example.replace("-", "_")
    module = sys.modules.get(name)
    if module is None:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return module


def private_scratch(repository: Path = REPO) -> Path:
    """A fresh private directory under the system temporary root; the caller removes it.

    The resolved path is returned because the release builder refuses a path
    with a symlink among its ancestors, and the system temporary root has one
    on macOS. The directory itself is the one `mkdtemp` created.
    """
    parent = Path(tempfile.gettempdir()).resolve()
    if parent == repository or parent.is_relative_to(repository):
        raise EvidenceUnavailable("temporary directory lies inside the repository")
    scratch = Path(tempfile.mkdtemp(prefix=SCRATCH_PREFIX)).resolve()
    os.chmod(scratch, 0o700)
    return scratch


def document(path: Path):
    if path.is_symlink() or not path.is_file():
        raise EvidenceUnavailable("canonical release document unavailable")
    if path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise EvidenceUnavailable("canonical release document exceeds the byte cap")
    with path.open("rb") as handle:
        return json.loads(handle.read())


def sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def release_conforms(source: dict, coverage: dict) -> bool:
    """True when the four batch signatures map and every payment and every market burn join once.

    The four signatures are absent from unsupported coverage, no row carries
    the burn gap or the unclaimed-burn gap, every payment joins under
    `adjacent-market-burn` with its burn carrying the same record back, and no
    burn is claimed twice.
    """
    unsupported = coverage["coverage"]["unsupported_events"]
    for key in unsupported:
        if any(signature in key for signature in BATCH_SIGNATURES):
            return False
        if key.startswith("decode:") and key.rsplit(":", 1)[-1] in BATCH_TOPICS:
            return False
    if unsupported.get(BURN_GAP, 0) or unsupported.get(UNCLAIMED_GAP, 0):
        return False
    gaps = {item["source_selector"]: set(item["gaps"]) for item in source["dispositions"]}
    records = {item["source_selector"]: item for item in source["mapping_records"]}
    claimed: dict[str, int] = {}
    for selector, record in records.items():
        if record["signature"] != PAYMENT:
            continue
        join = record.get("join")
        if not isinstance(join, dict) or join.get("rule") != BURN_JOIN_RULE:
            return False
        if join.get("primary_selector") != selector:
            return False
        companion = join.get("companion_selector")
        burn = records.get(companion)
        if burn is None or burn.get("join") != join:
            return False
        if BURN_GAP in gaps.get(selector, ()) or UNCLAIMED_GAP in gaps.get(companion, ()):
            return False
        claimed[companion] = claimed.get(companion, 0) + 1
    return all(count == 1 for count in claimed.values())


def require_payment(generation: str, source: dict) -> None:
    """Refuse a release with no payment row: every condition below would hold vacuously on it."""
    if not any(record["signature"] == PAYMENT for record in source["mapping_records"]):
        raise EvidenceUnavailable(generation + " maps no withdrawal-batch payment")


def verified(canonical: Path) -> bool:
    try:
        verifier.verify(canonical / "coverage.json")
    except TabulariumError:
        return False
    return True


def retained_conformance(generations=GENERATIONS, environ=None, witness=None):
    """Resolve the criterion over every generation; return (bool, observations).

    Custody is checked for every generation before any directory is created,
    so an absent or unreadable variable refuses by name with nothing to clean
    up. `witness`, when given, receives the scratch path so a test can confirm
    it is gone afterwards.
    """
    environ = os.environ if environ is None else environ
    roots = [(spec, spec.custody(environ)) for spec in generations]
    scratch = private_scratch()
    if witness is not None:
        witness(scratch)
    inputs, passed = [], []
    try:
        value = True
        for spec, root in roots:
            raw = spec.rebuild(root, scratch / (spec.generation + "-raw"))
            canonical = scratch / (spec.generation + "-canonical")
            build_wildcat_canonical(raw, canonical, spec.generation + RELEASE_SUFFIX)
            source = document(canonical / "source.json")
            coverage = document(canonical / "coverage.json")
            require_payment(spec.generation, source)
            conformant = verified(canonical) and release_conforms(source, coverage)
            inputs.append({"generation": spec.generation,
                           "raw_release_id": source["raw_release"]["release_id"],
                           **{field: sha256_file(canonical / name) for field, name in DIGEST_FILES}})
            if conformant:
                passed.append(spec.generation)
            value = value and conformant
    finally:
        shutil.rmtree(scratch)
    return value, {"inputs": inputs, "passed_generations": passed}


def retained_resolver(generations=GENERATIONS, witness=None):
    """A resolver the dispatch table can call with no arguments."""
    def resolve():
        return retained_conformance(generations, witness=witness)
    return resolve
