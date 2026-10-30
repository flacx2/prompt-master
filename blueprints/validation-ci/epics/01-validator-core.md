# Epic 01: Validator core

> After this epic the repository can state, in one command, whether it is self-consistent: seven rules exist, six of them here, and every one is green against the untouched upstream documents.

| | |
|---|---|
| **Epic id** | `01-validator-core` |
| **Tasks** | `E1-T1` … `E1-T6` (6 tasks) |
| **Depends on** | nothing — start here |
| **Unlocks** | `02-gate-and-ci` |
| **Parallel with** | nothing — every task edits `scripts/validate_skill.py` |

You do not need any other file to complete this epic. Everything below is repeated here on
purpose.

---

## Stack

A Markdown Claude Skill plus this repository's own validator. Python 3, standard library only — no
framework, no database, no dependency, no package manifest and no lockfile. The Python floor the code
targets is 3.9; the maintainer's machine runs 3.12 and CI pins the 3.12 series. There is no lockfile
to read a version out of, because there is nothing installed.

Use `python`, never `python3`: on the maintainer's Windows machine `python3` resolves to the Store
stub rather than an interpreter.

| Task | Command |
|---|---|
| Validate the skill | `python scripts/validate_skill.py` |
| Run one rule | `python scripts/validate_skill.py --rule <name>` |
| List the rules | `python scripts/validate_skill.py --list-rules` |
| Validate another tree | `python scripts/validate_skill.py --root <dir>` |
| Prove the rules can fail | `python scripts/validate_skill.py --self-test` |
| JSON output | `python scripts/validate_skill.py --format json` |
| CI annotations | `python scripts/validate_skill.py --format github` |
| Byte-compile the validator | `python -m compileall -q scripts` |
| Check the config parses | `python -m json.tool scripts/validator-config.json` |

**Gate:** `python scripts/validate_skill.py && python -m compileall -q scripts` passes before any
task here is marked done.

No task in this epic verifies against a service: there is none in this stack. The data layer is the
four committed Markdown files, read from disk.

## The two standing constraints

Both bind every task below, and breaking either is worse than leaving a task unfinished.

1. **`SKILL.md`, `README.md`, `LICENSE` and everything under `references/` are read-only.** This
   repository is a fork of `nidhinjs/prompt-master` and those files stay byte-identical so upstream
   merges never conflict. A rule that would need one of them edited to pass is a wrong rule — fix the
   rule. Every rule below was confirmed green against the real, untouched files on 2026-10-21, so a
   red rule on unmodified content means the rule drifted, not the documents.
2. **Standard library only.** No third-party import, no manifest, no lockfile. If a check seems to
   need a package, it is the wrong check.

## The exit-code contract

Every rule, every flag and both epics depend on this. It is three values and they are not
interchangeable:

| Exit | Meaning |
|---|---|
| `0` | every rule that ran produced no finding |
| `1` | at least one finding |
| `2` | the validator's own usage error — unknown flag, unknown rule name, missing or unparseable `scripts/validator-config.json`, a file named in the config's `files` that cannot be read |

Never collapse `2` into `1`. A gate whose pass condition were merely "non-zero" would accept a typo
in its own flag as proof the repository is broken, which is why several `Verify` lines below capture
the status and assert the exact code - `rc=0; <command> || rc=$?; test "$rc" -eq 2` - rather than
writing a bare negation or trailing `; test $? -eq 2`. The trailing form aborts under `set -e`,
which is how an unattended runner and every GitHub Actions `run:` step execute a block, so the
assertion never runs and the step dies claiming the command failed.

## The `Finding` shape

One record type, returned by every rule, rendered by one reporter so the three output formats cannot
drift apart:

| Field | Type | Notes |
|---|---|---|
| `rule` | string | one of the seven registry keys |
| `path` | string | repository-relative, forward slashes — never absolute, never backslashed, so output is identical on Windows and on the runner |
| `line` | int or null | 1-based when known; null for a whole-file finding |
| `message` | string | one line, stating what was expected and what was found |

Text output is `<path>:<line>: <rule>: <message>`, or `<path>: <rule>: <message>` when the line is
null, followed by one summary line.

## Directory subtree

Only the parts this epic touches:

```
SKILL.md                      # READ-ONLY (upstream) — 496 lines, three zone headings
README.md                     # READ-ONLY (upstream) — 422 lines
references/
  patterns.md                 # READ-ONLY (upstream) — 37 numbered table rows
  templates.md                # READ-ONLY (upstream) — 13 "## Template " headings
scripts/
  validator-config.json       # exists — landed by the workspace copy before task one. Do not edit
  validate_skill.py           # NEW in E1-T1, extended by every task in this epic
```

