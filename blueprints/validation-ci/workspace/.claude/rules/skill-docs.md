---
description: The skill documents are upstream content and are read-only to this repository's tooling
paths:
  - "SKILL.md"
  - "README.md"
  - "references/**"
---

# Skill documents — read-only

This repository is a fork of `nidhinjs/prompt-master`. These four files are kept byte-identical to
upstream so that pulling from it never conflicts.

- **Do not edit them.** Not to fix a count, not to normalise a line ending, not to trim trailing
  whitespace, not to rename a heading. The validator adapts to their content; it does not correct it.
- **The three-zone order in `SKILL.md` is positional and load-bearing**: `## PRIMACY ZONE` →
  `## MIDDLE ZONE` → `## RECENCY ZONE`. The `zones` rule asserts each appears exactly once, in that
  order.
- **Counts are derived, never asserted.** `references/patterns.md` numbered rows and
  `references/templates.md` `## Template ` headings are the truth; any "N patterns" or "N templates"
  claim elsewhere must agree with them.
- **README's Version History is historical and exempt.** Claims below `## ℹ️ Version History`
  describe past releases — the `1.1.0` entry says "35 credit killing patterns" and will always say
  it. The `counts` rule stops scanning `README.md` at that heading.
- **If upstream changes a count, the rule goes green or red on its own.** Do not pre-empt it by
  editing these files.
