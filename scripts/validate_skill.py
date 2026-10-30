#!/usr/bin/env python
"""validate_skill - assert that this repository is self-consistent.

The skill this repository ships is Markdown, so its correctness is a property of
its prose: a heading that moved, a count that no longer matches the table it
describes, a reference link pointing at a file that was renamed. This script is
the executable statement of those rules.

Standard library only. It reads; it never writes.

Exit codes are a public interface:
    0  every rule that ran produced no finding
    1  at least one finding
    2  the validator's own usage error
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

TOOL = "validate_skill"
VERSION = "1.0.0"
MIN_PYTHON = (3, 9)

if sys.version_info < MIN_PYTHON:
    sys.stderr.write(
        "python: %s needs Python %d.%d or newer, found %d.%d\n"
        % (TOOL, MIN_PYTHON[0], MIN_PYTHON[1], sys.version_info[0], sys.version_info[1])
    )
    raise SystemExit(2)


# --------------------------------------------------------------------------- #
# records


@dataclass(frozen=True)
class Finding:
    """One defect. The only record type a rule returns."""

    rule: str
    path: str
    line: Optional[int]
    message: str


@dataclass
class FileEntry:
    """One document: raw bytes always, LF-normalised text when it decodes."""

    path: str
    raw: bytes
    text: Optional[str]


@dataclass
class Context:
    root: str
    config: dict
    files: Dict[str, FileEntry]


def relpath(root, path):
    """The one place a path becomes output: repository-relative, forward slashes."""
    return os.path.relpath(path, root).replace(os.sep, "/")


def die(message):
    """Exit 2. Only the loader and the entry point may call this, never a rule."""
    sys.stderr.write(message.rstrip("\n") + "\n")
    raise SystemExit(2)


# --------------------------------------------------------------------------- #
# config, the exclusion guard, the context


def validate_config_shape(config):
    """Everything a rule is allowed to assume about the config is checked here."""
    files = config.get("files")
    if not isinstance(files, dict):
        die("config: files must be an object")
    for rel, spec in files.items():
        if not isinstance(rel, str):
            die("config: files keys must be strings, found %r" % (rel,))
        ceiling = spec.get("max_lines") if isinstance(spec, dict) else None
        if not isinstance(ceiling, int) or isinstance(ceiling, bool):
            die("config: files[%r] has no integer max_lines" % rel)


def load_config(path):
    try:
        with open(path, "rb") as handle:
            config = json.loads(handle.read().decode("utf-8"))
    except FileNotFoundError:
        die("config: %s does not exist" % path)
    except OSError as exc:
        die("config: %s could not be read (%s)" % (path, exc))
    except ValueError as exc:
        die("config: %s is not valid JSON (%s)" % (path, exc))
    if not isinstance(config, dict):
        die("config: %s must hold a JSON object" % path)
    validate_config_shape(config)
    return config


def assert_not_excluded(root, target, config, what):
    """exclude_dirs is a guard, not a filter.

    The bundle this validator was designed in lives at blueprints/ inside this
    repository and carries its own copy of the config, so being pointed at it is
    a mistake worth refusing out loud rather than filtering quietly.
    """
    rel = relpath(root, target)
    for entry in config.get("exclude_dirs", []):
        entry = entry.strip("/")
        if rel == entry or rel.startswith(entry + "/"):
            die("%s: %s resolves inside the excluded directory %r" % (what, rel, entry))


def build_context(root, config):
    wanted = list(config.get("files", {}).keys())
    for key in ("skill_file", "readme_file"):
        name = config.get(key)
        if name and name not in wanted:
            wanted.append(name)

    files = {}
    for rel in wanted:
        full = os.path.join(root, rel)
        assert_not_excluded(root, full, config, "config")
        if not os.path.isfile(full):
            die("config: %s is listed but does not exist under %s" % (rel, root))
        try:
            with open(full, "rb") as handle:
                raw = handle.read()
        except OSError as exc:
            die("config: %s could not be read (%s)" % (rel, exc))
        try:
            text = raw.decode("utf-8").replace("\r\n", "\n")
        except UnicodeDecodeError:
            text = None  # the encoding rule owns this failure
        files[rel] = FileEntry(path=rel, raw=raw, text=text)
    return Context(root=root, config=config, files=files)


# --------------------------------------------------------------------------- #
# rules


def rule_budgets(ctx):
    """Every document is at or under its declared ceiling.

    Line count is len(text.splitlines()) - the number of newline-terminated
    lines, which is what `wc -l` reports and what the ceilings were chosen
    against. Splitting on the newline character would report one more.
    """
    findings = []
    for rel, spec in ctx.config.get("files", {}).items():
        ceiling = spec["max_lines"]  # shape guaranteed by validate_config_shape
        entry = ctx.files[rel]
        if entry.text is None:
            continue
        count = len(entry.text.splitlines())
        if count > ceiling:
            findings.append(
                Finding(
                    rule="budgets",
                    path=rel,
                    line=None,
                    message="%d lines exceeds the ceiling of %d" % (count, ceiling),
                )
            )
    return findings


FRONTMATTER_DELIMITER = "---"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def parse_frontmatter(text):
    """The skill file's delimited header, parsed once and reused by every rule.

    Returns (mapping, error). The mapping is empty when error is set. Six lines
    of string handling rather than a YAML dependency: the block is three flat
    keys deep and is the only YAML in the repository.
    """
    if text is None:
        return {}, "the file does not decode as UTF-8"
    lines = text.split("\n")
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return {}, "no frontmatter block: the file does not open with %r" % FRONTMATTER_DELIMITER
    fields = {}
    for line in lines[1:]:
        if line.strip() == FRONTMATTER_DELIMITER:
            return fields, None
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return {}, "the frontmatter block is never closed by %r" % FRONTMATTER_DELIMITER


def rule_frontmatter(ctx):
    """The skill file's header carries the keys the loader reads, with sane values."""
    rel = ctx.config.get("skill_file")
    entry = ctx.files[rel]
    fields, error = parse_frontmatter(entry.text)
    if error:
        return [Finding(rule="frontmatter", path=rel, line=1, message=error)]

    findings = []
    for key in ctx.config.get("required_frontmatter_keys", []):
        if key not in fields:
            findings.append(
                Finding(
                    rule="frontmatter",
                    path=rel,
                    line=1,
                    message="required key %r is missing from the frontmatter" % key,
                )
            )
        elif not fields[key]:
            findings.append(
                Finding(
                    rule="frontmatter",
                    path=rel,
                    line=1,
                    message="required key %r is present but empty" % key,
                )
            )

    expected = ctx.config.get("expected_name")
    # The expected name comes from the config, never from the directory name:
    # a fixture tree lives in a differently named directory and must not fail
    # this rule for that reason alone.
    if expected and fields.get("name") and fields["name"] != expected:
        findings.append(
            Finding(
                rule="frontmatter",
                path=rel,
                line=1,
                message="name is %r; the config expects %r" % (fields["name"], expected),
            )
        )

    version = fields.get("version")
    if version and not SEMVER.match(version):
        findings.append(
            Finding(
                rule="frontmatter",
                path=rel,
                line=1,
                message="version %r is not three dot-separated runs of digits" % version,
            )
        )
    return findings