Everything outside this subtree is out of scope for this epic. If a task seems to require editing a
file not listed here, stop and report — it means the epic boundary is wrong.

## Configuration this epic reads

`scripts/validator-config.json` is already at the repository root before task one — it ships in the
blueprint bundle's `workspace/` and §10's Bootstrap copy lands it. **It is data, never logic: no
regular expression belongs in it.** Do not edit it; read these keys out of it.

| Key | What it holds |
|---|---|
| `files` | the four documents, each with `max_lines` (the ceiling the `budgets` rule enforces) and `counted_at_authoring` (what the file measured on 2026-10-21 — informational, compared by nothing) |
| `exclude_dirs` | `blueprints`, `.git`, `.github`, `.claude`, `.claude-flow`, `.swarm`, `scripts/tests/fixtures`, `__pycache__` |
| `skill_file`, `readme_file` | `SKILL.md` and `README.md` |
| `required_frontmatter_keys` | `name`, `version`, `description` |
| `expected_name` | `prompt-master` — the value the frontmatter `name` is compared against, **not** the directory name, which is what lets a fixture tree isolate one rule |
| `zones` | the three zone names, in the order they must appear |
| `counts` | per count kind: the `truth_file` and a `truth_kind` of `numbered_table_row` or `template_heading` |
| `claim_scan_stop_markers` | per file: the heading at which claim scanning stops. `README.md` stops at its Version History heading, below which a historical "35 credit killing patterns" entry must never be reported |
| `encoding` | `require_utf8`, `forbid_bom`, `require_single_trailing_newline`, and `forbid_crlf` which is **false** on purpose — every committed blob is CRLF and normalising them would edit a read-only file |

## Data model touched here

There is no database. The artifacts under validation are the data:

| Artifact | What this epic reads or asserts about it | Notes |
|---|---|---|
| `SKILL.md` frontmatter | `name`, `version`, `description`; `name` equals `expected_name`; `version` is three dot-separated digit runs | Read-only. Parsed in one place and reused |
| Numbered rows of `references/patterns.md` | the pattern count, derived at run time | 37 on the current tree. Never stored |
| `## Template ` headings of `references/templates.md` | the template count, derived at run time | 13 on the current tree. Never stored |
| Count claims in the documents | each must equal its derived truth, scanning `README.md` only above its Version History heading | Five claims on the current tree, all agreeing |
| Zone headings of `SKILL.md` | three names, each once, in order | Positional; the order is the mechanism |
| Line counts of the four documents | at or under `max_lines` | 496 / 422 / 82 / 442 against ceilings of 520 / 450 / 110 / 470 |
| Raw bytes of the four documents | UTF-8, no byte-order mark, exactly one trailing newline | CRLF is tolerated on purpose |

## Contracts

**Consumed** — already exists, do not rebuild:

| From | Interface | Guarantee |
|---|---|---|
| the bundle's `workspace/` | `scripts/validator-config.json` | every key in the configuration table above is present before task one; the file is data only and is not edited by any task |

**Produced** — later work depends on exactly these. Changing one breaks it:

| Export | Signature or shape | Used by |
|---|---|---|
| `scripts/validate_skill.py` -> `RULES` | an ordered mapping from rule name to a function taking the context and returning a list of findings | `02-gate-and-ci` |
| `scripts/validate_skill.py` -> `Finding` | the four-field record every rule returns and the reporter renders | `02-gate-and-ci` |
| `scripts/validate_skill.py` -> the frontmatter parser | returns the key-value mapping of the skill file's delimited header, or a parse failure | `02-gate-and-ci` |
| `scripts/validate_skill.py` -> `build_context` | reads the configured documents once: bytes, UTF-8 decode, CRLF normalised, keyed repository-relative | `02-gate-and-ci` |
| the exit-code contract 0 / 1 / 2 | clean / findings / usage error, asserted by gates in both epics | `02-gate-and-ci` |

## Conventions that bite in this area

- **Rules are pure functions.** They read and return findings. They never print, never write a file, never call `sys.exit`.
- **Only the reporter prints.** This is what keeps the three output formats in epic 02 from drifting.
- **Derive, never store.** Any number a rule compares against is counted from the file that owns it, at run time.
- **Normalise before analysing.** Read bytes, decode UTF-8, replace CRLF with LF — then every rule sees the same text.
- **Nothing walks the tree.** Rules read the configured paths and nothing else; `exclude_dirs` is a guard that exits 2 on a target resolving inside it, which is what keeps the validator out of `blueprints/`.
- **One parser per artifact.** The frontmatter block is parsed in one place and reused, not re-parsed per rule.

