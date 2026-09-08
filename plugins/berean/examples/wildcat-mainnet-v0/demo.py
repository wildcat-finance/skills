#!/usr/bin/env python3
"""Verify, rebuild and exercise the fixed Wildcat release without a network."""

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rebuild
from berean_lib import BereanError, answers, evals, reads, release
sys.path.insert(0, str(HERE.parents[2] / "ariadne/scripts"))
from ariadne_lib.capture import grounded_agent

RELEASE_DIGEST = "063f677f19f6cdd1ac45b7dad64d02325d332d4b82240367423caffa9e76e36c"
STATEMENT_DIGEST = "0d315ca32edb9169de0f592fea631293813ccb4c8d6d5d17222465b0fa003c8a"
ADVERSARIAL = {"stale-state", "poisoned-document", "prompt-injection", "citation-mismatch", "unsupported-inference"}


def require(condition, reason):
    if not condition:
        raise BereanError(reason)


def check_binding(directory, statement, output):
    """Recompute the existing adapter projection; require every statement field."""
    predicate = statement["predicate"]
    adapter = predicate["adapter"]
    captured = grounded_agent.capture(
        str(directory), "wildcat-mainnet-v0", adapter["tool"], adapter["tool_version"],
        adapter["command"], str(output),
        first_capture_reason=predicate["comparison"]["first_capture_reason"])
    require(captured == statement, "statement: release binding differs")
    require(len(captured["subject"]) == 18, "statement: expected 18 components")
    return captured


def snapshot(directory, statement):
    """Read the already checked component set with the builder's bounded reader."""
    predicate = statement["predicate"]
    given, produced = predicate["given"], predicate["produced"]
    components = [predicate["release"]["document"], given["corpus"]["manifest"]]
    components += given["corpus"]["components"] + [given["reads"]["component"]]
    components += produced["answers"] + list(produced["evaluations"].values())
    components += [produced["promotion"]["component"]]
    return {item["path"]: rebuild.checked_bytes(directory / item["path"]) for item in components}


def demonstrate(reference=HERE / "release", statement_path=HERE / "grounded-agent.intoto.json", inputs=HERE / "inputs"):
    """Return checked identities and refusals; never write to any supplied input."""
    raw = rebuild.checked_bytes(statement_path)
    require(hashlib.sha256(raw).hexdigest() == STATEMENT_DIGEST, "statement: fixed bytes changed")
    statement = json.loads(raw)
    checks = release.verify(str(reference))
    require(all(check.passed for check in checks), "original: release gates failed")
    document = release.load(str(reference))
    require(document["release_digest"] == RELEASE_DIGEST, "original: unexpected release digest")
    report, results = evals.run(str(reference))
    require(report["failed"] == 0 and report["cases"] == 10, "evaluation: expected ten passing cases")
    classes = {case["adversarial"] for case, passed, reason in results if case["adversarial"]}
    require(classes == ADVERSARIAL, "evaluation: adversarial classes differ")
    with tempfile.TemporaryDirectory(prefix="berean-wildcat-demo-") as temporary:
        holder = Path(temporary).resolve()
        check_binding(reference, statement, holder / "original-statement.json")
        before = snapshot(reference, statement)
        fresh = holder / "release"
        require(rebuild.build(inputs, fresh) == RELEASE_DIGEST, "rebuild: release digest differs")
        check_binding(fresh, statement, holder / "rebuilt-statement.json")
        require(snapshot(fresh, statement) == before, "rebuild: component bytes differ")
        manifest = json.loads(before["corpus-manifest.json"])
        records = reads.load(str(reference / "reads.jsonl"))
        original = json.loads(before["answers/grounded.json"])
        refusals = {}
        for name in ("citation", "block", "missing-read"):
            specimen = copy.deepcopy(original)
            selected_records = dict(records)
            if name == "citation":
                specimen["citations"][0]["display_text"] += " altered"
                expected = "answer-citations"
            elif name == "block":
                specimen["reads"][0]["block_number"] += 1
                expected = "answer-reads"
            else:
                del selected_records[specimen["reads"][0]["request_key"]]
                expected = "answer-reads"
            failures = [check.name for check in answers.check(specimen, manifest, str(reference / "corpus"),
                        selected_records, rebuild.CHAIN_ID, rebuild.BLOCK_NUMBER) if not check.passed]
            require(failures == [expected], "refusal: " + name + " did not reach its named gate")
            refusals[name] = expected
        check_binding(reference, statement, holder / "final-statement.json")
        require(snapshot(reference, statement) == before, "original: bytes changed during demonstration")
    return {"event": "wildcat_demo_complete", "release_digest": RELEASE_DIGEST,
            "statement_sha256": STATEMENT_DIGEST, "market": rebuild.MARKET,
            "chain_id": rebuild.CHAIN_ID, "block_number": rebuild.BLOCK_NUMBER,
            "block_hash": rebuild.BLOCK_HASH, "components": len(before), "cases": report["cases"],
            "adversarial_classes": sorted(classes), "refusals": refusals,
            "status": "mixed", "model_executed": False, "reads_evidence": "recorded-rpc"}


def main():
    try:
        result = demonstrate()
    except (BereanError, grounded_agent.CaptureError, OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"event": "wildcat_demo_refused", "reason": grounded_agent.diagnostic(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
