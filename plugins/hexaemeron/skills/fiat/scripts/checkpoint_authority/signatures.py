"""Exact DSSE bytes and pinned, public-key-only signature verification."""
from __future__ import annotations

import base64
from dataclasses import dataclass
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import struct
import subprocess
import tempfile
import time

from .canonical import Refusal, canonical, decode, digest
from .records import parse_record
from .schema import KEY, PREDICATE, STATEMENT, validate

PAYLOAD_TYPE = "application/vnd.in-toto+json"
SPKI_PREFIX = bytes.fromhex("3059301306072a8648ce3d020106082a8648ce3d03010703420004")
P256_ORDER = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
NAMESPACE = "wildcat-checkpoint-authority-v1"
MAX_ENVELOPE_BYTES = 128 * 1024


def b64decode(value, *, maximum=65536):
    if type(value) is not str or len(value) > (maximum + 2) // 3 * 4:
        raise Refusal("base64-limit", "signature")
    if re.fullmatch(r"[A-Za-z0-9+/_-]*={0,2}", value, re.ASCII) is None:
        raise Refusal("invalid-base64", "signature")
    if any(x in value for x in "+/") and any(x in value for x in "-_"):
        raise Refusal("mixed-base64", "signature")
    bare = value.rstrip("=")
    padding = len(value) - len(bare)
    required = (-len(bare)) % 4
    if required == 3 or padding not in (0, required):
        raise Refusal("invalid-base64", "signature")
    try:
        data = base64.b64decode(bare + "=" * required, altchars=b"-_", validate=True)
    except ValueError:
        raise Refusal("invalid-base64", "signature") from None
    if len(data) > maximum or base64.b64encode(data).decode().rstrip("=") != bare.replace("-", "+").replace("_", "/"):
        raise Refusal("invalid-base64", "signature")
    return data


def b64(data):
    return base64.b64encode(data).decode("ascii")


def pae(payload: bytes, payload_type=PAYLOAD_TYPE) -> bytes:
    if type(payload) is not bytes or type(payload_type) is not str:
        raise Refusal("invalid-pae", "signature")
    kind = payload_type.encode("utf-8")
    return b"DSSEv1 " + str(len(kind)).encode() + b" " + kind + b" " + str(len(payload)).encode() + b" " + payload


def check_der(data):
    if type(data) is not bytes or not 8 <= len(data) <= 72 or data[:1] != b"\x30" or data[1] != len(data) - 2:
        raise Refusal("invalid-der", "signature")
    cursor = 2
    for _ in range(2):
        if cursor + 2 > len(data) or data[cursor] != 2:
            raise Refusal("invalid-der", "signature")
        size = data[cursor + 1]
        cursor += 2
        integer = data[cursor:cursor + size]
        cursor += size
        if not 1 <= size <= 33 or len(integer) != size or integer[0] & 128 or (size > 1 and integer[0] == 0 and integer[1] < 128):
            raise Refusal("invalid-der", "signature")
        if not 0 < int.from_bytes(integer) < P256_ORDER:
            raise Refusal("invalid-der", "signature")
    if cursor != len(data):
        raise Refusal("invalid-der", "signature")


@dataclass(frozen=True)
class ToolPin:
    """A caller-owned executable pin; no record may choose a tool or pathname."""
    name: str
    path: str
    sha256: str

    def check(self):
        if type(self.name) is not str or type(self.path) is not str or type(self.sha256) is not str or self.name not in ("openssl", "ssh-keygen", "gpg", "cosign") or not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise Refusal("tool-pin", "signature")
        path = Path(self.path)
        if not path.is_absolute():
            raise Refusal("tool-pin", "signature")
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            try:
                before = os.fstat(fd)
                if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= 256 * 1024 * 1024:
                    raise Refusal("tool-pin", "signature")
                import hashlib
                hasher = hashlib.sha256()
                size = 0
                with os.fdopen(fd, "rb", closefd=False) as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        size += len(chunk)
                        if size > 256 * 1024 * 1024:
                            raise Refusal("tool-pin", "signature")
                        hasher.update(chunk)
                after = os.fstat(fd)
                identity = lambda x: (x.st_dev, x.st_ino, x.st_mode, x.st_size, x.st_mtime_ns, x.st_ctime_ns)
                if identity(before) != identity(after) or identity(before) != identity(path.stat()) or hasher.hexdigest() != self.sha256:
                    raise Refusal("tool-pin", "signature")
            finally:
                os.close(fd)
        except OSError:
            raise Refusal("tool-unavailable", "signature") from None


