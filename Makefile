# One entry point for the checks. `make check` before finishing any change.

PY := python3
SRC := src tests
# every test except the two repo-wide checks, which have their own targets
TESTS := $(sort $(shell find tests -name 'test_*.py' \
	! -name 'test_instruction_paths.py' ! -name 'test_docs.py'))

.PHONY: check lint paths docs tests

check: lint paths docs tests

lint:
	ruff check $(SRC)

# every path named in AGENTS.md, the READMEs, docs/ and TODO.md exists
paths:
	$(PY) tests/test_instruction_paths.py

# docs/: log names and frontmatter, no log edited after its day, topic files, decision IDs
docs:
	$(PY) tests/test_docs.py

tests:
	@for t in $(TESTS); do $(PY) $$t >/dev/null || { echo "FAIL $$t"; exit 1; }; echo "PASS $$t"; done

# A second interpreter (a venv with the heavy deps, while the tools stay on
# system Python) is a variable and a target of its own, not a different PY:
#
# VENV_PY := <path>/venv/bin/python
# HEAVY_TESTS := $(sort $(shell find tests/<component> -name 'test_*.py'))
#
# heavy-tests:
#	@for t in $(HEAVY_TESTS); do $(VENV_PY) $$t >/dev/null || { echo "FAIL $$t"; exit 1; }; echo "PASS $$t"; done
#
# A heavier gate (a regression run against a stored baseline, minutes not
# seconds) gets its own .PHONY target outside `check`, so `make check` stays
# fast enough to run on every change.
