# Op Spec v0.1

**Status:** Public discussion draft

**Stability:** Experimental; this is not yet the official 0.1 release

## Purpose

This is the adopt-now definition of an Op.

The goal of v0.1 is to make Ops concrete enough that someone can write one,
share it, inspect it, and recognize it without first adopting a particular
runner, hosting product, or marketplace.

v0.1 makes an Op **recognizable, inspectable, and self-identifying**, and it
states the few principles every way of running an Op keeps. It does not define a
single executable format. How an Op's steps, mappings, Gates, and records are
written down is defined by an **execution profile**, named by the Op itself,
for the same reason the Cog Spec leaves a Cog's manifest to profiles: the shape
should follow implementation experience rather than precede it.

This repository also carries the first execution profile,
[`openteams/op-manifest [0.2]`](profiles/op-manifest/PROFILE.md), and the
[step result envelope](ENVELOPE.md) that Cogs return to Ops. Neither is
privileged by this core document. Other profiles may exist beside them.

## Definition

An **Op** is a portable, inspectable composition of Cogs that produces one
requested outcome. It says which Cogs take part, in what order and on what
inputs, where results are checked and accepted, and what the finished
deliverable is. Every run of an Op leaves a record of what actually happened.

An Op describes:

- the outcome it produces;
- the Cogs that take part, and the work each one does;
- how results flow from one step to the next;
- the checkpoints at which results are accepted or rejected, including those a
  person decides;
- what authority the work needs outside the run, if any; and
- the shape of the final deliverable.

An Op is not, merely by being loaded or installed, a running process, a
deployment, or a grant of authority.

## Relationship to related artifacts

### Cogs

