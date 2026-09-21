"""One-body ordered replay of complete authenticated checkpoint authority history.

The transport interleaves policy records, prerequisite evidence, decision/event
pairs and heads. A head commits both streams at its exact position. This reader
never signs, publishes, renews a lease, chooses a fork or executes a gateway.
"""
from __future__ import annotations

from .canonical import MAX_ENTRIES, MAX_TOTAL_BYTES, Refusal, canonical, digest
from .eligibility import Freshness, current, grant_at
from .parents import check_parent, native_projection
from .records import references, time_value
from .signatures import _decode_envelope, freeze, thaw
from .schema import HASH, validate
from .trust import TRUST_TYPES, TrustPrefix

EVENTS = frozenset({"acceptance", "cancellation", "publication-finalization", "denial", "authorized-removal", "stream-permit"})
# Explicit projections hold only fields consumed by a later join. Immutable
# authenticated bodies are released after this append or its adjacent journal.
RETAIN = {
    "upload-endorsement": ("actor_id", "enrollment", "grant", "identities", "carrier_length", "issued_at", "expires_at", "candidate_id", "parent"),
    "validation": ("identities", "carrier_length", "native", "release", "authorization", "candidate_id", "parent", "coverage"),
    "storage-copy": ("role", "location_id", "object", "object_key", "configuration_policy_sha256"),
    "parent-link": ("registration", "initial_base", "parents", "prior_receipts", "producer_prefix_sha256", "native"),
    "authority-head": ("policy_history", "decisions", "issued_at", "expires_at"),
}


def commitment(previous, journal_sha256, event_sha256):
    """Domain-separated commitment to exact signed journal and event envelopes."""
    return digest(b"wildcat/checkpoint-authority/journal/v1\x00" + canonical({
        "previous": previous, "journal": journal_sha256, "event": event_sha256}))


class DecisionIndex:
    """The same bounded decision transition kernel serves replay and measurement."""
    def __init__(self):
        self.states = {}

    def transition(self, key, action):
        old = self.states.get(key)
        allowed = {"authorize": (None,), "cancel": (None,), "finalize": ("authorize",),
                   "permit": ("finalize",), "deny": ("authorize", "finalize", "deny")}
        if action not in allowed or old not in allowed[action]:
            raise Refusal("decision-exclusivity" if action in ("authorize", "cancel") else "decision-order", "replay")
        if len(self.states) >= MAX_ENTRIES and key not in self.states:
            raise Refusal("decision-limit", "replay")
        if action != "permit":
            self.states[key] = action


