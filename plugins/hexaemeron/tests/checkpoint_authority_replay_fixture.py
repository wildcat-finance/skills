"""Generate compact signed histories with explicitly synthetic native attestations.

These cases exercise authority replay. They make no claim to execute native
commands; Step 3's separately pinned real-native corpus owns that evidence.
The same helpers load the committed positive history and apply its recorded
unsigned hostile mutations, so the generator and the tests read one contract.
"""
from __future__ import annotations

import base64
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_checkpoint_authority_records import AuthenticatedHostileTests, FIXTURES, specimen
from checkpoint_authority import signatures, trust
from checkpoint_authority.canonical import Refusal, canonical, digest
from checkpoint_authority.eligibility import Freshness
from checkpoint_authority.native import NativeResult
from checkpoint_authority.native_records import NATIVE_COMMIT, CONTROLLER_SHA256, PROFILE, IDENTITY_DOMAIN
from checkpoint_authority.replay import Replay, commitment

HISTORY_SCHEMA = "checkpoint-authority-replay-history/v1"
HOSTILE_SCHEMA = "checkpoint-authority-replay-hostile/v1"
HISTORY_PATH = FIXTURES / "replay-history.json"
HOSTILE_PATH = FIXTURES / "replay-hostile.json"


class Signer(AuthenticatedHostileTests):
    """Only constructed by helpers; this module is outside unittest discovery."""


