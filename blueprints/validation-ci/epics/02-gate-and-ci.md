# Epic 02: Gate and CI

> After this epic every rule has been proven able to fail, the validator speaks JSON and GitHub annotations, and a pull request cannot be merged past a drift without someone choosing to ignore a red check.

| | |
|---|---|
| **Epic id** | `02-gate-and-ci` |
| **Tasks** | `E2-T1` … `E2-T6` (6 tasks) |
| **Depends on** | `01-validator-core` |
| **Unlocks** | nothing — this is the last epic |
| **Parallel with** | nothing — E2-T1 through E2-T4 all edit `scripts/validate_skill.py`, and E2-T5 and E2-T6 depend on them |

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
SKILL.md                      # READ-ONLY (upstream)
README.md                     # READ-ONLY (upstream)
references/
  patterns.md                 # READ-ONLY (upstream) — 37 numbered table rows
  templates.md                # READ-ONLY (upstream) — 13 "## Template " headings
scripts/
  validator-config.json       # exists — landed by the workspace copy. Do not edit
  validate_skill.py           # exists from epic 01 — extended by E2-T1 through E2-T4
  tests/
    fixtures/                 # NEW in E2-T2 and E2-T3; only --self-test reads them
      budgets/ frontmatter/ counts/ zones/ links/ version-sync/ encoding/
.github/
  workflows/
    validate.yml              # NEW in E2-T5
.githooks/
  pre-commit                  # NEW in E2-T6
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
| `01-validator-core` | `RULES`, `Finding`, `build_context`, the frontmatter parser | six rules registered and green against the untouched repository; findings carry repository-relative forward-slash paths |
| `01-validator-core` | the exit-code contract | 0 clean, 1 findings, 2 usage error — the fixtures' gates assert 1 and the flag gates assert 2 |
| the bundle's `workspace/` | `scripts/validator-config.json`, `.claude/settings.json` | the config's `exclude_dirs` already lists `scripts/tests/fixtures`; the settings file already allows every command below |

**Produced** — later work depends on exactly these. Changing one breaks it:

| Export | Signature or shape | Used by |
|---|---|---|
| `scripts/validate_skill.py` -> `--root` | resolves every path relative to the given directory while the config still defaults to the repository's own | E2-T3, and anyone debugging a rule |
| `scripts/validate_skill.py` -> `--self-test` | exits 0 only when every fixture fails its own rule and no other, and when every registered rule has a fixture | E2-T5's workflow, E2-T6's hook |
| `scripts/validate_skill.py` -> `--format json` | the five-key object: `tool`, `repo_root`, `rules_run`, `findings`, `exit_code` | any consumer; E2-T6's gate |
| `scripts/validate_skill.py` -> `--format github` | one `::error file=...` annotation per finding | E2-T5's workflow |
| `.github/workflows/validate.yml` | one job running compile, config parse, self-test and annotated run, on `pull_request` and `push` to `main` | the repository's merge process |
| `.githooks/pre-commit` | the same gate locally, aborting a commit on the first failure | the maintainer, after one `git config core.hooksPath .githooks` |

## Conventions that bite in this area

- **A fixture breaks exactly one thing.** Everything else in it is valid, or `--self-test` fails for the wrong reason.
- **A fixture may carry its own config.** `scripts/tests/fixtures/<rule>/validator-config.json` wins over the repository's when present — this is how `budgets` is tested without a 521-line file.
- **Formatting lives in the reporter.** Three output formats, one code path.
- **Actions are pinned by commit SHA**, tag in a trailing comment. Never a tag reference.
- **`contents: read` is the permission ceiling.** Nothing in this workflow writes.
- **`python`, never `python3`** — in the workflow, in the hook, everywhere.
- **CI blocks, the hook reminds.** Never make anything depend on the hook having run.

Full project rules: `CLAUDE.md`. Area rules: `.claude/rules/validator.md`,
`.claude/rules/skill-docs.md`, `.claude/rules/ci.md`. All of them sit in the repository root —
the builder copied them there from the bundle's `workspace/` before task one.

---

## Tasks

Listed in the same order as `tasks.json`. That order is the build order — work top to bottom and
do not re-rank by priority or by what looks quick.

### `E2-T1` — Add the encoding rule

