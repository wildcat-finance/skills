"""Preserve the exact JSON-RPC responses for the Base pilot block, before the provider's proof window passes.

    LAZARUS_BASE_RPC=... LAZARUS_BASE_RPC_RECEIPTS=... python3 preserve_base_pin.py --out base-pin-51579258

Each request is sent as canonical JSON and each response is written byte for byte next to it. The manifest records the
method, parameters, both digests, the response length, the UTC time and the retries. It records no URL or credential.
A provider's rate-limit or timeout error is retried and never stored as a result.
"""
import argparse, datetime, hashlib, json, os, pathlib, time, urllib.error, urllib.request

PIN = "0x313097a"                      # Base 51,579,258
PIN_HASH = "0x0366446fd6fca93d511f0dd1700076670f0608a1dc73e6be2bd1329f217f611d"
COLLISION = "0x18d10cd"                # Ethereum 26,022,093: the same number exists on Base, with a different hash
ADMIN = "0x10d6a54a4754c8869d6886b5f5d7fbfa5b4522237ea5c60d11bc4e7a1ff9390b"
IMPL = "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3"
ACCOUNTS = [("multicall3", "0xcA11bde05977b3631167028862bE2a173976CA11", []),
            ("permit2", "0x000000000022D473030F116dDEE9F6B43aC78BA3", []),
            ("usdc", "0x833589fCD6eDb6E08f4C7C32D4f71b54bDA02913", [ADMIN, IMPL])]   # slots sorted and unique
REQUESTS = [("chainid", "eth_chainId", [], "primary"),
            ("header", "eth_getBlockByNumber", [PIN, False], "primary"),
            ("header-same-number-as-ethereum-pin", "eth_getBlockByNumber", [COLLISION, False], "primary")]
for name, addr, slots in ACCOUNTS:
    REQUESTS.append((f"proof-{name}", "eth_getProof", [addr, slots, PIN], "primary"))
    REQUESTS.append((f"code-{name}", "eth_getCode", [addr, PIN], "primary"))
REQUESTS.append(("receipts", "eth_getBlockReceipts", [PIN], "receipts"))


def fetch(url, body):
    req = urllib.request.Request(url, data=body, headers={"content-type": "application/json", "user-agent": "curl/8.7.1"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.status, resp.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = pathlib.Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=False)
    routes = {"primary": os.environ["LAZARUS_BASE_RPC"], "receipts": os.environ["LAZARUS_BASE_RPC_RECEIPTS"]}
    entries = []
    for i, (name, method, params, route) in enumerate(REQUESTS, 1):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, separators=(",", ":")).encode()
        retries = 0
        while True:
            time.sleep(0.4)
            try:
                status, data = fetch(routes[route], body)
                obj = json.loads(data)
                if "error" in obj:
                    raise RuntimeError(str(obj["error"])[:160])
                break
            except (urllib.error.URLError, RuntimeError, ValueError) as exc:
                retries += 1
                if retries > 10:
                    raise SystemExit(f"{method} gave up: {exc}")
                time.sleep(min(30, 2 ** retries))
        stem = f"{i:02d}-{name}"
        (out / f"{stem}.request.json").write_bytes(body)
        (out / f"{stem}.response.json").write_bytes(data)
        entries.append({"index": i, "name": name, "method": method, "params": params, "route": route, "http_status": status,
                        "request_sha256": hashlib.sha256(body).hexdigest(), "response_sha256": hashlib.sha256(data).hexdigest(),
                        "response_bytes": len(data), "observed_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "retries": retries})
        print(stem, len(data), "bytes", "retries", retries)
    manifest = {"format": "lazarus-base-pin-preservation/v1", "chain_id": "0x2105", "block": PIN, "expected_block_hash": PIN_HASH,
                "entries": entries}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")


if __name__ == "__main__":
    main()
