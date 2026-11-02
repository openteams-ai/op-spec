# Op Spec

Op Spec defines a portable, inspectable composition of Cogs that produces one
requested outcome: which Cogs take part, how results flow between them, where
results are accepted — including by a person — and the record every run leaves.

## Status

Version 0.1 is a **public discussion draft**. It is experimental and has not
been adopted as the official 0.1 release.

> **Before release:** select a license and add it to a root `LICENSE` file.

## What is here

| Path | What it is |
|---|---|
| [SPEC.md](SPEC.md) | The core: what an Op is, the `OP.md` entry file, and what every execution profile must keep |
| [ENVELOPE.md](ENVELOPE.md) | The step result envelope a Cog returns to an Op, with its [JSON Schema](schemas/envelope-1.schema.json) |
| [profiles/op-manifest/](profiles/op-manifest/PROFILE.md) | The first execution profile, `openteams/op-manifest [0.2]`: the `op.yaml` vocabulary, its JSON Schema, and a conformance corpus |
| [examples/](examples/) | Complete example Ops |
| [tools/](tools/) | A core validator and the conformance checker |
| [design-history/](design-history/README.md) | How the format came about, decisions, proposed changes, and open questions |

## An Op in brief

An Op is a directory with an `OP.md` entry file and the manifest it names:

```text
video-transcription/
├── OP.md
└── op.yaml
```

```markdown
---
type: op [0.1]
name: video-transcription
description: Produces a timestamped, speaker-labelled transcript from a recording.
manifest: op.yaml
manifest_schema: openteams/op-manifest [0.2]
---

# Video transcription with speaker attribution
...
```

The core fixes only `OP.md`. The manifest's format is whatever its execution
profile defines; `manifest_schema` says which one.

## Related specifications

- [Cog Spec](https://github.com/openteams-ai/cog-spec) — the workers an Op
  composes. A Cog does not need to take part in an Op to be valid.
- [Frame Spec](https://github.com/openteams-ai/frame-spec) — the context that
  governs work.

The reference implementation of the `op.yaml` profile is the Op machinery in
[Cog Smith](https://github.com/cogcloud-ai/cog-smith).

## Checking

With [Pixi](https://pixi.sh):

```bash
pixi run check                         # corpus, examples, fixtures
pixi run validate examples/video-transcription
pixi run check-reference ../cog-smith/templates/op/src/op_spec.py
```

`check-reference` also requires an implementation's verdict to match every
conformance case. The implementation is passed by path; this repository depends
on no other checkout.
