"""Caller-owned freshness and grant scope; offline history supplies neither."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from .canonical import Refusal
from .records import time_value
from .schema import HASH, ID, POSITIVE, validate


@dataclass(frozen=True)
class Freshness:
    """Values obtained independently by the caller, never inferred from the journal."""
    challenge: str
    now: datetime
    policy_count: int
    policy_tail: str | None
    decision_count: int
    decision_tail: str | None

    def check(self):
        validate(self.challenge, ID)
        if type(self.now) is not datetime or self.now.utcoffset() is None:
            raise Refusal("trusted-time-required", "eligibility")
        for count, tail in ((self.policy_count, self.policy_tail), (self.decision_count, self.decision_tail)):
            if type(count) is not int or count < 0 or count > 65536 or (count == 0) != (tail is None):
                raise Refusal("head-floor", "eligibility")
            if tail is not None:
                validate(tail, HASH)


def current(head, policy, freshness, floor_seen):
    if freshness is None:
        return False
    if not isinstance(freshness, Freshness):
        raise Refusal("freshness-input", "eligibility")
    freshness.check()
    if not all(floor_seen):
        raise Refusal("head-rollback", "eligibility")
    now, issued, expiry = freshness.now, time_value(head["issued_at"]), time_value(head["expires_at"])
    if head["challenge"] != freshness.challenge:
        raise Refusal("head-challenge", "eligibility")
    if not issued <= now < expiry or (now-issued).total_seconds() > policy["max_head_age_seconds"]:
        raise Refusal("head-stale", "eligibility")
    return True


def grant_at(trust, reference, actor, instant, permission):
    grant = trust._reference(reference, "run-grant")
    if grant["actor_id"] != actor or permission not in grant["permissions"]:
        raise Refusal("grant-scope", "eligibility")
    if not time_value(grant["not_before"]) <= instant < time_value(grant["not_after"]):
        raise Refusal("grant-expired", "eligibility")
    trust._active_enrollment(grant["enrollment"], actor, instant)
    return grant


GATEWAY_CONTRACT = {
    "cancel_push_required": True, "head_check_max_seconds": 2,
    "head_check_max_bytes": 8 * 1024 * 1024, "channel_stale_cancel_seconds": 5,
    "range_enabled": False, "delivered_bytes_recall": False,
    "gateway_execution_established": False, "offline_unused_nonce_established": False,
}