Full project rules: `CLAUDE.md`. Area rules: `.claude/rules/validator.md`,
`.claude/rules/skill-docs.md`, `.claude/rules/ci.md`. All of them sit in the repository root —
the builder copied them there from the bundle's `workspace/` before task one.

---

## Tasks

Listed in the same order as `tasks.json`. That order is the build order — work top to bottom and
do not re-rank by priority or by what looks quick.

### `E1-T1` — Build the validator harness and the budgets rule

**Depends on:** nothing · **Priority:** p0 — metadata for scope cuts, not a
running order

Create `scripts/validate_skill.py` from nothing. It is the harness every later task extends, so
get the seams right before adding rules: a `Finding` record, a config loader that exits 2 on any
problem with the file, a context builder that reads the documents once (bytes, UTF-8 decode, CRLF
normalised to LF, keyed by repository-relative path), an ordered `RULES` registry, and a reporter
that is the only thing in the program that prints.

Register exactly one rule here: `budgets`, which emits one finding per file over its `max_lines`.
**Line count is `len(text.splitlines())` — the number of newline-terminated lines, which is what
`wc -l` reports** and what the 496 / 422 / 82 / 442 figures in this epic were measured with. Splitting
on the newline character gives one more than that for a file ending in a newline, which all four do,
so a finding would quote a number nobody can reproduce.

**Validate the config's shape in the loader, not in the rule.** A `files` entry with a missing or
non-integer `max_lines` exits 2 — from `load_config`, because a rule is a pure function that returns
findings and never calls `sys.exit`. Validate the whole map once and every later rule can trust it.

Two things that look like details and are not. **No rule walks the tree** — the file set is exactly
what the config names, so `exclude_dirs` is enforced as a guard rather than a filter:
`assert_not_excluded` exits 2 when the `--config` path, a configured document path, a `--root` or a
fixture directory resolves inside one of those entries. **The `--config` path is in that list for a
reason:** a live run of this step proved that guarding only the document paths leaves
`--config blueprints/validation-ci/workspace/scripts/validator-config.json` perfectly runnable, which
is precisely the mistake the guard exists to refuse. And **a file listed in `files` that is absent exits 2, not 1**: that is a
broken config, not a drifted repository.

Add a version guard that exits 2 with a named error below Python 3.9, so an old interpreter produces
a sentence rather than a syntax error.

The file writes nothing, creates nothing and imports nothing outside the standard library — the last
of which this task's own gate asserts mechanically.

**Files**

- `scripts/validate_skill.py`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN `python scripts/validate_skill.py --version` runs THE SYSTEM SHALL print `validate_skill 1.0.0` and exit 0.
2. WHEN `python scripts/validate_skill.py --list-rules` runs THE SYSTEM SHALL print `budgets` and exit 0.
3. WHEN `python scripts/validate_skill.py` runs against this repository THE SYSTEM SHALL report zero findings and exit 0, because each document's newline-terminated line count — 496, 422, 82 and 442 — is under its ceiling in `scripts/validator-config.json`.
4. WHEN an unknown flag is passed THE SYSTEM SHALL exit 2 and SHALL NOT exit 1, so a malformed command can never be mistaken for a failing repository.
5. WHEN `--rule no-such-rule` is passed THE SYSTEM SHALL exit 2 and print the registered rule names.
6. WHEN `--config` names a file that does not exist THE SYSTEM SHALL exit 2 with a message beginning `config:`.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
python scripts/validate_skill.py --version
python scripts/validate_skill.py --version | grep -qx 'validate_skill 1.0.0'
python scripts/validate_skill.py --list-rules | grep -qx budgets
python scripts/validate_skill.py
python scripts/validate_skill.py --rule budgets
rc=0; python scripts/validate_skill.py --not-a-flag || rc=$?; test "$rc" -eq 2
rc=0; python scripts/validate_skill.py --rule no-such-rule || rc=$?; test "$rc" -eq 2
rc=0; python scripts/validate_skill.py --config scripts/nope.json || rc=$?; test "$rc" -eq 2
python -m compileall -q scripts
rc=0; grep -rn "^import \|^from " scripts/validate_skill.py | grep -vE "argparse|json|os|re|sys|pathlib|typing|dataclasses|collections" || rc=$?; test "$rc" -eq 1
test -f scripts/validator-config.json
rc=0; python scripts/validate_skill.py --config blueprints/validation-ci/workspace/scripts/validator-config.json || rc=$?; test "$rc" -eq 2
```

**Checkpoint**

```bash
git add -A && git commit -m "E1-T1: Build the validator harness and the budgets rule"
git tag step-01-harness
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