def _run(pin, args, directory, *, input_bytes=b"", timeout=10):
    """Drain bounded child streams under one deadline; diagnostics stay private."""
    pin.check()
    environment = {"PATH": "/usr/bin:/bin", "HOME": str(directory), "LC_ALL": "C",
                   "OPENSSL_CONF": "/dev/null", "GNUPGHOME": str(directory)}
    try:
        with tempfile.TemporaryFile() as source:
            source.write(input_bytes)
            source.seek(0)
            process = subprocess.Popen([pin.path, *args], stdin=source,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=directory,
                env=environment, start_new_session=True)
            buffers = {"stdout": bytearray(), "stderr": bytearray()}
            try:
                deadline = time.monotonic() + timeout
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
                    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
                    while selector.get_map():
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise Refusal("tool-timeout", "signature")
                        for key, _ in selector.select(min(remaining, 0.1)):
                            chunk = os.read(key.fileobj.fileno(), 8192)
                            if not chunk:
                                selector.unregister(key.fileobj)
                                continue
                            buffers[key.data].extend(chunk)
                            cap = 65536 if key.data == "stdout" else 16384
                            if len(buffers[key.data]) > cap:
                                raise Refusal("tool-output-limit", "signature")
                    exit_code = process.wait(timeout=max(0.001, deadline - time.monotonic()))
            finally:
                # An exited leader can leave descendants holding output pipes.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                process.stdout.close()
                process.stderr.close()
        pin.check()
        return exit_code, bytes(buffers["stdout"]), bytes(buffers["stderr"])
    except subprocess.TimeoutExpired:
        raise Refusal("tool-timeout", "signature") from None
    except (OSError, subprocess.SubprocessError):
        raise Refusal("tool-unavailable", "signature") from None


def public_key(key):
    """Check canonical public encodings and role-specific fingerprints."""
    validate(key, KEY)
    data = b64decode(key["public"], maximum=8192)
    if b64(data) != key["public"]:
        raise Refusal("noncanonical-public-key", "signature")
    kind = key["format"]
    if kind == "spki-p256":
        if len(data) != 91 or not data.startswith(SPKI_PREFIX):
            raise Refusal("wrong-key-curve", "signature")
        point = data[len(SPKI_PREFIX):]
        x, y = int.from_bytes(point[:32]), int.from_bytes(point[32:])
        prime = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
        coefficient = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
        if x >= prime or y >= prime or (y*y - (x*x*x - 3*x + coefficient)) % prime:
            raise Refusal("invalid-public-key", "signature")
        expected = digest(data)
    elif kind.startswith("ssh-"):
        offset = 0
        parts = []
        while offset < len(data):
            if offset + 4 > len(data):
                raise Refusal("invalid-public-key", "signature")
            size = struct.unpack(">I", data[offset:offset + 4])[0]
            offset += 4
            if size > len(data) - offset:
                raise Refusal("invalid-public-key", "signature")
            parts.append(data[offset:offset + size])
            offset += size
        good = (kind == "ssh-ed25519" and len(parts) == 2 and parts[0] == b"ssh-ed25519" and len(parts[1]) == 32)
        good |= (kind == "ssh-p256" and len(parts) == 3 and parts[:2] == [b"ecdsa-sha2-nistp256", b"nistp256"] and len(parts[2]) == 65 and parts[2][:1] == b"\x04")
        if not good:
            raise Refusal("invalid-public-key", "signature")
        expected = "SHA256:" + b64(bytes.fromhex(digest(data))).rstrip("=")
    else:
        # Native OpenPGP canonical export/fingerprint checks require the pinned tool.
        if not data or len(data) > 6144:
            raise Refusal("invalid-public-key", "signature")
        return data
    if key["fingerprint"] != expected or b64(data) != key["public"]:
        raise Refusal("key-fingerprint", "signature")
    return data


