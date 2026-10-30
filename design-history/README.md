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

**2026-10-30 — The draft was compared with the code.** The conformance corpus
agreed with the reference validator, and every `op.yaml` in the public builder
suite passed the `[0.2]` JSON Schema. No Op in the suite had an `OP.md`, and
much of what a runner does was written only in code. The decisions below come
from that comparison.

**2026-10-30 — `[0.2]` stays open until it is implemented.** No runner
implements `[0.2]` yet, so a tightening no existing Op relies on goes into
`[0.2]` now. Changes that need existing Ops or Cogs to migrate wait for a later
version.

**2026-10-30 — Identity is the manifest `id`.** `OP.md`'s `name` is the last
segment of `id`, as a Cog's `COG.md` `name` is the last segment of its
manifest's `id`. `op.yaml`'s human-readable `name` becomes `title`, so "name"
means one thing. `version` must agree; descriptions are not compared. Rejected:
comparing `OP.md`'s `name` with a title, and adding `id` to `OP.md`, which
would make `OP.md` differ from `COG.md`.

**2026-10-30 — A write needs the admission and a person.** The run owner's
admission sets what a run may ever write; a person approves the exact changes
within it. A person's approval alone is not enough, because the person at a
pause may not be the run owner, and an Op may come from someone else. A change
names its `target`. Rejected: a human decision as the only authority for a
write.

