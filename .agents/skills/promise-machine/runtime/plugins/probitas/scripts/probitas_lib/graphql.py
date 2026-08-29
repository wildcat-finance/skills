"""A GraphQL POST, with the standard library and nothing else.

Small on purpose. What it does carry is the handling that matters when the
response is attacker-influenced and the caller is writing a document from it: a
timeout, a cap on how much will be read, and a refusal to treat a GraphQL
`errors` payload as a successful empty result.

That last one is the point. A subgraph answering `{"errors": [...]}` returns
HTTP 200, so a client that only checks the status code sees a well-formed reply
with no markets in it, and reports a borrower with a delinquency history as a
borrower with a clean one.
"""

import json
import urllib.error
import urllib.request

DEFAULT_TIMEOUT = 30
MAX_RESPONSE_BYTES = 32 * 1024 * 1024


class GraphQLError(RuntimeError):
    """The venue did not answer, or answered with an error."""


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    """Refuse to follow a redirect.

    Following one would let an https endpoint hand the client off to plain
    http, or to a different host entirely, and the answer would still arrive
    looking like data from the venue that was asked. A venue that has moved is
    a configuration change, not something to discover mid-query.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GraphQLError(f"{req.full_url} redirected to {newurl}; refusing to follow")


_OPENER = urllib.request.build_opener(_NoRedirects)


def post(endpoint, query, variables=None, timeout=DEFAULT_TIMEOUT):
    """Run one query and return its `data` block, or raise."""
    if not endpoint.startswith("https://"):
        raise GraphQLError(f"refusing a non-https endpoint: {endpoint}")

    body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "probitas/0.1.0",
        },
        method="POST",
    )

    try:
        with _OPENER.open(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        raise GraphQLError(f"HTTP {error.code} from {endpoint}") from error
    except urllib.error.URLError as error:
        raise GraphQLError(f"{endpoint} unreachable: {error.reason}") from error
    except TimeoutError as error:
        raise GraphQLError(f"{endpoint} timed out after {timeout}s") from error

    if len(raw) > MAX_RESPONSE_BYTES:
        raise GraphQLError(f"response from {endpoint} over {MAX_RESPONSE_BYTES} bytes")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as error:
        raise GraphQLError(f"{endpoint} returned something that is not JSON") from error

    if not isinstance(payload, dict):
        raise GraphQLError(f"{endpoint} returned {type(payload).__name__}, not an object")

    if payload.get("errors"):
        first = payload["errors"][0]
        message = first.get("message") if isinstance(first, dict) else str(first)
        raise GraphQLError(f"{endpoint} returned an error: {message}")

    data = payload.get("data")
    if data is None:
        raise GraphQLError(f"{endpoint} returned no data block")
    return data
