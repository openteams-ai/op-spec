---
type: op [0.1]
name: contract-acceptance
description: Drafts a Cog contract from a brief, has a person accept it, then authors source bound to exactly the accepted contract.
version: "0.1.0"
manifest: op.yaml
manifest_schema: openteams/op-manifest [0.2]
---

# Contract acceptance

Shows a human Gate over an **artifact**: one versioned thing accepted or
rejected whole, bound to its digest.

1. **Design** — `example.org/cog-author` drafts a contract from the brief. The
   step's Gate asks a person to accept that contract, identified by the
   canonical SHA-256 of its content.
2. **Author** — runs only after acceptance, and receives the accepted digest so
   it can refuse to author against any other contract.

A rejection ends the run. A different contract is a new run.

**Deliverable:** authored source and the digest of the contract it implements.
