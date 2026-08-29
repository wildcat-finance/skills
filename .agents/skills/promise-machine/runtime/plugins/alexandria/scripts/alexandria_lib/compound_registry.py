"""Pinned Compound III production-deployment registry generation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

from .canonical import canonical_bytes
from .errors import AlexandriaError


COMET_COMMIT = "f766f51583c23acc33b2a7824654ef2029a96804"
COMET_TREE = "1101bf195fce18dc1feb3e56c992adfddac27b0e"
DEPLOYMENTS_TREE = "cf2dc2381d00a3c60563f4b5aa486412ddd40d62"
REGISTRY_SHA256 = "3eff07d0c032d8ab1b614d5ee7691b77e198daa31fa824c739ee7056340b848e"
CHAIN_IDS = {
    "arbitrum": 42161,
    "base": 8453,
    "linea": 59144,
    "mainnet": 1,
    "mantle": 5000,
    "optimism": 10,
    "polygon": 137,
    "ronin": 2020,
    "scroll": 534352,
    "unichain": 130,
}
EXPECTED_MARKETS = (
    "arbitrum/usdc", "arbitrum/usdc.e", "arbitrum/usdt", "arbitrum/weth",
    "base/aero", "base/usdbc", "base/usdc", "base/usds", "base/weth",
    "linea/usdc", "linea/weth",
    "mainnet/usdc", "mainnet/usds", "mainnet/usdt", "mainnet/wbtc",
    "mainnet/weth", "mainnet/wsteth",
    "mantle/usde",
    "optimism/usdc", "optimism/usdt", "optimism/weth",
    "polygon/usdc", "polygon/usdt",
    "ronin/weth", "ronin/wron",
    "scroll/usdc",
    "unichain/usdc", "unichain/weth",
)
SOURCE_FILES = ("roots.json", "configuration.json", "deploy.ts", "relations.ts")
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


def _git(repo: Path, *arguments: str, binary: bool = False):
    result = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(repo), *arguments],
        check=False,
        capture_output=True,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise AlexandriaError(f"Comet git read failed: {message or arguments[0]}")
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def _address(value, label: str) -> str:
    if not isinstance(value, str) or ADDRESS_RE.fullmatch(value) is None:
        raise AlexandriaError(f"{label} is not an EVM address")
    return value.lower()


def _source(repo: Path, path: str) -> tuple[bytes, dict]:
    data = _git(repo, "show", f"{COMET_COMMIT}:{path}", binary=True)
    blob = _git(repo, "rev-parse", f"{COMET_COMMIT}:{path}")
    if SHA1_RE.fullmatch(blob) is None:
        raise AlexandriaError(f"invalid Git blob identity for {path}")
    return data, {
        "blob_sha1": blob,
        "bytes": len(data),
        "path": path,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def generate_registry(repo: Path) -> dict:
    """Generate the fixed production registry from Git object bytes only."""
    repo = repo.absolute()
    if _git(repo, "rev-parse", f"{COMET_COMMIT}^{{commit}}") != COMET_COMMIT:
        raise AlexandriaError("pinned Comet commit is unavailable")
    if _git(repo, "rev-parse", f"{COMET_COMMIT}^{{tree}}") != COMET_TREE:
        raise AlexandriaError("pinned Comet tree does not match")
    if _git(repo, "rev-parse", f"{COMET_COMMIT}:deployments") != DEPLOYMENTS_TREE:
        raise AlexandriaError("pinned deployments tree does not match")

    names = _git(repo, "ls-tree", "-r", "--name-only", f"{COMET_COMMIT}:deployments")
    discovered = {
        "/".join(path.split("/")[:2])
        for path in names.splitlines()
        if path.endswith("/roots.json") and path.count("/") == 2
    }
    production = discovered - {"hardhat/dai"}
    if production != set(EXPECTED_MARKETS):
        raise AlexandriaError("pinned production deployment set does not match the 28-market allowlist")

    entries = []
    proxies = set()
    for deployment in EXPECTED_MARKETS:
        network, market = deployment.split("/", 1)
        files = []
        raw = {}
        for filename in SOURCE_FILES:
            path = f"deployments/{deployment}/{filename}"
            data, metadata = _source(repo, path)
            files.append(metadata)
            raw[filename] = data
        try:
            roots = json.loads(raw["roots.json"])
            configuration = json.loads(raw["configuration.json"])
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AlexandriaError(f"invalid pinned deployment JSON for {deployment}") from error
        proxy = _address(roots.get("comet"), f"{deployment} Comet")
        proxy_key = (CHAIN_IDS[network], proxy)
        if proxy_key in proxies:
            raise AlexandriaError("duplicate chain-qualified Comet proxy in pinned registry")
        proxies.add(proxy_key)
        bulker_raw = roots.get("bulker")
        bulker = None if bulker_raw is None else _address(bulker_raw, f"{deployment} Bulker")
        base_token = _address(
            configuration.get("baseTokenAddress"), f"{deployment} base token"
        )
        entries.append({
            "base_token": base_token,
            "bulker": bulker,
            "chain_id": CHAIN_IDS[network],
            "files": files,
            "market": market,
            "network": network,
            "proxy": proxy,
        })
    return {
        "entries": entries,
        "format": "alexandria-compound-v3-registry/v1",
        "source": {
            "commit": COMET_COMMIT,
            "deployments_tree": DEPLOYMENTS_TREE,
            "repository": "https://github.com/compound-finance/comet",
            "tree": COMET_TREE,
        },
    }


def registry_bytes(repo: Path) -> bytes:
    registry = generate_registry(repo)
    validate_registry(registry)
    return canonical_bytes(registry)


def deployment_source_bytes(repo: Path, deployment="mainnet/usdc") -> dict[str, bytes]:
    if deployment not in EXPECTED_MARKETS:
        raise AlexandriaError("requested Comet deployment is outside the production allowlist")
    result = {}
    for filename in SOURCE_FILES:
        result[filename] = _source(repo.absolute(), f"deployments/{deployment}/{filename}")[0]
    return result


def validate_registry(registry) -> None:
    if not isinstance(registry, dict) or set(registry) != {"entries", "format", "source"}:
        raise AlexandriaError("Compound registry has an unknown shape")
    if registry["format"] != "alexandria-compound-v3-registry/v1":
        raise AlexandriaError("Compound registry format is unknown")
    source = registry["source"]
    if not isinstance(source, dict) or set(source) != {
        "commit", "deployments_tree", "repository", "tree"
    } or source.get("commit") != COMET_COMMIT:
        raise AlexandriaError("Compound registry commit does not match the pin")
    if source.get("tree") != COMET_TREE or source.get("deployments_tree") != DEPLOYMENTS_TREE:
        raise AlexandriaError("Compound registry tree identity does not match the pin")
    if source.get("repository") != "https://github.com/compound-finance/comet":
        raise AlexandriaError("Compound registry repository does not match the pin")
    entries = registry["entries"]
    if not isinstance(entries, list) or len(entries) != 28:
        raise AlexandriaError("Compound registry must contain 28 production markets")
    keys = []
    proxies = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "base_token", "bulker", "chain_id", "files", "market",
            "network", "proxy",
        }:
            raise AlexandriaError("Compound registry entry has an unknown shape")
        key = f"{entry.get('network')}/{entry.get('market')}"
        keys.append(key)
        proxies.append((entry.get("chain_id"), _address(entry.get("proxy"), f"{key} Comet")))
        if entry.get("chain_id") != CHAIN_IDS.get(entry.get("network")):
            raise AlexandriaError(f"{key} chain id does not match")
        _address(entry.get("base_token"), f"{key} base token")
        if entry.get("bulker") is not None:
            _address(entry.get("bulker"), f"{key} Bulker")
        files = entry.get("files")
        if not isinstance(files, list) or len(files) != 4:
            raise AlexandriaError(f"{key} source-file set is incomplete")
        expected_paths = [f"deployments/{key}/{name}" for name in SOURCE_FILES]
        paths = []
        for item in files:
            if not isinstance(item, dict) or set(item) != {
                "blob_sha1", "bytes", "path", "sha256"
            }:
                raise AlexandriaError(f"{key} source-file record has an unknown shape")
            if SHA1_RE.fullmatch(str(item["blob_sha1"])) is None:
                raise AlexandriaError(f"{key} source-file Git identity is invalid")
            if not isinstance(item["bytes"], int) or isinstance(item["bytes"], bool) or item["bytes"] < 1:
                raise AlexandriaError(f"{key} source-file byte count is invalid")
            if re.fullmatch(r"[0-9a-f]{64}", str(item["sha256"])) is None:
                raise AlexandriaError(f"{key} source-file digest is invalid")
            paths.append(item["path"])
        if paths != expected_paths:
            raise AlexandriaError(f"{key} source-file paths do not match the pin")
    if tuple(keys) != EXPECTED_MARKETS or len(proxies) != len(set(proxies)):
        raise AlexandriaError("Compound registry entries do not match the pinned allowlist")
    if hashlib.sha256(canonical_bytes(registry)).hexdigest() != REGISTRY_SHA256:
        raise AlexandriaError("Compound registry bytes do not match the pinned registry")
