"""Redaction for anything a capture records verbatim.

A build command is the likeliest place for a credential to ride along: an RPC
URL with a key in its path, a token passed as an argument, an environment
variable expanded before the shell handed the line over. Capture writes those
words into a document meant to be published and signed, so they get redacted
first.

Redaction is visible. A removed token is replaced by a marker naming what kind
of thing was there, because a statement that silently dropped an argument would
describe a command nobody ran.
"""

import re

URL = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.-]*)://(.*)$")

KEYLIKE = re.compile(r"^[A-Za-z0-9_\-]{32,}$")
"""Long enough and mixed enough to be a token rather than a word. The mixture
is checked separately, so `--optimize-runs-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
stays put."""

HEXLIKE = re.compile(r"^(0x)?[0-9a-fA-F]{40,}$")
"""An address or a hash is hex too, so hex alone is not redacted. This exists
to describe what the marker means when a private key turns up."""

DELIMITER = re.compile(r"[/?#]")
"""RFC 3986 ends a URL's authority at the first of these."""

SECRET_FLAGS = frozenset(
    {
        "--rpc-url",
        "--fork-url",
        "--private-key",
        "--mnemonic",
        "--etherscan-api-key",
        "--api-key",
        "--password",
        "--token",
    }
)

REDACTED_URL = "%s://<redacted>"
REDACTED_TOKEN = "<redacted>"


def mixed(token):
    """True when a token mixes letter kinds the way a key does and a word does not."""
    return (
        any(c.isdigit() for c in token)
        and any(c.isalpha() for c in token)
        and (any(c.isupper() for c in token) or "_" in token or "-" in token)
    )


def token(word):
    """Redact one argument, keeping enough shape to read the command."""
    if not isinstance(word, str):
        return word
    match = URL.match(word)
    if match:
        return REDACTED_URL % match.group(1)
    if HEXLIKE.match(word) and len(word.lstrip("0x")) >= 64:
        # A 32-byte hex string is a private key more often than anything else
        # worth putting on a command line. Addresses and transaction hashes are
        # shorter, and they belong in the statement.
        return REDACTED_TOKEN
    if KEYLIKE.match(word) and mixed(word):
        return REDACTED_TOKEN
    return word


def assignment(word):
    """Redact the value half of `NAME=value`, keeping the name.

    Covers both `--fork-url=https://...` and an inline `PRIVATE_KEY=0x...`,
    which is how a key most often reaches a command line without a flag in
    front of it.
    """
    name, _, value = word.partition("=")
    if name in SECRET_FLAGS:
        return "%s=%s" % (name, REDACTED_TOKEN)
    return "%s=%s" % (name, token(value))


def argv(words):
    """Redact a command line, including the value after a flag that names a secret."""
    out = []
    redact_next = False
    for word in words:
        if redact_next:
            out.append(REDACTED_TOKEN)
            redact_next = False
            continue
        if isinstance(word, str) and "=" in word:
            out.append(assignment(word))
            continue
        out.append(token(word))
        redact_next = isinstance(word, str) and word in SECRET_FLAGS
    return out


def credentials(url):
    """Strip userinfo from a URL, keeping the URL.

    A repository is recorded so a reader can find it, so redacting the whole
    thing would defeat the field. What has to go is the `user:token@` some
    tooling leaves in front of the host.

    The host starts after the last `@` ahead of the first `/`, `?` or `#`
    that follows the first `@`. Splitting at the first `@` alone turned
    `https://a@user:token@host/p` into `https://user:token@host/p`, keeping
    the credential this exists to remove. An `@` past that delimiter belongs
    to the path and stays, so `https://token@host/owner/repo.git@v1` keeps its
    ref. Whenever `URL` matches, what comes back holds no `@` ahead of its own
    first delimiter, so RFC 3986 finds no userinfo in it.

    Two shapes still come out wrong. An `@` with no userinfo in front of it is
    read as the end of one, so `https://host/repo@v1` is recorded as
    `https://v1`: the location is lost, though no credential is kept. And a
    userinfo carrying an `@` ahead of an unencoded `/`, `?` or `#`, such as
    `a@b/c` in `https://a@b/c@host/p`, reads exactly like a credential
    followed by a path holding an `@`, so `b/c@host/p` survives. RFC 3986
    allows none of those four characters unencoded in userinfo.
    """
    if not isinstance(url, str):
        return url
    match = URL.match(url)
    if not match:
        return url
    scheme, rest = match.group(1), match.group(2)
    first = rest.find("@")
    if first == -1:
        return url
    delimiter = DELIMITER.search(rest, first)
    end = delimiter.start() if delimiter else len(rest)
    host = rest.rindex("@", first, end) + 1
    return "%s://%s" % (scheme, rest[host:])


def redacted(words):
    """How many arguments a redaction removed, for recording beside the command."""
    return sum(1 for before, after in zip(words, argv(words)) if before != after)
