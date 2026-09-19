"""Derive governed ranges from verified producer receipts and native Git ancestry."""
from __future__ import annotations

from dataclasses import dataclass
import re

from .canonical import Refusal, canonical, decode, digest
from .native_records import count, hexadecimal, shas
from .signatures import public_key


@dataclass(frozen=True)
class ApprovedRun:
    """Externally approved inputs, not values inferred from the carried archive.

    Each canonical history row binds a public key, enrollment reference, actor
    and inclusive Step interval. The caller must authenticate that history and
    its policy before using this API; Step 4 owns complete authority replay.
    ``start_commit`` is the separately approved first governed range base.
    """
    anchor_sha256: str
    initial_base: str
    start_commit: str
    history: tuple[bytes, ...]

    def keys(self):
        hexadecimal(self.anchor_sha256)
        hexadecimal(self.initial_base, commit=True)
        hexadecimal(self.start_commit, commit=True)
        if type(self.history) is not tuple or not 1 <= len(self.history) <= 128:
            raise Refusal("native-trust-required", "trust")
        rows, seen = [], set()
        for encoded in self.history:
            row = decode(encoded, require_canonical=True)
            if type(row) is not dict or set(row) != {"key", "enrollment", "actor_id", "first_step", "last_step"}:
                raise Refusal("native-key-history", "trust")
            count(row["actor_id"], 2**63 - 1, minimum=1)
            count(row["first_step"], 4096, minimum=1); count(row["last_step"], 4096, minimum=1)
            if row["first_step"] > row["last_step"]:
                raise Refusal("native-key-history", "trust")
            ref = row["enrollment"]
            if type(ref) is not dict or set(ref) != {"type", "sha256"} or ref["type"] not in ("key-enrollment", "key-rotation"):
                raise Refusal("native-key-history", "trust")
            hexadecimal(ref["sha256"])
            public_key(row["key"])
            if row["key"]["format"] != "openpgp-v4":
                raise Refusal("native-signature-format-unavailable", "trust")
            key = (row["key"]["fingerprint"], row["first_step"], row["last_step"])
            if key in seen:
                raise Refusal("native-key-history-duplicate", "trust")
            seen.add(key); rows.append(row)
        for index, row in enumerate(rows):
            for other in rows[index + 1:]:
                if (row["key"]["fingerprint"] == other["key"]["fingerprint"]
                    and max(row["first_step"], other["first_step"]) <= min(row["last_step"], other["last_step"])):
                    raise Refusal("native-key-history-ambiguous", "trust")
        return rows

    @property
    def sha256(self):
        return digest(canonical({"anchor_sha256": self.anchor_sha256,
            "initial_base": self.initial_base, "start_commit": self.start_commit,
            "history": self.keys()}))


def _range(git, base, head):
    hexadecimal(base, commit=True); hexadecimal(head, commit=True)
    if git(["cat-file", "-t", base]).strip() != b"commit" or git(["cat-file", "-t", head]).strip() != b"commit":
        raise Refusal("native-required-object-unavailable", "coverage")
    git(["merge-base", "--is-ancestor", base, head])
    values = git(["rev-list", "--reverse", "--max-count=4097", base + ".." + head])
    try:
        commits = list(shas(values.decode("ascii").splitlines(), empty=False))
    except UnicodeError:
        raise Refusal("native-coverage-shape", "coverage") from None
    if commits[-1] != head or base in commits:
        raise Refusal("native-range-boundary", "coverage")
    return commits


def _same_claim(actual, claimed):
    claimed = shas(claimed)
    if set(actual) != set(claimed) or len(actual) != len(claimed):
        raise Refusal("native-range-coverage", "coverage")


