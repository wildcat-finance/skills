#!/usr/bin/env python3
"""Collect a bounded Ethereum USDC Comet block interval, resumably.

The network path is explicit and lives in one place: `HttpsTransport`, built
from an environment variable that is never written anywhere. Every other path
in this module takes a transport it was handed, so the whole collector is
exercised offline against a fixture provider and no test opens a socket.

The loop is the one `docs/compound-v3-harvest.md` specifies. It binds the end
boundary under a named finality policy before it asks for a shard, walks the
plan in bounded shards, checkpoints only after the bytes are fsynced, and
rewinds to the last remembered boundary that still matches when a hash has
changed under it.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))

from alexandria_lib.canonical import MAX_CONTROL_BYTES, canonical_bytes, load_bytes, load_raw_json
from alexandria_lib.errors import AlexandriaError
from alexandria_lib.interval import (
    EVIDENCE_CLASSES,
    MAX_DISPUTES,
    Staging,
    log_identity,
    plan_digest,
    validate_plan,
    validate_reconciliation,
    validate_shard_coverage,
)
from alexandria_lib.paths import read_confined_file
from alexandria_lib.release import MAX_RAW_COMPONENT_BYTES


ENDPOINT_ENV = "ALEXANDRIA_COMPOUND_RPC_URL"
MAX_COLLECT_SECONDS = 3_600
MAX_COLLECT_BYTES = 512 * 1024 * 1024
MAX_RESPONSE_NODES = 2_000_000
RECEIPTS_DIRECTORY = "receipts"
ERROR_RECEIPTS = "errors.jsonl"
RECONCILIATION_DIRECTORY = "reconciliation"
RECONCILIATION_RECORD = "reconciliation.json"
DISPUTED_RESPONSES = "disputed.jsonl"

FINALITY_TAGS = {"finalized": "finalized", "safe": "safe"}


class TransportError(AlexandriaError):
    """The provider could not be reached, or answered outside the contract."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TransportError("the Compound RPC endpoint redirected")


