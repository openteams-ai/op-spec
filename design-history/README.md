# Design history

Why the Op Spec looks the way it does, what was decided, and what is still open.
Nothing here is normative.

## Origin

The Op format was not designed ahead of time. It grew as needed inside Cog Smith's
Op machinery, one capability at a time, as real Ops required them. The
validator and the runner were the working definition throughout, and the
documents all kept declaring `openteams/op-manifest [0.1]` while the vocabulary
grew:

| Machinery | Added |
|---|---|
| before 0.4 | linear Cog steps, mapping expressions, `foreach`, the default Gate, `on_fail`, the Track |
| 0.4.1 | the `--request` / `--bundle` flag negotiated at the invocation seam |
| 0.4.6 | `tool:` refused permanently, pointing at Cogs of `kind: code` |
| 0.5.0 (2026-09-17) | authority, admission, grants, the human Gate, pause and resume |
| 0.5.4 | applied decisions say who decided, when, and what was edited |
| 0.5.5 | resuming a failed run at the step that stopped it |
| 0.6.0 | `repeat` |
| 0.6.3 | the Cog package digest taken per invocation |
| 0.6.4 | `repeat.mode` |
| 0.6.5 – 0.6.6 | repeat budgets as a ledger; one immutable file per attempt |
| 0.7.0 (2026-09-23) | human Gates over an artifact, `decides`, `$sha256` |
| 0.8.0 (2026-10-08) | `targets` as the name for `repositories`, which stays an alias |
| 0.8.1 | explicitly deferred changes |
| 0.9.0 – 0.9.3 | bounded declarative cycles, then hardening |

The consequence that prompted formalization: two runtimes could accept
different documents under the same identifier. One Op package in the public builder
suite still carries a pre-0.8.0 runtime, without `targets` or `cycle`, while
declaring the same `[0.1]` as packages that use them.

This repository is derived only from public sources: Cog Smith's
`BUILDING_OPS.md`, `ENVELOPE.md`, and `templates/op/src/op_spec.py` at
`c700f66`. The Op runner was originally implemented from an internal design note
that was never distributed. Nothing here depends on it; anything in it that the
specification needs has to be written here.

## Decisions

**2026-10-20 — Core plus profiles.** Op Spec follows the Cog Spec and Frame
Spec: a small core (`OP.md`, `type`, `name`, `description`, `manifest`,
`manifest_schema`) that makes an Op recognizable and self-identifying, with
execution formats defined by profiles. The core adds a short list of properties
every execution profile must keep, because an Op, unlike a Cog, is defined by
how it runs. `op.yaml` becomes the first profile rather than *the* format, so
another runtime can implement Ops without adopting Cog Smith's runner.

**2026-10-20 — A separate public repository.** Op Spec lives in its own
repository beside `cog-spec` and `frame-spec`, public from the start, so the
specification is not owned by any one implementation.

**2026-10-20 — The envelope belongs here.** A Cog need not take part in an Op to
be valid, so the Cog Spec stays silent on results. The envelope is what a Cog
implements to be usable as an Op step.

**2026-10-20 — Profile `[0.2]`.** The first written profile is the 0.9.3
vocabulary under a new identifier, rather than a redefinition of `[0.1]`, which
names no single vocabulary.

**2026-10-20 — Review before carrying forward.** Because the vocabulary grew
as needed, extraction includes review: constructs kept only so existing Ops
still load are listed for change instead of being presented as design.

## Proposed changes to the current profile

Numbered as in the profile's [Open for review](../profiles/op-manifest/PROFILE.md#open-for-review).

1. **Operator keys with siblings.** `{$from: x, label: y}` is ordinary data, so
   `{$from: x, default: y}` (a typo for `$default`) silently stops being a read.
   Proposal: refuse an object that mixes operator keys with other keys, and use
   `$literal` for data that needs `$` keys.
2. **`track.records`.** Declared, never acted on. Proposal: drop it, or make it
   select what the Track records.
3. **`gate.guards`.** Exists only to be empty. Proposal: drop it until Guards
   are specified.
4. **`repositories`.** Proposal: refuse it in the next profile version, with a
   migration note.
5. **`--request` / `--bundle`.** Two flags for one thing, inherited from two
   machinery lineages. Proposal: one flag, declared by the Cog's interface,
   with no retry.
6. **`warn`.** Proposal: refuse it in the next envelope version.
7. **`cog.version`.** Proposal: required, with mismatch an error — which the
   registry-reference work below needs anyway.
8. **Audience inference.** Proposal: interfaces declare their audience;
   no name list.
9. **Cycle refusals.** Proposal: refuse cycle mistakes by name, like everything
   else.
10. **Roadmap text in refusals.** The reference refuses `state:` by saying
    "phase 4 adds it", which names an internal plan. Proposal: say what is
    refused and why, not when.

## Open questions

### Referencing Cogs beyond a local path

`cog.source` is a path relative to the Op package. Sharing Ops means naming
Cogs that live in a registry. The candidates:

- **An OCI reference with a required digest**, for Cogs published as
  [Nebi](https://nebi.nebari.dev) bundles. `nebi publish` bundles the whole
  workspace directory (minus `.git`, `.pixi`, ignored files, symlinks, and
  `[tool.nebi.bundle]` excludes) and `nebi import` restores it, so a Cog
  package is already a valid bundle. Nebi 0.10 imports by tag only, and tags
  can move, so this needs digest references on import, or a digest check
  after import.
- **An `op.lock`**: `op.yaml` names Cogs by version or tag; the lock pins
  resolved digests, the way `pixi.lock` pins packages.
- **Cogs as packages pinned in the Op's own lockfile**, as the Cog Spec's Nebi
  example pins Frames. The obstacle is that each Cog runs in its own
  environment, not the Op's.

Each of these needs a definition of a Cog package digest that a runner, a
registry, and a person can all compute. Today the runner defines its own
(`cog_sha256`: the manifest, `context/` and `src/`, and part of `model.json`),
which is not what an OCI digest covers.

### What a Cog must declare to be an Op step

The runner's checks against a Cog read `id`, `version`, `kind`, `reaches`, and
`interfaces[].task` / `.audience` from the `openteams/cog-manifest [0.1]`
profile. The Cog Spec core declares `name` (not `id`) in `COG.md` and leaves
the manifest to profiles, and its Nebi example uses `[tool.nebi.cog]` rather
than `[tool.cog]`. One option: a small "Op participation" requirement in this
repository, listing what a Cog's manifest must declare, in whatever profile, to
be invoked as a step.

### Frames at the Op level

The Frame Spec's account of the boundary says an Op names "which Frames apply
at the workflow level". `op.yaml` has no way to do that yet, and nothing says
how an Op-level Frame reaches the Cogs.

### Companion documents

Admission, grant, pending decision, decision, Track, and cycle state each have
an identifier and no specification. The Track is the most important: it is the
record the core promises.

### Distribution and publishing

How an Op itself is shared (an `OP.md` at the root of a Nebi workspace, as the
Cog Spec's example does for `COG.md`), and where publishing a Cog built by an Op
belongs — necessarily after a human Gate, and, because an Op carries no code, as
a Cog step or a documented manual step.

### Durable state and Guards

Both are refused by the current profile and named as future work by the
core.