class History:
    def __init__(self, signer, *, anchor_run_id=None):
        self.signer = signer
        self.keys, self.tools = signer.keys, signer.tools
        self.run_id = "fiat-" + "a"*64
        self.scope = {"repository_id": 23, "run_id": self.run_id}
        self.bootstrap = trust.Bootstrap("test", "test-service", 23, self.run_id,
            (canonical({"environment": "test", "key": self.keys["root"]}),))
        self.envelopes, self.records, self.native = [], {}, {}
        self.policy_count = self.journal_count = self.head_count = 0
        self.policy_tail = self.journal_sha = self.journal_tail = self.last_head = None
        self.clock = "2026-09-16T00:00:00Z"
        self.parents = []
        self.base = "1"*40
        self.pin = {"source_commit": NATIVE_COMMIT, "executable_sha256": CONTROLLER_SHA256, "profile": PROFILE}
        # A producer anchor naming another run is a base/run mismatch the parent join refuses.
        self.run = {"schema": "fiat-run-anchor/v1", "run_id": anchor_run_id or self.run_id,
            "repository": "example/project", "task": {"kind": "github-issue", "number": 1},
            "run_branch": "fiat/example", "initial_base_sha": self.base, "integration_branch": "main",
            "controller": {"name": "hexctl", "state_version": 1, "version": "fiat-v6.61.1"}}
        self.producer = b""
        self._producer()
        policy = self.body("authority-policy")
        policy["authorities"] = [{"key": self.keys["root"], "roles": ["policy", "operator", "validator", "copy-verifier", "signer", "journal"],
            "not_before": "2026-09-15T00:00:00Z", "not_after": "2026-09-18T00:00:00Z"}]
        policy["native"] = self.pin
        self.policy = self.add_trust(policy)
        challenge = self.body("enrollment-challenge")
        challenge.update(key=self.keys["contributor"], actor_id=1, expires_at="2026-09-16T00:05:00Z")
        challenge_ref = self.add_trust(challenge)
        enrollment = self.body("key-enrollment")
        enrollment.update(actor_id=1, key=self.keys["contributor"], not_before="2026-09-16T00:00:00Z", not_after="2026-09-18T00:00:00Z",
            proof={"challenge": challenge_ref, "signature": signatures.b64(signer.sign(trust.proof_message(self.records[challenge_ref['sha256']]), "contributor"))})
        self.enrollment = self.add_trust(enrollment)
        grant = self.body("run-grant")
        grant.update(actor_id=1, enrollment=self.enrollment, permissions=["announce", "upload", "read_status", "read_receipt", "download"],
            not_before="2026-09-16T00:00:00Z", not_after="2026-09-18T00:00:00Z")
        self.grant = self.add_trust(grant)
        registration = self.body("run-registration")
        registration.update(native_anchor_sha256=digest(canonical(self.run)), initial_base=self.base, source=self.pin,
            owner_id=1, root_authorized=True, initial_parent=None)
        self.registration = self.add_trust(registration)

    def _producer(self):
        old = json.loads(self.producer.splitlines()[-1])['hash'] if self.producer else "genesis"
        row = {"ts": "2026-09-16T00:00:00Z", "event": "init" if not self.producer else "done:push", "data": {}, "prev": old, "state": "2"*64}
        row["hash"] = digest(canonical(row))
        self.producer += canonical(row)+b"\n"

    def body(self, kind):
        value = specimen(kind)
        value.update(scope=self.scope, issuer=self.keys["root"]["fingerprint"], issued_at=self.clock, sequence=1, previous=None)
        if "policy" in value:
            value["policy"] = self.policy
        return value

    def add(self, value, key="root"):
        encoded = self.signer.envelope(value, key)
        ref = {"type": value["type"], "sha256": digest(encoded)}
        self.envelopes.append(encoded)
        self.records[ref["sha256"]] = copy.deepcopy(value)
        return ref

    def add_trust(self, value):
        value["sequence"] = self.policy_count+1
        value["previous"] = self.policy_tail
        reference = self.add(value)
        self.policy_count += 1
        self.policy_tail = reference
        return reference

    def event(self, value, decision=None):
        value["sequence"] = self.journal_count+1
        value["previous"] = None if self.journal_sha is None else {"type": "journal-entry", "sha256": self.journal_sha}
        reference = self.add(value)
        journal = self.body("journal-entry")
        journal.update(sequence=self.journal_count+1, previous=value["previous"], stream="decisions", event=reference,
            decision_id=decision, payload_sha256=digest(signatures.statement_bytes(canonical(value))), previous_commitment=self.journal_tail)
        journal_ref = self.add(journal)
        self.journal_count += 1
        self.journal_tail = commitment(self.journal_tail, journal_ref["sha256"], reference["sha256"])
        self.journal_sha = journal_ref["sha256"]
        return reference

    def head(self, challenge="challenge-1"):
        expiry=(datetime.fromisoformat(self.clock)+timedelta(seconds=300)).strftime("%Y-%m-%dT%H:%M:%SZ")
        value = self.body("authority-head")
        value.update(sequence=self.head_count+1, previous=self.last_head, challenge=challenge,
            expires_at=expiry, policy_history={"count": self.policy_count, "tail": self.policy_tail["sha256"]},
            decisions={"count": self.journal_count, "tail": self.journal_tail})
        self.last_head = self.add(value)
        self.head_count += 1
        return self.last_head

    def copies(self, artifact):
        rows = []
        for role in ("primary", "recovery"):
            record = self.body("storage-copy")
            record.update(role=role, location_id=role+"-eu", object=artifact, object_key="sha256/"+artifact["sha256"],
                get_sha256=artifact["sha256"], get_length=artifact["length"], verified_at=self.clock,
                configuration_policy_sha256=self.records[self.policy['sha256']]["storage_policy_sha256"])
            reference = self.add(record)
            rows.append({key: record[key] for key in ("role", "location_id", "object", "object_key")} | {"evidence": reference})
        return rows

    def validated(self, name, *, alternate=False, mutate_parent=None):
        if not alternate:
            self._producer()
        tail = json.loads(self.producer.splitlines()[-1])["hash"]
        evidence = {"ledger_entries": len(self.producer.splitlines()), "ledger_sha256": digest(self.producer), "ledger_tail": tail,
            "observation_bindings": 1, "observation_status": "bound", "run_anchor_sha256": digest(canonical(self.run))}
        evidence.update({key: digest(key.encode()) for key in ("observation_sha256", "policy_sha256", "runbook_sha256", "state_fingerprint", "study_sha256")})
        identity = {"schema": "fiat-checkpoint-identity/v1", "run": self.run,
            "boundary": {"kind": "post-push", "step": len(self.producer.splitlines()), "working_commit_sha": "3"*40}, "evidence": evidence}
        ids = {"snapshot_id": digest(IDENTITY_DOMAIN+canonical(identity)), "controller_manifest_sha256": digest((name+"manifest").encode()), "outer_sha256": digest(name.encode())}
        link = self.body("parent-link")
        link.update(registration=self.registration, initial_base=self.base, parents=self.parents[-1:], prior_receipts=self.parents[:], producer_prefix_sha256=digest(self.producer), native=self.pin)
        if mutate_parent:
            mutate_parent(link)
        parent = self.add(link)
        endorsement = self.body("upload-endorsement")
        endorsement.update(issuer=self.keys["contributor"]["fingerprint"], actor_id=1, enrollment=self.enrollment, grant=self.grant,
            candidate_id=name, nonce=name, identities=ids, carrier_length=123, parent=parent, expires_at="2026-09-16T00:05:00Z")
        endorsed = self.add(endorsement, "contributor")
        validation = self.body("validation")
        validation.update(candidate_id=name, attempt_id=name, lease_id=name, identities=ids, carrier_length=123,
            native=self.pin, release=self.records[self.policy['sha256']]["release"], input_sha256=ids["outer_sha256"],
            started_at=self.clock, ended_at=self.clock, authorization=self.grant, parent=parent,
            coverage={"required": ["3"*40], "verified": [{"commit": "3"*40, "enrollment": self.enrollment, "evidence_class": "local-signature"}]},
            resources={"input_bytes": 123, "output_bytes": 0, "duration_ms": 1, "peak_rss_bytes": 1})
        value = {"schema": "checkpoint-authority-native-result/v1", "complete": True, "operation_ran": True,
            "request": {"candidate_id": name, "attempt_id": name, "lease_id": name, "carrier_length": 123, **ids},
            **self.pin, "identity": {"schema": "fiat-checkpoint-identity-result/v1", "identity": identity, "snapshot_id": ids["snapshot_id"]},
            "native_results": validation["native_results"], "coverage": {
                **validation["coverage"], "complete": True,
                "verified": [dict(row, fingerprint=self.keys["contributor"]["fingerprint"], native_current_boundary=True)
                             for row in validation["coverage"]["verified"]]}}
        payload = canonical(value)
        validation["output_sha256"] = digest(payload)
        self.native[digest(payload)] = (NativeResult(payload, Path("/synthetic-unexecuted-native")), self.producer)
        validated = self.add(validation)
        return ids, parent, endorsed, validated

    def accept(self, name="candidate-1", *, finalize=True, final_copies=True, mutate_parent=None, mutate_acceptance=None):
        ids, parent, endorsed, validated = self.validated(name, mutate_parent=mutate_parent)
        record = self.body("acceptance")
        archive = {"sha256": ids["outer_sha256"], "length": 123}
        record.update(identities=ids, carrier_length=123, accepted_representation=archive, native=self.pin,
            release=self.records[self.policy['sha256']]["release"], initial_base=self.base, actor_id=1, endorsement=endorsed,
            contributor_key=self.keys["contributor"], enrollment=self.enrollment, signing_history=[self.enrollment], grant=self.grant,
            validation=validated, copies=self.copies(archive), signer_policy_identity=self.policy["sha256"],
            parent_acceptance_ids=[] if not self.parents else [self.ids[self.parents[-1]['sha256']]],
            transition={"kind": "registered-root", "registration": self.registration} if not self.parents else
            {"kind": "continuation", "parent": parent, "producer_prefix_sha256": digest(self.producer), "initial_base": self.base})
        # Copy every referenced prerequisite once in each account. Observations
        # themselves and stream containers are excluded from this finite set.
        for encoded in list(self.envelopes):
            kind = self.records[digest(encoded)]["type"]
            if kind not in ("storage-copy", "journal-entry", "authority-head", "publication-finalization"):
                self.copies({"sha256": digest(encoded), "length": len(encoded)})
        if mutate_acceptance:
            mutate_acceptance(record)
        receipt = self.event(record, ids["snapshot_id"])
        acceptance_id = digest(b"wildcat/checkpoint-authority/acceptance/v1\0"+canonical(record))
        self.ids = getattr(self, "ids", {}) | {receipt["sha256"]: acceptance_id}
        self.parents.append(receipt)
        auth_head = self.head()
        if finalize:
            final = self.body("publication-finalization")
            final.update(acceptance_id=acceptance_id, acceptance=receipt, authorization_head=auth_head,
                archives=record["copies"], receipts=self.copies({"sha256": receipt["sha256"], "length": len(next(e for e in self.envelopes if digest(e)==receipt['sha256']))}))
            finalized = self.event(final, acceptance_id)
            if final_copies:
                self.copies({"sha256": finalized["sha256"], "length": len(next(e for e in self.envelopes if digest(e)==finalized['sha256']))})
            self.head()
        return receipt, acceptance_id

    def permit(self, receipt, acceptance_id, nonce="nonce-1", session="session-1", *, mutate=None):
        final = next({"type": "publication-finalization", "sha256": key} for key, value in self.records.items()
            if value["type"] == "publication-finalization" and value["acceptance_id"] == acceptance_id)
        record = self.body("stream-permit")
        record.update(actor_id=1, session_id=session, nonce=nonce, expires_at="2026-09-16T00:01:00Z",
            outer_sha256=self.records[receipt['sha256']]["identities"]["outer_sha256"], receipt_sha256=receipt["sha256"],
            acceptance_id=acceptance_id, finalization=final, head=self.last_head, grant=self.grant)
        if mutate:
            mutate(record)
        self.event(record, acceptance_id)
        self.head()

    def deny(self, receipt, *, poison=True, mutate=None):
        record = self.body("denial")
        record.update(target={"kind": "snapshot", "snapshot_id": self.records[receipt['sha256']]["identities"]["snapshot_id"]},
            reason="operator-revoked", descendants="poison" if poison else "none", effective_at=self.clock, policy_head=self.last_head)
        if mutate:
            mutate(record)
        result = self.event(record)
        self.head()
        return result

    def reader(self, freshness=None, envelopes=None):
        reader = Replay(self.bootstrap, self.tools, native_evidence=self.native.__getitem__, freshness=freshness)
        for encoded in self.envelopes if envelopes is None else envelopes:
            reader.append(encoded)
        return reader

    def presence(self, reader):
        return {(sha, role): True for sha, length in reader.copies for role in ("primary", "recovery")}