class HttpsTransport:
    """The one network path. The endpoint reaches no file, receipt or message."""

    def __init__(self, endpoint: str, timeout: int) -> None:
        if not endpoint.startswith("https://") or any(c.isspace() for c in endpoint):
            raise AlexandriaError(f"{ENDPOINT_ENV} must name an HTTPS endpoint")
        self._endpoint = endpoint
        self._timeout = timeout
        self._opener = urllib.request.build_opener(_NoRedirect)

    @classmethod
    def from_environment(cls, timeout: int, environ=None) -> "HttpsTransport":
        values = os.environ if environ is None else environ
        return cls(values.get(ENDPOINT_ENV, ""), timeout)

    def request(self, payload: bytes, label: str) -> bytes:
        message = urllib.request.Request(
            self._endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._opener.open(message, timeout=self._timeout) as response:
                if response.status != 200:
                    raise TransportError(f"{label} returned HTTP {response.status}")
                return response.read(MAX_RAW_COMPONENT_BYTES + 1)
        except urllib.error.URLError as error:
            raise TransportError(f"{label} transport failed") from error


def request_bytes(identifier: int, method: str, params) -> bytes:
    return canonical_bytes({"id": identifier, "jsonrpc": "2.0", "method": method, "params": params})


def request_identifier(shard: int, name: str) -> int:
    """Derive an id from the plan, so a resumed run asks for the same bytes."""
    return shard * len(EVIDENCE_CLASSES) + EVIDENCE_CLASSES.index(name) + 1


def shard_requests(plan, shard) -> list[tuple[str, str, list]]:
    proxy = plan["proxy"]
    start = hex(shard["start"])
    end = hex(shard["end"])
    return [
        ("boundary-blocks", "eth_getBlockByNumber", [end, False]),
        ("logs", "eth_getLogs", [{"address": proxy, "fromBlock": start, "toBlock": end}]),
        ("traces", "trace_filter", [{"fromBlock": start, "toAddress": [proxy], "toBlock": end}]),
    ]


class Collector:
    """One bounded collection over one plan, against one transport."""

    def __init__(self, plan, staging_root, transport, *, receipts_root=None) -> None:
        validate_plan(plan)
        self.plan = plan
        self.digest = plan_digest(plan)
        self.transport = transport
        self.provider = plan["provider"]
        self.staging = Staging(staging_root, plan)
        root = Path(receipts_root) if receipts_root else self.staging.root
        self.receipts = root / RECEIPTS_DIRECTORY
        try:
            self.receipts.mkdir(exist_ok=True)
        except OSError as exc:
            raise AlexandriaError(f"cannot open the receipts directory: {exc}") from exc
        if self.receipts.is_symlink() or not self.receipts.is_dir():
            raise AlexandriaError("the receipts directory is not a directory")
        self._started = None
        self._bytes = 0

    # -- bounds -----------------------------------------------------------

    def _spend(self, count: int) -> None:
        self._bytes += count
        if self._bytes > MAX_COLLECT_BYTES:
            raise AlexandriaError("collection exceeded its total byte ceiling")
        if self._started is not None and time.monotonic() - self._started > MAX_COLLECT_SECONDS:
            raise AlexandriaError("collection exceeded its elapsed-time ceiling")

    # -- one request ------------------------------------------------------

    def _ask(self, shard_index: int, name: str, method: str, params) -> tuple[bytes, bytes, object]:
        identifier = request_identifier(shard_index, name)
        payload = request_bytes(identifier, method, params)
        self._spend(len(payload))
        label = f"shard {shard_index} {name}"
        try:
            data = self.transport.request(payload, label)
        except AlexandriaError:
            self.record_error(shard_index, name, "transport")
            raise
        if len(data) > MAX_RAW_COMPONENT_BYTES:
            self.record_error(shard_index, name, "oversized-response", len(data))
            raise AlexandriaError(f"{label} exceeded the component byte ceiling")
        self._spend(len(data))
        try:
            envelope = load_raw_json(
                data, label, max_bytes=MAX_RAW_COMPONENT_BYTES, max_nodes=MAX_RESPONSE_NODES,
                preserve_integers=True,
            )
        except AlexandriaError:
            self.record_error(shard_index, name, "malformed-response")
            raise
        if not isinstance(envelope, dict) or envelope.get("jsonrpc") != "2.0" or envelope.get("id") != identifier:
            self.record_error(shard_index, name, "envelope-mismatch")
            raise AlexandriaError(f"{label} envelope does not match its request")
        if "error" in envelope:
            code = envelope["error"].get("code") if isinstance(envelope["error"], dict) else None
            self.record_error(
                shard_index, name, "json-rpc-error",
                code if isinstance(code, int) and not isinstance(code, bool) else None,
            )
            raise AlexandriaError(f"{label} returned a JSON-RPC error")
        if "result" not in envelope:
            self.record_error(shard_index, name, "no-result")
            raise AlexandriaError(f"{label} carried neither result nor error")
        result = envelope["result"]
        if isinstance(envelope.get("truncated"), bool) and envelope["truncated"]:
            self.record_error(shard_index, name, "truncated-response")
            raise AlexandriaError(f"{label} was marked truncated")
        if isinstance(result, list) and len(result) >= self.provider["page_limit"]:
            self.record_error(shard_index, name, "page-limit", len(result))
            raise AlexandriaError(
                f"{label} returned a page at the provider's limit, so it may be short"
            )
        return payload, data, result

    def record_error(self, shard_index: int, name: str, code: str, status=None) -> None:
        """Append one receipt built here, not copied from anything the provider said.

        A receipt is a durable file, and the only text a transport can reach is
        its own exception message. A caller-supplied transport that puts its
        endpoint in that message would otherwise write the endpoint, and any
        credential inside it, straight to disk. So nothing from an exception is
        copied: the receipt carries the code this module chose, the class, the
        shard, the unresolved range, the provider class the plan declared, and
        one bounded status this module computed. The exception text still
        reaches the operator on stderr, which is not a file this writes.
        """
        shard = self.plan["shards"][shard_index] if 0 <= shard_index < len(self.plan["shards"]) else None
        if status is not None and not isinstance(status, (int, str)):
            raise AlexandriaError("an error receipt status must be a number or a short string")
        if isinstance(status, str) and (len(status) > 64 or not status.replace("-", "").isalnum()):
            raise AlexandriaError("an error receipt status string must be short and plain")
        receipt = {
            "class": name if name in EVIDENCE_CLASSES else "boundary",
            "code": code,
            "provider_class": self.provider["class"],
            "shard": shard_index,
            "status": status,
            "unresolved": (
                {"end": shard["end"], "start": shard["start"]} if shard else None
            ),
        }
        path = self.receipts / ERROR_RECEIPTS
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags, 0o600)
        except OSError as exc:
            raise AlexandriaError(f"cannot open the error receipt file: {exc}") from exc
        try:
            with os.fdopen(descriptor, "ab", closefd=False) as handle:
                handle.write(canonical_bytes(receipt))
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            os.close(descriptor)

    # -- the loop ---------------------------------------------------------

    def bind_finality(self) -> dict:
        """Read the boundary the plan's named policy points at, before any shard."""
        policy = self.plan["finality"]["policy"]
        if policy == "confirmations":
            tag = hex(_number(self.plan["finality"]["block_number"]))
        else:
            tag = FINALITY_TAGS[policy]
        payload = request_bytes(0, "eth_getBlockByNumber", [tag, False])
        self._spend(len(payload))
        try:
            data = self.transport.request(payload, f"finality boundary under {policy}")
        except AlexandriaError:
            self.record_error(-1, "finality", "transport")
            raise
        self._spend(len(data))
        envelope = load_raw_json(
            data, "finality boundary", max_bytes=MAX_RAW_COMPONENT_BYTES,
            max_nodes=MAX_RESPONSE_NODES, preserve_integers=True,
        )
        header = envelope.get("result") if isinstance(envelope, dict) else None
        if not isinstance(header, dict):
            self.record_error(-1, "finality", "no-result")
            raise AlexandriaError("the finality boundary response carries no header")
        declared = self.plan["finality"]
        if header.get("hash") != declared["block_hash"]:
            raise AlexandriaError(
                f"the {policy} boundary the provider reports does not match the plan"
            )
        if _hex(header.get("number"), "finality boundary number") != _number(declared["block_number"]):
            raise AlexandriaError(
                f"the {policy} boundary block number does not match the plan"
            )
        return header

    def _boundary_hash(self, shard_index: int) -> str:
        """Re-read one already accepted shard's boundary block."""
        shard = self.plan["shards"][shard_index]
        payload = request_bytes(
            request_identifier(shard_index, "boundary-blocks"),
            "eth_getBlockByNumber", [hex(shard["end"]), False],
        )
        self._spend(len(payload))
        try:
            data = self.transport.request(payload, f"shard {shard_index} boundary re-read")
        except AlexandriaError:
            self.record_error(shard_index, "boundary-re-read", "transport")
            raise
        self._spend(len(data))
        envelope = load_raw_json(
            data, f"shard {shard_index} boundary re-read", max_bytes=MAX_RAW_COMPONENT_BYTES,
            max_nodes=MAX_RESPONSE_NODES, preserve_integers=True,
        )
        header = envelope.get("result") if isinstance(envelope, dict) else None
        if not isinstance(header, dict) or not isinstance(header.get("hash"), str):
            self.record_error(shard_index, "boundary-re-read", "no-result")
            raise AlexandriaError(f"shard {shard_index} boundary re-read carries no block hash")
        return header["hash"]

    def _settle_start(self) -> int:
        """Resume, then rewind past any boundary whose hash has changed under us."""
        state = self.staging.resume()
        if state["next_shard"] == 0:
            return 0
        for entry in reversed(state["history"]):
            if self._boundary_hash(entry["shard"]) == entry["block_hash"]:
                if entry["shard"] == state["next_shard"] - 1:
                    return state["next_shard"]
                self.staging.rewind_to(entry["shard"])
                return entry["shard"] + 1
        if state["history"] and state["history"][0]["shard"] == 0:
            self.staging.discard()
            return 0
        raise AlexandriaError(
            "the chain moved under every remembered boundary; the reorg is deeper "
            "than the checkpoint's rewind history"
        )

    def collect(self) -> dict:
        self._started = time.monotonic()
        self.bind_finality()
        start = self._settle_start()
        shards = self.plan["shards"]
        counts = {name: 0 for name in EVIDENCE_CLASSES}
        for index in range(start, len(shards)):
            shard = shards[index]
            boundary = None
            for name, method, params in shard_requests(self.plan, shard):
                payload, data, result = self._ask(index, name, method, params)
                if name == "boundary-blocks":
                    if not isinstance(result, dict) or not isinstance(result.get("hash"), str):
                        raise AlexandriaError(f"shard {index} boundary block carries no hash")
                    boundary = result["hash"]
                if isinstance(result, list):
                    counts[name] += len(result)
                else:
                    counts[name] += 1
                self.staging.record(index, name, payload, data)
            self.staging.commit(index, shard["end"], boundary)
        self.staging.close()
        return {
            "collected_shards": len(shards) - start,
            "record_counts": counts,
            "resumed_from": start,
            "shards": len(shards),
        }



