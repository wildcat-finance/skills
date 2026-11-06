"""One credential-free fixed-socket client. Request enters on stdin."""
import grp
import pwd
import sys

sys.path.insert(0, "/Library/WildcatIssuePublisher/plugins/hexaemeron/skills/phylax/scripts")
from github_issue_publisher_lib.canonical import MAX_REQUEST_BYTES, canonical_json
from github_issue_publisher_lib.client import PublisherClient
from github_issue_publisher_lib.errors import PublisherError


def main():
    try:
        if sys.argv[1:] != ["publish"]:
            raise PublisherError("GIP199", "cli.arguments")
        service = pwd.getpwnam("_wildcatpublisher")
        group = grp.getgrnam("_wildcatpublishers")
        request = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        result = PublisherClient(service_uid=service.pw_uid, service_gid=group.gr_gid).publish(request)
        sys.stdout.buffer.write(canonical_json(result) + b"\n")
        return 0 if result.get("outcome") == "published" else 1
    except Exception:
        sys.stderr.buffer.write(canonical_json(PublisherError("GIP199", "client.refused").diagnostic()) + b"\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