**Depends on:** `E1-T1` · **Priority:** p1 — metadata for scope cuts, not a
running order

Add `rule_encoding` and register it last — it is the only rule that looks at raw bytes, so it runs
after the structural ones have had their say.

Three assertions, each switched by the config's `encoding` object: the bytes decode as UTF-8 (name the
offset when they do not), there is no byte-order mark, and the file ends with exactly one newline —
not zero, not two.

**`forbid_crlf` is false and the rule must honour it.** Every committed blob in this repository is
CRLF and `core.autocrlf` is `true` locally; flagging that would demand a rewrite of all four
read-only documents and guarantee a conflict on the next upstream merge. The rule normalises CRLF for
analysis and says nothing about it. The config carries a comment explaining why, so do not flip the
flag without reading the blueprint's Non-Goals.

This task closes the registry at seven rules, and its gate asserts that count.

**Files**

- `scripts/validate_skill.py`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN the `encoding` rule runs against this repository THE SYSTEM SHALL report zero findings for all four documents.
2. WHEN a file carries a byte-order mark THE SYSTEM SHALL report one finding for that file.
3. WHEN a file ends with two or more newlines THE SYSTEM SHALL report one finding for that file.
4. WHEN a file ends with no newline THE SYSTEM SHALL report one finding for that file.
5. WHEN a file contains CRLF line endings and `forbid_crlf` is false in `scripts/validator-config.json` THE SYSTEM SHALL report nothing for it.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
python scripts/validate_skill.py --rule encoding
python scripts/validate_skill.py --list-rules | grep -qx encoding
python scripts/validate_skill.py
test "$(python scripts/validate_skill.py --list-rules | wc -l | tr -d ' ')" = 7
python -m compileall -q scripts
```

**Checkpoint**

```bash
git add -A && git commit -m "E2-T1: Add the encoding rule"
git tag step-07-encoding
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

### `E2-T2` — Add --root and the first three negative fixtures

**Depends on:** `E1-T1`, `E1-T2`, `E1-T3` · **Priority:** p0 — metadata for scope cuts, not a
running order

Two pieces: the `--root` flag, and the first three fixtures.

`--root` makes every path the validator resolves relative to the given directory while the config
still defaults to the repository's own. That split is deliberate — most fixtures want the real config
and a broken tree.

Then build three minimal four-document trees under `scripts/tests/fixtures/`, each breaking exactly
one rule. **The isolation is the whole value of a fixture**, so every fixture's skill file carries the
configured expected name, the three zones in order, resolvable reference paths and a bold version
matching its own frontmatter. A fixture that trips three rules proves nothing about any of them.

- `budgets/` — plus its **own** `validator-config.json` with a `max_lines` of 1 for the skill file.
  That is how a ceiling breach is demonstrated without committing a 521-line document, and E2-T3's
  self-test prefers a fixture-local config when one exists.
- `frontmatter/` — the skill file's `version` value replaced by something that is not three
  dot-separated digit runs.
- `counts/` — one pattern claim in the readme stating a number that differs from the rows in that
  fixture's own patterns reference, **and** a Version History section below the stop marker whose
  historical claim also differs. One fixture, both halves of the rule: the first claim must be
  reported and the second must not, which is why this task's gate expects exactly one finding.

Nothing walks the tree, so none of this is reachable from a plain run — and the fixture directory is
named by `fixtures_dir` rather than `exclude_dirs` precisely so `--root` can still point at it. A
live build proved the alternative: with the fixtures inside `exclude_dirs`, every gate below exits 2.

**Files**

