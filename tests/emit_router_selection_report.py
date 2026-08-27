#!/usr/bin/env python3
"""Print what the router-selection corpus covers and whether a run is recorded.

Two questions a person actually asks, and this answers both. Which cases exist,
and for which canonical selection? And what did the last grading run find? With
no run recorded the answer is the word `not-run`, which is an answer rather than
an empty report.

Every line names its subject and the corpus path, so a line pasted into an issue
still says what it is about. No line carries a request phrasing or a deciding
sentence: those are the fields a graded agent must not see, and a report that
echoes them is a route from this file into the context being graded.
"""

from __future__ import annotations

from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tests.test_router_selection import (  # noqa: E402
    CORPUS_PATH,
    CorpusError,
    corpus_digest,
    load_corpus,
)

SUBJECT = "router-selection"


def line(*fields: str) -> str:
    return " ".join((SUBJECT, CORPUS_PATH) + fields)


def report(document: dict) -> list[str]:
    cases = document["cases"]
    lines = [
        line(
            f"schema={document.get('schema')}",
            f"cases={len(cases)}",
            f"pairs={len(document['pairs'])}",
            f"corpus_sha256={corpus_digest(cases)}",
        )
    ]
    selections: dict[str, list] = {}
    for case in cases:
        expect = case.get("expect") or {}
        key = expect.get("canonical") or f"refuse:{expect.get('reason')}"
        selections.setdefault(key, []).append(case)
    for key in sorted(selections):
        probed = sorted({name for case in selections[key] for name in case["contested"]})
        lines.append(
            line(
                f"selection={key}",
                f"cases={len(selections[key])}",
                "contested=" + (",".join(probed) if probed else "none"),
            )
        )
    runs = document["runs"]
    if not runs:
        lines.append(line("run=not-run"))
    else:
        for run in runs:
            lines.append(
                line(
                    f"run={run.get('date')}",
                    f"model={run.get('model')}",
                    f"cases={run.get('cases')}",
                    f"passed={run.get('passed')}",
                    f"failed={run.get('failed')}",
                    "failures=" + (",".join(run.get("failures") or []) or "none"),
                )
            )
    return lines


def main() -> int:
    try:
        document = load_corpus()
    except CorpusError as error:
        print(line(f"unreadable={error}"), file=sys.stderr)
        return 1
    for text in report(document):
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
