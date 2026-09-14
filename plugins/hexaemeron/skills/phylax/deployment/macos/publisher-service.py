"""launchd inetd entrypoint; consumes only the accepted descriptor zero."""
import os
import pwd
import socket
import sys

sys.path.insert(0, "/Library/WildcatIssuePublisher/plugins/hexaemeron/skills/phylax/scripts")
from github_issue_publisher_lib.receipts import MemoryReceiptSink
from github_issue_publisher_lib.runtime import PublisherRuntime
from github_issue_publisher_lib.server import PublisherServer
from github_issue_publisher_lib.signer import OpenSSLSigner
from github_issue_publisher_lib.transport import PinnedGitHubTransport


def main():
    if sys.argv[1:]:
        return 2
    service = pwd.getpwnam("_wildcatpublisher")
    if os.geteuid() != service.pw_uid or service.pw_uid == 0:
        return 2
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, fileno=0)
    runtime = PublisherRuntime(signer=OpenSSLSigner(),
        transport=PinnedGitHubTransport(), receipt_sink=MemoryReceiptSink())
    PublisherServer(runtime=runtime, service_uid=service.pw_uid).serve_connection(connection)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(2) from None
