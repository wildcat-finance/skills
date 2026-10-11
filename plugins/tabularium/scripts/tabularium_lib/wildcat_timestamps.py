"""Join only provider-recorded headers with the exact native event identity."""

import re

QUANTITY = re.compile(r"0x(?:0|[1-9a-f][0-9a-f]*)\Z")
HASH = re.compile(r"0x[0-9a-f]{64}\Z")


def quantity(value):
    if isinstance(value, str) and len(value) <= 66 and QUANTITY.fullmatch(value):
        return int(value, 16)
    return None


class HeaderIndex:
    """Retain all candidates so duplicates cannot choose a date by order."""

    def __init__(self, candidates):
        self.pairs = {}
        self.numbers = set()
        self.hashes = set()
        for header, source in candidates:
            if not isinstance(header, dict):
                continue
            number, block_hash = quantity(header.get("number")), header.get("hash")
            if number is None or not isinstance(block_hash, str) or not HASH.fullmatch(block_hash):
                continue
            self.numbers.add(number)
            self.hashes.add(block_hash)
            self.pairs.setdefault((number, block_hash), []).append((header, source))

    def resolve(self, event):
        number, block_hash = quantity(event.get("blockNumber")), event.get("blockHash")
        candidates = self.pairs.get((number, block_hash), [])
        if not candidates:
            reason = ("header-hash-mismatch" if number in self.numbers else
                      "header-number-mismatch" if block_hash in self.hashes else "header-missing")
            return {"status": "unsupported", "reason": reason}
        dates = [quantity(header.get("timestamp")) for header, _ in candidates]
        if any(date is None for date in dates):
            return {"status": "unsupported", "reason": "header-timestamp-missing-or-malformed"}
        if len(set(dates)) != 1:
            return {"status": "unsupported", "reason": "header-timestamps-conflict"}
        # An identical duplicate retains every source instead of first/last wins.
        sources = sorted((source for _, source in candidates), key=lambda ref: (
            ref["component"], ref["journal_selector"], ref["selector"]))
        return {"status": "supported", "observed_at": dates[0], "sources": sources}
