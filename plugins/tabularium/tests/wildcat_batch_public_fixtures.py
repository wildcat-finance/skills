"""Reproduce the constructed batch specimens through the native release owners.

Each specimen is one block of transactions in the pinned source emission
order: the generation's queue path, two payments to one expiry in one
transaction, expiry processing then closure, a repayment paying two unpaid
batches equal amounts, the V2 `closeMarket` sequence, and the five hostile
shapes that leave a named gap and no join. Every log is synthetic.
"""

import json
from pathlib import Path
import shutil
import tempfile

if __package__:
    from .test_wildcat_v3_release import constructed_release
    from .wildcat_batch_fixtures import HOSTILE_SPECIMENS, SOURCE_SPECIMENS, raws_for
    from .wildcat_v3_public_fixtures import inventory, observation
else:
    from test_wildcat_v3_release import constructed_release
    from wildcat_batch_fixtures import HOSTILE_SPECIMENS, SOURCE_SPECIMENS, raws_for
    from wildcat_v3_public_fixtures import inventory, observation

from tabularium_lib.core import canonical_json
from tabularium_lib import verifier
from tabularium_lib.wildcat_release import build_wildcat_canonical


VENUES = ("wildcat-v1", "wildcat-v2")
ROOT = "release"
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
# The five hostile shapes, in the order their transactions sit in each block.
HOSTILE_ORDER = ("burn-after-payment", "burn-value-changed", "burn-without-payment",
                 "two-burns-one-payment", "payment-without-burn")
# V2 closeMarket: the pending batch is paid, expired and closed; a one-second
# batch is created when the expiry equals the closing timestamp; MarketClosed
# follows. V1 closeMarket emits no batch event.
V2_CLOSE_MARKET = SOURCE_SPECIMENS["v2-close-market"] + [("market-closed", 1730000000)]
# Transaction names per generation, in block order; hostile names follow.
SOURCE_ORDER = {
    "wildcat-v1": ("v1-queue-first-batch", "queue-double-payment-same-expiry", "expired-paid-closed",
                   "repay-two-unpaid-equal-amounts"),
    "wildcat-v2": ("v2-queue-first-batch", "queue-double-payment-same-expiry", "expired-paid-closed",
                   "repay-two-unpaid-equal-amounts", "v2-close-market"),
}
TRANSACTIONS = {**SOURCE_SPECIMENS, **HOSTILE_SPECIMENS, "v2-close-market": V2_CLOSE_MARKET}


def specimen_names(venue):
    """The transaction names of one generation's specimen, in block order."""
    if venue not in VENUES:
        raise ValueError("unknown public Wildcat batch specimen generation")
    return SOURCE_ORDER[venue] + HOSTILE_ORDER


def specimen_transactions(venue):
    return [TRANSACTIONS[name] for name in specimen_names(venue)]


def specimen_raws(venue):
    """The raw logs of one generation's specimen, block-wide indices in emission order."""
    return raws_for(specimen_transactions(venue))


def release_id(venue):
    """Return the fixed release name, including its constructed qualification."""
    if venue not in VENUES:
        raise ValueError("unknown public Wildcat batch specimen generation")
    return venue + "-constructed-batches-v0"


def example_directory(venue):
    return EXAMPLES / (venue + "-batches-v0")


def build_batch_release(base, venue, release_name):
    """Build into an absent root and discard the original synthetic inputs."""
    raws = specimen_raws(venue)

    def replace_logs(document, journal, plan):
        response = json.loads(journal["records"][0]["response"])
        response["result"] = raws
        journal["records"][0]["response"] = canonical_json(response).decode()
        plan["release"]["name"] = venue + "-constructed-batches"

    with tempfile.TemporaryDirectory(prefix="tabularium-constructed-batches-") as temporary:
        raw = constructed_release(Path(temporary).resolve(), venue, replace_logs)
        build_wildcat_canonical(raw, Path(base), release_name)
    coverage = Path(base) / "coverage.json"
    verifier.verify(coverage)
    return coverage


def build_specimen(directory, venue):
    """Build the one closed root below an existing fixture folder."""
    directory = Path(directory)
    build_batch_release(directory / ROOT, venue, release_id(venue))
    return {ROOT: observation(directory / ROOT)}


def compare_specimen(published, rebuilt):
    """Require every release file and its bytes to match the published root."""
    expected = inventory(Path(published) / ROOT)
    actual = inventory(Path(rebuilt) / ROOT)
    if actual != expected:
        raise ValueError("rebuilt %s differs from the public batch specimen" % ROOT)
    for relative in expected:
        published_bytes = (Path(published) / ROOT / relative).read_bytes()
        rebuilt_bytes = (Path(rebuilt) / ROOT / relative).read_bytes()
        if published_bytes != rebuilt_bytes:
            raise ValueError("rebuilt %s/%s bytes differ" % (ROOT, relative))
    return {ROOT: observation(Path(rebuilt) / ROOT)}


def rebuild_example(venue, examples=EXAMPLES):
    """Rebuild fresh, compare every file, move the root, then verify offline."""
    published = Path(examples) / (venue + "-batches-v0")
    expected = json.loads((published / "expected.json").read_bytes())
    with tempfile.TemporaryDirectory(prefix="tabularium-" + venue + "-batches-") as temporary:
        base = Path(temporary).resolve()
        original = base / "original"
        original.mkdir()
        built = build_specimen(original, venue)
        if built != expected:
            raise ValueError("fresh fixture identities differ from expected.json")
        result = compare_specimen(published, original)
        moved = base / "moved"
        shutil.move(str(original / ROOT), moved)
        for path in moved.rglob("*"):
            if path.is_file():
                path.chmod(0o444)
        verifier.verify(moved / "coverage.json")
        shutil.rmtree(original)
        verifier.verify(moved / "coverage.json")
        print(canonical_json({"event": "wildcat.batch-specimen.reproduced", "venue": venue,
                              "roots": {ROOT: {key: result[ROOT][key] for key in
                                               ("release", "rows", "native_logs", "canonical_sha256")}}}).decode())
    return 0
