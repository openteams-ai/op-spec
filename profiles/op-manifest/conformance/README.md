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
| `note` | Informative. |

Case names begin with `v` (conforms), `s` (refused by the schema), or `p`
(refused by a profile rule).

The `layer` split is checked, so the corpus also records exactly what the JSON
Schema cannot see. A new rule needs a case; a case moves from `profile` to
`schema` when the schema learns to express it.

```bash
python tools/check_conformance.py [--reference path/to/op_spec.py]
```

With `--reference`, an implementation that implements this vocabulary under the
earlier identifier `[0.1]` is checked by substituting its identifier for
`[0.2]`.
