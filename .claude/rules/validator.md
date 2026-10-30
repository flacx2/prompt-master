---
description: Conventions for the repository's own validator — standard library only, rules as pure functions, exit codes as a public interface
paths:
  - "scripts/**"
---

# Validator conventions

- **Standard library only.** No third-party import, ever. No manifest, no lockfile. If a rule seems
  to need a package, the rule is wrong.
- **Python 3.9 floor.** No `match`, no `tomllib`, no PEP 604 unions evaluated at runtime.
- **A rule is a pure function**: `rule_<name>(ctx) -> list[Finding]`. It reads, it returns findings.
  It never prints, never writes a file, never calls `sys.exit`.
- **Register every rule in `RULES`**, keyed by its kebab-case name. `--list-rules` prints the
  registry; `--rule <name>` runs exactly one.
- **A `Finding` carries** `rule`, `path`, `line` (or `None`) and `message`. One reporter formats all
  three output modes, so default, `json` and `github` output cannot drift apart.
- **Exit codes:** `0` no findings · `1` findings · `2` the validator's own usage error — unknown
  flag, unknown rule name, missing or unparseable `scripts/validator-config.json`, unreadable file.
  Never return 1 for a usage error: a vacuous gate is worse than no gate.
- **Config holds data, not logic.** Ceilings, paths, zone names, excluded directories and required
  frontmatter keys live in `scripts/validator-config.json`. Regular expressions live in the code.
- **Derive counts at run time.** Never cache the pattern or template count anywhere.
- **Normalise before analysing.** Read bytes, decode UTF-8, replace CRLF with LF. The committed
  blobs are CRLF and that is upstream's choice, not a defect to flag.
- **Every rule gets a negative fixture** in `scripts/tests/fixtures/<rule>/`, and `--self-test`
  asserts that fixture fails that rule and no other.
- **No rule walks the tree.** A rule reads only the paths the config names. `exclude_dirs` is a
  guard: the validator exits 2 rather than read a configured path, a `--root` or a fixture directory
  resolving inside it, which is what keeps it out of `blueprints/` and out of the fixtures. Only
  `--self-test` reaches `scripts/tests/fixtures/`.
