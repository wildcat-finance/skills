"""Constructed logs from the frozen concrete ABI inventory; no retained data."""

import json
from pathlib import Path
import re
import tempfile

from wildcat_v3_fixtures import ACCOUNT, MARKET, OTHER, ZERO, log, record, word
from test_wildcat_v3_release import constructed_release
from tabularium_lib.core import canonical_json
from tabularium_lib.wildcat_abi import VARIANTS
from tabularium_lib.wildcat_release import build_wildcat_canonical

ROOT = Path(__file__).resolve().parents[3]
INVENTORY = json.loads((ROOT / "docs/kickoff/2090/design/event-inventory.json").read_bytes())
EXAMPLES = ROOT / "plugins/tabularium/examples"


def suffix(entry):
    name = re.sub(r"(?<!^)(?=[A-Z])", "-", entry["signature"].split("(", 1)[0]).lower()
    return {"controller": "controller-", "hooks-instance": "hooks-"}.get(entry["role"], "") + name


def encoded(entry, emitter, index=0, maximum=False, zero=False, name="constructed hook"):
    """Encode the declared ABI independently, including dynamic strings."""
    fields = entry["fields"]
    values = {}
    for field in fields:
        kind = field["type"]
        if kind == "address":
            value = ZERO if zero else (MARKET if field["name"] == "market" else
                                       OTHER if field["name"] == "providerAddress" else ACCOUNT)
        elif kind == "string":
            value = name
        elif kind == "bool":
            value = not zero
        else:
            value = (1 << int(kind[4:])) - 1 if maximum else 0 if zero else 7
        values[field["name"]] = value
    data_fields = [field for field in fields if not field["indexed"]]
    head, tail = [], b""
    for field in data_fields:
        value = values[field["name"]]
        if field["type"] != "string":
            head.append(word(value))
        else:
            raw = value.encode()
            head.append(word(len(data_fields) * 32 + len(tail)))
            tail += len(raw).to_bytes(32, "big") + raw + b"\x00" * (-len(raw) % 32)
    raw = log(entry["signature"], [values[f["name"]] for f in fields if f["indexed"]], (), emitter, index)
    raw["data"] = "0x" + "".join(head) + tail.hex()
    expected = {f["name"]: str(values[f["name"]]) if f["type"].startswith("uint") else values[f["name"]] for f in fields}
    return raw, expected


def inputs(venue, group="required", **options):
    entries = [entry for entry in INVENTORY[group] if entry["generation"] == venue]
    contexts, records, expected = {}, [], []
    for index, entry in enumerate(entries):
        # Repeating-byte addresses remain visibly synthetic; each concrete ABI
        # gets its own emitter even where the signature repeats.
        emitter = "0x" + ("%02x" % (0x90 + index)) * 20
        variant = VARIANTS[entry["variant"]]
        contexts[emitter] = {"role": entry["role"], "asset": None, "market": MARKET,
                             "abi_variant": entry["variant"], "concrete_contract": variant["contract"],
                             "source": [{"class": "declared-constructed-context", "fixture": "2090-native-state"}]}
        if entry["role"] == "wrapper":
            contexts[emitter]["asset"] = MARKET
        raw, values = encoded(entry, emitter, index, **options)
        records.append(record(raw))
        expected.append((entry, emitter, values))
    return contexts, records, expected


def raw_release(base, venue):
    contexts, records, _ = inputs(venue)

    def replace(document, journal, plan):
        document["contexts"] = [{"address": address, **{key: context[key] for key in
                                  ("role", "asset", "market", "abi_variant", "concrete_contract")}}
                                for address, context in sorted(contexts.items())]
        response = json.loads(journal["records"][0]["response"])
        response["result"] = [raw for raw, _ in records]
        request = json.loads(journal["records"][0]["request"])
        request["params"][0]["address"] = sorted(contexts)
        journal["records"][0].update(request=canonical_json(request).decode(), response=canonical_json(response).decode())
        for capture in plan["captures"]:
            capture["scope"]["subjects"] = ["eip155:1:" + address for address in sorted(contexts)]
        plan["release"]["name"] = venue + "-constructed-parameters"

    return constructed_release(Path(base), venue, replace)


def build_specimen(directory, venue):
    """Build a fresh parameter release through the raw-release owners."""
    directory = Path(directory)
    with tempfile.TemporaryDirectory(prefix="tabularium-constructed-parameters-") as temporary:
        raw = raw_release(Path(temporary).resolve(), venue)
        build_wildcat_canonical(raw, directory / "release", venue + "-constructed-parameters-v0", "1.2.0")


def rebuild_example(venue):
    """Compare every committed release byte with a fresh offline rebuild."""
    from wildcat_v3_public_fixtures import inventory
    published = EXAMPLES / (venue + "-parameters-v0") / "release"
    with tempfile.TemporaryDirectory(prefix="tabularium-parameter-rebuild-") as temporary:
        base = Path(temporary).resolve()
        build_specimen(base, venue)
        assert inventory(base / "release") == inventory(published)
        for relative in inventory(published):
            assert (base / "release" / relative).read_bytes() == (published / relative).read_bytes()
    return 0