A Cog is a portable, installable AI worker, defined by the
[Cog Spec](https://github.com/openteams-ai/cog-spec). An Op uses Cogs; it never
contains or imports one. A Cog does not need to take part in any Op to be a
valid Cog, and nothing in this specification changes what qualifies as one.

A Cog that can serve as an Op step implements the
[step result envelope](ENVELOPE.md) on the interfaces an Op invokes. That is a
requirement of this specification on a Cog's *Op-facing interfaces*, not a
requirement of the Cog Spec.

### Frames

A Frame carries durable context: rules, terminology, norms, and expectations
that govern work. It is defined by the
[Frame Spec](https://github.com/openteams-ai/frame-spec). Cogs consume Frames,
and an Op may name Frames that apply to the whole outcome. v0.1 does not define
how an Op names Frames; see [Not defined in v0.1](#not-defined-in-v01).

### Runners and hosting environments

A runner is the software that executes an Op under some execution profile. A
hosting environment is where that runner operates and where authority is
admitted. Neither is part of the Op. An Op written against a profile should run
on any runner that implements that profile.

## File format

An Op is a directory. Its entry file is named `OP.md`, and that file names the
manifest:

```text
my-op/
├── OP.md           # Required: the entry file
├── op.yaml         # Required: the manifest named by `manifest`
├── examples/       # Optional: runnable requests
├── tests/          # Optional: the Op's own checks
└── ...             # Other profile- or implementation-specific files
```

Only `OP.md` and the manifest it names are required. `op.yaml` is shown because
it is the conventional filename; the manifest may use any format and name, and
`OP.md` says which file it is.

An execution profile may require more files or a specific layout. Additional
files do not make a conforming Op non-conforming.

### Drafts

An `OP.md` written on its own, before a manifest exists, is a **draft**. It is
the proposal: the outcome, the steps, and who decides what, in prose. It is a
useful artifact — it is the design record, and tooling that builds Ops takes it
as input — but it is not yet an Op, because nothing can run it. A validator
given a loose `OP.md` should check what it can and report a draft.

## `OP.md` contents

`OP.md` contains YAML frontmatter followed by a Markdown body.

```markdown
---
type: op [0.1]
name: video-transcription
description: Produces a timestamped, speaker-labelled transcript from a recording.
version: "0.1.0"
manifest: op.yaml
manifest_schema: example.org/op-workflow [0.1]
---

# Video transcription with speaker attribution

Transcribe the recording, then attribute each segment to a speaker...
```

### Required frontmatter

| Field | Meaning |
|---|---|
| `type` | Identifies the file as an Op |
| `name` | Short machine-readable name |
| `description` | What the Op produces and when it should be used |
| `manifest` | Relative path to the Op's execution manifest |
| `manifest_schema` | Identifier of the execution profile that manifest follows |

#### `type`

The value is exactly `op`, or, to declare this specification version, exactly
`op [0.1]`. The versioned form is recommended for shared Ops.

The general Op-family grammar is `^op( \[[0-9]+\.[0-9]+\])?$`. The values
accepted for v0.1 conformance are `^op( \[0\.1\])?$`. Another well-formed
version, such as `op [0.2]`, may be recognized as an Op but must not be reported
as conforming to v0.1.

#### `name`

`name` must be 1–64 characters of lowercase ASCII letters, digits, and hyphens;
must not begin or end with a hyphen; and must not contain consecutive hyphens.
The Op's directory should normally have the same name.

These are the Cog Spec's rules, so a name valid for one is valid for the other.

#### `description`

`description` must be non-empty and no more than 1,024 characters, and should
be understandable without reading the body.

### Recommended frontmatter

| Field | Meaning |
|---|---|
| `version` | Version of this Op, quoted |
| `publisher` | The identity releasing this Op |
| `license` | License name or reference to a bundled license file |
| `repository` | Where its source is maintained |

A shared or repeatedly revised Op should include `version`, `publisher`, and
`license`. `version` tracks the Op's own revision, not this specification's or
the profile's. Quote it: unquoted, `1.0` is a number.

Frontmatter is a flat mapping of string keys to scalar values. Structure an Op
needs belongs in its manifest, not in nested frontmatter.

### Markdown body

The body is the Op's human-readable account of itself: the outcome, the
participating Cogs and why each is there, the checkpoints and who decides at
each, the authority the work needs, and the deliverable. It should agree with
the manifest. Where they disagree, the manifest is what runs, and a
profile-aware validator should report the disagreement it can detect.

## Manifest and execution profiles

`manifest` must be a relative path inside the Op directory; must not be absolute
or escape the Op root with `..`; must name a file that exists; and must remain
inside the Op root after symbolic links are resolved.

`manifest_schema` names the execution profile the manifest follows. It is an
opaque, namespaced, versioned identifier to this core specification, which
defines what any profile must keep (below) but not what a manifest contains. An
implementation that does not support a profile should say so — *this Op follows
`example.org/op-workflow [0.1]`, which I do not run* — rather than guess.

The manifest is not authority. Its presence or contents grant nothing.

### What every execution profile keeps

A profile may choose any vocabulary. To be an execution profile for Ops, it must
preserve these properties:

1. **An Op is a composition, not a program.** The Op carries no executable code
   of its own. Work that needs code is done by a Cog, invoked as a step.
2. **Steps invoke Cogs through interfaces the Cog declares for use.** Each step
   names the Cog it invokes by an identity the Cog itself declares, and the
   runner confirms that identity before invoking it.
3. **Results are step result envelopes.** Each invocation's result is an
   [envelope](ENVELOPE.md), or is synthesized as one when the Cog failed to
   produce one.
4. **The Gate decides, never the Cog.** Each step's result passes a declared
   Gate before anything later depends on it. A Cog's self-reported problems are
   evidence for the Gate, not its verdict.
5. **People decide where the Op says they do.** A profile can declare a
   checkpoint at which a person accepts or rejects a result, and nothing after
   that checkpoint runs on the result until they have.
6. **Authority is never implied.** Loading, installing, or admitting an Op
   grants nothing by itself. Any authority a step uses outside the run comes
   from an explicit admission by the run's owner or an explicit human decision,
   and the profile says which.
7. **Every run leaves a record.** A run records its inputs, each step's request
   and result, each Gate decision, and its outputs, durably enough that an
   interrupted run still says what was attempted.
8. **The vocabulary is versioned.** A profile identifier changes whenever the
   set of documents it accepts changes, and a runner refuses a profile version
   it does not implement.

The `openteams/op-manifest [0.2]` profile has one known exception to
principles 4 and 5: a cycle routes a result back for revision on the outcome
step's own payload, before that step's Gate is consulted and before any person
sees it. Nothing routed back is accepted, and the profile lists the exception
for review.

## Validation

A v0.1 core validator checks that:

1. `OP.md` is valid UTF-8 and begins with valid YAML frontmatter;
2. the frontmatter contains valid `type`, `name`, and `description` fields;
3. `name` follows the naming rules;
4. the Op declares both `manifest` and `manifest_schema`; the path is relative,
   resolves to an existing file inside the Op root after symbolic links are
   followed, and the schema identifier is a non-empty string.

A core validator does not interpret the manifest. A profile-aware validator
additionally validates the manifest against its profile, and may check the
Cogs it names.

Given a loose Markdown file, a validator checks 1 through 3 and reports a
**draft**. Unknown frontmatter fields and additional files must not, by
themselves, cause rejection, and must never be read as granting authority.

Validation establishes format compatibility only. It does not establish quality,
safety, authenticity, licensing rights, or that the Cogs an Op names are
available.

## Versioning

This core document, each execution profile, and the envelope are versioned
independently:

| Thing | Where its version appears | Example |
|---|---|---|
| This specification | `type` in `OP.md` | `op [0.1]` |
| An execution profile | `manifest_schema` in `OP.md`, and the manifest's own declaration | `openteams/op-manifest [0.2]` |
| The step result envelope | `envelope` in every result | `1` |
| The Op itself | `version` in `OP.md` | `"0.3.0"` |

## Not defined in v0.1

v0.1 deliberately leaves these to later versions or to profiles. Each is tracked
in [design-history](design-history/README.md):

- **Referencing a Cog by something other than a local path**, such as an OCI
  reference with a pinned digest, and how an Op locks the Cogs it resolved.
- **Naming Frames at the Op level**, and how they reach the participating Cogs.
- **Distribution.** How an Op and the Cogs it uses are packaged and shared, for
  example as [Nebi](https://nebi.nebari.dev) workspaces.
- **Durable state across runs**, beyond what one run records.
- **Guards** — independent verifiers a hosting environment supplies beside a
  Gate.
- **Interoperability between profiles.** Two Ops written against different
  profiles are both recognizable Ops; v0.1 does not make one runnable by the
  other's runner.