def b64(data):
    return base64.b64encode(data).decode("ascii")


def unb64(text):
    return base64.b64decode(text.encode("ascii"), validate=True)


def export(history, *, challenge="challenge-1", now="2026-09-16T00:00:10Z"):
    """Serialize one complete history as the committed positive fixture."""
    reader = history.reader()
    result = reader.finish()
    return {"schema": HISTORY_SCHEMA,
        "note": "Synthetic signed history with ephemeral test keys and unexecuted synthetic native attestations; no native command ran and no private key is retained.",
        "bootstrap": {"environment": "test", "service": "test-service", "repository_id": 23, "run_id": history.run_id,
                      "roots": [b64(root) for root in history.bootstrap.roots]},
        "freshness": {"challenge": challenge, "now": now},
        "envelopes": [b64(encoded) for encoded in history.envelopes],
        "native": {key: {"result": b64(native.payload), "producer": b64(producer)}
                   for key, (native, producer) in history.native.items()},
        "expected": {"records": result["records"], "bytes": result["bytes"], "head_sha256": result["head_sha256"],
                     "policy_history": result["policy_history"], "decisions": result["decisions"],
                     "accepted": [row["acceptance_id"] for row in result["accepted"]],
                     "historical_permits": result["historical_permits"], "cancelled": result["cancelled"]}}