- `scripts/validate_skill.py`
- `scripts/tests/fixtures/budgets/**`
- `scripts/tests/fixtures/frontmatter/**`
- `scripts/tests/fixtures/counts/**`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN the validator runs with `--root` pointed at the budgets fixture and that fixture's own config THE SYSTEM SHALL report at least one `budgets` finding and exit 1.
2. WHEN it runs the `zones` rule against that same fixture THE SYSTEM SHALL report zero findings and exit 0, proving the fixture isolates one rule.
3. WHEN it runs the `frontmatter` rule against the frontmatter fixture THE SYSTEM SHALL report at least one finding and exit 1.
4. WHEN it runs the `counts` rule against the counts fixture THE SYSTEM SHALL report exactly one finding — the claim above the stop marker, not the historical one below it — and exit 1.
5. WHEN a plain full run of the repository runs after the fixtures are added THE SYSTEM SHALL still exit 0, because no rule reads anything the config does not name — and the fixture directory is named by `fixtures_dir` rather than `exclude_dirs`, so `--root` can still reach it.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
rc=0; python scripts/validate_skill.py --root scripts/tests/fixtures/budgets --config scripts/tests/fixtures/budgets/validator-config.json --rule budgets || rc=$?; test "$rc" -eq 1
python scripts/validate_skill.py --root scripts/tests/fixtures/budgets --rule zones
rc=0; python scripts/validate_skill.py --root scripts/tests/fixtures/frontmatter --rule frontmatter || rc=$?; test "$rc" -eq 1
python scripts/validate_skill.py --root scripts/tests/fixtures/frontmatter --rule counts
rc=0; python scripts/validate_skill.py --root scripts/tests/fixtures/counts --rule counts || rc=$?; test "$rc" -eq 1
python scripts/validate_skill.py --root scripts/tests/fixtures/counts --rule zones
python scripts/validate_skill.py
python -m compileall -q scripts
```

**Checkpoint**

```bash
git add -A && git commit -m "E2-T2: Add --root and the first three negative fixtures"
git tag step-08-fixtures-a
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

### `E2-T3` — Add the remaining four fixtures and --self-test

**Depends on:** `E1-T4`, `E1-T5`, `E1-T6`, `E2-T1`, `E2-T2` · **Priority:** p0 — metadata for scope cuts, not a
running order

Four more fixtures on the pattern E2-T2 established — `zones/` with two zone headings transposed,
`links/` with a table-of-contents anchor no heading produces, `version-sync/` with a frontmatter
version absent from its readme, `encoding/` with a document ending in two newlines — and then
`--self-test`, which is what turns seven rules into seven rules that can be trusted.

`--self-test` enumerates the directories under `scripts/tests/fixtures/`, skipping any directory named in
`exclude_dirs` so a stray `__pycache__` is never taken for a fixture, and for each one runs **every** registered rule
with that directory as the root, using a fixture-local `validator-config.json` when one is present and
the repository's otherwise. It asserts two things per fixture: the rule of the same name reports at
least one finding, and every other rule reports none.

Make a registered rule with no fixture directory an exit-1 failure. That is the line that stops rule
number eight from shipping without its proof, and it is why the `add-validator-rule` skill in
`.claude/skills/` lists the fixture as a step rather than a suggestion.

**Files**

- `scripts/validate_skill.py`
- `scripts/tests/fixtures/zones/**`
- `scripts/tests/fixtures/links/**`
- `scripts/tests/fixtures/version-sync/**`
- `scripts/tests/fixtures/encoding/**`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN `--self-test` runs THE SYSTEM SHALL print one line per fixture directory and exit 0.
2. WHEN a fixture stops failing its own rule THE SYSTEM SHALL exit 1 naming that fixture and the rule that went silent.
3. WHEN a fixture fails a rule other than its own THE SYSTEM SHALL exit 1 naming the fixture and the unexpected rule.
4. WHEN a rule is registered with no fixture directory of the same name THE SYSTEM SHALL exit 1, so a rule added later cannot skip its proof.
5. WHEN a plain full run of the repository runs afterwards THE SYSTEM SHALL still exit 0.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
python scripts/validate_skill.py --self-test
rc=0; python scripts/validate_skill.py --root scripts/tests/fixtures/zones --rule zones || rc=$?; test "$rc" -eq 1
rc=0; python scripts/validate_skill.py --root scripts/tests/fixtures/links --rule links || rc=$?; test "$rc" -eq 1
rc=0; python scripts/validate_skill.py --root scripts/tests/fixtures/version-sync --rule version-sync || rc=$?; test "$rc" -eq 1
rc=0; python scripts/validate_skill.py --root scripts/tests/fixtures/encoding --rule encoding || rc=$?; test "$rc" -eq 1
python scripts/validate_skill.py
python -m compileall -q scripts
```

**Checkpoint**

```bash
git add -A && git commit -m "E2-T3: Add the remaining four fixtures and --self-test"
git tag step-09-fixtures-b
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

### `E2-T4` — Add the json and github output formats

