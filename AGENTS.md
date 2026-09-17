# AGENTS.md — read this first

<One paragraph: what this repo is, what it runs on, and what it runs against.>

This file has the map and the rules that apply everywhere. A subtree with its
own `AGENTS.md` adds the rules for working there; read it before changing that
subtree. Each component's README is the reference for its steps.

## Where truth lives

1. Each component's `README.md`: the current design. If the code and it
   disagree, one of them is a bug.
2. `docs/decisions.md`: settled choices, one line each. Do not reopen one
   without a new line that supersedes it.
3. `docs/research/<topic>.md` with `status: current`: the current measurements
   per model or technique (`status: history` files describe removed code).
4. `TODO.md`: open work, each item with how to check it.
5. `docs/log/`: dated PLAN/RESEARCH/SESSION records. History: never edit one
   after the day it was written; correct it in a new one.

`docs/AGENTS.md` says which docs file answers which question, and the
conventions for each.

## Definition of done

`make check` exits 0; <the heavier gate, e.g. `make regress`, when
<what it covers> changed>; the README and `TODO.md` say what the code now
does; <owner> is told what changed and what is uncommitted.

## Commands

    make check      # before finishing any change: <what it runs>
    make <gate>     # after any change to <area>: <what it compares>
    <the entry point a human runs, with an example argument>

## Map

| Path | What | Git |
|---|---|---|
| `<entry points>` | for humans: pick the interpreter, hand off, no logic | tracked |
| `<component>/<ordered steps>` | steps, run in order as scripts from their own dir | tracked |
| `<component>/*.py` (no number) | shared modules; steps import these, never each other | tracked |
| `tests/` | every test at the path of the file it tests, plain scripts, exit 0 = pass; plus repo-wide checks (a doc naming a path that is not on disk; the `docs/` conventions) | tracked |
| `Makefile` | the checks, one entry point | tracked |
| `docs/AGENTS.md` | which docs file answers what; the decision, topic-file and log conventions | tracked |
| `docs/decisions.md` | settled choices with stable IDs (`D1`…), append-only | tracked |
| `docs/research/` | what each model and technique measured on this corpus, one file per topic; numbers only | tracked |
| `docs/log/` | dated `PLAN_`, `RESEARCH_` and `SESSION_` records (see rule 5) | tracked |
| `.claude/skills/fe-*/` | Claude Code skills; Fernando's all carry the `fe-` prefix | tracked |
| `data/` | <inputs, per-run output, deliveries> | ignored |
| `tmp/` | scratch; nothing here is read by the code | ignored |
| `<deps file>` | the environment | tracked |

All paths come from a single module (derived from the file's location). Never
hardcode one.

## Hard rules

1. **<The one call that is the owner's, not yours>** — e.g. an identity, a
   name, a threshold. Never guess it, never accept a close match. Settled
   answers are not re-litigated.
2. **Only describe what exists.** Before documenting or relying on a file,
   script, model, or number, verify it's in the repo or on disk. The path test
   checks the paths; numbers are on you. A planned thing is written as "not
   built yet".
3. **Run `ruff check <source dirs>`** after every Python edit (`.ruff.toml`;
   new shared modules go in `known-first-party`).
4. **Git:** commit only when asked. <Say whether there is a remote.>
5. **Log plans, research and sessions** in `docs/log/` as
   `<YYYYMMDD_HHMMSS>_<TYPE>_<slug>.md`, with the
   frontmatter in `docs/AGENTS.md`:
   - `PLAN`: when a plan is asked for, or plan mode is used;
   - `RESEARCH`: every research effort; also merge the findings into the
     matching `docs/research/*.md` (or a new topic file), and add a line to
     `docs/decisions.md` when it settles a choice;
   - `SESSION`: at sign-off, not before.
6. **A failing check is information, not an obstacle.** If a change needs a
   test, the path check or a baseline to change, stop and say why; never
   weaken a check or re-save a baseline to turn it green.
7. **Deferred work goes in `TODO.md`**, with the case that shows it and how to
   check it is done, instead of being chased live.

## Code Style Overrides

- **Type hints required** on all function signatures.
- **Linting: ruff** (replaces flake8 + isort); config in `.ruff.toml`.
- **Helper functions at the bottom** of each file, not the top.
- **No docstrings** — a single short comment only when the *why* is non-obvious.
- **No mutable default arguments** — use `None` instead of `[]`, `{}`, or `set()`.
- **No `print()`** in library or pipeline code — use the `logging` module.
- **Logging format:** every `logging.basicConfig` call uses
  `format="%(asctime)s %(levelname)s %(message)s"` and
  `datefmt="%Y-%m-%d %H:%M:%S"`.
- **`if __name__ == "__main__":`** must be the last block in every script file.

## Which Python

| What | Interpreter |
|---|---|
| <component> | <path to its venv; say what it needs it for> |
| <tools/tests> | any `python3` |

<The entry points and the `Makefile` encode this table — use them and the
choice is made for you.>

## Contracts with things outside this repo

- <Every file, service or hand-kept copy outside the repo that a change here
  must reach, and how it reaches it.>