def derive(metadata, reconstructed_identity, approval, git):
    """Return a complete local denominator; embedded commit lists are comparisons."""
    state, entries = metadata.state, metadata.entries
    identity = reconstructed_identity["identity"]
    anchor = identity["run"]
    if (digest(canonical(anchor)) != approval.anchor_sha256
        or anchor["initial_base_sha"] != approval.initial_base
        or state.get("receipts", {}).get("run_anchor") != anchor
        or metadata.manifest["boundary"]["refs"].get(anchor["run_branch"]) != approval.start_commit
        or metadata.manifest["boundary"]["refs"].get(approval.initial_base) != approval.initial_base):
        raise Refusal("native-approved-base-mismatch", "coverage")
    # An approved base endpoint is distinct from local governed signature coverage.
    git(["merge-base", "--is-ancestor", approval.initial_base, approval.start_commit])
    if git(["rev-parse", "--verify", anchor["run_branch"]]).strip() != approval.start_commit.encode():
        raise Refusal("native-approved-base-mismatch", "coverage")
    if entries[0]["event"] != "init" or entries[0]["data"].get("run_anchor_sha256") != approval.anchor_sha256:
        raise Refusal("native-anchor-ledger", "coverage")
    required, ranges, origins = set(), [], {}
    previous_head, previous_branch = approval.start_commit, anchor["run_branch"]
    boundary_expected = None
    boundary = identity["boundary"]
    all_step_numbers = [step.get("n") for step in state["steps"]]
    if all_step_numbers != list(range(1, len(all_step_numbers) + 1)) or len(all_step_numbers) > 4096:
        raise Refusal("native-step-topology", "coverage")
    for step in state["steps"]:
        number = step["n"]
        receipts = step["receipts"]
        implementation = receipts.get("implement")
        if implementation is None:
            if number <= boundary["step"]:
                raise Refusal("native-implementation-missing", "coverage")
            continue
        if number > boundary["step"] or type(implementation) is not dict:
            raise Refusal("native-step-topology", "coverage")
        events = [(index + 1, event) for index, event in enumerate(entries) if event["data"].get("step") == number]
        implemented = [(index, event) for index, event in events if event["event"] == "done:implement"]
        if len(implemented) != 1:
            raise Refusal("native-implementation-ledger", "coverage")
        _, implement_event = implemented[0]
        for field in ("branch", "commit", "verified_commits"):
            if implement_event["data"].get(field) != implementation.get(field):
                raise Refusal("native-implementation-ledger", "coverage")
        head = hexadecimal(implementation.get("commit"), commit=True)
        branch = implementation.get("branch")
        if type(branch) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9/_.-]{0,1023}", branch) is None:
            raise Refusal("native-step-topology", "coverage")

        def add(kind, start, end, claims):
            actual = _range(git, start, end)
            _same_claim(actual, claims)
            required.update(actual)
            if len(required) > 4096:
                raise Refusal("native-coverage-limit", "coverage")
            for commit in actual:
                origins.setdefault(commit, set()).add(number)
            ranges.append({"step": number, "kind": kind, "base": start,
                           "head": end, "commits": actual})
            return actual

        add("implementation", previous_head, head, implementation.get("verified_commits"))
        audit_events = [event["data"] for _, event in events if event["event"] == "audit-round"]
        rounds = step.get("audit", {}).get("rounds")
        if type(rounds) is not list or len(audit_events) != len(rounds):
            raise Refusal("native-audit-ledger", "coverage")
        last_range = []
        for round_number, (record, event) in enumerate(zip(rounds, audit_events), 1):
            if record.get("round") != round_number or any(event.get(field) != value for field, value in record.items()):
                raise Refusal("native-audit-ledger", "coverage")
            if record.get("fixes_commit") is None:
                if record.get("verified_commits") != []:
                    raise Refusal("native-audit-coverage", "coverage")
                last_range = []
            else:
                end = hexadecimal(record["fixes_commit"], commit=True)
                last_range = add("audit-fixes", head, end, record.get("verified_commits"))
                head = end
        push = receipts.get("push")
        push_events = [event["data"] for _, event in events if event["event"] == "done:push"]
        if push is not None:
            if len(push_events) != 1 or any(push_events[0].get(field) != value for field, value in push.items()):
                raise Refusal("native-push-ledger", "coverage")
            if push.get("pr_base") != previous_branch:
                raise Refusal("native-step-base", "coverage")
            if push.get("merge_commit") is not None or push.get("early_merge") is not None or push.get("github_merge_verified") != []:
                raise Refusal("native-platform-evidence-unavailable", "coverage")
            end = hexadecimal(push.get("head_commit"), commit=True)
            git(["merge-base", "--is-ancestor", head, end])
            last_range = add("push", previous_head, end, push.get("verified_commits"))
            if metadata.manifest["boundary"]["refs"].get(branch) != end or git(["rev-parse", "--verify", branch]).strip() != end.encode():
                raise Refusal("native-step-ref-moved", "coverage")
            head = end
        elif push_events or number != boundary["step"] or boundary["kind"] != "audit-verdict":
            raise Refusal("native-push-ledger", "coverage")
        if number == boundary["step"]:
            if boundary["working_commit_sha"] != head or (boundary["kind"] == "post-push" and push is None):
                raise Refusal("native-working-commit", "coverage")
            boundary_expected = last_range
        previous_head, previous_branch = head, branch
    if boundary_expected is None or not required:
        raise Refusal("native-coverage-empty", "coverage")
    return {"required": sorted(required), "native_expected": sorted(boundary_expected),
            "ranges": ranges, "steps": {sha: sorted(origins[sha]) for sha in sorted(origins)},
            "base_history": {"evidence_class": "approved-base-endpoints",
                "initial_base": approval.initial_base, "start_commit": approval.start_commit,
                "local_governed_signature_claim": False}, "platform_commits": []}


def verify_complete(denominator, inspected, approval, verify_commit):
    """Compare native coverage exactly, then independently check every local commit."""
    claims = inspected["signatures"]
    claimed = [row["sha"] for row in claims]
    shas(claimed)
    if sorted(claimed) != denominator["native_expected"]:
        raise Refusal("native-current-boundary-coverage", "coverage")
    keys = approval.keys()
    verified = []
    native_fingerprints = {row["sha"]: row["fingerprint"] for row in claims}
    for commit in denominator["required"]:
        fingerprint = verify_commit(commit)
        enrollments = []
        for step in denominator["steps"][commit]:
            matching = [row for row in keys if row["key"]["fingerprint"] == fingerprint
                        and row["first_step"] <= step <= row["last_step"]]
            if len(matching) != 1:
                raise Refusal("native-signer-unapproved", "coverage")
            enrollments.append(matching[0]["enrollment"])
        if any(enrollment != enrollments[0] for enrollment in enrollments):
            raise Refusal("native-enrollment-ambiguous", "coverage")
        if commit in native_fingerprints and native_fingerprints[commit] != fingerprint:
            raise Refusal("native-signature-contradiction", "coverage")
        verified.append({"commit": commit, "enrollment": enrollments[0],
                         "evidence_class": "local-signature", "fingerprint": fingerprint,
                         "native_current_boundary": commit in native_fingerprints})
    return {**denominator, "verified": verified, "complete": True,
            "historical_required": sorted(set(denominator["required"]) - set(claimed)),
            "approved_history_sha256": approval.sha256}
