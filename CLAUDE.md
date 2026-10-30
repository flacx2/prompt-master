# prompt-master

A Claude Skill that turns a rough idea into one production-ready prompt for a specific AI tool. The
product is Markdown; the only code in the repository is its own validator.

## Commands

| Task | Command |
|---|---|
| Validate the skill | `python scripts/validate_skill.py` |
| Validate, JSON output | `python scripts/validate_skill.py --format json` |
| Validate, CI annotations | `python scripts/validate_skill.py --format github` |
| List the rules | `python scripts/validate_skill.py --list-rules` |
| Run one rule | `python scripts/validate_skill.py --rule counts` |
| Prove the rules can fail | `python scripts/validate_skill.py --self-test` |
| Byte-compile the validator | `python -m compileall -q scripts` |
| Check the config parses | `python -m json.tool scripts/validator-config.json` |
| Install the local hook | `git config core.hooksPath .githooks` |

**Gate:** `python scripts/validate_skill.py && python -m compileall -q scripts` must exit 0 before
any task is marked done.

Python floor is 3.9; this machine runs 3.12 and CI pins 3.12. There is no manifest and no lockfile —
the validator imports only the standard library, which is a rule, not an accident.

## Stack

Markdown skill + Python 3 standard library + GitHub Actions. No framework, no database, no
dependencies.

## Architecture

**The one real flow.** `python scripts/validate_skill.py` → loads `scripts/validator-config.json` →
reads exactly the files that config names → runs each registered rule over them → prints one line per
finding → exits 0 with no findings, 1 with findings, 2 on its own usage error.

**No rule walks the tree.** `exclude_dirs` is a guard, not a filter: the validator exits 2 rather
than read a configured path, a `--root` or a fixture directory that resolves inside it, which is what
keeps it out of `blueprints/` — the bundle sits in this repository and carries its own copy of the
config.

**Boundaries.** Cross one of these the wrong way and the change is wrong, not merely untidy:

| Area | May do | Must never |
|---|---|---|
| `scripts/validate_skill.py` | read any committed file, print findings, exit 0/1/2 | write to any file, import a third-party package, shell out |
| `scripts/validator-config.json` | hold data — ceilings, paths, zone names, exclusions | hold a regular expression or any other executable logic |
| `scripts/tests/fixtures/**` | contain deliberately broken copies, reached through `--root` and `--self-test` | be read by a normal run — nothing walks the tree. It is named by `fixtures_dir`, never by `exclude_dirs` |
| `.github/workflows/**` | run the gate, read the repository | get a permission wider than `contents: read`, or a float action tag |
| `SKILL.md`, `README.md`, `references/**`, `LICENSE` | be read | **be edited by anything in this repository's own tooling** |

**Where things live.**

| Concern | Single source of truth |
|---|---|
| Line ceilings, excluded paths, zone names, required frontmatter keys | `scripts/validator-config.json` |
| What each rule asserts | the rule function in `scripts/validate_skill.py` |
| Proof that a rule can still fail | `scripts/tests/fixtures/<rule>/` plus `--self-test` |
| The pattern and template counts | `references/patterns.md` and `references/templates.md` themselves — the validator derives them, never stores them |
| Action versions | `.github/workflows/validate.yml`, pinned by 40-character commit SHA with the tag in a trailing comment |

## Code rules

1. **Standard library only.** If a rule needs a dependency, the rule is wrong. There is deliberately
   no `requirements.txt`, no `pyproject.toml` and no lockfile.
2. **Python 3.9 floor.** No match statements, no `tomllib`, no `|` type unions at runtime.
3. **One rule, one function, one registry entry.** A rule takes the loaded config and the file map
   and returns a list of findings. It never prints and it never calls `sys.exit`.
4. **A finding is data**: rule name, path, line (or `None`), message. Formatting happens once, in the
   reporter, so `--format json` and `--format github` cannot drift from the default output.
5. **Exit codes are a public interface.** `0` clean, `1` findings, `2` usage — a bad flag, a missing
   config, an unreadable file. Never collapse 2 into 1.
6. **The docs are read-only.** A rule that would need `SKILL.md` edited to pass is a rule that needs
   rewriting. Record the disagreement instead; upstream merge-cleanliness outranks tidiness here.
7. **Derive counts, never store them.** The expected number of patterns and templates is counted from
   the reference files at run time.
8. **Every new rule ships with a negative fixture** under `scripts/tests/fixtures/<rule>/` that
   `--self-test` proves exits 1 for that rule and that rule only.

## Environment

This project reads no environment variables and needs no accounts. There is no `.env`, and no
`.env.example`, because there is nothing to put in one.

## Rules

Deferred conventions — read the matching file before editing that area:

| File | Applies to |
|---|---|
| `.claude/rules/validator.md` | `scripts/**` |
| `.claude/rules/skill-docs.md` | `SKILL.md`, `README.md`, `references/**` |
| `.claude/rules/ci.md` | `.github/**`, `.githooks/**` |

## Non-negotiable

1. Never edit `SKILL.md`, `README.md`, `LICENSE` or `references/**`. This fork tracks
   `nidhinjs/prompt-master`; those files stay byte-identical so upstream merges never conflict.
   Sole exception: the `**1.8.2**` Version History line in `README.md`, because upstream
   bumped the version without one and `version-sync` caught it.
2. Never add a third-party Python package, a manifest or a lockfile.
3. Never relax a rule to turn a gate green. Fix the drift, or fix the rule and re-prove it with a
   fixture.
4. Never write a gate whose success condition is a bare non-zero exit — assert the code:
   `cmd; test $? -eq 1`.
5. Never float a GitHub Action to a tag. Pin the 40-character commit SHA, tag in a comment.
6. Never grant a workflow more than `permissions: contents: read`.
7. Never mark a task done with a failing gate command.