class Replay:
    """Consume bounded bytes with explicit roots and caller-owned native evidence.

    native_evidence(output_sha256) returns (NativeResult, exact producer ledger).
    It is a trusted local lookup, never a record-selected locator or command.
    Freshness is separately supplied by an authenticated control-channel caller.
    Any refusal makes this instance unusable; construct a new replay to retry.
    """
    def __init__(self, bootstrap, tools, *, native_evidence, freshness=None):
        self.trust = TrustPrefix(bootstrap, tools)
        self.native_evidence = native_evidence
        self.freshness = freshness
        if freshness is not None:
            if not isinstance(freshness, Freshness):
                raise Refusal("freshness-input", "replay")
            freshness.check()
        self.floor_seen = [freshness is None or freshness.policy_count == 0,
                           freshness is None or freshness.decision_count == 0]
        self.nodes, self.decisions, self.acceptances, self.snapshots = {}, {}, {}, {}
        self.index = DecisionIndex()
        self.pending = None
        self.count = self.bytes = self.journal_count = self.head_count = 0
        self.journal_tail = self.journal_sha = self.last_head = self.last_time = None
        self.head = None
        self.failed = False
        self.denials, self.removals, self.nonces = {}, {}, set()
        self.native = {}
        self.copies = {}
        self.last_kind = None

    def node(self, reference, *kinds):
        found = self.nodes.get(reference["sha256"])
        if found is None or found["type"] != reference["type"] or (kinds and found["type"] not in kinds):
            raise Refusal("missing-or-forward-reference", "replay")
        return found

    def record(self, reference, *kinds):
        return thaw(self.node(reference, *kinds)["value"])

    def _floors(self):
        if self.freshness is None:
            return
        for i, (count, tail, floor, expected) in enumerate((
            (self.trust.count, self.trust.tail, self.freshness.policy_count, self.freshness.policy_tail),
            (self.journal_count, self.journal_tail, self.freshness.decision_count, self.freshness.decision_tail))):
            if count == floor:
                if tail != expected:
                    raise Refusal("head-rollback", "replay")
                self.floor_seen[i] = True

    def append(self, envelope):
        if self.failed:
            raise Refusal("replay-failed", "replay")
        try:
            return self._append(envelope)
        except Exception:
            self.failed = True
            raise

    def _append(self, envelope):
        if type(envelope) is not bytes:
            raise Refusal("bytes-required", "replay")
        if self.count >= MAX_ENTRIES or self.bytes + len(envelope) > MAX_TOTAL_BYTES:
            raise Refusal("aggregate-limit", "replay")
        decoded = _decode_envelope(envelope)
        body = decoded[2]["predicate"]
        kind = body.get("type") if type(body) is dict else None
        if type(kind) is not str:
            raise Refusal("unsupported-record-type", "replay")
        if self.pending is not None and kind != "journal-entry":
            raise Refusal("event-not-journaled", "replay")
        verified = (self.trust.append(envelope, _decoded=decoded) if kind in TRUST_TYPES
                    else self.trust.authenticate(envelope, _decoded=decoded))
        record = verified.record
        identity = verified.envelope_sha256
        if identity in self.nodes:
            raise Refusal("duplicate-record", "replay")
        instant = time_value(record["issued_at"])
        if self.last_time is not None and instant < self.last_time:
            raise Refusal("history-time-order", "replay")
        for reference in references(record):
            if reference["sha256"] == identity:
                raise Refusal("self-reference", "replay")
            self.node(reference)
        if kind not in TRUST_TYPES | EVENTS | {"journal-entry", "authority-head"}:
            if record["sequence"] != 1 or record["previous"] is not None:
                raise Refusal("evidence-sequence", "replay")
        if kind in EVENTS:
            previous = None if self.journal_sha is None else {"type": "journal-entry", "sha256": self.journal_sha}
            if record["sequence"] != self.journal_count+1 or record["previous"] != previous:
                raise Refusal("event-sequence", "replay")
            self.pending = (verified, record)
        elif kind == "journal-entry":
            self._journal(record, identity)
        elif kind == "authority-head":
            self._head(record, identity)
        elif kind == "validation":
            policy = self.trust.policy.record
            if record["native"] != policy["native"] or record["release"] != policy["release"]:
                raise Refusal("validation-pins", "replay")
            try:
                result, producer = self.native_evidence(record["output_sha256"])
            except (KeyError, LookupError, OSError, TypeError, ValueError):
                raise Refusal("native-evidence-unavailable", "replay") from None
            self.native[identity] = native_projection(result, producer, record)
        elif kind == "storage-copy":
            self._copy_policy(record)
            self.copies.setdefault((record["object"]["sha256"], record["object"]["length"]), set()).add(record["role"])
        projection = {"type": kind, **{key: record[key] for key in RETAIN.get(kind, ())}}
        if kind in TRUST_TYPES:
            projection = self.trust.records[identity].record
        elif kind == "journal-entry":
            projection = {"type": kind}
        self.nodes[identity] = {"type": kind, "value": freeze(projection), "length": len(envelope),
                                "payload": digest(verified.payload), "record": digest(verified.record_bytes),
                                "refs": tuple((ref["type"], ref["sha256"]) for ref in references(record))}
        self.count += 1
        self.bytes += len(envelope)
        self.last_time = instant
        self.last_kind = kind
        self._floors()
        return identity

    def _copy_policy(self, record):
        policy = self.trust.policy.record
        location = next((row for row in policy["locations"] if row["role"] == record["role"]), None)
        if (location is None or record["location_id"] != location["location_id"]
            or record["configuration_policy_sha256"] != policy["storage_policy_sha256"]):
            raise Refusal("copy-policy", "replay")

    def _copies(self, locations, artifact):
        if [row["role"] for row in locations] != ["primary", "recovery"]:
            raise Refusal("copy-roles", "replay")
        for location in locations:
            copy = self.record(location["evidence"], "storage-copy")
            if any(copy[key] != location[key] for key in ("role", "location_id", "object", "object_key")) or location["object"] != artifact:
                raise Refusal("copy-evidence-binding", "replay")
            self._copy_policy(copy)

    def _head(self, record, identity):
        previous = None if self.last_head is None else {"type": "authority-head", "sha256": self.last_head}
        if (record["sequence"] != self.head_count+1 or record["previous"] != previous
            or record["policy_history"] != {"count": self.trust.count, "tail": self.trust.tail}
            or record["decisions"] != {"count": self.journal_count, "tail": self.journal_tail}):
            raise Refusal("head-completeness", "replay")
        self.head, self.last_head = record, identity
        self.head_count += 1

    def _journal(self, record, identity):
        previous = None if self.journal_sha is None else {"type": "journal-entry", "sha256": self.journal_sha}
        if self.pending is None:
            raise Refusal("journal-event-required", "replay")
        verified, event = self.pending
        event_id = verified.envelope_sha256
        if (record["stream"] != "decisions" or record["sequence"] != self.journal_count+1
            or record["previous"] != previous or record["previous_commitment"] != self.journal_tail
            or record["event"] != {"type": event["type"], "sha256": event_id}
            or record["payload_sha256"] != digest(verified.payload)):
            raise Refusal("journal-chain", "replay")
        kind = event["type"]
        expected = (event["identities"]["snapshot_id"] if kind == "acceptance" else
                    event["decision_id"] if kind == "cancellation" else
                    event["acceptance_id"] if kind in ("publication-finalization", "stream-permit") else None)
        if record["decision_id"] != expected:
            raise Refusal("journal-decision", "replay")
        if kind == "acceptance":
            self._authorize(event, verified)
        elif kind == "cancellation":
            if any(item.get("candidate_id") == event["candidate_id"] for item in self.decisions.values()):
                raise Refusal("decision-exclusivity", "replay")
            self.index.transition(expected, "cancel")
            self.decisions[expected] = {"state": "cancel", "candidate_id": event["candidate_id"]}
        elif kind == "publication-finalization":
            self._finalize(event, verified)
        elif kind == "denial":
            self._deny(event, event_id)
        elif kind == "authorized-removal":
            self._remove(event)
        elif kind == "stream-permit":
            self._permit(event, event_id)
        self.journal_count += 1
        self.journal_tail = commitment(self.journal_tail, identity, event_id)
        self.journal_sha = identity
        self.pending = None
        # Signed event bodies are consumed once. Retain only the typed locator.
        self.nodes[event_id]["value"] = freeze({"type": kind})

    def _authorize(self, record, verified):
        snapshot = record["identities"]["snapshot_id"]
        if snapshot in self.decisions:
            raise Refusal("decision-exclusivity", "replay")
        endorsement = self.record(record["endorsement"], "upload-endorsement")
        validation = self.record(record["validation"], "validation")
        instant = time_value(record["issued_at"])
        grant = grant_at(self.trust, record["grant"], record["actor_id"], instant, "upload")
        enrollment = self.trust._active_enrollment(record["enrollment"], record["actor_id"], instant)
        if (record["contributor_key"] != enrollment["key"] or grant["enrollment"] != record["enrollment"]
            or any(endorsement[key] != record[key] for key in ("actor_id", "enrollment", "grant", "identities", "carrier_length"))
            or not time_value(endorsement["issued_at"]) <= instant < time_value(endorsement["expires_at"])
            or any(validation[key] != record[key] for key in ("identities", "carrier_length", "native", "release"))
            or validation["authorization"] != record["grant"] or validation["candidate_id"] != endorsement["candidate_id"]
            or validation["parent"] != endorsement["parent"]
            or record["signer_policy_identity"] != self.trust.policy.envelope_sha256):
            raise Refusal("acceptance-evidence-binding", "replay")
        history = self.trust.signing_history([record["enrollment"],
            *(row["enrollment"] for row in validation["coverage"]["verified"])])
        if record["signing_history"] != history:
            raise Refusal("signing-history-coverage", "replay")
        parent_ref = endorsement["parent"]
        parent = self.record(parent_ref, "parent-link")
        registration_id = parent["registration"]["sha256"]
        registration = self.trust._reference(parent["registration"], "run-registration")
        native = self.native[record["validation"]["sha256"]]
        for reference, fingerprint in native["signers"]:
            signer = self.trust._reference(reference, "key-enrollment", "key-rotation")
            if signer["key"]["fingerprint"] != fingerprint:
                raise Refusal("native-signer-binding", "replay")
        for prior_item in self.decisions.values():
            if prior_item["state"] == "authorize":
                prior_item["publication"] = self._publication(prior_item)
        prior, parent_id = check_parent(parent, registration, native, self.decisions,
            record | {"parent_link": parent_ref["sha256"]}, registration_id)
        self._copies(record["copies"], record["accepted_representation"])
        # Prerequisites are finite: typed authority/evidence objects, excluding
        # storage observations and stream containers. Their copies do not recurse.
        required = set()
        stack = list(references(record))
        while stack:
            reference = stack.pop()
            if reference["type"] in ("storage-copy", "authority-head", "journal-entry") or reference["sha256"] in required:
                continue
            node = self.node(reference)
            required.add(reference["sha256"])
            stack.extend({"type": kind, "sha256": sha} for kind, sha in node["refs"])
        for reference in required:
            node = self.nodes[reference]
            if self.copies.get((reference, node["length"]), set()) != {"primary", "recovery"}:
                raise Refusal("prerequisite-copies-incomplete", "replay")
        acceptance_id = digest(b"wildcat/checkpoint-authority/acceptance/v1\x00" + verified.record_bytes)
        item = {"state": "authorize", "acceptance_id": acceptance_id, "receipt": verified.envelope_sha256,
            "receipt_length": self.nodes[verified.envelope_sha256]["length"],
            "payload": digest(verified.payload), "snapshot_id": snapshot, "identities": record["identities"],
            "archive": record["accepted_representation"], "registration": registration_id,
            "producer": native["producer"], "producer_count": native["count"], "prior": prior,
            "parent": parent_id, "poisoned": False, "denied": False, "publication": "incomplete",
            "finalization": None, "authorization_count": self.journal_count+1,
            "enrollment": record["enrollment"], "history": history, "actor_id": record["actor_id"],
            "grant": record["grant"], "candidate_id": endorsement["candidate_id"], "prerequisites": sorted(required)}
        if any(old.get("candidate_id") == item["candidate_id"] for old in self.decisions.values()):
            raise Refusal("candidate-decision-conflict", "replay")
        for denial in self.denials.values():
            if self._matches(item, denial):
                raise Refusal("authorization-denied", "replay")
        self.index.transition(snapshot, "authorize")
        self.decisions[snapshot] = item
        self.acceptances[acceptance_id] = snapshot
        self.snapshots[snapshot] = verified.envelope_sha256
        del self.native[record["validation"]["sha256"]]

    def _accepted(self, acceptance_id):
        if acceptance_id not in self.acceptances:
            raise Refusal("acceptance-required", "replay")
        return self.decisions[self.acceptances[acceptance_id]]

    def _finalize(self, record, verified):
        item = self._accepted(record["acceptance_id"])
        head = self.record(record["authorization_head"], "authority-head")
        if (record["acceptance"]["sha256"] != item["receipt"] or item["finalization"] is not None
            or item["denied"] or head["decisions"]["count"] < item["authorization_count"]
            or record["authorization_head"]["sha256"] != self.last_head):
            raise Refusal("finalization-binding", "replay")
        grant_at(self.trust, item["grant"], item["actor_id"], time_value(record["issued_at"]), "upload")
        self._copies(record["archives"], item["archive"])
        self._copies(record["receipts"], {"sha256": item["receipt"], "length": item["receipt_length"]})
        self.index.transition(item["snapshot_id"], "finalize")
        item["finalization"] = verified.envelope_sha256
        item["finalization_length"] = self.nodes[verified.envelope_sha256]["length"]
        item["finalization_count"] = self.journal_count+1

    def _matches(self, item, denial):
        target = denial["target"]
        kind = target["kind"]
        return (kind == "snapshot" and target["snapshot_id"] == item["snapshot_id"]
            or kind == "representation" and target["outer_sha256"] == item["archive"]["sha256"]
            or kind == "run" and target["run_id"] == self.trust.bootstrap.run_id
            or kind == "key" and (target["enrollment"] == item["enrollment"] or target["enrollment"] in item["history"]))

    def _deny(self, record, identity):
        if record["policy_head"]["sha256"] != self.last_head:
            raise Refusal("denial-head", "replay")
        affected = set()
        self.denials[identity] = {"target": record["target"], "descendants": record["descendants"], "affected": affected}
        for item in self.decisions.values():
            if item["state"] == "authorize" and self._matches(item, record):
                affected.add(item["snapshot_id"])
                item["denied"] = True
                item["poisoned"] |= record["descendants"] == "poison"
                self.index.transition(item["snapshot_id"], "deny")
        # Parents always precede descendants, so one insertion-order traversal closes poison.
        for item in self.decisions.values():
            if (record["descendants"] == "poison" and item.get("parent")
                and self._accepted(item["parent"])["snapshot_id"] in affected):
                affected.add(item["snapshot_id"])
                item["denied"] = item["poisoned"] = True
                self.index.transition(item["snapshot_id"], "deny")

    def _remove(self, record):
        denial = self.denials.get(record["denial"]["sha256"])
        if denial is None:
            raise Refusal("removal-denial", "replay")
        allowed = {}
        for item in self.decisions.values():
            if item["state"] == "authorize" and item["snapshot_id"] in denial["affected"]:
                allowed[item["archive"]["sha256"]] = item["archive"]["length"]
                allowed[item["receipt"]] = item["receipt_length"]
                if item["finalization"]:
                    allowed[item["finalization"]] = item["finalization_length"]
        for artifact in record["removed"]:
            if allowed.get(artifact["sha256"]) != artifact["length"] or artifact["sha256"] in self.removals:
                raise Refusal("removal-scope", "replay")
            self.removals[artifact["sha256"]] = artifact["length"]

    def _publication(self, item):
        if not item["finalization"]:
            return "incomplete"
        roles = self.copies.get((item["finalization"], item["finalization_length"]), set())
        return "complete" if roles == {"primary", "recovery"} else "incomplete"

    def _permit(self, record, identity):
        item = self._accepted(record["acceptance_id"])
        head = self.record(record["head"], "authority-head")
        nonce = (record["actor_id"], record["session_id"], record["nonce"])
        if (record["head"]["sha256"] != self.last_head or item["denied"]
            or head["policy_history"] != {"count": self.trust.count, "tail": self.trust.tail}
            or head["decisions"] != {"count": self.journal_count, "tail": self.journal_tail}
            or self._publication(item) != "complete" or record["finalization"]["sha256"] != item["finalization"]
            or (record["outer_sha256"], record["receipt_sha256"]) != (item["archive"]["sha256"], item["receipt"])
            or head["decisions"]["count"] < item["finalization_count"]):
            raise Refusal("permit-ineligible", "replay")
        issued = time_value(record["issued_at"])
        if not time_value(head["issued_at"]) <= issued < time_value(head["expires_at"]):
            raise Refusal("permit-head-stale", "replay")
        grant_at(self.trust, record["grant"], record["actor_id"], issued, "download")
        if nonce in self.nonces:
            raise Refusal("permit-nonce-used", "replay")
        self.index.transition(item["snapshot_id"], "permit")
        self.nonces.add(nonce)

    def finish(self, *, presence=None):
        """Return only complete-head history; absent freshness never authorizes use.

        Optional presence is the caller's exact scoped GET/hash observation map,
        keyed by (object digest, primary|recovery), with bool values. It is not
        inferred from historical copy claims. Missing rows mean unknown.
        """
        if self.failed or self.pending is not None or self.head is None or self.last_kind != "authority-head":
            raise Refusal("history-incomplete", "replay")
        if (self.head["policy_history"] != {"count": self.trust.count, "tail": self.trust.tail}
            or self.head["decisions"] != {"count": self.journal_count, "tail": self.journal_tail}):
            raise Refusal("head-completeness", "replay")
        fresh = current(self.head, self.trust.policy.record, self.freshness, self.floor_seen)
        if presence is not None and (type(presence) is not dict or len(presence) > MAX_ENTRIES
            or any(type(key) is not tuple or len(key) != 2 or key[1] not in ("primary", "recovery") or type(value) is not bool for key, value in presence.items())):
            raise Refusal("presence-shape", "replay")
        for key in presence or ():
            validate(key[0], HASH)
        rows = []
        for snapshot, item in self.decisions.items():
            if item["state"] == "cancel":
                continue
            publication = self._publication(item)
            artifacts = [*item["prerequisites"], item["archive"]["sha256"], item["receipt"], item["finalization"]]
            if presence is not None:
                missing = [obj for obj in artifacts if obj is not None and any(presence.get((obj, role)) is not True for role in ("primary", "recovery"))]
                if missing:
                    publication = "authorized-absence" if all(obj in self.removals for obj in missing) else "unexplained-absence"
            item["publication"] = publication
            eligible = "unknown" if not fresh else "denied" if item["denied"] else "unavailable" if publication != "complete" or presence is None else "eligible"
            rows.append({"acceptance_id": item["acceptance_id"], "identities": item["identities"],
                "receipt_sha256": item["receipt"], "finalization_sha256": item["finalization"],
                "historical": "valid", "publication": publication, "current_eligibility": eligible})
        return {"schema": "checkpoint-authority-replay/v1", "complete": True,
            "head_sha256": self.last_head, "policy_history": self.head["policy_history"],
            "decisions": self.head["decisions"], "records": self.count, "bytes": self.bytes,
            "accepted": sorted(rows, key=lambda row: row["acceptance_id"]),
            "cancelled": sum(row["state"] == "cancel" for row in self.decisions.values()),
            "historical_permits": len(self.nonces), "offline_unused_nonce": "unknown",
            "gateway_execution": "not-established"}

    def retry(self, envelope):
        """Check a signature retry against the first canonical decision without mutation.

        The signer is authenticated through the replayed policy, never through a
        caller-supplied key, and nothing here appends to the journal.
        """
        verified = self.trust.authenticate(envelope)
        record = verified.record
        if record["type"] != "acceptance":
            raise Refusal("acceptance-required", "replay")
        identity = digest(b"wildcat/checkpoint-authority/acceptance/v1\x00" + verified.record_bytes)
        item = self._accepted(identity)
        if item["payload"] != digest(verified.payload):
            raise Refusal("retry-payload", "replay")
        return {"acceptance_id": identity, "receipt_sha256": item["receipt"],
            "disposition": "exact-retry" if verified.envelope_sha256 == item["receipt"] else "equivalent-signature",
            "new_decision": False}

    def equivalent(self, validation):
        """Bind a newly authenticated validation to the canonical accepted representation."""
        value = self.record(validation, "validation")
        item = self.decisions.get(value["identities"]["snapshot_id"])
        proof = self.native.get(validation["sha256"])
        if not item or item["state"] != "authorize" or proof is None or self._publication(item) != "complete":
            raise Refusal("equivalence-unavailable", "replay")
        if proof["producer"] != item["producer"]:
            raise Refusal("semantic-conflict", "replay")
        return {"state": "equivalent_snapshot", "acceptance_id": item["acceptance_id"],
            "outer_sha256": item["archive"]["sha256"], "receipt_sha256": item["receipt"],
            "submitted_alternate_accepted": False, "new_child": False}


def replay(envelopes, bootstrap, tools, *, native_evidence, freshness=None, presence=None):
    reader = Replay(bootstrap, tools, native_evidence=native_evidence, freshness=freshness)
    for envelope in envelopes:
        reader.append(envelope)
    return reader.finish(presence=presence)