class Reconciler:
    """Run a completed staging tree past a second provider.

    A disagreement is never settled here. Neither provider wins by answering
    first or by being in a majority of two, so the record says which identities
    disagreed and both sets of bytes are kept.
    """

    def __init__(self, plan, staging_root, transport, provider_class) -> None:
        validate_plan(plan)
        self.plan = plan
        self.transport = transport
        if not isinstance(provider_class, str) or not 1 <= len(provider_class) <= 256:
            raise AlexandriaError("the second provider class is not a bounded name")
        if any(character in provider_class for character in ("://", "@")):
            raise AlexandriaError("the second provider class must not carry an endpoint")
        self.provider_class = provider_class
        self.staging = Staging(staging_root, plan)
        self.root = self.staging.root
        directory = self.root / RECONCILIATION_DIRECTORY
        try:
            directory.mkdir(exist_ok=True)
        except OSError as exc:
            raise AlexandriaError(f"cannot open the reconciliation directory: {exc}") from exc
        if directory.is_symlink() or not directory.is_dir():
            raise AlexandriaError("the reconciliation directory is not a directory")
        self.directory = directory

    def _staged(self) -> dict:
        """The primary's responses, keyed by shard and class."""
        staged = {}
        for name in EVIDENCE_CLASSES:
            for entry in self.staging.entries(name):
                envelope = load_bytes(entry["response"].encode(), f"staged {name} response")
                staged[(entry["shard"], name)] = envelope.get("result")
        return staged

    def _second(self, shard_index: int, name: str, method: str, params):
        identifier = request_identifier(shard_index, name)
        payload = request_bytes(identifier, method, params)
        data = self.transport.request(payload, f"shard {shard_index} {name} second provider")
        if len(data) > MAX_RAW_COMPONENT_BYTES:
            raise AlexandriaError(
                f"shard {shard_index} {name} second-provider response exceeded the byte ceiling"
            )
        envelope = load_raw_json(
            data, f"shard {shard_index} {name} second provider",
            max_bytes=MAX_RAW_COMPONENT_BYTES, max_nodes=MAX_RESPONSE_NODES,
            preserve_integers=True,
        )
        if not isinstance(envelope, dict) or envelope.get("id") != identifier or "result" not in envelope:
            raise AlexandriaError(
                f"shard {shard_index} {name} second-provider envelope does not match its request"
            )
        return envelope["result"], data

    def _keep(self, shard_index: int, name: str, data: bytes) -> None:
        """Preserve the second provider's bytes for a shard that disagreed."""
        record = canonical_bytes({
            "class": name,
            "provider_class": self.provider_class,
            "response": data.decode("utf-8"),
            "shard": shard_index,
        })
        path = self.directory / DISPUTED_RESPONSES
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags, 0o600)
        except OSError as exc:
            raise AlexandriaError(f"cannot open the disputed-response file: {exc}") from exc
        try:
            with os.fdopen(descriptor, "ab", closefd=False) as handle:
                handle.write(record)
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            os.close(descriptor)

    def reconcile(self) -> dict:
        state = self.staging.resume()
        shards = self.plan["shards"]
        if state["next_shard"] != len(shards):
            raise AlexandriaError(
                "the interval is not completely collected, so there is nothing to reconcile"
            )
        staged = self._staged()
        for index in range(len(shards)):
            for name in EVIDENCE_CLASSES:
                if (index, name) not in staged:
                    raise AlexandriaError(
                        f"shard {index} has no staged {name} response to reconcile"
                    )

        compared = 0
        matched = 0
        disputed = []
        statuses = {}
        counts = {}
        for shard in shards:
            index = shard["index"]
            boundary = staged[(index, "boundary-blocks")]
            logs = staged[(index, "logs")]
            traces = staged[(index, "traces")]
            counts[index] = {
                "boundary-blocks": 1,
                "logs": len(logs) if isinstance(logs, list) else 0,
                "traces": len(traces) if isinstance(traces, list) else 0,
            }
            status = "complete"
            try:
                second_boundary, boundary_bytes = self._second(
                    index, "boundary-blocks", "eth_getBlockByNumber", [hex(shard["end"]), False]
                )
                second_logs, logs_bytes = self._second(
                    index, "logs", "eth_getLogs",
                    [{"address": self.plan["proxy"], "fromBlock": hex(shard["start"]), "toBlock": hex(shard["end"])}],
                )
            except AlexandriaError:
                return self._unreconciled(shards, counts, staged)

            compared += 1
            if not isinstance(second_boundary, dict) or second_boundary.get("hash") != boundary.get("hash"):
                status = "failed"
                disputed.append({
                    "identity": f"block {shard['end']}",
                    "kind": "boundary-hash",
                    "shard": index,
                })
                self._keep(index, "boundary-blocks", boundary_bytes)
            else:
                matched += 1
                first_transactions = _transaction_order(boundary)
                second_transactions = _transaction_order(second_boundary)
                compared += 1
                if first_transactions != second_transactions:
                    status = "partial" if status == "complete" else status
                    disputed.append({
                        "identity": f"block {shard['end']} transaction order",
                        "kind": "transaction-order",
                        "shard": index,
                    })
                    self._keep(index, "boundary-blocks", boundary_bytes)
                else:
                    matched += 1

            first_identities = [log_identity(record) for record in logs] if isinstance(logs, list) else []
            second_identities = (
                [log_identity(record) for record in second_logs] if isinstance(second_logs, list) else []
            )
            agreed, disagreements = _identity_comparison(first_identities, second_identities)
            compared += agreed + len(disagreements)
            matched += agreed
            if disagreements:
                if status != "failed":
                    status = "partial"
                self._keep(index, "logs", logs_bytes)
                for identity in disagreements:
                    if len(disputed) < MAX_DISPUTES:
                        disputed.append({"identity": identity, "kind": "log-identity", "shard": index})
            statuses[index] = status

        record = {
            "compared": compared,
            "disputed": disputed,
            "matched": matched,
            "provider_class": self.provider_class,
            "status": "disputed" if disputed else "agreed",
        }
        return self._write(shards, counts, statuses, record, staged)

    def _unreconciled(self, shards, counts, staged) -> dict:
        for shard in shards:
            counts.setdefault(shard["index"], {
                "boundary-blocks": 1,
                "logs": len(staged[(shard["index"], "logs")]),
                "traces": len(staged[(shard["index"], "traces")]),
            })
        record = {
            "compared": 0,
            "disputed": [],
            "matched": 0,
            "provider_class": self.provider_class,
            "status": "unreconciled",
        }
        statuses = {shard["index"]: "complete" for shard in shards}
        return self._write(shards, counts, statuses, record, staged)

    def _write(self, shards, counts, statuses, record, staged) -> dict:
        table = [
            {
                "end": shard["end"],
                "end_hash": staged[(shard["index"], "boundary-blocks")]["hash"],
                "index": shard["index"],
                "record_counts": counts[shard["index"]],
                "start": shard["start"],
                "status": statuses[shard["index"]],
            }
            for shard in shards
        ]
        validate_shard_coverage(table, shards)
        validate_reconciliation(record)
        document = {
            "format": "alexandria-interval-reconciliation/v1",
            "plan_sha256": plan_digest(self.plan),
            "reconciliation": record,
            "shards": table,
        }
        _atomic_json(self.directory / RECONCILIATION_RECORD, document)
        self.staging.close()
        return document


