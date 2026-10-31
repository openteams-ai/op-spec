# Execution profile `openteams/op-manifest [0.2]`

**Status:** Public discussion draft

**Serves:** [Op Spec v0.1](../../SPEC.md)

**Reference implementation:** Cog Smith Op machinery 0.9.3
([cogcloud-ai/cog-smith](https://github.com/cogcloud-ai/cog-smith) at
`c700f66`), which accepts this vocabulary under the earlier identifier
`openteams/op-manifest [0.1]` — see [Versions](#versions). Where `[0.2]` is
stricter than the reference, [Tightenings](#tightenings) says so.

This profile defines `op.yaml`: a closed, declarative vocabulary for an Op whose
every step invokes a Cog. Anything the vocabulary does not carry is refused
**by name when the document loads**, so an author never discovers a missing
construct mid-run. A refusal SHOULD say what is refused and why; it never
names a plan or a version that might allow it later.

The structural rules are in
[op-manifest-0.2.schema.json](op-manifest-0.2.schema.json). Rules that relate
one part of a document to another are stated here and exercised by the
[conformance corpus](conformance/README.md); each carries a rule id the corpus
uses. A document conforms when it passes the JSON Schema **and** every rule
below. The key words MUST, SHOULD, and MAY are used as in RFC 2119.

## Versions

| Identifier | Vocabulary |
|---|---|
| `openteams/op-manifest [0.1]` | Historical. Used by every Op written before this profile was formalized, while the vocabulary grew across Op machinery releases up to 0.9.3. Different runtimes accept different documents under this identifier — `targets` exists only from 0.8.0 and `cycle` from 0.9.0 — so it does not name one vocabulary. |
| `openteams/op-manifest [0.2]` | This document: the 0.9.3 vocabulary, written down, with the tightenings below. |

A runner implementing `[0.2]` MAY also accept a `[0.1]` document that uses only
`[0.2]` vocabulary, reading its top-level `name` and each step's `name`
(including the steps a cycle transition prepares) as `title`, and SHOULD report
that it read it as `[0.2]`.

### Tightenings

The reference implementation (machinery 0.9.3) accepts, and `[0.2]` refuses:

- `id`, `version`, or `title` that is not a string; a non-string
  `description`, step `title`, or `expected_outcome`; a non-boolean
  `inputs[].required`; a `track.records` that is not a list of strings; and an
  empty top-level `authority: {}` beside a `cycle`.
- A present key of the wrong type that the reference reads as absent, such as
  `inputs: {}`, `outputs: []`, `track: null`, `authority: null`, a step's
  `depends_on`, `foreach`, `gate`, `authority`, or `repeat` of `null`,
  `authority: {ttl_minutes: null}` (read as the default 60), or
  `gate: {guards: false}`.
- `name` at the top level or on a step, which `[0.2]` calls `title`. To
  migrate, rename both; a `[0.1]` document is read with `name` as `title`.
- A step whose `cog` states no `version`.
- `repositories`, the former name of `targets`.
- A requirement whose `action` is neither `read` nor `write`.
- An object holding an operator key beside other keys, such as
  `{$from: x, label: y}` or a `$default` without `$from`.
- A `$path` value that begins with `~`.
- A `$run_dir` that names the run directory itself, or `requests`,
  `envelopes`, or `input-request.json`.
- A `foreach` step with a human Gate over changes, or with a human Gate over
  an artifact that reads the loop variable.
- A cycle limit that reads `run` or `request`.

At run time, `[0.2]` also requires what the reference treats as a warning or
does not check: a stated `cog.version` that differs from the Cog's is an
error; a named Cog that is not present when the run starts is an error; and an
envelope whose `cog.id` differs from the step's is a failed invocation.

The conformance corpus marks each case where the reference differs with
`reference_divergence`.

## The package

An Op package following this profile is:

```text
op-my-workflow/
├── OP.md                 # the core entry file: manifest: op.yaml
├── op.yaml               # this profile's manifest
├── pixi.toml             # tasks: op, test (and cycle, when the Op declares one)
├── examples/request.json # a runnable request
├── tests/
└── runs/                 # local and ignored: one directory per run, holding its Track
```

The Op itself contains no code. A runner may be supplied however its
implementation chooses; the reference implementation copies its runner into
`src/` and checks the copy by hash.

## Document

```yaml
schema: openteams/op-manifest [0.2]
id: example.org/video-transcription
version: "0.1.0"
title: Video transcription with speaker attribution
description: Produces a timestamped, speaker-labelled transcript from a recording.
inputs:  [...]
steps:   [...]
outputs: {...}
track:   {records: [...]}
```

| Key | Required | Meaning |
|---|---|---|
| `schema` | yes | Exactly `openteams/op-manifest [0.2]` |
| `id` | yes | Namespaced identity of this Op |
| `version` | yes | The Op's own revision, quoted |
| `title` | yes | Human-readable name |
| `description` | no | One-paragraph account |
| `inputs` | no | Ordered list of declared inputs |
| `steps` | yes | Non-empty ordered list of steps |
| `outputs` | no | Object of mapping expressions: what the run returns |
| `track` | no | Deprecated; accepted and ignored — see [Outputs and Track](#outputs-and-track) |
| `authority` | no | `{ttl_minutes}`: how long an issued grant stays valid, default 60 |
| `cycle` | no | A bounded declarative cycle; see [Cycles](#cycles) |

Every other key is refused. `state` is refused by name: durable state across
runs is not in this profile.

- **`present-key-typed`** — a key that is present has the type the JSON Schema
  gives it, at every level of the document. A value of another type is
  refused, never read as the key's absence: `inputs: {}`, `outputs: []`,
  `track: null`, and a step's `depends_on: null` are refused, as are
  `authority: {ttl_minutes: null}` (**`ttl-positive`**) and
  `gate: {guards: false}` (**`no-guards`**). Only an omitted key takes its
  default.

### Identity

`id` is the Op's identity. `OP.md`'s `name` is its short form, and `title` is
for people. Steps follow the same pattern: a step's `id` identifies it and its
`title` is for people, so `name` appears in `op.yaml` only for inputs.

- **`op-md-name-from-id`** — `OP.md`'s `name` SHOULD equal the last
  `/`-separated segment of `id`: `example.org/video-transcription` is named
  `video-transcription`.
- **`op-md-version-agrees`** — when `OP.md` states a `version`, it MUST be a
  string equal to `op.yaml`'s `version`, compared as written: an unquoted
  `null`, `false` or `1.0` is not the string `"None"`, `"False"` or `"1.0"`.
- `OP.md`'s `description` and `op.yaml`'s `title` and `description` are not
  compared.

A profile-aware validator SHOULD report a disagreement it can detect.

## Inputs

```yaml
inputs:
  - name: media_path
    description: The recording, relative to the request file.
    required: true
  - name: speaker_count
    required: false
    default: null
    schema: {type: [integer, "null"]}
```

An input is `{name, description, required, default, schema}`; only `name` is
required.

- **`unique-inputs`** — input names are unique.
- **`declared-request-keys`** — a request carrying a key that names no
  declared input is refused.
- `required` defaults to `true`.
- **`input-schema-valid`** — a declared `schema` is a valid JSON Schema
  (2020-12), checked at load.
- An input is **supplied** when the request carries its key; an explicit
  `null` is a value, and a default never replaces it. A declared `default`
  (even `null`) covers an omitted input. A required input with neither is
  missing, and the request is refused.
- **Absence is not null.** An optional input that is omitted and declares no
  default is not among the run's inputs: it is not validated, and reading it
  takes the expression's `$default` or fails as "not available in this run".
- A declared `schema` applies to every supplied value and every declared
  default, including `null`.

## Steps

```yaml
steps:
  - id: attribute-speakers
    title: Attribute transcript segments to speakers
    depends_on: [transcribe]
    cog:
      id: example.org/cog-speaker-attribution
      version: "0.1.0"
      source: ../cog-speaker-attribution
      task: attribute
    input:
      transcript_json: {$from: steps.transcribe.payload.transcript_json}
      output_dir: {$run_dir: attribution}
    expected_outcome: A transcript with explicit speaker labels.
    gate: {policy: envelope-ok-no-error-problems}
    on_fail: stop
```

| Key | Meaning |
|---|---|
| `id` | Required. Lowercase alphanumerics and single hyphens |
| `title`, `expected_outcome` | Human-readable; carried into the plan and Track |
| `depends_on` | Step ids that must finish first |
| `cog` | Required. `{id, version, source, task}` — see below |
| `input` | A mapping expression that evaluates to the step's request, read as written whenever present (`false`, `0`, `""`, `null`, and `[]` included); omitted, the request is `{}` |
| `foreach` | Run once per element; see [foreach](#foreach) |
| `repeat` | Ask the same request several times; see [repeat](#repeat) |
| `gate` | How the step's result is accepted; see [Gates](#gates) |
| `on_fail` | `stop` (default), `skip`, or `retry-once` |
| `authority` | What the step requires outside the run; see [Authority](#authority) |

A Cog step is the only kind of step. `tool:` and `human:` are refused by name:
deterministic work is a Cog of kind `code`, invoked as a step, and a human
checkpoint is a Gate policy on the step that produces what the person decides
about.

- **`unique-step-ids`** — step ids are unique.
- **`depends-on-declared`** — every `depends_on` entry names a declared step,
  and not the step itself.
- **`acyclic`** — `depends_on` forms no cycle. Steps run one at a time: the
  next step is always the earliest step, in document order, whose dependencies
  have all finished.

### The Cog a step names

`cog.id`, `cog.version`, `cog.source`, and `cog.task` are required strings
(**`cog-version-required`**).

- `source` is a filesystem path to the Cog's package directory, relative to the
  Op package root. This is the only reference form in `[0.2]`; registry
  references are an [open design question](../../design-history/README.md).
- `task` MUST name an interface the Cog declares for the **usage** audience.
- `id` MUST equal the identity the Cog's manifest declares.
- `version` MUST equal the version the Cog's manifest declares.

These are checked against the Cog itself; see
[Checks against the named Cogs](#checks-against-the-named-cogs).

## Mapping expressions

A step's `input`, a `foreach.items`, an artifact Gate's `artifact`, a
requirement's `targets` and `changes`, the `outputs`, and a cycle's limits are
**mapping expressions**. An object whose key set is **exactly** one of these
is that operator. An object with no `$`-prefixed key is ordinary data and is
walked recursively, and scalars are literals.

| Operator | Value |
|---|---|
| `{$from: PATH}` | The value at PATH; an error if it is not available |
| `{$from: PATH, $default: EXPR}` | The value at PATH when present and not null, else EXPR |
| `{$path: EXPR}` | EXPR as an absolute filesystem path: a relative value is resolved against the request file's directory, and symbolic links are resolved |
| `{$run_dir: SUBPATH}` | A directory inside this run, created; SUBPATH may itself be an expression |
| `{$stem: EXPR}` | The final path component of EXPR without its suffix |
| `{$literal: ANY}` | ANY verbatim — the escape for data that looks like an operator |
| `{$sha256: EXPR}` | The [canonical digest](#canonical-digest) of EXPR's value; null is refused |

- **`closed-operators`** — a `$`-prefixed key that names no operator is refused
  wherever it appears, with or without siblings.
- **`operator-exact-keyset`** — an object holding an operator key has exactly
  that operator's key set. `{$from: x, label: y}` and a `$default` without
  `$from` are refused rather than read as data, so a misspelled sibling
  (`default:` for `$default:`) is an error. Data that needs `$`-prefixed keys
  is written with `$literal`.
- **`path-no-home`** — a `$path` value never begins with `~`: an Op's paths do
  not depend on whose machine runs it. A value written in the document —
  including one wrapped in `$literal` — is refused at load, and a computed
  value at evaluation.
- `$path` and `$stem` give `null` for `null`.

### Paths

A PATH is a dotted string. Dotted keys index objects; integer segments index
arrays, and a negative integer counts from the end. Its root is one of:

| Root | Meaning |
|---|---|
| `inputs.<name>` | A declared input — **`input-declared`** |
| `steps.<id>.payload` / `.envelope` / `.decision` | An earlier step's result |
| `run.dir`, `run.id` | This run |
| `request.dir` | The directory of the request file |
| a `foreach` variable | The current element, inside that step |

- **`read-requires-dependency`** — a step may read `steps.<id>` only when
  `<id>` is in its transitive `depends_on`. (`outputs` may read any step.)
- **`decision-needs-human-gate`** — `steps.<id>.decision` exists only for a
  step whose Gate policy is `human`.
- **`no-grants-root`** — `grants` is never a path root. A grant travels beside
  a request, never inside it.

### `$run_dir`

The subpath is relative and never leaves the run (**`run-dir-relative`**):
absolute values, `..` escapes, and symbolic links out of the run are refused
before anything is created, including when the subpath arrived as mapped data.
No component may be a symbolic link.

- **`run-dir-not-root`** — the subpath names a directory inside the run, never
  the run directory itself: `""`, `.`, `null`, and anything that normalizes to
  the run root are refused.
- **`run-dir-reserved`** — after normalization, the subpath must not name or
  lie under the run's own entries: `grants`, `pending`, `decisions`,
  `journal`, `requests`, `envelopes`, `input-request.json`, `run.lock`,
  `track.json`, nor the `<file>.<pid>.tmp` siblings the runner rewrites
  `input-request.json`, `run.lock`, and `track.json` through. Names compare
  case-insensitively, by Unicode canonical caseless matching, so `Requests`
  and `GRANTS/x` are refused on every filesystem and the verdict does not
  depend on whether the one that runs folds case. At evaluation, an existing
  component that is the run directory or one of these entries under another
  name, such as a hard link, is refused too.

A literal subpath is checked at load; a computed one when it is evaluated,
before anything is created.

### Canonical digest

The canonical digest of a JSON value is the lowercase hex SHA-256 of its UTF-8
serialization with object keys sorted, separators `,` and `:` with no
whitespace, and non-ASCII characters written unescaped. It is the digest
`$sha256`, pending documents, decisions, and change hashes all use.

## `foreach`

```yaml
foreach: {items: {$from: inputs.github_items}, as: item}
```

`items` is an expression that evaluates to a list; `as` is the loop variable
(letters, digits, underscore; not starting with a digit), which becomes a path
root inside the step. `as` must not be `inputs`, `steps`, `run`, or `request`
(**`loop-variable-name`**).

- **`changes-gate-not-per-element`** — a `foreach` step has no human Gate over
  changes: a person decides about one list of changes, and a `foreach`
  payload is a list of element payloads.
- **`artifact-not-per-element`** — a human Gate over an artifact on a
  `foreach` step is one decision over the whole step, so its `artifact`
  never reads the loop variable: the Gate is evaluated after the loop, when
  no element is current. It reads the step's payload instead.

Elements run in order, each with its own request, envelope, and envelope Gate
decision. When every element has finished, a human Gate over an artifact, if
the step has one, puts one artifact to a person for the whole step. The
step's payload is the list of element payloads, `null` where an element
failed. The loop stops at the first element that finally fails; later elements
are recorded `not-reached` and are `null` in the payload, so the list still
lines up with `items`.

## `repeat`

```yaml
repeat: {count: 4, require: 1, mode: until-required}
```

The same request is put to the Cog in up to `count` slots (1–5). `require`
(1–`count`, **`repeat-require-bounds`**) is how many must pass, and defaults to
`count` only when omitted. `mode` is `all` (default: run every slot and return
every answer) or `until-required` (stop once `require` have passed).

- Under `all`, `on_fail: retry-once` applies to each slot, so a step can make
  up to twice `count` invocations. Under `until-required`, `retry-once` is not
  applied: the next slot is the retry.
- The payload is a list of slot payloads, `null` for a slot that failed. Under
  `until-required` it lists only the slots that ran.

The step's Gate fails when fewer than `require` repeats passed; otherwise it is
`pass-with-problems` when any repeat failed or carried problems; otherwise
`pass`. Inside a `foreach`, each element is repeated and the payload is a list
of lists.

A repeated step is never effectful: `repeat` is refused beside `authority`,
beside a human Gate (**`human-gate-no-repeat`**), and on a Cog that declares
`reaches`.

## Gates

```yaml
gate: {policy: envelope-ok-no-error-problems}
```

| Policy | Passes when |
|---|---|
| `envelope-ok-no-error-problems` (default) | The envelope is `ok` and carries no error-severity problem. Warnings give `pass-with-problems`. |
| `human` | The envelope passes the default policy **and** a person then accepts. |

`gate.guards` is deprecated: it is accepted only absent or empty
(**`no-guards`**) and is ignored. The name stays reserved for Guards, which a
hosting environment supplies and this profile does not define. `decides` and
`artifact` belong only to a human Gate (**`decides-human-only`**).

### A human Gate over changes

`gate: {policy: human}` (or `decides: changes`). The step's payload carries a
`changes` list; each change has a unique `change_id`, the `target` it changes,
a `content_sha256` (the canonical digest of the change object without its two
hash fields), and a `target_sha256` (the digest of the target as the Op read
it). Proposals the Gate cannot put to a person — no `changes` list, a
duplicate `change_id`, a `target` that is missing or not a non-empty string,
or a stated digest that is missing, malformed, or wrong — are a failed Gate: no pending decision is written, and `on_fail`
applies. The runner never repairs a hash.

The person gives every change exactly one verdict:

- `approve` — the change as proposed;
- `reject` — not written;
- `edit` — with the edited change, re-hashed from its edited content. An edit
  changes content only: it keeps the proposed change's keys and their types,
  its `target`, and its `target_sha256`;
- `defer` — neither approved nor rejected; not written by this run.

The applied decision is exposed as `steps.<id>.decision`:
`{approved, rejected, edited, deferred, history, decided_by, decided_at}`,
where `approved` carries the effective change objects.

### A human Gate over an artifact

```yaml
gate:
  policy: human
  decides: artifact
  artifact:
    kind: cog-contract
    summary: {$from: steps.design.payload.contract.purpose}
    digests:
      contract: {$sha256: {$from: steps.design.payload.contract}}
```

The Gate declares ONE versioned thing — `kind` and `digests` required
(**`artifact-declared`**, **`artifact-digests`**), `id`, `summary`, `detail`
optional — evaluated after the step's Cog answered, so it may read the step's
own payload but never its own decision (**`artifact-no-own-decision`**).
`digests` is a non-empty object of named digest expressions. An artifact the
Gate cannot state — one whose expressions cannot be evaluated included — or a
digest that is not a SHA-256, is a failed Gate, never a pause asking someone to
accept nothing, and `on_fail` applies.

The decision is one verdict, `accept` or `reject`, bound to both the payload
and artifact digests. A rejection states a non-empty `reason`. An accepted
artifact is exposed as
`{verdict, artifact, artifact_sha256, reason, decided_by, decided_at}`. A
rejection ends the run, finally, for those bytes.

## `on_fail`

- `stop` ends the run `failed` at this step.
- `skip` records the step `skipped` and every step depending on it `blocked`,
  and the run continues. A skipped single step's payload is `null`; a skipped
  `foreach` step keeps the payloads of the elements that finished.
- `retry-once` re-invokes exactly once, and only when the envelope was
  `ok: false`. An envelope naming another Cog is never retried: the same
  invocation would name it again. An error-severity problem in an `ok` envelope is a judgement,
  not a glitch, and is never retried. Refused on an effectful step
  (**`effectful-no-retry`**).

A step whose grant is denied is recorded `denied` and follows `on_fail` like a
failed step. A run whose steps all finished ends `completed-with-problems` when
any step is `passed-with-problems`, `skipped`, `blocked`, or `denied`, and
`completed` otherwise.

## Authority

A Cog that reaches outside the run declares `reaches` in its manifest, and runs
only under a **grant** the runner issues immediately before invoking it. There
are two sources of authority and no others:

- the run owner's **admission** (`openteams/op-authority [0.1]`), which lists
  the operations the run may perform: each a resource, an action, and the
  targets it covers; and
- a **human decision** at a Gate over changes, which approves exact changes.

A **read** needs the admission: every target the step asks for is one the
admission lists for that resource and action. A **write** — applying exactly
the approved, content-addressed changes to their targets — needs both: the
admission lists `write` on the resource, and every approved change's `target`
is a write target the admission lists; and a person approved those changes.
A run whose admission does not list an operation some step requires is
refused before it starts. A grant the runner cannot issue is a denial, never a
trimmed grant.

```yaml
- id: write-docs
  depends_on: [compose]
  cog: {id: example.org/cog-docs-writer, version: 0.1.0,
        source: ../cog-docs-writer, task: write}
  authority:
    requires:
      - {resource: docs-site, action: write,
         changes: {$from: steps.compose.decision.approved}}
```

A step declares what it requires; it never grants itself anything. Each
requirement is `{resource, action}` plus `targets` (for a read) or `changes`
(for a write). `resource` and each target are opaque names that the admission,
the step, the changes, and the Cog's `reaches` agree on.

- **`read-or-write`** — `action` is `read` or `write`. Other effects, such as
  publishing, sending, or deleting, are not in this profile.
- **`read-names-targets`** — a read requirement names `targets`, not null,
  and declares no `changes`.
- **`targets-only`** — `repositories`, the former name of `targets`, is
  refused.
- **`write-reads-approved`** — a write's `changes` is exactly
  `{$from: steps.<id>.decision.approved}`.
- **`write-needs-human-gate`** — that `<id>` has a human Gate over changes;
  **`artifact-authorizes-no-write`** — not one over an artifact.
- **`write-depends-on-gate`** — the writing step lists `<id>` directly in
  `depends_on`; all write requirements on one step read the same Gate.
- **`no-per-element-grants`** — `authority` is refused on a `foreach` step.
- **`ttl-positive`** — top-level `authority.ttl_minutes` is a positive number.

A grant carries no credentials. The host runs trusted code with the owner's
ambient credentials: the runner issues and records grants, and the code Cog
that receives one checks it before every external call. This profile does
**not** describe an enforced restricted environment, and a runner MUST NOT
present it as one.

## Outputs and Track

`outputs` is an object of mapping expressions, evaluated after the last step
and before the run is recorded complete.

`track.records` is deprecated: it is accepted and ignored. What a Track records
is fixed by this profile, not chosen by the Op, so that no Op can record less
than [core principle 7](../../SPEC.md#what-every-execution-profile-keeps)
requires.

## Cycles

A cycle runs an Op repeatedly under declared limits — for example, revise and
review a candidate until it is accepted or a budget is spent.

```yaml
cycle:
  outcome_step: review
  outcome_field: verdict
  max_attempts: {$from: inputs.max_attempts}
  max_cost_units: 12
  costs: {design: 1, author: 1, review: 1}
  transitions:
    revise: {restart: author}
  terminal_errors: {author: [contract-unsatisfiable]}
```

`outcome_step` is a declared step and `outcome_field` a field of its payload;
the field's value selects a transition. A transition is
`{restart, prepare, replace}`: restart at an earlier step, optionally run
`prepare` steps first, and optionally `replace` the `input` and `depends_on` of
restarted steps — nothing else about a step can change. `initial` is reserved.
Each **phase** is one run of the Op as a transition shapes it; the first phase
is the document without its `cycle`.

### Cycle rules

- **`cycle-outcome-declared`** — `outcome_step` names a declared step, and
  `outcome_field` is a non-empty string.
- **`cycle-previous-reserved`** — no input is named `cycle_previous`; every
  phase after the first receives it.
- **`cycle-restart-declared`** — a transition's `restart` names a declared
  step; **`cycle-restart-precedes-outcome`** — that step precedes the outcome
  step, or is it.
- **`cycle-replace-restarted-only`** — `replace` names only steps that run
  again: the restart step and those after it.
- **`cycle-phase-conforms`** — every expanded phase is itself a conforming
  document, validated before the first invocation.
- **`cycle-costs-complete`** — `costs` gives a non-negative integer for exactly
  every step of every phase. Costs are reservation units for declared
  invocations, not prices.
- **`cycle-terminal-errors-declared`** — `terminal_errors` maps steps of some
  phase to non-empty lists of distinct, non-empty envelope error codes.
- **`cycle-limits-read-inputs`** — `max_attempts` and `max_cost_units` read
  inputs only: no path rooted at `steps`, `run`, or `request` anywhere in the
  expression, including inside a `$default`, and no `$run_dir` or `$path`,
  which read a run's or the request's directory. They are evaluated once,
  when the cycle starts and before any run exists: `max_attempts` must be a
  positive integer and `max_cost_units` a non-negative integer.
- **`cycle-pure`** — a cycle Op declares no authority, top-level or on any
  step, including preparation steps, and every Cog it names is present and
  declares no `reaches` when the cycle starts.

### Running a cycle

- **Routing.** When the outcome step's Gate does not fail and its
  `outcome_field` holds a transition's name, the phase ends there as
  `cycle-transition` and the next phase starts. This is checked **before** the
  outcome step's human Gate: a result routed back is never put to a person.
  A value that names no transition lets the phase continue, through the human
  Gate if there is one, and the cycle ends when that phase ends. This
  precedence is a known exception to core principles 4 and 5; see
  [Open for review](#open-for-review).
- **Carried steps.** The steps before the restart step are not run again. Each
  is carried into the next phase with its recorded result, and only when it
  passed, its Cog's package digest is unchanged, and, if it has a human Gate,
  its decision accepted an artifact. A step behind a human Gate over changes
  is therefore never carried. A transition whose carried steps do not meet
  these conditions cannot continue: the cycle ends `cycle-failed`, recording
  the reason and the phase, outcome, and restart step involved. A cycle that
  cannot start its first phase, or whose phase cannot be run, ends the same
  way. A `cycle-failed` cycle is final; resuming it reports it and runs
  nothing. An interrupted cycle is not failed: it stays resumable.
- **Previous phase.** `cycle_previous` gives the next phase the previous
  phase's step requests, payloads, envelopes, and decisions.
- **Budgets.** `max_attempts` counts phases, the first included. Every
  invocation reserves its step's cost before it is made; a phase that would
  exceed either limit ends the cycle `budget-exhausted`, keeping every result.
- **Terminal errors.** A failed step whose envelope error code is listed for
  it in `terminal_errors` ends the cycle `refused` rather than recoverable,
  reading the code the Cog reported when the runner synthesized the failure.

## Checks against the named Cogs

A runner MUST make these checks for every named Cog before it invokes any
step, and refuse the run on any error; a named Cog that is not present when the
run starts is an error. A dry run invokes no step and need not make them. A
validator SHOULD make them too; a validator checking
an Op before its Cogs exist reports a missing Cog as a warning.

They read the Cog's manifest. In this draft the fields are those of the
`openteams/cog-manifest [0.1]` profile (`id`, `version`, `kind`, `reaches`,
`interfaces[].task`, `interfaces[].audience`); how these map onto the Cog Spec
is an [open question](../../design-history/README.md).

- The Cog declares the stated `id` and the stated `version`.
- `task` is a declared interface for the **usage** audience. An interface that
  declares no audience is `lifecycle` if its task is one of `resolve`, `use`,
  `check`, `eval`, `test`, `bundle`, or `serve`, and `usage` otherwise.
- `authority` is only on a step whose Cog is `kind: code`.
- Every requirement is covered by the Cog's `reaches`.
- A step whose Cog declares `reaches` declares `authority.requires`.
- A step whose Cog declares `reaches` declares neither `repeat` nor
  `on_fail: retry-once`.

## Invocation

The runner invokes each step as:

```text
pixi run --manifest-path <source>/pixi.toml <task> -- --request <request.json>
    [--grant <grant.json> --run-id <id> --journal <journal>]
```

The Cog writes its envelope as a JSON object on stdout; it may print other
text before it. The runner takes the **last** JSON object on stdout that has an
`envelope` key. Grant, run id, and journal travel **beside** the request, never
inside it.

The envelope's `cog.id` MUST equal the step's `cog.id`; an envelope naming
another Cog, or naming none, is a failed invocation that `retry-once` does not
retry. When the envelope's `cog.id` can be read — it is a string — and
differs from the step's, the failure is the identity mismatch, and is not
retried, whatever else is wrong with the envelope: a malformed envelope naming
another Cog is still that Cog's result. The runner digests the Cog package
immediately before each invocation and records it with the result.

If the Cog's argument parser rejects `--request` by name — exit code 2, the
diagnostic `unrecognized arguments: --request` on stderr, and no envelope on
stdout — the runner retries once with `--bundle`. Anything else is a result,
and an effectful Cog is never invoked twice. This retry is deprecated; see
[Open for review](#open-for-review).

## Runs

### Statuses

| Of | Statuses |
|---|---|
| A step | `passed`, `passed-with-problems`, `failed`, `skipped`, `blocked`, `denied`, `not-reached`, `awaiting-decision`, `rejected`, `running`, `planned` (a dry run), `budget-exhausted` (in a cycle) |
| A run | `planned`, `running`, `paused`, `completed`, `completed-with-problems`, `failed`, `rejected`, and in a cycle's phase `cycle-transition` and `budget-exhausted` |
| A cycle | `running`, `paused`, `completed`, `completed-with-problems`, `failed` (a phase failed; resumable), `rejected`, `refused`, `budget-exhausted`, `cycle-failed` (the cycle itself cannot continue; final) |

### Exit codes

Stdout is one JSON object.

| Code | Meaning |
|---|---|
| `0` | Completed, completed with problems, or a planned dry run |
| `1` | Failed, rejected, refused, budget exhausted, or cycle failed |
| `2` | Refused before execution or resumption proceeds: an invalid document, request, admission, or decision; a run another process holds; a dry run that cannot evaluate its request. A refused resume concerns a run directory that already exists |
| `3` | Paused for a human decision |
| `4` | Used only between a phase run and its cycle: the phase ended in a transition. A cycle never exits `4` |

### Evaluation failures

A mapping expression that cannot be evaluated once the run has started — a
`$from` path that is not available and declares no `$default`, a
`foreach.items` that is not a list, a `$run_dir` or `$path` operand refused at
evaluation, a requirement whose targets cannot be read — fails the step. The
step is recorded `failed`, with the reasons and whatever it had finished, such
as a `foreach`'s earlier elements; the steps after it are `not-reached`; and the
run is `failed`, with the Track's `reason` saying what could not be evaluated.
`on_fail` does not apply: the fault is in the Op, not in a Cog's result.
`outputs` that cannot be evaluated fail the run with every step keeping its
status, `outputs` null, and no `failed_step`.

A human artifact Gate's expressions are the exception. They are evaluated
after the step's Cog answered, and an artifact the Gate cannot state is a
failed Gate (see [A human Gate over an artifact](#a-human-gate-over-an-artifact)),
so their evaluation failures, an unavailable `$from` included, follow the
Gate's `on_fail`: with `skip`, the step is `skipped` and the run continues.

### Pausing and resuming

A human Gate writes `pending/<step>.json`
(`openteams/op-pending-decision [0.1]`) and exits `3`. A resume with an
`openteams/op-decision [0.1]` document reloads the Track, re-checks that
`op.yaml` still hashes the same and that the named Cogs still pass their
checks, applies the decision, and continues. A passed step is never re-run. A
failed run resumes at its `failed_step`. A rejected run and a dry run are never
resumed.

### Decisions

A decision document states the `run_id` and `step` it is about, the
`payload_sha256` of the payload the person saw (the runner re-digests the
pending payload and compares), a non-empty `decided_by`, and `decided_at` as an
ISO 8601 timestamp. A decision about changes gives every proposed change
exactly one verdict and names no other change; a decision about an artifact
gives one verdict and the `artifact_sha256` it is about. A decision that does
not meet these is refused and nothing is applied.

### Other run behaviour (informative)

- **Digests on every invocation.** `cog_sha256` is recorded beside
  `request_sha256`. A resume reuses an earlier answer only when both match.
- **Repeat budgets are a ledger.** Attempts are reserved before they are
  invoked, survive crashes and resumes, and are renewed only by an explicit
  request naming the step.
- **One run, one process,** held by an inherited lock on `run.lock`.
- **Durability order:** nothing external happens that the run directory does
  not already describe.
- **Companion documents**, each with its own identifier and none yet specified
  here: `openteams/op-authority [0.1]` (admission), `openteams/op-grant [0.1]`,
  `openteams/op-pending-decision [0.1]`, `openteams/op-decision [0.1]`,
  `openteams/op-track [0.1]`, and `openteams/op-cycle [0.1]` (cycle state).

The reference implementation's
[Building Ops](https://github.com/cogcloud-ai/cog-smith/blob/main/BUILDING_OPS.md)
guide describes all of this in full.

## Open for review

These are kept in `[0.2]` as they work today, and each is proposed for review;
see [design-history](../../design-history/README.md) for the reasoning.

1. **Cycle routing before the human Gate.** A transition is taken on the
   outcome step's own payload field, before that step's human Gate, so a Cog's
   output decides the route and a person never sees a result routed back. This
   is an exception to core principles 4 and 5.
2. `track.records` and `gate.guards`: deprecated, accepted and ignored.
3. The `--request`/`--bundle` retry.
4. `warn` as a spelling of `warning` in envelope 1.
5. Audience inference from a fixed list of lifecycle task names.
6. Retries in `repeat`: under `all`, `retry-once` applies per slot (up to twice
   `count` invocations); under `until-required`, it is not applied.
7. A skipped `foreach` step keeps its finished elements' payloads, while a
   skipped single step's payload is `null`.
8. The runner takes the last JSON object on stdout that has an `envelope` key,
   rather than requiring stdout to be exactly one envelope.
