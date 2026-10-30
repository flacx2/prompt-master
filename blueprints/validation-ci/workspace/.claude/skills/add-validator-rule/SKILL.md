---
name: add-validator-rule
description: Use when adding a new check to scripts/validate_skill.py, or when changing what an existing rule asserts. Covers the registry entry, the negative fixture, the self-test wiring and the documentation the rule has to stay consistent with. Trigger phrases include "add a rule", "the validator should also check", "catch this drift", "a new check for SKILL.md".
---

# Add a validator rule

A rule is only finished when it can fail for the right reason and a fixture proves it.

## Steps

1. **Name it** in kebab-case, one word where possible: `frontmatter`, `counts`, `zones`, `links`,
   `budgets`, `version-sync`, `encoding`. The name is the `--rule` argument and the `rule` field of
   every finding it emits.
2. **Write the function** in `scripts/validate_skill.py` as `rule_<name_with_underscores>(ctx)`,
   returning a list of `Finding`. Read from `ctx.files` and `ctx.config`; never print, never write a
   file, never call `sys.exit`.
3. **Register it** in the `RULES` dict, in the order it should run. Fast structural rules first,
   whole-file scans last.
4. **Put any new tuning data in `scripts/validator-config.json`** — a ceiling, a path, a heading
   name. Regular expressions stay in the code.
5. **Confirm the rule is green on the current tree** before going further:
   `python scripts/validate_skill.py --rule <name>`. If it is red, either the repository really has
   drifted or the rule is wrong — and since `SKILL.md`, `README.md` and `references/**` may not be
   edited, a red rule on untouched upstream content means the rule is wrong.
6. **Write the negative fixture** at `scripts/tests/fixtures/<name>/`, holding the smallest tree that
   breaks exactly this rule. Copy only what the rule reads.
7. **Wire it into `--self-test`**, which runs every rule against every fixture and asserts that
   fixture `<name>` fails rule `<name>` and passes the others.
8. **Document it** in the rule table in `CLAUDE.md` if the command surface changed, and in
   `.claude/rules/validator.md` if the convention changed.

## Verify

```bash
python scripts/validate_skill.py --rule <name>    # expect: exit 0 on the current tree
python scripts/validate_skill.py --self-test      # expect: exit 0 — every fixture fails its own rule
python scripts/validate_skill.py                  # expect: exit 0 — the full run is still clean
python -m compileall -q scripts                   # expect: exit 0
```

## Do not

- Do not edit `SKILL.md`, `README.md`, `LICENSE` or `references/**` to make a rule pass.
- Do not add a dependency. If the rule cannot be written against the standard library, it is the
  wrong rule.
- Do not assert a count you did not derive from the file that owns it.
- Do not write a check whose pass condition is a bare non-zero exit; assert the specific code.
- Do not skip the fixture. A rule with no fixture is a rule nobody has seen fail.