**Depends on:** `E1-T1`, `E2-T3` · **Priority:** p1 — metadata for scope cuts, not a
running order

Add `--format`, defaulting to `text`, with `json` and `github`.

Do the work in the reporter and nowhere else. If a rule starts formatting its own output, the three
formats drift and the JSON consumer gets something the text output does not say.

`json` emits exactly five keys — `tool`, `repo_root`, `rules_run`, `findings`, `exit_code` — with
`findings` a list of the four-field records, and nothing else on stdout. The process exit code still
follows the contract above, so a consumer can read either.

`github` emits one `::error file=<path>,line=<line>::<rule>: <message>` per finding, dropping the
line component when the finding has none. That is the annotation syntax that puts a finding on the
diff in a pull request, which is the whole reason CI runs this format last.

Use `json.dumps` with `indent=2` and leave the spacing alone: this task's gate greps for
`"exit_code": 0` and `"findings": []`, and a hand-built string or a different separator setting
breaks those lines for a reason that has nothing to do with the repository.

**`indent=2` also puts every non-empty list element on its own line**, so do not expect
`"rules_run": ["counts"]` to appear anywhere — a live build hit exactly that. The gate strips
whitespace with `tr -d '[:space:]'` before grepping — `' 
'` leaves the carriage returns a Windows
interpreter emits, which a live build spent a round on, which asserts the property without depending on the
formatter's line breaks.

**Files**

- `scripts/validate_skill.py`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN `--format json` runs on a clean tree THE SYSTEM SHALL print one JSON object whose `findings` is an empty list and whose `exit_code` is 0, and exit 0.
2. WHEN `--format json` runs THE SYSTEM SHALL emit the five keys `tool`, `repo_root`, `rules_run`, `findings` and `exit_code`, and nothing else on stdout.
3. WHEN `--format json` runs with a single rule selected THE SYSTEM SHALL list only that rule in `rules_run`.
4. WHEN `--format github` runs against a fixture that fails THE SYSTEM SHALL print at least one line beginning `::error file=` and exit 1.
5. WHEN `--format` is given an unknown value THE SYSTEM SHALL exit 2.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
python scripts/validate_skill.py --format json | python -m json.tool > /dev/null
python scripts/validate_skill.py --format json | grep -q '"exit_code": 0'
python scripts/validate_skill.py --format json | grep -qF '"findings": []'
python scripts/validate_skill.py --format json | grep -q '"tool": "validate_skill"'
python scripts/validate_skill.py --format json --rule counts | tr -d '[:space:]' | grep -qF '"rules_run":["counts"]'
python scripts/validate_skill.py --root scripts/tests/fixtures/zones --rule zones --format github | grep -q '^::error file='
rc=0; python scripts/validate_skill.py --format nope || rc=$?; test "$rc" -eq 2
python scripts/validate_skill.py --self-test
python -m compileall -q scripts
```

**Checkpoint**

```bash
git add -A && git commit -m "E2-T4: Add the json and github output formats"
git tag step-10-formats
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

### `E2-T5` — Add the blocking GitHub Actions workflow

**Depends on:** `E2-T4` · **Priority:** p0 — metadata for scope cuts, not a
running order

Create `.github/workflows/validate.yml`. One job, `validate`, on `ubuntu-latest`, triggered by
`pull_request` and by `push` restricted to `main` — the pull-request run is the one that blocks, and
the `main` run reports after the fact by construction.

Four things that are not stylistic:

- **`permissions: contents: read`** at the workflow level and nothing wider. This job reads the
  repository and reports a status; a write scope would be a standing credential for no reason.
- **Both actions pinned by 40-character commit SHA**, with the human tag in a trailing comment:
  `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1` and
  `actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7.1.0`. Both SHAs were read from
  the GitHub API on 2026-10-21 and both tag refs were type `commit`, so each SHA is the commit its tag
  names. Copy them character for character — a wrong digit fails CI with a message about a missing
  action, which reads as GitHub being broken.
- **`python-version: "3.12"`**, matching the maintainer's local interpreter. A gate that is green
  locally and red in CI on an interpreter difference is worse than one release behind.
- **`concurrency` keyed on workflow and ref with `cancel-in-progress: true`, and
  `timeout-minutes: 5`.** A stacked push should cancel the stale run, and a hung job should not hold a
  runner.