### `E1-T2` — Add the frontmatter rule

**Depends on:** `E1-T1` · **Priority:** p0 — metadata for scope cuts, not a
running order

Add `rule_frontmatter` and register it after `budgets`. Parse the delimited block at the top of the
skill file by hand — a line of three hyphens, then `key: value` lines, then a closing line of three
hyphens. Six lines of string handling; do not reach for a YAML package.

Compare the `name` value against the config's `expected_name`, **not** against the directory name.
This is the decision that makes the fixtures in E2-T2 possible: a fixture tree lives in a directory
called `frontmatter`, and a rule that inferred the expected name from the directory would fail every
fixture for the wrong reason.

Write the version check as three dot-separated runs of digits. Nothing stricter — upstream owns its
numbering, and this rule's job is to notice that the field became unparseable, not to have opinions
about pre-release suffixes.

Expose the parser so E1-T6 can reuse it. One parser, one place: two readers of the same block that
disagree is a defect waiting for a version bump.

**Files**

- `scripts/validate_skill.py`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN the `frontmatter` rule runs against this repository THE SYSTEM SHALL report zero findings, because `SKILL.md` carries `name`, `version` and `description` with `name` equal to the `expected_name` in `scripts/validator-config.json`.
2. WHEN the frontmatter block is missing its closing delimiter THE SYSTEM SHALL report exactly one finding at line 1.
3. WHEN a required key is absent THE SYSTEM SHALL report one finding naming that key.
4. WHEN the version value is not three dot-separated runs of digits THE SYSTEM SHALL report one finding quoting the value found.
5. WHEN `--list-rules` runs THE SYSTEM SHALL print both `budgets` and `frontmatter`.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
python scripts/validate_skill.py --rule frontmatter
python scripts/validate_skill.py --list-rules | grep -qx frontmatter
python scripts/validate_skill.py
python -m compileall -q scripts
```

**Checkpoint**

```bash
git add -A && git commit -m "E1-T2: Add the frontmatter rule"
git tag step-02-frontmatter
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

### `E1-T3` — Add the counts rule

**Depends on:** `E1-T1` · **Priority:** p0 — metadata for scope cuts, not a
running order

Add `rule_counts` and register it. This is the rule the whole change exists for — the one failure
this repository has already had, in `ab419d6`.

Derive each truth from its own file: numbered table rows in the patterns reference (a leading pipe,
optional spaces, digits, optional spaces, a pipe), and lines beginning with the literal
`## Template ` in the templates reference. **Never store 37 or 13 anywhere.** The whole point is that
upstream can change either number and the rule follows.

Then scan every document for claims, case-insensitively, as a number followed by at most one
intervening word and then the noun. That single shape is what catches all five forms the repository
actually uses — `37 patterns`, `37-pattern`, `37 Credit-Killing Patterns`, `13 templates` and
`13 Prompt Templates`.

**The stop marker is load-bearing, not an optimisation.** The readme's Version History records a
historical claim of 35 patterns in its `1.1.0` entry, and that entry is true about the past and will
never change. Scanning past the marker makes this rule permanently red on content the build may not
edit — which would be a wrong rule, by the first standing constraint above. Stop at
`claim_scan_stop_markers` for a file that has one; scan the whole file for one that does not.

A `counts` entry whose truth file is missing, or whose `truth_kind` is unknown, exits 2.

**Files**

- `scripts/validate_skill.py`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN the `counts` rule runs against this repository THE SYSTEM SHALL report zero findings, because every pattern claim equals the number of numbered table rows in `references/patterns.md` and every template claim equals the number of `## Template ` headings in `references/templates.md`.
2. WHEN a claim states a number that differs from its derived truth THE SYSTEM SHALL report one finding at that claim's line, naming both numbers.
3. WHEN a historical claim appears below the stop marker configured for that file THE SYSTEM SHALL report nothing for it.
4. WHEN a configured truth file is missing from the tree THE SYSTEM SHALL exit 2 rather than report a finding.
5. WHEN the number of rows in `references/patterns.md` changes and every claim is updated to match THE SYSTEM SHALL stay silent without any edit to the rule.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
python scripts/validate_skill.py --rule counts
python scripts/validate_skill.py --list-rules | grep -qx counts
python scripts/validate_skill.py
python -m compileall -q scripts
```

**Checkpoint**

```bash
git add -A && git commit -m "E1-T3: Add the counts rule"
git tag step-03-counts
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

