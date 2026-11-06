"""Join only provider-recorded headers with the exact native event identity."""

import re

from .core import TabulariumError

MAX_SOURCE_REFERENCES = 500_000
# Dossier dates must fit the UTC datetime range on supported hosts.
MAX_DOSSIER_TIMESTAMP = 253_402_300_799

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
        self.resolved = {}
        self.source_references = 0
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
        pair = (number, block_hash)
        if pair in self.resolved:
            return self._retain(self.resolved[pair])
        candidates = self.pairs.get(pair, [])
        if not candidates:
            reason = ("header-hash-mismatch" if number in self.numbers else
                      "header-number-mismatch" if block_hash in self.hashes else "header-missing")
            return {"status": "unsupported", "reason": reason}
        dates = [quantity(header.get("timestamp")) for header, _ in candidates]
        sources = sorted((source for _, source in candidates), key=lambda ref: (
            ref["component"], ref["journal_selector"], ref["selector"]))
        if any(date is None for date in dates):
            result = {"status": "unsupported", "reason": "header-timestamp-missing-or-malformed"}
        elif any(date > MAX_DOSSIER_TIMESTAMP for date in dates):
            result = {"status": "unsupported", "reason": "header-timestamp-outside-dossier-date-range"}
        elif len(set(dates)) != 1:
            result = {"status": "unsupported", "reason": "header-timestamps-conflict"}
        else:
            # Preserve every duplicate source; bound its fanout across output rows.
            result = {"status": "supported", "observed_at": dates[0]}
        result["sources"] = sources
        self.resolved[pair] = result
        return self._retain(result)

    def _retain(self, result):
        count = len(result.get("sources", []))
        if self.source_references + count > MAX_SOURCE_REFERENCES:
            raise TabulariumError("Wildcat timestamp provenance exceeds the source-reference budget")
        self.source_references += count
        return result
