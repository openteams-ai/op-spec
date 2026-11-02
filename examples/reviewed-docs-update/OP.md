---
type: op [0.1]
name: reviewed-docs-update
description: Reads documentation pages, proposes edits, and writes only the edits a person approves.
version: "0.1.0"
manifest: op.yaml
manifest_schema: openteams/op-manifest [0.2]
---

# Reviewed documentation update

Shows authority. Nothing here grants anything by being written down.

1. **Read** — `example.org/cog-site-reader` reads the requested pages. It
   declares that it reaches `docs-site` for `read`, so it runs only under a
   grant, and the grant covers only pages the run's owner admitted.
2. **Propose** — `example.org/cog-docs-editor` proposes a list of changes, each
   hashed. A person approves, rejects, or edits each one.
3. **Write** — `example.org/cog-docs-writer` receives a grant carrying exactly
   the approved changes, and checks each target's hash against a fresh read
   before writing. The grant is issued only if the run's owner also admitted
   writes to every page an approved change targets: a person's approval never
   reaches past the owner's admission.

**Deliverable:** the write Cog's report of what it applied.