RULES = {
    "budgets": rule_budgets,
    "frontmatter": rule_frontmatter,
}


# --------------------------------------------------------------------------- #
# reporting


def report(findings, rules_run):
    for finding in findings:
        if finding.line is None:
            print("%s: %s: %s" % (finding.path, finding.rule, finding.message))
        else:
            print(
                "%s:%d: %s: %s"
                % (finding.path, finding.line, finding.rule, finding.message)
            )
    if findings:
        touched = len(set(f.rule for f in findings))
        print("%d finding(s) across %d rule(s)" % (len(findings), touched))
    else:
        print("clean: %d rule(s), 0 findings" % len(rules_run))


# --------------------------------------------------------------------------- #
# entry point


def repo_root():
    """The parent of scripts/, never the current working directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_parser():
    parser = argparse.ArgumentParser(
        prog=TOOL,
        description="Assert that this repository's skill documents are self-consistent.",
    )
    parser.add_argument(
        "--version", action="store_true", help="print the tool version and exit"
    )
    parser.add_argument(
        "--list-rules", action="store_true", help="print the registered rules, in run order"
    )
    parser.add_argument("--rule", metavar="NAME", help="run exactly one rule")
    parser.add_argument("--config", metavar="PATH", help="use a different config file")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.version:
        print("%s %s" % (TOOL, VERSION))
        return 0

    if args.list_rules:
        for name in RULES:
            print(name)
        return 0

    root = repo_root()
    config_path = args.config or os.path.join(root, "scripts", "validator-config.json")
    config = load_config(config_path)
    assert_not_excluded(root, os.path.abspath(config_path), config, "config")

    if args.rule is not None and args.rule not in RULES:
        sys.stderr.write("rule: %r is not registered. Registered rules:\n" % args.rule)
        for name in RULES:
            sys.stderr.write("  %s\n" % name)
        return 2

    rules_run = [args.rule] if args.rule else list(RULES)
    ctx = build_context(root, config)

    findings = []
    for name in rules_run:
        findings.extend(RULES[name](ctx))

    report(findings, rules_run)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
