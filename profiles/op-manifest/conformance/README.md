# Conformance corpus for `openteams/op-manifest [0.2]`

Each directory under `cases/` holds an `op.yaml` and an `expected.json`:

```json
{"conforms": false, "layer": "profile", "rule": "read-requires-dependency",
 "reference_finding": "without depending on"}
```

| Field | Meaning |
|---|---|
| `conforms` | Whether the document conforms to the profile. Normative. |
| `layer` | For a non-conforming case, what refuses it: `schema` — the JSON Schema alone; `profile` — a rule stated only in PROFILE.md, which the JSON Schema accepts. |
| `rule` | The rule id in PROFILE.md. |
| `reference_finding` | Informative: text the reference implementation's finding contains. |
| `reference_divergence` | Informative: why a reference implementation that predates `[0.2]` gives a different verdict from `conforms`, for a rule this profile states and that reference does not implement. It never excuses a reference that accepts `[0.2]`. |
| `note` | Informative. |

Case names begin with `v` (conforms), `s` (refused by the schema), or `p`
(refused by a profile rule).

The `layer` split is checked, so the corpus also records exactly what the JSON
Schema cannot see. A new rule needs a case; a case moves from `profile` to
`schema` when the schema learns to express it.

```bash
python tools/check_conformance.py [--reference path/to/op_spec.py]
```

With `--reference`, an implementation that accepts `[0.2]` itself (its
`SCHEMA_STRING`, or its `SCHEMA_STRINGS`, includes it) is given each document
as written. One that implements this vocabulary only under the
earlier identifier `[0.1]` is checked by substituting its identifier for
`[0.2]` and reading `title` as that version's `name`, at the top level and
on every step, including the steps a cycle transition prepares.

A reference that accepts `[0.2]` must match `conforms` on every case. One
checked under `[0.1]` must match on every case except one that carries
`reference_divergence`, which is reported as a note: the field excuses a
reference that predates a rule, never one that claims to implement this
profile. Either way, a note says when the reference agrees on a case that
carries the field, so the field can be removed once no reference the corpus
is checked against still needs it.
