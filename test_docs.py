#!/usr/bin/env python3
"""docs/ follows the conventions in docs/AGENTS.md, and history is not rewritten.

The same file runs in every repo that uses this docs layout; only the
constants under "This repo" differ. A part whose directory or file does not
exist in a repo is skipped by an explicit check, not by a pytest skip.

- Logs (docs/log/): every file written from CONVENTION_FROM on is named
  <YYYYMMDD_HHMMSS>_<TYPE>_<MODEL_COMPANY>_<MODEL_NAME>_<slug>.md and opens
  with frontmatter: type (as in the name), models (the first gives the name),
  agent, and a commit that exists; a PLAN has a known status. Earlier files
  keep whatever name they had. A committed log differs from HEAD only on the
  day in its name (a rename is fine; so is a PLAN's status line).
- Decisions (docs/decisions.md): entries `- **D<n>**` numbered 1, 2, ... in
  order, and every D<n> cited exists.
- Research topics (docs/research/*.md): frontmatter status (current | history),
  summary, applies_to (paths that exist), updated (a date); each listed in
  docs/research/README.md.
- ADRs (docs/adr/NNNN-*.md): each has Status: and Date: lines and is linked
  from docs/adr/README.md, and every linked ADR exists.

Run: python3 tests/test_docs.py   (or pytest; exit 0 = pass)
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# --- This repo ----------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
CONVENTION_FROM = "00000000_000000"  # log files from here on follow the
# convention; a new repo starts at 0, an older one at the first log that does
# ------------------------------------------------------------------------------

DOCS = ROOT / "docs"
LOG = DOCS / "log"
DECISIONS = DOCS / "decisions.md"
RESEARCH = DOCS / "research"
ADR = DOCS / "adr"

TYPES = ("PLAN", "RESEARCH", "SESSION")
PLAN_STATUSES = ("proposed", "done", "dropped", "superseded")
TOPIC_STATUSES = ("current", "history")
NAME = re.compile(
    r"(?P<stamp>\d{8}_\d{6})_(?P<type>[A-Z]+)_(?P<company>[A-Z0-9-]+)"
    r"_(?P<model>[A-Z0-9-]+)_(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md$"
)
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DECISION_ID = re.compile(r"^- \*\*D(\d+)\*\*", re.MULTILINE)
DECISION_REF = re.compile(r"\bD(\d+)\b")
ADR_FILE = re.compile(r"^\d{4}-[a-z0-9-]+\.md$")


def test_log_names_and_frontmatter() -> None:
    problems: list[str] = []
    for path in sorted(LOG.glob("*.md")) if LOG.is_dir() else []:
        if path.name[:15] >= CONVENTION_FROM:
            problems += [f"{path.name}: {p}" for p in log_problems(path)]
    assert not problems, "\n".join(problems)


def test_logs_are_not_rewritten_after_their_day() -> None:
    today = datetime.now(UTC).astimezone().strftime("%Y%m%d")
    rewritten = [
        new
        for old, new in committed_log_changes()
        if not Path(new).name.startswith(today)
        and body(git("show", f"HEAD:{old}"))
        != body((ROOT / new).read_text(encoding="utf-8"))
    ]
    assert not rewritten, "log files edited after their day:\n" + "\n".join(rewritten)


def test_decision_ids() -> None:
    if not DECISIONS.is_file():
        return
    text = DECISIONS.read_text(encoding="utf-8")
    ids = [int(n) for n in DECISION_ID.findall(text)]
    assert ids == list(range(1, len(ids) + 1)), f"IDs out of order or reused: {ids}"
    cited = {int(n) for n in DECISION_REF.findall(text)}
    assert cited <= set(ids), f"cites decisions that do not exist: {cited - set(ids)}"


def test_research_topic_frontmatter() -> None:
    problems: list[str] = []
    for path in topic_files():
        fields = frontmatter(path.read_text(encoding="utf-8"))
        if fields is None:
            problems.append(f"{path.name}: no frontmatter")
            continue
        if fields.get("status") not in TOPIC_STATUSES:
            problems.append(f"{path.name}: status not in {TOPIC_STATUSES}")
        if not fields.get("summary"):
            problems.append(f"{path.name}: no summary")
        if not DATE.match(str(fields.get("updated", ""))):
            problems.append(f"{path.name}: updated is not a YYYY-MM-DD date")
        applies = fields.get("applies_to")
        if not isinstance(applies, list):
            problems.append(f"{path.name}: applies_to is not a list")
            continue
        problems += [
            f"{path.name}: applies_to {a} does not exist"
            for a in applies
            if not (ROOT / a).exists()
        ]
    assert not problems, "\n".join(problems)


def test_research_index_lists_every_topic() -> None:
    if not topic_files():
        return
    listed = linked_files(RESEARCH / "README.md")
    names = {p.name for p in topic_files()}
    assert names <= listed, f"not in research/README.md: {sorted(names - listed)}"
    assert listed <= names, f"listed, not on disk: {sorted(listed - names)}"


def test_adrs_have_status_and_are_indexed() -> None:
    if not ADR.is_dir():
        return
    adrs = {p.name: p for p in ADR.glob("*.md") if ADR_FILE.match(p.name)}
    problems = [
        f"{name}: no {field}: line"
        for name, path in sorted(adrs.items())
        for field in ("Status", "Date")
        if not re.search(rf"^{field}:", path.read_text(encoding="utf-8"), re.M)
    ]
    listed = linked_files(ADR / "README.md")
    problems += [f"{n}: not in adr/README.md" for n in sorted(set(adrs) - listed)]
    problems += [f"{n}: linked, not on disk" for n in sorted(listed - set(adrs))]
    assert not problems, "\n".join(problems)


def test_model_tokens() -> None:
    assert model_token("anthropic/claude-opus-5") == "ANTHROPIC_CLAUDE-OPUS-5"
    assert model_token("z-ai/glm-5.3") == "Z-AI_GLM-5-3"


def log_problems(path: Path) -> list[str]:
    match = NAME.match(path.name)
    if not match or match["type"] not in TYPES:
        return ["name is not <stamp>_<TYPE>_<COMPANY>_<MODEL>_<slug>.md"]
    fields = frontmatter(path.read_text(encoding="utf-8"))
    if fields is None:
        return ["no frontmatter"]
    required = ("type", "models", "agent", "commit")
    problems = [f"no {key}" for key in required if not fields.get(key)]
    if fields.get("type") and fields["type"] != match["type"]:
        problems.append(f"type {fields['type']} but the name says {match['type']}")
    models = fields.get("models") or []
    named = f"{match['company']}_{match['model']}"
    if models and model_token(models[0]) != named:
        problems.append(f"first model {models[0]} does not give {named}")
    if fields.get("commit") and not commit_exists(str(fields["commit"])):
        problems.append(f"commit {fields['commit']} does not exist")
    if match["type"] == "PLAN" and fields.get("status") not in PLAN_STATUSES:
        problems.append(f"PLAN status must be one of {', '.join(PLAN_STATUSES)}")
    return problems


def topic_files() -> list[Path]:
    if not RESEARCH.is_dir():
        return []
    return sorted(p for p in RESEARCH.glob("*.md") if p.name != "README.md")


def linked_files(index: Path) -> set[str]:
    text = index.read_text(encoding="utf-8") if index.is_file() else ""
    return set(re.findall(r"\]\(([\w.-]+\.md)\)", text)) - {"README.md"}


def frontmatter(text: str) -> dict[str, str | list[str]] | None:
    match = FRONTMATTER.match(text)
    if not match:
        return None
    fields: dict[str, str | list[str]] = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        value = value.split(" #")[0].strip()
        if value.startswith("[") and value.endswith("]"):
            fields[key.strip()] = [v.strip() for v in value[1:-1].split(",") if v]
        else:
            fields[key.strip()] = value
    return fields


def model_token(model_id: str) -> str:
    company, _, name = model_id.partition("/")
    return "_".join(re.sub(r"[.\s]", "-", t).upper() for t in (company, name))


def body(text: str) -> str:
    # a PLAN may be marked done after its day; nothing else may move
    return "\n".join(x for x in text.splitlines() if not x.startswith("status:"))


def committed_log_changes() -> list[tuple[str, str]]:
    changes = []
    for line in git("diff", "HEAD", "-M", "--name-status").splitlines():
        status, *paths = line.split("\t")
        old, new = paths[0], paths[-1]
        if (status.startswith("R") or status == "M") and "log/" in old:
            if Path(old).suffix == ".md":
                changes.append((old, new))
    return changes


def commit_exists(sha: str) -> bool:
    done = subprocess.run(  # noqa: S603
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return done.returncode == 0


def git(*args: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
