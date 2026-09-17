#!/usr/bin/env python3
"""Every path named in an instruction file must exist.

An agent follows the paths it reads in AGENTS.md, the READMEs, TODO.md and the
skills. A stale one sends it looking for a file that is not there, or inventing
it. The same file runs in every repo that uses this layout; only the constants
under "This repo" differ.

A backticked token containing "/" is a path claim. It passes if it exists
relative to the repo root, to one of BASES, or to the file that names it. It
is exempt when:
- the paragraph, list item or table row that holds it says "not built" or
  "not in this repo" (the text already says it is absent), or "model ID" (a
  model's name, like anthropic/claude-opus-5, is not a path);
- it is under a gitignored or outside-repo place (EXEMPT_PREFIXES: data/, tmp/,
  ~/, /, $VAR), or names a place inside one (DATA_DIRS), or matches one of
  EXEMPT_PATTERNS;
- it is a URL, a flag or a pattern (<stem>, *, {a,b}, ...).

docs/log/ is history and docs/research/ may record paths inside old inputs;
neither is scanned.

Run: python3 tests/test_instruction_paths.py   (exit 0 = pass)
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

# --- This repo ----------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

# the instruction files an agent reads; add a subtree's own AGENTS.md here
SCANNED = (
    "*.md",
    "src/*/*.md",
    ".claude/skills/*/SKILL.md",
    "tests/*.md",
    "docs/*.md",
)
# the scan is worthless if it silently matches nothing: these must be covered
REQUIRED = ("AGENTS.md",)
# a path may also be written relative to one of these, not only to the root
BASES = (ROOT, ROOT / "docs")
# gitignored or outside the repo: named, never on disk here
EXEMPT_PREFIXES = ("data/", "tmp/", "~", "/", "$", "-", "http")
# a directory inside an ignored tree, named without its parent (`runs/<id>/`)
DATA_DIRS = {"inbox", "outbox", "runs", "archive", "trash"}
# generated or per-run paths, e.g. a numbered stage's output: r"^\d\d_\w+/"
EXEMPT_PATTERNS: tuple[re.Pattern[str], ...] = ()
# ------------------------------------------------------------------------------

TOKEN = re.compile(r"`([^`\s]+)`")
ABSENT = re.compile(r"not built|not in this repo|model ID", re.IGNORECASE)
BLOCK_START = re.compile(r"^\s*(?:[-*+] |\d+\. |\||#|```)")


def test_scan_covers_the_instruction_files() -> None:
    names = {p.relative_to(ROOT).as_posix() for p in scanned_files()}
    assert set(REQUIRED) <= names, f"not scanned: {sorted(set(REQUIRED) - names)}"


def test_named_paths_exist() -> None:
    missing = [f"{path.relative_to(ROOT)}:{number}: `{token}`" for path in scanned_files() for number, token in path_claims(path) if not exists(token, path)]
    assert not missing, "paths named but not on disk:\n" + "\n".join(missing)


def scanned_files() -> list[Path]:
    return sorted({p for pattern in SCANNED for p in ROOT.glob(pattern)})


def path_claims(path: Path) -> Iterator[tuple[int, str]]:
    for block in blocks(path.read_text(encoding="utf-8")):
        if any(ABSENT.search(line) for _, line in block):
            continue
        for number, line in block:
            for match in TOKEN.finditer(line):
                if is_path_claim(match.group(1)):
                    yield number, match.group(1)


def blocks(text: str) -> Iterator[list[tuple[int, str]]]:
    # paragraphs, list items and table rows, with 1-based line numbers
    block: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or BLOCK_START.match(line):
            if block:
                yield block
            block = []
        if line.strip():
            block.append((number, line))
    if block:
        yield block


def is_path_claim(token: str) -> bool:
    return (
        "/" in token
        and "=" not in token
        and not any(char in token for char in "<>*{}()")
        and "..." not in token
        and not token.startswith(EXEMPT_PREFIXES)
        and token.split("/")[0] not in DATA_DIRS
        and not any(p.match(token) for p in EXEMPT_PATTERNS)
    )


def exists(token: str, named_in: Path) -> bool:
    path = token.split(":")[0].split(" ")[0].rstrip("/")
    return any((base / path).exists() for base in (*BASES, named_in.parent))


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
