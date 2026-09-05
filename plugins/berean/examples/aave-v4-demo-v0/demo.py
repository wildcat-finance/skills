#!/usr/bin/env python3
"""Walk the aave-v4-demo-v0 release end to end, offline.

Five stages, each printing its named result: verify the release's gates,
grade its evaluation corpus, replay the promotion chain, then prove the
pins bite by tampering copies three ways and watching each named gate
refuse. Exit 0 means every stage behaved; nothing here reaches a network.
"""

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(PLUGIN_ROOT, "scripts"))

from berean_lib import BereanError  # noqa: E402
from berean_lib import evals, promote, release  # noqa: E402

RELEASE_DIR = os.path.join(HERE, "release")


def stage(name):
    print(f"\n== {name} ==")


def failures(checks):
    return [check for check in checks if not check.passed]


def main():
    stage("verify the release")
    checks = release.verify(RELEASE_DIR)
    for check in checks:
        print(check.line())
    if failures(checks):
        print("the shipped release failed its own gates", file=sys.stderr)
        return 1

    stage("grade the evaluation corpus")
    report, results = evals.run(RELEASE_DIR)
    print(f"corpus digest  {report['corpus_digest']}")
    print(f"cases digest   {report['cases_sha256']}")
    print(f"answers digest {report['answers_digest']}")
    for case, passed, reason in results:
        print(f"{'pass' if passed else 'fail'}  {case['id']}: {reason}")
    if report["failed"]:
        print("the shipped corpus does not grade clean", file=sys.stderr)
        return 1

    stage("replay the promotion chain")
    document = release.load(RELEASE_DIR)
    chain = promote.load_chain(os.path.join(RELEASE_DIR, release.PROMOTIONS_FILE))
    print(f"records: {len(chain)}; state: {promote.state(chain, document)}")

    stage("tamper with a corpus byte")
    with tempfile.TemporaryDirectory() as holder:
        copy = os.path.join(holder, "release")
        shutil.copytree(RELEASE_DIR, copy)
        with open(os.path.join(copy, "corpus", "terms.md"), "ab") as handle:
            handle.write(b"\n")
        names = [check.name for check in failures(release.verify(copy))]
        print(f"refused by: {', '.join(names)}")
        if "release-corpus" not in names:
            print("a tampered corpus byte went unnoticed", file=sys.stderr)
            return 1

    stage("tamper with a preserved read")
    with tempfile.TemporaryDirectory() as holder:
        copy = os.path.join(holder, "release")
        shutil.copytree(RELEASE_DIR, copy)
        with open(os.path.join(copy, "reads.jsonl"), "ab") as handle:
            handle.write(b"\n")
        names = [check.name for check in failures(release.verify(copy))]
        print(f"refused by: {', '.join(names)}")
        if "release-reads" not in names:
            print("a tampered read record went unnoticed", file=sys.stderr)
            return 1

    stage("forge a promotion record")
    with tempfile.TemporaryDirectory() as holder:
        copy = os.path.join(holder, "release")
        shutil.copytree(RELEASE_DIR, copy)
        with open(os.path.join(copy, release.PROMOTIONS_FILE), "a", encoding="utf-8") as handle:
            handle.write('{"format":"berean-promotion/v1"}\n')
        names = [check.name for check in failures(release.verify(copy))]
        print(f"refused by: {', '.join(names)}")
        if "release-promotions" not in names:
            print("a forged promotion record went unnoticed", file=sys.stderr)
            return 1

    print("\nevery stage held")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BereanError as error:
        print(f"refused: {error}", file=sys.stderr)
        sys.exit(2)
