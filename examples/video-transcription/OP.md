---
type: op [0.1]
name: video-transcription
description: Produces a timestamped, speaker-labelled transcript from a recording.
version: "0.1.0"
manifest: op.yaml
manifest_schema: openteams/op-manifest [0.2]
---

# Video transcription with speaker attribution

A two-step linear Op. Every Cog it names is illustrative.

1. **Transcribe** the recording with `example.org/cog-media-transcriber`, which
   writes a timestamped transcript and normalized audio into the run.
2. **Attribute speakers** with `example.org/cog-speaker-attribution`, which
   labels each segment as one speaker, mixed, or unassigned.

Both steps use the default Gate: a step passes when its Cog reports `ok` with no
error-severity problem. No person decides anything, and nothing reaches outside
the run.

**Deliverable:** the speaker-labelled transcript in Markdown.