Then the four commands, in this order: `compileall`, `json.tool` on the config, `--self-test`, and
`--format github` last so a finding lands on the diff rather than in the log tail. Nothing is
installed, because there is nothing to install.

**Files**

- `.github/workflows/validate.yml`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN the workflow file is parsed by GitHub THE SYSTEM SHALL define exactly one job that runs `python -m compileall -q scripts`, `python -m json.tool scripts/validator-config.json`, `python scripts/validate_skill.py --self-test` and `python scripts/validate_skill.py --format github`, in that order.
2. WHEN either action is referenced THE SYSTEM SHALL name it by a 40-character commit SHA, never by a tag or a branch.
3. WHEN the workflow declares permissions THE SYSTEM SHALL grant `contents: read` and nothing else.
4. WHEN a pull request is opened or a commit lands on `main` THE SYSTEM SHALL be the complete trigger set, with no other event listed.
5. WHEN the job exceeds five minutes THE SYSTEM SHALL be cancelled by its own `timeout-minutes`.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
test -f .github/workflows/validate.yml
grep -q "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" .github/workflows/validate.yml
grep -q "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0" .github/workflows/validate.yml
grep -qE "^ *contents: read" .github/workflows/validate.yml
grep -q "pull_request" .github/workflows/validate.yml
grep -qE '^ *python-version: "3.12"' .github/workflows/validate.yml
grep -q "validate_skill.py --self-test" .github/workflows/validate.yml
grep -q "validate_skill.py --format github" .github/workflows/validate.yml
rc=0; grep -qE "uses: actions/[a-z-]+@v[0-9]" .github/workflows/validate.yml || rc=$?; test "$rc" -eq 1
rc=0; grep -qE "packages: write|contents: write|id-token: write" .github/workflows/validate.yml || rc=$?; test "$rc" -eq 1
python scripts/validate_skill.py && python scripts/validate_skill.py --self-test
```

**Checkpoint**

```bash
git add -A && git commit -m "E2-T5: Add the blocking GitHub Actions workflow"
git tag step-11-workflow
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

### `E2-T6` — Add the pre-commit hook and close the full gate

**Depends on:** `E2-T5` · **Priority:** p1 — metadata for scope cuts, not a
running order

Create `.githooks/pre-commit`: a POSIX shell script that runs `python -m compileall -q scripts`, then
`python scripts/validate_skill.py --self-test`, then `python scripts/validate_skill.py`, aborting on
the first non-zero exit with the reason on one line.

It runs under the shell git ships on Windows, so no bashisms, no arrays, and `python` rather than
`python3` — this task's gate greps for `python3` and expects not to find it.

Then `git config core.hooksPath .githooks`, which is repository-local and idempotent. Say in
`CLAUDE.md`'s command table that a fresh clone runs that once; a hook directory does nothing until
git is pointed at it.

**The hook is a convenience and never the gate.** It is bypassable with `--no-verify` and absent on a
fresh clone, so nothing may depend on it having run — which is exactly why E2-T5's workflow also runs
on `push` to `main`.

This task closes the epic, so its gate is the full set: compile, config parse, self-test, full run,
JSON parse, the hook itself, the unknown-flag exit code, and a diff of the four upstream documents
against `HEAD` to prove the change never touched them.

**Files**

- `.githooks/pre-commit`

**Acceptance**

Copied verbatim from this task's `acceptance` array in `tasks.json`. Each one is decidable by a
command below, on this machine, during the build.

1. WHEN `sh .githooks/pre-commit` runs on a clean tree THE SYSTEM SHALL exit 0.
2. WHEN the hook runs against a tree whose validator reports a finding THE SYSTEM SHALL exit non-zero with the reason on one line, so the commit is aborted.
3. WHEN `git config core.hooksPath` is read after this task THE SYSTEM SHALL return `.githooks`.
4. WHEN the hook is read THE SYSTEM SHALL contain no reference to `python3`, which resolves to the Windows Store stub rather than an interpreter on the maintainer's machine.
5. WHEN the whole gate runs — compile, config parse, self-test, full run, JSON parse, hook, unknown-flag exit code, and a diff of the four upstream documents against HEAD — THE SYSTEM SHALL exit 0 on every line.