### `E1-T4` — Add the zones rule

**Depends on:** `E1-T1` · **Priority:** p0 — metadata for scope cuts, not a
running order

Add `rule_zones` and register it. Read the three names from the config's `zones` list and assert each
appears exactly once in the skill file as the literal `## ` followed by the name, and that the three
appear in the listed order.

Three findings, three messages: missing, duplicated (carry the duplicate's line), and out of order
(name both zones involved). Keep them separate — a single "zones are wrong" message sends the reader
back to the file to work out which of the three happened.

The order is the mechanism this skill is built on, so the ordering half matters more than the
presence half.

**Files**

- `scripts/validate_skill.py`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN the `zones` rule runs against this repository THE SYSTEM SHALL report zero findings, because the three zone names in `scripts/validator-config.json` each appear exactly once in `SKILL.md` as a level-two heading, in the listed order.
2. WHEN a zone heading is absent THE SYSTEM SHALL report one finding naming that zone.
3. WHEN a zone heading appears twice THE SYSTEM SHALL report one finding carrying the line of the duplicate.
4. WHEN two zone headings appear in the wrong order THE SYSTEM SHALL report one finding naming both.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
python scripts/validate_skill.py --rule zones
python scripts/validate_skill.py --list-rules | grep -qx zones
python scripts/validate_skill.py
python -m compileall -q scripts
```

**Checkpoint**

```bash
git add -A && git commit -m "E1-T4: Add the zones rule"
git tag step-04-zones
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

### `E1-T5` — Add the links rule

**Depends on:** `E1-T1` · **Priority:** p0 — metadata for scope cuts, not a
running order

Add `rule_links` and register it. Two checks over text the context already holds.

Reference paths: every mention of a path under `references/` ending in `.md`, in either document, must
exist on disk. There are two such paths today and both resolve.

In-file anchors: in the templates reference, every Markdown link whose target starts with `#` must
resolve to a heading in that same file. **Implement GitHub's slug algorithm exactly** — lowercase the
heading text, drop every character that is not a word character, whitespace or a hyphen, then replace
EACH whitespace character with a hyphen - per character, never per run. The thirteen
table-of-contents entries use em dashes, so a
naive slugger that keeps punctuation or collapses double hyphens reports thirteen false findings on
correct content. All thirteen were confirmed to resolve under this algorithm on 2026-10-21; if your
implementation disagrees, the implementation is wrong.

**Files**

- `scripts/validate_skill.py`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN the `links` rule runs against this repository THE SYSTEM SHALL report zero findings, because both paths under `references/` that the documents mention exist on disk and every in-file anchor link in `references/templates.md` resolves to a heading in that same file.
2. WHEN a mentioned path under `references/` does not exist THE SYSTEM SHALL report one finding at the mention's line.
3. WHEN an in-file anchor names a slug no heading produces THE SYSTEM SHALL report one finding carrying that slug.
4. WHEN a heading contains an em dash THE SYSTEM SHALL compute the same slug GitHub computes — lowercase, drop every character that is not a word character, whitespace or hyphen, then replace EACH whitespace character with a hyphen, per character and never per run, so an em dash between two spaces yields a double hyphen — and a correct table-of-contents entry is therefore not reported.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
python scripts/validate_skill.py --rule links
python scripts/validate_skill.py --list-rules | grep -qx links
python scripts/validate_skill.py
python -m compileall -q scripts
```

**Checkpoint**

```bash
git add -A && git commit -m "E1-T5: Add the links rule"
git tag step-05-links
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

### `E1-T6` — Add the version-sync rule

**Depends on:** `E1-T1`, `E1-T2` · **Priority:** p1 — metadata for scope cuts, not a
running order

Add `rule_version_sync` under the registry name `version-sync`. Reuse the frontmatter parser from
E1-T2 rather than parsing the block a second time, then assert that the version rendered in bold
Markdown appears somewhere in the readme.

Presence, not ordering. Asserting that the newest Version History entry matches would be a regex over
upstream's prose formatting — a gate that breaks on a wording change rather than on a real defect, on
content that may not be edited to satisfy it.

When the frontmatter block does not parse, return nothing here and let the `frontmatter` rule own
that failure. One defect, one finding: two rules reporting the same broken header trains the reader
to skim.

**Files**

- `scripts/validate_skill.py`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN the `version-sync` rule runs against this repository THE SYSTEM SHALL report zero findings, because the frontmatter version rendered in bold Markdown appears in `README.md`.
2. WHEN the frontmatter version is bumped and `README.md` is not updated THE SYSTEM SHALL report exactly one finding naming the missing version.
3. WHEN the frontmatter block is unparseable THE SYSTEM SHALL report nothing here, leaving that failure to the `frontmatter` rule, so one defect produces one finding.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
python scripts/validate_skill.py --rule version-sync
python scripts/validate_skill.py --list-rules | grep -qx version-sync
python scripts/validate_skill.py
python -m compileall -q scripts
```

**Checkpoint**

```bash
git add -A && git commit -m "E1-T6: Add the version-sync rule"
git tag step-06-version-sync
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

---

## Epic acceptance

The epic is done when every task is `done` **and**:

1. WHEN `python scripts/validate_skill.py` runs against the untouched repository THE SYSTEM SHALL report zero findings and exit 0 with six rules registered.
2. WHEN `python scripts/validate_skill.py --list-rules` runs THE SYSTEM SHALL print `budgets`, `frontmatter`, `counts`, `zones`, `links` and `version-sync`.
3. WHEN any rule is given a tree whose relevant property is broken THE SYSTEM SHALL exit 1, and WHEN given a malformed command or an unusable config THE SYSTEM SHALL exit 2 instead.
4. WHEN the epic is complete THE SYSTEM SHALL have left `SKILL.md`, `README.md`, `LICENSE` and both files under `references/` byte-identical to their committed state.

```bash
python scripts/validate_skill.py
python -m compileall -q scripts
python scripts/validate_skill.py --list-rules
git diff --quiet HEAD -- SKILL.md README.md LICENSE references
```

Run from the repository root. Every criterion above is decidable by these commands — nothing here
waits on a human or an external service.

## Pitfalls

- **Adding a tree walk.** The validator reads the paths its config names and nothing else. An
  `rglob` added for convenience immediately finds `blueprints/validation-ci/workspace/`, which holds
  its own copy of the config, and the rules start reporting on the blueprint instead of on the skill.
  Enforce `exclude_dirs` as a guard in the first task; retrofitting it later means re-verifying every
  rule built before it.
- **Storing 37 or 13.** The counts rule derives both at run time. A constant anywhere in the file is
  the defect this whole change exists to prevent, written by the thing meant to prevent it.
- **Inferring the expected skill name from the directory.** It comes from `expected_name` in the
  config. The directory-name version passes here and breaks every fixture in epic 02.
- **Scanning the readme past its Version History heading.** The `1.1.0` entry claims 35 patterns,
  truthfully, about the past. A rule that reports it is permanently red on content nobody may edit.
- **A naive anchor slugger.** The thirteen table-of-contents headings contain em dashes. Drop every
  character that is not a word character, whitespace or hyphen, then replace EACH whitespace
  character with a hyphen. Per character, never per run: a live build collapsed the runs and reported
  all thirteen correct anchors as broken.
- **Returning exit 1 for a bad flag or a missing config.** Those are exit 2. Several gates assert the
  exact code, so collapsing them turns a green gate into a lie.
- **Reaching for PyYAML, pytest or ruff.** The frontmatter block is three flat keys and the file is
  one module. A dependency here breaks the rule that there are none.

## Before moving on

- [ ] Every task in this epic is `done` in `tasks.json` — no task left `in_progress`.
- [ ] Every `verify` command of every task passed, not just the first one.
- [ ] No `verify` command was edited, and none was skipped because a file it names did not exist.
- [ ] **Every task in this epic has its `checkpoint` tag in version control** — one tag per task,
      matching the `checkpoint` value in `tasks.json`. `git tag -l 'step-*'` lists them.
- [ ] The epic gate above passes clean, run from the repository root.
- [ ] Every "Produced" contract above exists with the stated shape.
- [ ] No file outside the subtree was modified — and in particular `SKILL.md`, `README.md`,
      `LICENSE` and `references/**` are byte-identical to `HEAD`.
- [ ] This project has no environment variables and no `.env.example`, so there is nothing to
      update — stated here rather than left as an unchecked box.
- [ ] One commit per task, each prefixed with its task id, each followed by its checkpoint tag.
