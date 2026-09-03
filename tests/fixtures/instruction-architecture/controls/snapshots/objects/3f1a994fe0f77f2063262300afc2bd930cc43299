#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import sys


ARITY = {
    # sapheneia specimen
    "msg.front": 2, "msg.ask": 2, "msg.visible": 2, "msg.absent": 2,
    "remains": 1, "msg.tail": 3, "claim": 3, "pref": 1, "asks": 2,
    "msg.explain": 4, "destructive": 1, "confirm": 2, "genuine": 1,
    "ask": 3, "rank": 1, "force": 1, "conflict": 2, "obey": 1,
    "preserve": 2, "msg.conforms": 1,
    # phylax specimen
    "sec.ingress": 1, "argv.list": 1, "dep.pin_exact": 1,
    "secret.env": 1, "check.unavailable": 1, "continue": 1,
    "secret.commit": 1, "secret.log": 1, "argv.has": 2, "derived": 2,
    "shell.exec": 1, "source": 2, "eval": 1, "query": 1, "path.use": 1,
    "purpose": 2, "verify.weaken": 1, "ingest.new": 1, "test.equiv": 2,
    "url.guard": 2, "dns_rebind_risk": 1, "resolve_once": 1,
    "secured_by": 1,
    # reachable module definitions
    "truth_source": 2, "created_by": 2, "local_sig.valid": 1,
    "prov.exact1": 1, "pushed": 1, "gh.verified_valid": 1,
    "merge_sha": 1, "step_pr.not_base": 1, "step.merge_during_steps": 1,
    "step.branch_from_stack": 1, "stack.lands_integrate": 1,
    "shape_before_fields": 1, "reject_not_coerce": 1, "bounded": 2,
    "json.stdlib": 1, "unpickle": 1,
    # fiat specimen
    "receipt.fail": 1, "advance": 1, "config.change": 1,
    "allowed_config": 1, "state.source": 1, "occurred": 1,
    "claim_occurred": 1, "git.receipt": 1, "git.stack_shape": 1,
    "git.base_merges_gt": 2, "issue.attach_after": 1, "routine_left": 1,
    "claim_complete": 1, "issue.create": 1, "contributor_check": 1,
    "disclose": 1,
    # brevitas full specimen
    "frontier.advance": 1, "read": 1, "frontier.mature": 1, "run": 1,
    "recommend": 1, "unk": 1, "performs": 2, "active": 1, "shape": 1,
    "invoked": 1, "output.kind": 2, "topic.in": 2,
    "excluded_class": 1,
    "report": 1, "constrain": 1, "validate": 2, "causal": 1, "render": 1,
    "introduce_claim": 1, "exact.keep": 1, "keep": 1, "fit": 2,
    "yield": 1, "irreducible": 1, "compression_drops": 1,
    "exception.use": 1, "adjacent_before": 2, "line.extra": 1,
    "restate": 1, "intro": 1, "budget": 2, "schema": 2, "order": 1,
    "render.with": 2, "adjacent": 1, "between": 2, "table": 1,
    "ge": 2, "rows": 1, "data_cols": 1, "headings": 1,
    "sections_excluding_title": 1, "le": 2, "qualifiers": 1,
    "prose": 1, "phrase": 1, "reprint": 1, "quote": 1, "target": 1,
    "mode": 1, "lint.mode": 1, "material": 1, "diag": 1, "fix": 1,
    "rerun": 1, "outside": 1, "host.requires": 1, "emit": 1,
    "eval.check": 1, "apply": 2, "change": 1, "conforms": 2,
    "present": 1, "tokens_survive": 3, "save": 1, "handoff": 1,
    "derived": 2, "derivation.of": 1, "restore": 1, "exception.scoped": 1,
}

DIRECTIVE_UNARY = {"!", "-", "+"}
TERM_UNARY = {"~"}
TERM_BINARY = {"=", "=>"}
DIRECTIVE_BINARY = {"?", "/", "@", "^"}
ORDER_BINARY = {"<"}
ROOT_KINDS = {
    "definition", "directive", "order", "override", "promise", "handoff",
    "transition", "rule", "exception", "import",
}


class Refusal(ValueError):
    pass


@dataclass(frozen=True)
class Node:
    op: str
    args: tuple["Node", ...] = ()
    kind: str = "term"

    def tokens(self) -> list[str]:
        out = [self.op]
        for arg in self.args:
            out.extend(arg.tokens())
        return out


