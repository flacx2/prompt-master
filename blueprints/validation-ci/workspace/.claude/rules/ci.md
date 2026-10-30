---
description: Workflow and git-hook conventions — SHA-pinned actions, least privilege, the same gate locally and in CI
paths:
  - ".github/**"
  - ".githooks/**"
---

# CI and hook conventions

- **Pin every action by 40-character commit SHA**, with the human tag in a trailing comment:
  `uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`. A moving tag is a
  supply-chain hole; the comment is what makes the pin readable.
- **`permissions: contents: read`** at the workflow level and nothing wider. This workflow reads the
  repository and reports a status. It never needs to write.
- **The workflow runs the same commands as the local gate**, in the same order. If CI runs something
  the `CLAUDE.md` command table does not list, one of the two is wrong.
- **Triggers:** `pull_request` and `push` to `main`. The PR run is the blocking one; a push run on
  `main` reports after the fact, by construction.
- **Pin the interpreter** with `actions/setup-python` and a `python-version` that matches the version
  the maintainer runs locally — `3.12`. Dev parity matters more here than being on the newest
  release, because this gate has to reproduce on the maintainer's machine.
- **Add `concurrency` and a `timeout-minutes`** so a stacked push cancels the stale run and a hung
  job cannot sit for six hours.
- **The hook is a convenience, never the gate.** `.githooks/pre-commit` runs the validator so drift
  is caught before the push; CI is what actually blocks the merge. A hook can be bypassed with
  `--no-verify`, so nothing may depend on it having run.