**2026-10-30 — `read` and `write` only.** "Write" means applying exactly the
approved, content-addressed changes to admitted targets. Every other action is
refused until the effects an Op can have are classified (see
[Open questions](#classifying-outside-effects)).

**2026-10-30 — Runtime rules written down as they work.** Statuses, exit codes,
cycle carry-over, decision documents, `on_fail` with denied steps, inputs, and
mapping details are stated in the profile as the reference implements them.
Where they are inconsistent, they are listed for review rather than redesigned.
A runtime evaluation failure is a recorded failed step and run, as core
principle 7 requires; the reference was changed to do so (machinery 0.10.0).

**2026-10-30 — Identity is checked, not warned about.** `cog.version` is
required and must match; a Cog missing when the run starts is an error; an
envelope must name the step's Cog.

**2026-10-30 — Review items settled for `[0.2]`.** Objects mixing operator keys
with other keys are refused, and `$literal` carries such data. `repositories`
is refused. `track.records` and `gate.guards` are accepted and ignored, and the
reference stops generating them; "Guards" stays reserved. `warn` stays in
envelope 1. Cycle refusals each have a named rule. A refusal says what is
refused and why, never when. `$path` does not expand `~`. The `--request` /
`--bundle` retry and audience inference from task names are written down as
they work; declaring either belongs to
[Op participation](#what-a-cog-must-declare-to-be-an-op-step).

## Proposed changes to the current profile

Numbered as in the profile's [Open for review](../profiles/op-manifest/PROFILE.md#open-for-review).

1. **Cycle routing before the human Gate.** See
   [Routing as a Gate outcome](#routing-as-a-gate-outcome).
2. **`track.records` and `gate.guards`.** Refuse both in the next profile
   version. Guards, if they return, are supplied by a hosting environment.
3. **`--request` / `--bundle`.** One flag, declared by the Cog's interface,
   with no retry; see [Op participation](#what-a-cog-must-declare-to-be-an-op-step).
4. **`warn`.** Refuse it in the next envelope version.
5. **Audience inference.** Interfaces declare their audience; no name list.
   Also part of Op participation.
6. **Retries in `repeat`.** Make `retry-once` mean the same in both modes, or
   refuse it beside `repeat`.
7. **Partial payloads of skipped steps.** Decide whether a skipped `foreach`
   step exposes its finished elements or `null`, as a single step does.
8. **Envelope parsing.** Require stdout to carry exactly one envelope. Cogs
   that print progress to stdout would have to move it to stderr, so this
   needs a migration.

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

Two review items belong here: which invocation flag an interface takes
(replacing the `--request` / `--bundle` retry), and which audience an
interface serves (replacing inference from task names). Both are things a Cog
declares in order to take part in an Op, so they would be defined in this
repository, as the envelope is, and would not change the Cog Spec.

### Finalization

*Under consideration; not decided.* A candidate organizing principle for the
next profile version and the core:

> Only a person finalizes. Machines may produce, check, route, revise, and
> reject; they never finalize. Finalization is a person accepting an exact
> result, identified by its digest. Anything later steps treat as accepted,
> and any effect that leaves the run, comes from a finalization of exactly
> that content; changed content needs a new finalization.

It would explain the current design: an artifact Gate already takes digests,
changes already carry `content_sha256` and `target_sha256`, an edit is already
re-hashed, and an Op with no human Gate can return results but cause no
outside effect. It would also make clear why a cycle may route a result back
without a person (nothing is finalized) but may not accept one.

**Decided (2026-10-30):** a policy a person approved in advance may stand in
for that person. Each pass under it is recorded as finalized under that
policy, citing the policy's digest, and never as a person's decision. This
covers op-cog-builder's request for a caller policy that passes acceptance
Gates on evidence
([cogcloud-ai/op-cog-builder#3](https://github.com/cogcloud-ai/op-cog-builder/issues/3)).

**Open, to be decided before the next profile version:**

- Is every human acceptance a finalization, including one in the middle of a
  run (a contract the rest of the run is bound to), or are there two levels: a
  person steering at a checkpoint, and a person finalizing?
- How a finalization is shown to come from a person. Today a decision is a
  file with `decided_by`, and a runner cannot tell a person from a script that
  wrote it. That is likely the hosting environment's to establish, as with
  Guards, and the specification should not imply a runner enforces it.
- Whether a finalization can be withdrawn before its effect is applied.

### Routing as a Gate outcome

*Under consideration; not decided.* In `[0.2]`, a cycle reads a field of the
outcome step's payload and routes on it before the step's Gate. The Cog
decides the route, an exception to "the Gate decides, never the Cog", and a
person can never send a result back: an artifact Gate offers only `accept` and
`reject`, and a rejection ends the cycle.

The proposal: a Gate's result can be pass, fail, or a named route, and
transitions are keyed on the Gate's result. The decider can be a declared
machine rule that turns evidence (such as a review's classification) into a
route, a person choosing accept, reject, or a route with a reason that reaches
the next phase, or, later, an approved policy. One step may use more than one:
a machine rule routing cheap rounds and a person deciding acceptance, as
op-cog-builder's review step effectively does now. Whether a person sees every
round would then be how an Op configures its Gate, not a special rule for
cycles.

Open: the vocabulary, how a person's reason reaches the next phase (a
revision step that today reads a reviewer Cog's envelope would also read the
person's decision), and how this relates to finalization.

### Classifying outside effects

*Under consideration; not decided.* In `[0.2]`, "write" is narrow: apply an
exact, reviewed change set to admitted targets. Effects that are not a change
set have no route yet. Three questions decide the route for an effect: can it
be shown exactly in advance, can it be undone, and whose consent does it need
— the run owner's in advance, a person's at the time, or both.

| Effect | Shown in advance as | Reversible | A possible route |
|---|---|---|---|
| Read | Target names | — | Admission |
| Change to a target | An exact diff | Usually | Admission, then a person approves the diff (`[0.2]` write) |
| Routine change | Target and kind of change | Yes | Admission alone, declared in advance |
| Publish, open a pull request, deploy | A digest of what goes out | Hard | Admission, then a person accepts the whole artifact |
| Send, delete, spend | The exact action | No | Admission, then a person; never repeated |

Publishing a Cog an Op built is the likely first case beyond `write`; see
[Distribution and publishing](#distribution-and-publishing).

### Frames at the Op level

The Frame Spec's account of the boundary says an Op names "which Frames apply
at the workflow level". `op.yaml` has no way to do that yet, and nothing says
how an Op-level Frame reaches the Cogs.

### Companion documents

Admission, grant, pending decision, decision, Track, and cycle state each have
an identifier and no specification. The Track is the most important: it is the
record the core promises, and it comes first. Decision and admission documents
follow; [finalization](#finalization) rests on them.

### Distribution and publishing

How an Op itself is shared (an `OP.md` at the root of a Nebi workspace, as the
Cog Spec's example does for `COG.md`), and where publishing a Cog built by an Op
belongs — necessarily after a human Gate, and, because an Op carries no code, as
a Cog step or a documented manual step.

### Durable state and Guards

Both are refused by the current profile and named as future work by the
core.
