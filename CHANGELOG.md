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

- `op.yaml` names the human-readable name of the Op and of each step
  `title`. `OP.md`'s `name` should be
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
- The conformance corpus has 18 new cases and uses `title`, and the checker reports
  known differences from the reference as notes.
- Design history records the decisions and three questions under
  consideration: finalization, routing as a Gate outcome, and classifying
  outside effects.

### Changes from an independent review (2026-10-31)

- A human Gate over an artifact on a `foreach` step is one decision over the
  whole step, after the loop, and its artifact never reads the loop variable
  (`artifact-not-per-element`). Each element has its own envelope Gate.
- `cycle-limits-read-inputs` names what a limit may not read: `steps`, `run`,
  or `request`, inside a `$default` too, and `$run_dir` or `$path`.
- A present key of the wrong type is refused, never read as absent
  (`present-key-typed`).
- An envelope that names another Cog fails as an identity mismatch, and is
  not retried, even when it is also malformed.
- The checker holds a reference that implements `[0.2]` to every case;
  `reference_divergence` excuses only a reference that predates it. The
  corpus has 11 new cases.
- `run-dir-reserved` compares names case-insensitively, by Unicode canonical
  caseless matching, so `$run_dir: Requests` is refused whether or not the
  filesystem folds case; an existing alias of a reserved entry is refused at
  evaluation. One new corpus case, `p31-run-dir-reserved-case`.
- Evaluation failures exclude a human artifact Gate's expressions: an
  artifact that cannot be evaluated is a failed Gate and follows `on_fail`,
  so `skip` continues the run, as the reference does.
- `op-md-version-agrees` compares a version as written: a stated `OP.md`
  `version` is a string, so `null` never agrees with `"None"`. The reference
  validator no longer coerces both sides with `str()`, and `pixi run check`
  runs it over new fixtures in `tools/validate-op-fixtures`.
