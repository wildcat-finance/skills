PYTHON ?= python3
FILE ?=
MODE ?= auto
SOURCE ?=
REPORT ?= .elenchus/brevitas-unittest.json

.PHONY: lint test unit evals report

lint:
	@test -n "$(FILE)" || { echo "usage: make lint FILE=report.md [SOURCE=original.md] [MODE=report]" >&2; exit 2; }
	$(PYTHON) scripts/brevitas.py "$(FILE)" --mode "$(MODE)" $(if $(SOURCE),--source "$(SOURCE)",)

unit:
	$(PYTHON) -m unittest discover -s ../../tests -t ../.. -v

evals:
	$(PYTHON) scripts/run_evals.py

report:
	$(PYTHON) ../../tests/run_tests.py "$(REPORT)"

test: unit evals
