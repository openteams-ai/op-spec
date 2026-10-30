# Changelog

## Unreleased

Initial public discussion draft.

- Op Spec v0.1 core: `OP.md`, required and recommended frontmatter, drafts,
  manifest and execution profiles, the properties every profile keeps,
  validation, and versioning.
- Step result envelope 1, extracted from Cog Smith, with a JSON Schema and
  fixtures.
- Execution profile `openteams/op-manifest [0.2]`: the Cog Smith Op machinery
  0.9.3 vocabulary written down, with a JSON Schema, named rules, a conformance
  corpus checked against the reference implementation, and a list of
  constructs proposed for review.

### Changes from the comparison with the reference implementation (2026-10-30)

- `op.yaml` names its human-readable name `title`. `OP.md`'s `name` should be
  the last segment of the manifest's `id`, and its `version` must agree.
- Writes need the run owner's admission and a person's approval of the exact
  changes; a change names its `target`; actions are `read` or `write`.
- `[0.2]` refuses `repositories`, an object mixing operator keys with other
  keys, a step without `cog.version`, a `$path` beginning with `~`, a
  `$run_dir` naming the run root or the runner's own entries, and a `foreach`
  step with a human Gate over changes. A `cog.version` mismatch, a missing Cog
  at run start, and an envelope naming another Cog are errors.
- The profile states statuses, exit codes, evaluation failures, decisions,
  cycle rules (each refusal named), carried steps, budgets, `repeat` retries,
  and `on_fail` with denied steps. Cycle routing before the outcome step's
  human Gate is written down as it works and listed for review.
- `track.records` and `gate.guards` are deprecated, accepted, and ignored.
- Envelope 1: malformed errors and problems are stated, and a nonzero exit
  keeps the Cog's own envelope in `error.evidence.envelope`.
- The conformance corpus has 16 new cases and uses `title`, and the checker reports
  known differences from the reference as notes.
- Design history records the decisions and three questions under
  consideration: finalization, routing as a Gate outcome, and classifying
  outside effects.
