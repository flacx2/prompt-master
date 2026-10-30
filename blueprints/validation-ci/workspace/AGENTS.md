# prompt-master — agent instructions

A Claude Skill that turns a rough idea into a production-ready prompt for a specific AI tool. The
deliverable is Markdown: `SKILL.md`, `README.md` and `references/`. There is no application code
besides the repository's own validator.

## Commands

| Task | Command |
|---|---|
| Validate the skill | `python scripts/validate_skill.py` |
| Validate, JSON output | `python scripts/validate_skill.py --format json` |
| List the rules | `python scripts/validate_skill.py --list-rules` |
| Run one rule | `python scripts/validate_skill.py --rule counts` |
| Prove the rules can fail | `python scripts/validate_skill.py --self-test` |
| Byte-compile the validator | `python -m compileall -q scripts` |
| Check the config parses | `python -m json.tool scripts/validator-config.json` |

**Gate:** `python scripts/validate_skill.py && python -m compileall -q scripts` must exit 0 before
any task is marked done.

## Non-negotiable

1. Never edit `SKILL.md`, `README.md`, `LICENSE` or anything under `references/`. This repository is
   a fork of `nidhinjs/prompt-master` and those files are kept byte-identical to upstream so merges
   never conflict. The validator adapts to their content; it does not correct it.
2. Never add a third-party Python package. The validator is standard library only — no manifest, no
   lockfile, nothing to audit.
3. Never widen a rule to make a failure go away. A red rule is either a real drift in the docs or a
   wrong rule; fix the rule and add the fixture that proves it still fails for the right reason.
4. Never add a check whose success condition is a bare non-zero exit. Assert the specific exit code.
5. Never commit secrets, and never add a workflow permission beyond `contents: read`.

Full architecture, boundaries and conventions: see `CLAUDE.md` in this directory.