def verify_signature(message: bytes, signature: bytes, key: dict, tools: dict):
    if (type(message) is not bytes or len(message) > MAX_ENVELOPE_BYTES
        or type(signature) is not bytes or not 1 <= len(signature) <= 16384):
        raise Refusal("signature-input-limit", "signature")
    data = public_key(key)
    with tempfile.TemporaryDirectory(prefix="checkpoint-public-verify-") as temporary:
        directory = Path(temporary)
        (directory / "message").write_bytes(message)
        (directory / "signature").write_bytes(signature)
        if key["format"] == "spki-p256":
            check_der(signature)
            (directory / "public.der").write_bytes(data)
            pin = tools.get("openssl")
            if pin is None or pin.name != "openssl":
                raise Refusal("tool-required", "signature")
            result = _run(pin, ["dgst", "-sha256", "-verify", "public.der", "-keyform", "DER",
                                "-signature", "signature", "message"], directory)
            if result[0] != 0:
                raise Refusal("signature-invalid", "signature")
        elif key["format"].startswith("ssh-"):
            name = "ssh-ed25519" if key["format"] == "ssh-ed25519" else "ecdsa-sha2-nistp256"
            (directory / "allowed").write_text("contributor " + name + " " + b64(data) + "\n")
            pin = tools.get("ssh-keygen")
            if pin is None or pin.name != "ssh-keygen":
                raise Refusal("tool-required", "signature")
            result = _run(pin, ["-Y", "verify", "-f", "allowed", "-I", "contributor",
                                "-n", NAMESPACE, "-s", "signature"], directory, input_bytes=message)
            if result[0] != 0:
                raise Refusal("signature-invalid", "signature")
        else:
            (directory / "public.pgp").write_bytes(data)
            pin = tools.get("gpg")
            if pin is None or pin.name != "gpg":
                raise Refusal("tool-required", "signature")
            # Import starts an unnecessary agent and fails on long socket paths.
            # A fixed public keyring supports all three read-only operations.
            prefix = ["--batch", "--no-options", "--no-auto-key-retrieve", "--no-autostart",
                      "--homedir", str(directory), "--no-default-keyring",
                      "--keyring", str(directory / "public.pgp")]
            result = _run(pin, [*prefix, "--with-colons", "--list-keys"], directory)
            rows = result[1].decode("ascii", errors="replace").splitlines()
            fingerprints = [line.split(":")[9] for line in rows if line.startswith("fpr:")]
            if result[0] != 0 or sum(line.startswith("pub:") for line in rows) != 1 or not fingerprints or fingerprints[0] != key["fingerprint"]:
                raise Refusal("key-fingerprint", "signature")
            result = _run(pin, [*prefix, "--export", key["fingerprint"]], directory)
            if result[0] != 0 or result[1] != data:
                raise Refusal("noncanonical-public-key", "signature")
            result = _run(pin, [*prefix, "--status-fd", "1", "--verify", "signature", "message"], directory)
            valid = [line.split() for line in result[1].decode("ascii", errors="replace").splitlines() if line.startswith("[GNUPG:] VALIDSIG ")]
            if result[0] != 0 or len(valid) != 1 or key["fingerprint"] not in (valid[0][2], valid[0][-1]):
                raise Refusal("signature-invalid", "signature")
            if (directory / "public.pgp").read_bytes() != data:
                raise Refusal("noncanonical-public-key", "signature")


def subjects(record):
    if "identities" in record:
        return [{"name": role, "digest": {"sha256": record["identities"][role]}}
                for role in ("snapshot_id", "controller_manifest_sha256", "outer_sha256")]
    return [{"name": "record", "digest": {"sha256": digest(canonical(record))}}]


def statement_bytes(record_bytes):
    record = parse_record(record_bytes)
    return canonical({"_type": STATEMENT, "subject": subjects(record),
                      "predicateType": PREDICATE, "predicate": record})


def envelope_bytes(payload, signature):
    """Package an externally produced signature with the profile's empty key hint."""
    return canonical({"payloadType": PAYLOAD_TYPE, "payload": b64(payload),
                      "signatures": [{"keyid": "", "sig": b64(signature)}]}, limit=MAX_ENVELOPE_BYTES)


@dataclass(frozen=True)
class VerifiedPayload:
    payload: bytes
    record_bytes: bytes
    envelope_sha256: str
    key_fingerprint: str

    @property
    def record(self):
        return parse_record(self.record_bytes)


def verify_envelope(envelope: bytes, key: dict, tools: dict, *, scope=None):
    """Authenticate exactly the decoded bytes, then admit their closed statement."""
    outer = decode(envelope, limit=MAX_ENVELOPE_BYTES)
    if type(outer) is not dict or set(outer) != {"payloadType", "payload", "signatures"}:
        raise Refusal("envelope-fields", "signature")
    if outer["payloadType"] != PAYLOAD_TYPE:
        raise Refusal("payload-type", "signature")
    rows = outer["signatures"]
    if type(rows) is not list or len(rows) != 1 or type(rows[0]) is not dict or set(rows[0]) != {"keyid", "sig"}:
        raise Refusal("signature-count", "signature")
    if rows[0]["keyid"] != "":
        raise Refusal("key-hint", "signature")
    payload = b64decode(outer["payload"])
    signature = b64decode(rows[0]["sig"], maximum=16384)
    verify_signature(pae(payload), signature, key, tools)
    statement = decode(payload, require_canonical=True)
    if type(statement) is not dict or set(statement) != {"_type", "subject", "predicateType", "predicate"} or statement["_type"] != STATEMENT or statement["predicateType"] != PREDICATE:
        raise Refusal("statement-fields", "statement")
    record_bytes = canonical(statement["predicate"])
    record = parse_record(record_bytes, scope=scope)
    if statement["subject"] != subjects(record):
        raise Refusal("subject-roles", "statement")
    if record["issuer"] != key["fingerprint"]:
        raise Refusal("issuer-key", "statement")
    return VerifiedPayload(payload, record_bytes, digest(envelope), key["fingerprint"])
