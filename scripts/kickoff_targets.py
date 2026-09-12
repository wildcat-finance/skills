#!/usr/bin/env python3
"""Check the kickoff target-input registry, and judge a specimen against it.

The registry at ``docs/kickoff/1359/targets.json`` names, for every kickoff
consumer that depends on an unnamed venue, the candidate or selected target
rows: repository, immutable source commit, chain, addresses, observed code
hashes and the build inputs a consumer compiles from. Issue 1482 asked for two
mechanical properties on top of the record itself: every consumer maps to a
row, and a specimen carrying the wrong generation or the wrong code hash is
rejected rather than absorbed.

This module holds both. ``check`` reads the registry and its evidence files
and reports every shape defect it finds: a consumer with no row, a row whose
status claims more than its fields carry, an evidence file whose digest moved,
a contract whose recorded code hash disagrees with the chain observation it
cites. ``specimen`` takes one claim of the form "this address on this chain is
generation G of target T with code hash H" and accepts it only when every part
agrees with the registry.

Nothing here reaches the network, runs a subprocess or reads the environment.
The chain observations were recorded once, with the commands the record
names, and this module compares against those bytes. A clean ``check``
therefore establishes that the registry agrees with itself and with the
evidence files committed beside it. It does not establish that the chain still
holds that code, that a source commit is the one a maintainer meant, or that a
pending decision has been taken.

Exit codes: 0 clean or accepted, 1 findings or rejected, 2 usage or a file
that cannot be read as the registry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = Path("docs/kickoff/1359/targets.json")
SCHEMA = "wildcat.kickoff-targets.v1"
OBSERVATIONS_SCHEMA = "wildcat.kickoff-targets.observations.v1"
STATUSES = ("resolved", "candidate", "blocked")
DECISION_STATUSES = ("pending", "recorded")
MAX_BYTES = 4 * 1024 * 1024

KEBAB = re.compile(r"\A[a-z0-9]+(?:[.-][a-z0-9]+)*\Z")
HEX40 = re.compile(r"\A[0-9a-f]{40}\Z")
ADDRESS = re.compile(r"\A0x[0-9a-fA-F]{40}\Z")
HASH32 = re.compile(r"\A0x[0-9a-f]{64}\Z")
SHA256 = re.compile(r"\A[0-9a-f]{64}\Z")
HTTPS = re.compile(r"\Ahttps://[^\s]+\Z")


class RegistryError(Exception):
    """The file is not a registry this module can read."""


def read_json(path: Path, limit: int = MAX_BYTES):
    """Read one JSON document from a regular file below the size cap."""
    if not path.is_file():
        raise RegistryError(f"{path}: not a regular file")
    size = path.stat().st_size
    if size > limit:
        raise RegistryError(f"{path}: {size} bytes exceeds the {limit} byte cap")
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise RegistryError(f"{path}: grew past the {limit} byte cap while reading")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RegistryError(f"{path}: not JSON ({error})") from error


def sha256_of(path: Path, limit: int = MAX_BYTES) -> str:
    if not path.is_file():
        raise RegistryError(f"{path}: not a regular file")
    if path.stat().st_size > limit:
        raise RegistryError(f"{path}: exceeds the {limit} byte cap")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(65536)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _is_str(value) -> bool:
    return isinstance(value, str) and value != ""


class Checker:
    """Collect findings over one registry document rooted at ``root``."""

    def __init__(self, registry: dict, root: Path, registry_path: Path):
        self.registry = registry
        self.root = root
        self.registry_path = registry_path
        self.findings: list[str] = []
        self.observations: dict[int, dict[str, dict]] = {}

    def finding(self, text: str) -> None:
        self.findings.append(text)

    # -- top level ---------------------------------------------------------

    def run(self) -> list[str]:
        registry = self.registry
        if not isinstance(registry, dict):
            self.finding("registry: top level is not an object")
            return self.findings
        if registry.get("schema") != SCHEMA:
            self.finding(f"registry: schema is {registry.get('schema')!r}, expected {SCHEMA!r}")
        for key in ("record", "produced_on", "producer", "consumers", "decisions", "targets", "evidence_digests"):
            if key not in registry:
                self.finding(f"registry: missing top-level key {key!r}")
        self.check_evidence_digests()
        decisions = self.check_decisions()
        targets = self.check_targets(decisions)
        self.check_consumers(targets)
        return self.findings

    # -- evidence ----------------------------------------------------------

    def check_evidence_digests(self) -> None:
        digests = self.registry.get("evidence_digests")
        if not isinstance(digests, dict) or not digests:
            self.finding("evidence_digests: missing or empty")
            return
        for relative, recorded in sorted(digests.items()):
            if not _is_str(relative) or relative.startswith("/") or ".." in Path(relative).parts:
                self.finding(f"evidence_digests: unsafe path {relative!r}")
                continue
            if not (isinstance(recorded, str) and SHA256.fullmatch(recorded)):
                self.finding(f"evidence_digests: {relative}: digest is not 64 hex characters")
                continue
            path = self.root / relative
            try:
                actual = sha256_of(path)
            except RegistryError as error:
                self.finding(f"evidence_digests: {error}")
                continue
            if actual != recorded:
                self.finding(f"evidence_digests: {relative}: sha256 {actual} differs from recorded {recorded}")
                continue
            if relative.endswith(".json") and "/evidence/" in relative:
                self.load_observations(path, relative)

    def load_observations(self, path: Path, relative: str) -> None:
        try:
            document = read_json(path)
        except RegistryError as error:
            self.finding(f"evidence: {error}")
            return
        if not isinstance(document, dict) or document.get("schema") != OBSERVATIONS_SCHEMA:
            return
        chain_id = document.get("chain_id")
        if not isinstance(chain_id, int):
            self.finding(f"evidence: {relative}: chain_id is not an integer")
            return
        table = self.observations.setdefault(chain_id, {})
        for entry in document.get("code") or []:
            if not isinstance(entry, dict):
                continue
            address = entry.get("address")
            if not (isinstance(address, str) and ADDRESS.fullmatch(address)):
                self.finding(f"evidence: {relative}: code entry without a valid address")
                continue
            keccak = entry.get("code_keccak256")
            if not (isinstance(keccak, str) and HASH32.fullmatch(keccak)):
                self.finding(f"evidence: {relative}: {address}: code_keccak256 is not a 32-byte hash")
                continue
            table[address.lower()] = entry

    # -- decisions ---------------------------------------------------------

    def check_decisions(self) -> dict[str, dict]:
        decisions = self.registry.get("decisions")
        found: dict[str, dict] = {}
        if not isinstance(decisions, list) or not decisions:
            self.finding("decisions: missing or empty")
            return found
        for index, decision in enumerate(decisions):
            label = f"decisions[{index}]"
            if not isinstance(decision, dict):
                self.finding(f"{label}: not an object")
                continue
            identifier = decision.get("id")
            if not (_is_str(identifier) and KEBAB.fullmatch(identifier)):
                self.finding(f"{label}: id is not kebab-case")
                continue
            if identifier in found:
                self.finding(f"{label}: duplicate decision id {identifier}")
                continue
            found[identifier] = decision
            if not _is_str(decision.get("question")):
                self.finding(f"decision {identifier}: question is empty")
            if decision.get("decision_maker_role") is None:
                self.finding(f"decision {identifier}: decision_maker_role is missing")
            status = decision.get("status")
            if status not in DECISION_STATUSES:
                self.finding(f"decision {identifier}: status {status!r} is not one of {DECISION_STATUSES}")
                continue
            options = decision.get("options")
            if not isinstance(options, list) or not options:
                self.finding(f"decision {identifier}: options is missing or empty")
            if status == "recorded":
                maker = decision.get("decision_maker")
                if not isinstance(maker, dict):
                    self.finding(f"decision {identifier}: recorded without a decision_maker object")
                else:
                    for key in ("name", "role", "date", "reference"):
                        if not _is_str(maker.get(key)):
                            self.finding(f"decision {identifier}: decision_maker.{key} is empty")
                    reference = maker.get("reference")
                    if _is_str(reference) and not HTTPS.fullmatch(reference):
                        self.finding(f"decision {identifier}: decision_maker.reference is not an https URL")
                if decision.get("selection") in (None, "", [], {}):
                    self.finding(f"decision {identifier}: recorded without a selection")
            else:
                if decision.get("decision_maker") not in (None, {}):
                    self.finding(f"decision {identifier}: pending yet names a decision_maker")
                if decision.get("selection") not in (None, "", [], {}):
                    self.finding(f"decision {identifier}: pending yet carries a selection")
        return found

    # -- targets -----------------------------------------------------------

    def check_targets(self, decisions: dict[str, dict]) -> dict[str, dict]:
        targets = self.registry.get("targets")
        found: dict[str, dict] = {}
        if not isinstance(targets, list) or not targets:
            self.finding("targets: missing or empty")
            return found
        for index, target in enumerate(targets):
            label = f"targets[{index}]"
            if not isinstance(target, dict):
                self.finding(f"{label}: not an object")
                continue
            identifier = target.get("id")
            if not (_is_str(identifier) and KEBAB.fullmatch(identifier)):
                self.finding(f"{label}: id is not kebab-case")
                continue
            if identifier in found:
                self.finding(f"{label}: duplicate target id {identifier}")
                continue
            found[identifier] = target
            self.check_target(identifier, target, decisions)
        return found

    def check_target(self, identifier: str, target: dict, decisions: dict[str, dict]) -> None:
        prefix = f"target {identifier}"
        for key in ("venue", "generation"):
            if not _is_str(target.get(key)):
                self.finding(f"{prefix}: {key} is empty")
        status = target.get("status")
        if status not in STATUSES:
            self.finding(f"{prefix}: status {status!r} is not one of {STATUSES}")
            return
        consumers = target.get("consumers")
        if not isinstance(consumers, list) or any(not isinstance(item, int) for item in consumers):
            self.finding(f"{prefix}: consumers is not a list of issue numbers")
        for relative in target.get("evidence") or []:
            if relative not in (self.registry.get("evidence_digests") or {}):
                self.finding(f"{prefix}: evidence {relative} has no recorded digest")
        source = target.get("source")
        deployment = target.get("deployment")
        if status == "blocked":
            if not _is_str(target.get("blocker")):
                self.finding(f"{prefix}: blocked without a blocker")
            recovery = target.get("recovery")
            if not (_is_str(recovery) and HTTPS.fullmatch(recovery)):
                self.finding(f"{prefix}: blocked without a recovery issue URL")
        if status == "candidate":
            pending = target.get("pending_on")
            if not isinstance(pending, list) or not pending:
                self.finding(f"{prefix}: candidate without pending_on")
            else:
                for item in pending:
                    if item not in decisions:
                        self.finding(f"{prefix}: pending_on names unknown decision {item!r}")
        if status == "resolved":
            decided_by = target.get("decision")
            if decided_by not in decisions:
                self.finding(f"{prefix}: resolved without a known decision id")
            elif decisions[decided_by].get("status") != "recorded":
                self.finding(f"{prefix}: resolved on decision {decided_by} that is still pending")
            if not isinstance(source, dict):
                self.finding(f"{prefix}: resolved without a source object")
            if not isinstance(deployment, dict):
                self.finding(f"{prefix}: resolved without a deployment object")
        if isinstance(source, dict):
            self.check_source(prefix, source, strict=(status == "resolved"))
        if isinstance(deployment, dict):
            self.check_deployment(prefix, deployment, strict=(status == "resolved"))

    def check_source(self, prefix: str, source: dict, strict: bool) -> None:
        repository = source.get("repository")
        if not (_is_str(repository) and HTTPS.fullmatch(repository)):
            self.finding(f"{prefix}: source.repository is not an https URL")
        commit = source.get("commit")
        if not (_is_str(commit) and HEX40.fullmatch(commit)):
            self.finding(f"{prefix}: source.commit is not a 40-character lowercase hex SHA")
        for extra in source.get("equivalent_commits") or []:
            if not (_is_str(extra) and HEX40.fullmatch(extra)):
                self.finding(f"{prefix}: source.equivalent_commits carries a malformed SHA")
        if source.get("relation") not in ("deployed", "proposed", "located"):
            self.finding(f"{prefix}: source.relation must be deployed, proposed or located")
        inputs = source.get("build_inputs")
        if strict and (not isinstance(inputs, list) or not inputs):
            self.finding(f"{prefix}: resolved without build_inputs")
        for index, item in enumerate(inputs or []):
            if not isinstance(item, dict):
                self.finding(f"{prefix}: build_inputs[{index}] is not an object")
                continue
            if not _is_str(item.get("path")):
                self.finding(f"{prefix}: build_inputs[{index}] has no path")
            blob = item.get("blob_sha1")
            if not (_is_str(blob) and HEX40.fullmatch(blob)):
                self.finding(f"{prefix}: build_inputs[{index}] blob_sha1 is malformed")
            digest = item.get("sha256")
            if not (_is_str(digest) and SHA256.fullmatch(digest)):
                self.finding(f"{prefix}: build_inputs[{index}] sha256 is malformed")
        if strict:
            compiler = source.get("compiler")
            if not isinstance(compiler, dict) or not _is_str(compiler.get("solc")):
                self.finding(f"{prefix}: resolved without compiler.solc")

    def check_deployment(self, prefix: str, deployment: dict, strict: bool) -> None:
        chain_id = deployment.get("chain_id")
        if not isinstance(chain_id, int):
            self.finding(f"{prefix}: deployment.chain_id is not an integer")
            return
        observed = deployment.get("observed_block")
        if not isinstance(observed, dict) or not isinstance(observed.get("number"), int) \
                or not (_is_str(observed.get("hash")) and HASH32.fullmatch(observed["hash"])):
            self.finding(f"{prefix}: deployment.observed_block needs an integer number and a 32-byte hash")
        contracts = deployment.get("contracts")
        if not isinstance(contracts, list) or not contracts:
            if strict:
                self.finding(f"{prefix}: resolved deployment lists no contracts")
            return
        table = self.observations.get(chain_id, {})
        seen: set[str] = set()
        for index, contract in enumerate(contracts):
            label = f"{prefix}: contracts[{index}]"
            if not isinstance(contract, dict):
                self.finding(f"{label}: not an object")
                continue
            address = contract.get("address")
            if not (_is_str(address) and ADDRESS.fullmatch(address)):
                self.finding(f"{label}: address is malformed")
                continue
            lowered = address.lower()
            if lowered in seen:
                self.finding(f"{label}: address {lowered} listed twice")
            seen.add(lowered)
            for key in ("role", "name"):
                if not _is_str(contract.get(key)):
                    self.finding(f"{label}: {key} is empty")
            keccak = contract.get("code_keccak256")
            if not (_is_str(keccak) and HASH32.fullmatch(keccak)):
                self.finding(f"{label}: code_keccak256 is not a 32-byte hash")
                continue
            observation = table.get(lowered)
            if observation is None:
                self.finding(f"{label}: {lowered} has no code observation in the chain {chain_id} evidence")
            elif observation.get("code_keccak256") != keccak:
                self.finding(f"{label}: {lowered} code_keccak256 {keccak} disagrees with the evidence {observation.get('code_keccak256')}")
            match = contract.get("code_match")
            if not isinstance(match, dict) or not _is_str(match.get("method")):
                self.finding(f"{label}: code_match.method is empty")
            elif match.get("source_commit") is not None and not HEX40.fullmatch(str(match["source_commit"])):
                self.finding(f"{label}: code_match.source_commit is malformed")

    # -- consumers ---------------------------------------------------------

    def check_consumers(self, targets: dict[str, dict]) -> None:
        consumers = self.registry.get("consumers")
        if not isinstance(consumers, list) or not consumers:
            self.finding("consumers: missing or empty")
            return
        seen: set[int] = set()
        for index, consumer in enumerate(consumers):
            label = f"consumers[{index}]"
            if not isinstance(consumer, dict):
                self.finding(f"{label}: not an object")
                continue
            issue = consumer.get("issue")
            if not isinstance(issue, int):
                self.finding(f"{label}: issue is not an integer")
                continue
            if issue in seen:
                self.finding(f"{label}: issue {issue} listed twice")
            seen.add(issue)
            url = consumer.get("url")
            if not (_is_str(url) and HTTPS.fullmatch(url) and url.endswith(f"/{issue}")):
                self.finding(f"consumer {issue}: url does not end in the issue number")
            rows = consumer.get("targets")
            if not isinstance(rows, list) or not rows:
                self.finding(f"consumer {issue}: maps to no target row")
                continue
            for row in rows:
                if row not in targets:
                    self.finding(f"consumer {issue}: names unknown target {row!r}")
                elif issue not in (targets[row].get("consumers") or []):
                    self.finding(f"consumer {issue}: target {row} does not list it back")


def judge_specimen(registry: dict, specimen: dict) -> list[str]:
    """Reasons to reject a specimen; an empty list means it is accepted."""
    reasons: list[str] = []
    if not isinstance(specimen, dict):
        return ["specimen is not an object"]
    for key in ("target", "generation", "chain_id", "address", "code_keccak256"):
        if key not in specimen:
            reasons.append(f"specimen lacks {key}")
    if reasons:
        return reasons
    targets = {t.get("id"): t for t in registry.get("targets") or [] if isinstance(t, dict)}
    target = targets.get(specimen["target"])
    if target is None:
        return [f"unknown target {specimen['target']!r}"]
    if specimen["generation"] != target.get("generation"):
        reasons.append(f"generation {specimen['generation']!r} is not the row's {target.get('generation')!r}")
    deployment = target.get("deployment") or {}
    if specimen["chain_id"] != deployment.get("chain_id"):
        reasons.append(f"chain {specimen['chain_id']!r} is not the row's {deployment.get('chain_id')!r}")
    address = specimen["address"]
    if not (isinstance(address, str) and ADDRESS.fullmatch(address)):
        reasons.append("address is malformed")
        return reasons
    contract = None
    for candidate in deployment.get("contracts") or []:
        if isinstance(candidate, dict) and str(candidate.get("address", "")).lower() == address.lower():
            contract = candidate
            break
    if contract is None:
        reasons.append(f"address {address.lower()} is not a contract of the row")
        return reasons
    if specimen["code_keccak256"] != contract.get("code_keccak256"):
        reasons.append(f"code hash {specimen['code_keccak256']!r} is not the recorded {contract.get('code_keccak256')!r}")
    return reasons


def command_check(arguments) -> int:
    root = Path(arguments.root).resolve() if arguments.root else REPOSITORY_ROOT
    registry_path = (root / arguments.registry) if not Path(arguments.registry).is_absolute() else Path(arguments.registry)
    try:
        registry = read_json(registry_path)
    except RegistryError as error:
        print(f"kickoff-targets: {error}", file=sys.stderr)
        return 2
    findings = Checker(registry, root, registry_path).run()
    if findings:
        for line in findings:
            print(line)
        print(f"kickoff-targets: {len(findings)} finding(s)")
        return 1
    targets = registry.get("targets") or []
    counts = {status: sum(1 for t in targets if isinstance(t, dict) and t.get("status") == status) for status in STATUSES}
    pending = sum(1 for d in registry.get("decisions") or [] if isinstance(d, dict) and d.get("status") == "pending")
    print(
        f"kickoff-targets: clean; {len(registry.get('consumers') or [])} consumers, "
        f"{len(targets)} targets ({counts['resolved']} resolved, {counts['candidate']} candidate, "
        f"{counts['blocked']} blocked), {pending} pending decision(s)"
    )
    return 0


def command_specimen(arguments) -> int:
    root = Path(arguments.root).resolve() if arguments.root else REPOSITORY_ROOT
    registry_path = (root / arguments.registry) if not Path(arguments.registry).is_absolute() else Path(arguments.registry)
    try:
        registry = read_json(registry_path)
        specimen = read_json(Path(arguments.specimen))
    except RegistryError as error:
        print(f"kickoff-targets: {error}", file=sys.stderr)
        return 2
    reasons = judge_specimen(registry, specimen)
    if reasons:
        print("rejected: " + "; ".join(reasons))
        return 1
    print(f"accepted: {specimen['address'].lower()} is {specimen['target']} generation {specimen['generation']} on chain {specimen['chain_id']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check the kickoff target-input registry or judge a specimen against it.")
    parser.add_argument("--root", help="repository root the registry and evidence paths resolve against (default: this checkout)")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="registry path relative to the root")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="report every shape, digest and cross-reference defect")
    specimen = commands.add_parser("specimen", help="accept or reject one target claim")
    specimen.add_argument("--specimen", required=True, help="JSON file with target, generation, chain_id, address and code_keccak256")
    return parser


def main(argv=None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "check":
        return command_check(arguments)
    return command_specimen(arguments)


if __name__ == "__main__":
    sys.exit(main())