def _transaction_order(header) -> list:
    transactions = header.get("transactions") if isinstance(header, dict) else None
    if transactions is None:
        return []
    if not isinstance(transactions, list):
        raise AlexandriaError("a block header's transaction list is not a list")
    order = []
    for item in transactions:
        if isinstance(item, str):
            order.append(item.lower())
        elif isinstance(item, dict) and isinstance(item.get("hash"), str):
            order.append(item["hash"].lower())
        else:
            raise AlexandriaError("a block header transaction carries no hash")
    return order


def _identity_comparison(first, second):
    """How many identities both providers hold, and every one only one of them does."""
    remaining = list(second)
    agreed = 0
    disagreements = []
    for identity in first:
        if identity in remaining:
            remaining.remove(identity)
            agreed += 1
        else:
            disagreements.append(identity)
    disagreements.extend(remaining)
    return agreed, disagreements


def _atomic_json(path: Path, value) -> None:
    import tempfile

    data = canonical_bytes(value)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def _number(value) -> int:
    return int(value)


def _hex(value, label: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise AlexandriaError(f"{label} is not a hexadecimal quantity")
    try:
        return int(value, 16)
    except ValueError as exc:
        raise AlexandriaError(f"{label} is not a hexadecimal quantity") from exc


def load_control(path: Path, label: str):
    path = path.absolute()
    return load_bytes(
        read_confined_file(path.parent, path.name, label, max_bytes=MAX_CONTROL_BYTES),
        label,
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Collect a bounded Ethereum USDC Comet interval, resumably."
    )
    commands = value.add_subparsers(dest="command", metavar="{collect,reconcile}")
    collect = commands.add_parser("collect", help="collect the plan's interval from the explicit RPC endpoint")
    collect.add_argument("--plan", required=True, type=Path)
    collect.add_argument("--staging", required=True, type=Path)
    reconcile = commands.add_parser(
        "reconcile", help="run the collected interval past a second provider"
    )
    reconcile.add_argument("--plan", required=True, type=Path)
    reconcile.add_argument("--staging", required=True, type=Path)
    reconcile.add_argument("--provider-class", required=True)
    return value


def main(argv=None) -> int:
    value = parser()
    args = value.parse_args(argv)
    if args.command is None:
        value.print_help(sys.stderr)
        return 2
    try:
        plan = load_control(args.plan, "interval plan")
        validate_plan(plan)
        transport = HttpsTransport.from_environment(plan["provider"]["timeout_seconds"])
        if args.command == "reconcile":
            document = Reconciler(plan, args.staging, transport, args.provider_class).reconcile()
            sys.stdout.buffer.write(canonical_bytes(document))
            return 0
        args.staging.mkdir(parents=True, exist_ok=True)
        summary = Collector(plan, args.staging, transport).collect()
        sys.stdout.buffer.write(canonical_bytes(summary))
        return 0
    except (AlexandriaError, OSError) as error:
        print(f"usdc-interval: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
