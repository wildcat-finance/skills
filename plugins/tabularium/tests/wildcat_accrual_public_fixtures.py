"""Reproduce the constructed accrual specimens through the native release owners.

Each specimen is one block of three transactions, the same in both
generations, because the pinned V1 and V2 market sources emit these logs in
the same order. `updateState` calls `_getUpdatedState`, which emits
`InterestAndFeesAccrued`, and then `_writeState`, which emits `StateUpdated`.
The first market's context declares its asset; the second market's declares
none. Every log and value is synthetic.
"""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile

if __package__:
    from .test_wildcat_v3_release import constructed_release
    from .wildcat_batch_fixtures import SECOND_MARKET, step_log
    from .wildcat_v3_fixtures import ACCRUAL, MARKET, RAY, STATE, log
    from .wildcat_v3_public_fixtures import inventory, observation
else:
    from test_wildcat_v3_release import constructed_release
    from wildcat_batch_fixtures import SECOND_MARKET, step_log
    from wildcat_v3_fixtures import ACCRUAL, MARKET, RAY, STATE, log
    from wildcat_v3_public_fixtures import inventory, observation

from tabularium_lib.core import canonical_json
from tabularium_lib import verifier
from tabularium_lib.wildcat_release import build_wildcat_canonical


VENUES = ("wildcat-v1", "wildcat-v2")
ROOT = "release"
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
# The block's constructed timestamp; only the accrual intervals carry it.
BLOCK_TIME = 2000
EXPIRY = 1500
# Transaction name, emitter and steps, in block order. An accrual step holds
# fromTimestamp, toTimestamp, scaleFactor, baseInterestRay, delinquencyFeeRay
# and protocolFees; a state step holds scaleFactor and the isDelinquent word.
TRANSACTIONS = (
    # updateState with a batch that expired at 1500: _getUpdatedState accrues
    # to the expiry, _processExpiredWithdrawalBatch pays, expires and closes
    # the batch, the second accrual runs to the block time, then _writeState.
    ("expired-batch-update-state", MARKET, (
        ("accrual", 1000, EXPIRY, RAY + 10 ** 25, 10 ** 25, 0, 100),
        ("burn", 25), ("payment", EXPIRY, 25, 25), ("expired", EXPIRY, 25, 25, 25), ("closed", EXPIRY),
        ("accrual", EXPIRY, BLOCK_TIME, RAY + 2 * 10 ** 25, 2 * 10 ** 25, 0, 200),
        ("state", RAY + 2 * 10 ** 25, 0))),
    # updateState again at the same block time: no time has elapsed, so
    # _getUpdatedState emits no accrual and _writeState emits StateUpdated alone.
    ("same-timestamp-update-state", MARKET, (
        ("state", RAY + 2 * 10 ** 25, 0),)),
    # updateState on the second market, whose context declares no asset.
    ("unknown-asset-update-state", SECOND_MARKET, (
        ("accrual", 1000, BLOCK_TIME, RAY + 5 * 10 ** 25, 3 * 10 ** 25, 10 ** 25, 300),
        ("state", RAY + 5 * 10 ** 25, 1))),
)


def specimen_names(venue):
    """The transaction names of one generation's specimen, in block order."""
    if venue not in VENUES:
        raise ValueError("unknown public Wildcat accrual specimen generation")
    return tuple(name for name, _emitter, _steps in TRANSACTIONS)


def _step_log(step, index, emitter):
    if step[0] == "accrual":
        return log(ACCRUAL, (), step[1:], emitter, index)
    if step[0] == "state":
        return log(STATE, (), step[1:], emitter, index)
    return step_log(step, index, emitter)


def specimen_raws(venue):
    """The raw logs of one generation's specimen, block-wide indices in emission order."""
    specimen_names(venue)
    raws, index = [], 0
    for position, (_name, emitter, steps) in enumerate(TRANSACTIONS):
        for step in steps:
            raw = _step_log(step, index, emitter)
            raw["transactionHash"] = "0x" + ("%02x" % (0xb0 + position)) * 32
            raw["transactionIndex"] = hex(2 + position)
            raws.append(raw)
            index += 1
    return raws


def release_id(venue):
    """Return the fixed release name, including its constructed qualification."""
    if venue not in VENUES:
        raise ValueError("unknown public Wildcat accrual specimen generation")
    return venue + "-constructed-accrual-v0"


def example_directory(venue):
    return EXAMPLES / (venue + "-accrual-v0")


def declare_second_market(raws, raw_release_name):
    """The `constructed_release` mutation behind each specimen.

    It declares the second market with no asset beside the first, puts both
    emitters in the request and capture scopes, replaces the logs with `raws`
    and names the raw release.
    """
    def mutate(document, journal, plan):
        (first,) = [item for item in document["contexts"] if item["address"] == MARKET]
        second = deepcopy(first)
        second.update(address=SECOND_MARKET, asset=None)
        document["contexts"] = sorted(document["contexts"] + [second], key=lambda item: item["address"])
        emitters = [item["address"] for item in document["contexts"]]
        request = json.loads(journal["records"][0]["request"])
        request["params"][0]["address"] = emitters
        response = json.loads(journal["records"][0]["response"])
        response["result"] = raws
        journal["records"][0] = {"request": canonical_json(request).decode(),
                                 "response": canonical_json(response).decode()}
        for capture in plan["captures"]:
            capture["scope"]["subjects"] = ["eip155:1:" + address for address in emitters]
        plan["release"]["name"] = raw_release_name

    return mutate


def build_accrual_release(base, venue, release_name):
    """Build into an absent root and discard the original synthetic inputs."""
    mutate = declare_second_market(specimen_raws(venue), venue + "-constructed-accrual")
    with tempfile.TemporaryDirectory(prefix="tabularium-constructed-accrual-") as temporary:
        raw = constructed_release(Path(temporary).resolve(), venue, mutate)
        build_wildcat_canonical(raw, Path(base), release_name)
    coverage = Path(base) / "coverage.json"
    verifier.verify(coverage)
    return coverage


def build_specimen(directory, venue):
    """Build the one closed root below an existing fixture folder."""
    directory = Path(directory)
    build_accrual_release(directory / ROOT, venue, release_id(venue))
    return {ROOT: observation(directory / ROOT)}


def compare_specimen(published, rebuilt):
    """Require every release file and its bytes to match the published root."""
    expected = inventory(Path(published) / ROOT)
    actual = inventory(Path(rebuilt) / ROOT)
    if actual != expected:
        raise ValueError("rebuilt %s differs from the public accrual specimen" % ROOT)
    for relative in expected:
        published_bytes = (Path(published) / ROOT / relative).read_bytes()
        rebuilt_bytes = (Path(rebuilt) / ROOT / relative).read_bytes()
        if published_bytes != rebuilt_bytes:
            raise ValueError("rebuilt %s/%s bytes differ" % (ROOT, relative))
    return {ROOT: observation(Path(rebuilt) / ROOT)}


def rebuild_example(venue, examples=EXAMPLES):
    """Rebuild fresh, compare every file, move the root, then verify offline."""
    published = Path(examples) / (venue + "-accrual-v0")
    expected = json.loads((published / "expected.json").read_bytes())
    with tempfile.TemporaryDirectory(prefix="tabularium-" + venue + "-accrual-") as temporary:
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
        print(canonical_json({"event": "wildcat.accrual-specimen.reproduced", "venue": venue,
                              "roots": {ROOT: {key: result[ROOT][key] for key in
                                               ("release", "rows", "native_logs", "canonical_sha256")}}}).decode())
    return 0