**Verify** — every command, in order, run from the repository root. Each exits 0 when this task
is correct; the last one exiting 0 is what makes the task done. Exit-code wrapping is part of the
command - do not unwrap `rc=0; ... || rc=$?; test "$rc" -eq N` into the bare call, and do not
shorten it to a trailing `; test $? -eq N`, which `set -e` aborts before the assertion.

```bash
test -x .githooks/pre-commit || test -f .githooks/pre-commit
sh .githooks/pre-commit
rc=0; grep -q "python3" .githooks/pre-commit || rc=$?; test "$rc" -eq 1
git config core.hooksPath .githooks
test "$(git config core.hooksPath)" = ".githooks"
python -m compileall -q scripts
python -m json.tool scripts/validator-config.json > /dev/null
python scripts/validate_skill.py --self-test
python scripts/validate_skill.py
python scripts/validate_skill.py --format json | python -m json.tool > /dev/null
git diff --quiet HEAD -- SKILL.md README.md LICENSE references
```

**Checkpoint**

```bash
git add -A && git commit -m "E2-T6: Add the pre-commit hook and close the full gate"
git tag step-12-hook
```

Run both after the last `Verify` command exits 0, before starting the next task. The tag is this
task's rollback target and one of the twelve the final gate counts — if the next task goes wrong,
`git reset --hard` to *this* tag rather than debugging forward.

---

## Epic acceptance

The epic is done when every task is `done` **and**:

1. WHEN `python scripts/validate_skill.py --self-test` runs THE SYSTEM SHALL exit 0, having proved that each of the seven rules reports a finding on its own fixture and stays silent on the other six.
2. WHEN `python scripts/validate_skill.py --format json` runs on a clean tree THE SYSTEM SHALL emit one parseable object with an empty `findings` list and `exit_code` 0.
3. WHEN `.github/workflows/validate.yml` is read THE SYSTEM SHALL carry both 40-character action SHAs, the `contents: read` ceiling, the `pull_request` and `push`-to-`main` triggers, and the four gate commands in order.
4. WHEN `sh .githooks/pre-commit` runs on a clean tree THE SYSTEM SHALL exit 0, and WHEN the validator reports a finding THE SYSTEM SHALL exit non-zero so the commit is aborted.
5. WHEN the epic is complete THE SYSTEM SHALL have left `SKILL.md`, `README.md`, `LICENSE` and both files under `references/` byte-identical to their committed state, and SHALL have added no manifest and no lockfile.

```bash
python scripts/validate_skill.py --self-test
python scripts/validate_skill.py
python -m compileall -q scripts
python -m json.tool scripts/validator-config.json > /dev/null
sh .githooks/pre-commit
git diff --quiet HEAD -- SKILL.md README.md LICENSE references
```

Run from the repository root. Every criterion above is decidable by these commands — nothing here
waits on a human or an external service.

## Pitfalls

- **Normalising CRLF.** Every committed blob is CRLF. `forbid_crlf` is false on purpose; flipping it
  makes the gate red on day one and fixable only by rewriting the four read-only documents.
- **A fixture that trips more than its own rule.** `--self-test` fails on exactly this, and it is
  easy to cause by forgetting a zone heading or a bold version in a fixture's documents. Give every
  fixture a complete, valid set and break one thing.
- **Giving the budgets fixture a 521-line document.** It gets its own `validator-config.json` with a
  one-line ceiling instead.
- **Hand-building the JSON.** Use `json.dumps(..., indent=2)`. The gate greps for `"exit_code": 0`
  and `"findings": []`, and a different separator setting breaks those lines for a reason unrelated to
  the repository.
- **A floating action tag.** `actions/checkout@v7` is a remote-code-execution path into CI. The gate
  greps for that shape and expects no match; pin the SHA and put the tag in a comment.
- **Any write permission in the workflow.** `contents: read` and nothing else. The gate greps for
  `contents: write`, `packages: write` and `id-token: write` and expects none.
- **`python3` in the hook.** It resolves to the Windows Store stub on the maintainer's machine, so the
  hook would abort every commit with a message about installing Python.
- **Treating the hook as the gate.** It is bypassable and absent on a fresh clone. CI blocks; the hook
  is a convenience.
- **Editing an upstream document to turn something green.** The last gate in E2-T6 diffs all four
  against `HEAD` precisely so that this cannot pass unnoticed.

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
