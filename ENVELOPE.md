# Step result envelope, version 1

**Status:** Public discussion draft, extracted from the envelope Cog Smith's
generated Cogs emit and its Op runner consumes.

The envelope is the JSON object a Cog writes as the result of one invocation of
an Op-facing interface. It is the seam between an Op and a Cog: the fields are
exactly what a Gate reads, a Guard checks, and a Track records.

The envelope belongs to this specification rather than to the Cog Spec because a
Cog does not need to take part in an Op to be valid. A Cog that only ever runs
on its own may return whatever it likes. A Cog that serves as an Op step
returns this envelope from every interface an Op invokes. Other consumers, such
as a client that invokes a Cog directly, may read the same envelope.

The structural part is defined by [schemas/envelope-1.schema.json](schemas/envelope-1.schema.json).
The key words MUST, SHOULD, and MAY are used as in RFC 2119.

## Example

```json
{
  "envelope": 1,
  "cog":      {"id": "example.org/cog-summarizer", "version": "0.2.0"},
  "task":     "summarize",
  "ok":       true,
  "error":    null,
  "payload":  {"summary": "..."},
  "raw":      "<verbatim model text>",
  "problems": [
    {"check": "grounding", "detail": "quote 3 is not a verbatim span of the source", "severity": "error"}
  ],
  "binding":  {"model_identity": "verified", "violations": []},
  "timing":   {"latency_s": 2.31}
}
```

## Fields

### Required of every envelope

A consumer MUST treat an object without these as malformed output, not as a
result:

- **`envelope`** — the integer `1`. Not `true`, not `"1"`. Consumers detect the
  envelope version here, never by sniffing field shapes.
- **`ok`** — a boolean. `true` means the invocation completed and produced a
  parseable payload. It does **not** mean the payload is acceptable: `ok: true`
  MAY coexist with error-severity `problems`. Deciding that is the Gate's job,
  never the Cog's.
- **`problems`** — a list of objects, possibly empty. See [Problems](#problems).

### Required of a producing Cog

A Cog MUST also emit:

- **`cog`** — `{id, version}`: the identity the Cog declares for itself, so a
  saved result says what produced it.
- **`task`** — the interface that was invoked.
- **`payload`** — the result. Its shape is the Cog's own declared output
  schema. It is `null` when the invocation errored or the output did not parse.
- **`error`** — `null`, or `{code, detail}`. When it is an object, `ok` MUST be
  `false`.

### Optional

- **`raw`** — the verbatim model text, for audit and salvage review; `null` or
  absent for a Cog that calls no model.
- **`binding`** — the complete binding identity of the model the Cog used
  (which pinned model, which endpoint, the identity verdict, any violations),
  copied into every result so a saved result identifies its run without reading
  the current installation. It MUST NOT contain credentials.
- **`timing`** — `{latency_s}`.
- **`provider_result`** — for a decision Cog, the provider's result as
  received, kept separately from the derived payload.

## Errors

`error.code` is a non-empty string. These codes are registered:

| Code | Meaning | HTTP status, for an HTTP interface |
|---|---|---|
| `invalid-input` | The request did not satisfy the Cog's input contract | 422 |
| `binding-invalid` | The Cog's model binding is missing or invalid | 503 |
| `model-unavailable` | The bound model could not be reached | 503 |
| `model-call-failed` | The model call failed upstream | 502 |
| `model-response-malformed` | The model answered with something unusable | 502 |
| `invocation-failed` | Synthesized by a runner: the Cog produced no well-formed envelope | — |

A Cog MAY use additional codes. A consumer MUST treat any `error` as a failed
invocation, whether or not it recognizes the code.

### Synthesized envelopes

When a Cog cannot be launched, exits without a well-formed envelope, or writes
something that is not envelope 1, the runner synthesizes an envelope with
`ok: false`, `error.code: invocation-failed`, and the process evidence in one
place, `error.evidence`:

```json
{"command": ["..."], "returncode": 1, "stdout_tail": "...", "stderr_tail": "...",
 "previous_attempts": [{"command": ["..."], "returncode": 2, "stdout_tail": "", "stderr_tail": "..."}]}
```

Each tail is at most the last 2,000 characters of the stream. `returncode` is
`null` only when the command could not be launched. `previous_attempts` is
present when the runner tried another invocation form first. The Gate decides
about a synthesized envelope like any other.

## Problems

A problem is `{check, detail, severity}`:

- `check` — a machine-readable category: `schema`, `grounding`, `citation`,
  `identity`, `input`, or another the Cog defines.
- `detail` — one human sentence.
- `severity` — `error` or `warning`. `warn` is accepted as a spelling of
  `warning` and is deprecated.

Problems are the Cog checking its **own** declared contract. An independent
Guard verifies against the system's requirements and never treats this
self-report as its verdict.

- An error-severity problem from the Cog's **input** check refuses the
  invocation. A warning on input allows the work and stays in `problems`.
  A missing or unrecognized input severity refuses the invocation.
- Problems from the Cog's **output** check, of either severity, stay in
  `problems` for the Gate.
- A warning alone never makes `ok` false.

## Versioning

This document defines `envelope: 1`. Adding an optional field does not change
the version. Changing the meaning or type of an existing field does.
Consumers MUST ignore fields they do not recognize.