def load_history(path=HISTORY_PATH):
    value = json.loads(Path(path).read_bytes())
    if value.get("schema") != HISTORY_SCHEMA:
        raise Refusal("history-fixture", "fixture")
    return value


def bootstrap_of(history, *, run_id=None, roots=None):
    row = history["bootstrap"]
    return trust.Bootstrap(row["environment"], row["service"], row["repository_id"], run_id or row["run_id"],
                           tuple(roots if roots is not None else (unb64(root) for root in row["roots"])))


def native_of(history):
    table = {key: (NativeResult(unb64(row["result"]), Path("/synthetic-unexecuted-native")), unb64(row["producer"]))
             for key, row in history["native"].items()}
    return table.__getitem__


def freshness_of(history, *, now=None, decision_count=None, decision_tail=None):
    row, expected = history["freshness"], history["expected"]
    instant = datetime.strptime(now or row["now"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return Freshness(row["challenge"], instant, expected["policy_history"]["count"], expected["policy_history"]["tail"],
                     expected["decisions"]["count"] if decision_count is None else decision_count,
                     expected["decisions"]["tail"] if decision_tail is None else decision_tail)


HOSTILE_MUTATIONS = (
    {"id": "omitted-trust-record", "kind": "omit", "index": 2},
    {"id": "omitted-journal-entry", "kind": "omit-type", "type": "journal-entry", "occurrence": 0},
    {"id": "duplicate-trust-record", "kind": "duplicate", "index": 4},
    {"id": "duplicate-journal-entry", "kind": "duplicate-type", "type": "journal-entry", "occurrence": 0},
    {"id": "reordered-trust-records", "kind": "swap", "indexes": [1, 2]},
    {"id": "reordered-decision-events", "kind": "swap-type", "types": ["acceptance", "publication-finalization"]},
    {"id": "truncated-head", "kind": "truncate", "count": 1},
    {"id": "tampered-payload", "kind": "tamper", "index": 0},
    {"id": "tampered-signature", "kind": "tamper-signature", "index": 0},
    {"id": "foreign-root", "kind": "foreign-root"},
    {"id": "foreign-scope", "kind": "foreign-scope"},
    {"id": "stale-head", "kind": "stale-freshness", "now": "2026-09-16T01:00:00Z"},
    {"id": "rollback-below-floor", "kind": "rollback-floor"},
    {"id": "forged-decision-tail", "kind": "forged-tail"},
)
"""Unsigned mutations of the committed history; each must refuse by a recorded code."""


def _typed_indexes(history, envelopes, kind):
    found = []
    for index, encoded in enumerate(envelopes):
        statement = json.loads(unb64(json.loads(encoded)["payload"]))
        if statement["predicate"]["type"] == kind:
            found.append(index)
    return found


def replay_history(history, tools, mutation=None, *, with_freshness=False):
    """Replay the committed history, optionally under one recorded hostile mutation."""
    envelopes = [unb64(text) for text in history["envelopes"]]
    bootstrap = bootstrap_of(history)
    freshness = freshness_of(history) if with_freshness else None
    kind = None if mutation is None else mutation["kind"]
    if kind == "omit":
        del envelopes[mutation["index"]]
    elif kind == "omit-type":
        del envelopes[_typed_indexes(history, envelopes, mutation["type"])[mutation["occurrence"]]]
    elif kind == "duplicate":
        envelopes.insert(mutation["index"] + 1, envelopes[mutation["index"]])
    elif kind == "duplicate-type":
        index = _typed_indexes(history, envelopes, mutation["type"])[mutation["occurrence"]]
        envelopes.insert(index + 1, envelopes[index])
    elif kind == "swap":
        i, j = mutation["indexes"]
        envelopes[i], envelopes[j] = envelopes[j], envelopes[i]
    elif kind == "swap-type":
        i = _typed_indexes(history, envelopes, mutation["types"][0])[0]
        j = _typed_indexes(history, envelopes, mutation["types"][1])[0]
        envelopes[i], envelopes[j] = envelopes[j], envelopes[i]
    elif kind == "truncate":
        del envelopes[len(envelopes) - mutation["count"]:]
    elif kind == "tamper":
        outer = json.loads(envelopes[mutation["index"]])
        payload = bytearray(unb64(outer["payload"]))
        payload[-2] ^= 0x01
        outer["payload"] = b64(bytes(payload))
        envelopes[mutation["index"]] = canonical(outer, limit=signatures.MAX_ENVELOPE_BYTES)
    elif kind == "tamper-signature":
        outer = json.loads(envelopes[mutation["index"]])
        signature = bytearray(unb64(outer["signatures"][0]["sig"]))
        signature[-1] ^= 0x01
        outer["signatures"][0]["sig"] = b64(bytes(signature))
        envelopes[mutation["index"]] = canonical(outer, limit=signatures.MAX_ENVELOPE_BYTES)
    elif kind == "foreign-root":
        other = json.loads((FIXTURES / "other-public.json").read_bytes())
        bootstrap = bootstrap_of(history, roots=(canonical({"environment": "test", "key": other}),))
    elif kind == "foreign-scope":
        bootstrap = bootstrap_of(history, run_id="fiat-" + "b" * 64)
    elif kind == "stale-freshness":
        freshness = freshness_of(history, now=mutation["now"])
    elif kind == "rollback-floor":
        freshness = freshness_of(history, decision_count=history["expected"]["decisions"]["count"] + 1)
    elif kind == "forged-tail":
        freshness = freshness_of(history, decision_tail="f" * 64)
    elif kind is not None:
        raise Refusal("hostile-mutation", "fixture")
    reader = Replay(bootstrap, tools, native_evidence=native_of(history), freshness=freshness)
    for encoded in envelopes:
        reader.append(encoded)
    return reader


def hostile_codes(history, tools):
    """Run every recorded mutation and return its actual refusal code and stage."""
    rows = []
    for mutation in HOSTILE_MUTATIONS:
        try:
            reader = replay_history(history, tools, mutation, with_freshness=True)
            reader.finish()
        except Refusal as refusal:
            rows.append({**mutation, "code": refusal.code, "stage": refusal.stage})
        else:
            raise AssertionError("hostile mutation admitted: " + mutation["id"])
    return {"schema": HOSTILE_SCHEMA, "cases": rows}