def parse(tokens: list[str], at: int = 0) -> tuple[Node, int]:
    if at >= len(tokens):
        raise Refusal("unexpected end")
    tok = tokens[at]
    at += 1

    if tok in DIRECTIVE_UNARY:
        arg, at = parse(tokens, at)
        if arg.kind != "term":
            raise Refusal(f"{tok} requires term, got {arg.kind}")
        return Node(tok, (arg,), "directive"), at

    if tok in TERM_UNARY:
        arg, at = parse(tokens, at)
        if arg.kind != "term":
            raise Refusal(f"{tok} requires term, got {arg.kind}")
        return Node(tok, (arg,), "term"), at

    if tok in TERM_BINARY:
        args = []
        for _ in range(2):
            arg, at = parse(tokens, at)
            if arg.kind != "term":
                raise Refusal(f"{tok} requires terms")
            args.append(arg)
        return Node(tok, tuple(args), "term"), at

    if tok in DIRECTIVE_BINARY:
        left, at = parse(tokens, at)
        right, at = parse(tokens, at)
        if tok in {"?", "/", "@"}:
            if left.kind != "term" or right.kind != "directive":
                raise Refusal(f"{tok} requires term then directive")
        elif left.kind != "term" or right.kind != "term":
            raise Refusal("^ requires actor/effect terms")
        return Node(tok, (left, right), "directive"), at

    if tok in ORDER_BINARY:
        args = []
        for _ in range(2):
            arg, at = parse(tokens, at)
            if arg.kind != "term":
                raise Refusal(f"{tok} requires terms")
            args.append(arg)
        return Node(tok, tuple(args), "order"), at

    if tok == "O":
        args = []
        for _ in range(5):
            arg, at = parse(tokens, at)
            if arg.kind != "term":
                raise Refusal("O requires five term fields")
            args.append(arg)
        return Node(tok, tuple(args), "override"), at

    if len(tok) >= 2 and tok[0] in {"&", "|", "*", ";"} and tok[1:].isdigit():
        count = int(tok[1:])
        if count < 1:
            raise Refusal(f"empty variadic {tok}")
        args = []
        expected = "directive" if tok[0] == ";" else "term"
        for _ in range(count):
            arg, at = parse(tokens, at)
            if arg.kind != expected:
                raise Refusal(f"{tok} requires {expected}, got {arg.kind}")
            args.append(arg)
        return Node(tok, tuple(args), "directive" if tok[0] == ";" else "term"), at

    if tok == "P":
        args = []
        for _ in range(10):
            arg, at = parse(tokens, at)
            if arg.kind != "term":
                raise Refusal("P requires ten term fields")
            args.append(arg)
        return Node(tok, tuple(args), "promise"), at

    if tok == "R":
        rule_id, at = parse(tokens, at)
        directive, at = parse(tokens, at)
        if rule_id.kind != "term" or directive.kind != "directive":
            raise Refusal("R requires id then directive")
        return Node(tok, (rule_id, directive), "rule"), at

    if tok == "D":
        if at >= len(tokens):
            raise Refusal("D missing name")
        name = Node(tokens[at])
        at += 1
        params, at = parse(tokens, at)
        body, at = parse(tokens, at)
        if name.args or params.op[:1] != "*" or body.kind != "term":
            raise Refusal("D requires name, parameter list, and term body")
        return Node(tok, (name, params, body), "definition"), at

    if tok == "H":
        args = []
        for _ in range(10):
            arg, at = parse(tokens, at)
            if arg.kind != "term":
                raise Refusal("H requires ten term fields")
            args.append(arg)
        return Node(tok, tuple(args), "handoff"), at

    if tok == ">":
        args = []
        for _ in range(7):
            arg, at = parse(tokens, at)
            if arg.kind != "term":
                raise Refusal("> requires seven term fields")
            args.append(arg)
        return Node(tok, tuple(args), "transition"), at

    if tok == "X":
        args = []
        for _ in range(8):
            arg, at = parse(tokens, at)
            if arg.kind != "term":
                raise Refusal("X requires eight term fields")
            args.append(arg)
        return Node(tok, tuple(args), "exception"), at

    if tok == "I":
        args = []
        for _ in range(2):
            arg, at = parse(tokens, at)
            if arg.kind != "term":
                raise Refusal("I requires module and digest")
            args.append(arg)
        return Node(tok, tuple(args), "import"), at

    if tok in ARITY:
        args = []
        for _ in range(ARITY[tok]):
            arg, at = parse(tokens, at)
            if arg.kind != "term":
                raise Refusal(f"predicate {tok} requires term arguments")
            args.append(arg)
        return Node(tok, tuple(args), "term"), at

    if tok in {"P", "H", ">", "D", "R", "X", "I", "!", "-", "+", "?", "/", "@", "^", "<", "O", "=>"}:
        raise Refusal(f"invalid structural token {tok}")
    return Node(tok), at


def validate(path: Path) -> tuple[str, list[Node]]:
    raw = path.read_bytes()
    if b"\r" in raw or not raw.endswith(b"\n"):
        raise Refusal("canonical LF/final-LF violation")
    text = raw.decode("ascii")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("N0 "):
        raise Refusal("missing N0 header")
    nodes = []
    for lineno, line in enumerate(lines[1:], 2):
        if not line or line != line.strip() or "  " in line:
            raise Refusal(f"line {lineno}: noncanonical whitespace")
        tokens = line.split(" ")
        try:
            node, end = parse(tokens)
        except Refusal as exc:
            raise Refusal(f"line {lineno}: {exc}") from exc
        if end != len(tokens):
            raise Refusal(f"line {lineno}: trailing tokens {tokens[end:]}")
        if node.kind not in ROOT_KINDS:
            raise Refusal(f"line {lineno}: root {node.op} is {node.kind}")
        if node.tokens() != tokens:
            raise Refusal(f"line {lineno}: round-trip mismatch")
        nodes.append(node)
    return sha256(raw).hexdigest(), nodes


def main() -> int:
    for value in sys.argv[1:]:
        path = Path(value)
        try:
            digest, nodes = validate(path)
        except (OSError, UnicodeError, Refusal) as exc:
            print(f"REFUSE {path}: {exc}")
            return 2
        print(f"OK {path} records={len(nodes)} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
