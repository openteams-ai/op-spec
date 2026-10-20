# Execution profile `openteams/op-manifest [0.2]`

**Status:** Public discussion draft

**Serves:** [Op Spec v0.1](../../SPEC.md)

**Reference implementation:** Cog Smith Op machinery 0.9.3
([cogcloud-ai/cog-smith](https://github.com/cogcloud-ai/cog-smith) at
`c700f66`), which accepts this vocabulary under the earlier identifier
`openteams/op-manifest [0.1]` — see [Versions](#versions).

This profile defines `op.yaml`: a closed, declarative vocabulary for an Op whose
every step invokes a Cog. Anything the vocabulary does not carry is refused
**by name when the document loads**, so an author never discovers a missing
construct mid-run.

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
`[0.2]` vocabulary, and SHOULD report that it read it as `[0.2]`.

**Tightenings.** The reference implementation accepts, and `[0.2]` refuses:
`id`, `version`, or `name` that is not a string (any non-empty value is accepted
today); a non-string `description`, step `name`, or `expected_outcome`; a
non-boolean `inputs[].required`; a `track.records` that is not a list of
strings; and an empty top-level `authority: {}` beside a `cycle`.

## The package

An Op package following this profile is:

```text
op-my-workflow/
├── OP.md                 # the core entry file, manifest: op.yaml
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
id: example.org/op-video-transcription
version: "0.1.0"
name: Video transcription with speaker attribution
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
| `name` | yes | Human-readable name |
| `description` | no | One-paragraph account |
| `inputs` | no | Ordered list of declared inputs |
| `steps` | yes | Non-empty ordered list of steps |
| `outputs` | no | Object of mapping expressions: what the run returns |
| `track` | no | `{records: [...]}` — see [Review](#open-for-review) |
| `authority` | no | `{ttl_minutes}`: how long an issued grant stays valid, default 60 |
| `cycle` | no | A bounded declarative cycle; see [Cycles](#cycles) |

Every other key is refused. `state` is refused by name: durable state across
runs is not in this profile.

When `OP.md` and `op.yaml` both state a name, version, or description, they
SHOULD agree; a profile-aware validator SHOULD report disagreement.

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
    name: Attribute transcript segments to speakers
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
| `name`, `expected_outcome` | Human-readable; carried into the plan and Track |
| `depends_on` | Step ids that must finish first |
| `cog` | Required. `{id, version, source, task}` — see below |
| `input` | A mapping expression that evaluates to the step's request |
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

`cog.id`, `cog.source`, and `cog.task` are required strings; `cog.version` is
optional.

- `source` is a filesystem path to the Cog's package directory, relative to the
  Op package root. This is the only reference form in `[0.2]`; registry
  references are an [open design question](../../design-history/README.md).
- `task` MUST name an interface the Cog declares for the **usage** audience.
- `id` MUST equal the identity the Cog's manifest declares.
- `version`, when stated, SHOULD equal the version the Cog's manifest declares;
  a mismatch is a warning.

These are checked against the Cog itself; see
[Checks against the named Cogs](#checks-against-the-named-cogs).

## Mapping expressions

A step's `input`, a `foreach.items`, an artifact Gate's `artifact`, a
requirement's `targets` and `changes`, the `outputs`, and a cycle's limits are
**mapping expressions**. An object is an operator only when its key set is
**exactly** one of these; every other object is ordinary data and is walked
recursively, and scalars are literals.

| Operator | Value |
|---|---|
| `{$from: PATH}` | The value at PATH; an error if it is not available |
| `{$from: PATH, $default: EXPR}` | The value at PATH when present and not null, else EXPR |
| `{$path: EXPR}` | EXPR as an absolute filesystem path, resolved against the request file's directory |
| `{$run_dir: SUBPATH}` | A directory inside this run, created; SUBPATH may itself be an expression |
| `{$stem: EXPR}` | The final path component of EXPR without its suffix |
| `{$literal: ANY}` | ANY verbatim — the escape for data that looks like an operator |
| `{$sha256: EXPR}` | The [canonical digest](#canonical-digest) of EXPR's value; null is refused |

- **`closed-operators`** — a `$`-prefixed key that names no operator is refused
  wherever it appears, with or without siblings.

### Paths

A PATH is a dotted string. Dotted keys index objects; integer segments index
arrays. Its root is one of:

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

- **`run-dir-reserved`** — after normalization, the subpath must not name or
  lie under the run's control entries: `grants`, `pending`, `decisions`,
  `journal`, `run.lock`, `track.json`.

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

Elements run in order, each with its own request, envelope, and Gate decision.
The step's payload is the list of element payloads, `null` where an element
failed. The loop stops at the first element that finally fails; later elements
are recorded `not-reached` and are `null` in the payload, so the list still
lines up with `items`.

## `repeat`

```yaml
repeat: {count: 4, require: 1, mode: until-required}
```

The same request is invoked up to `count` times (1–5). `require` (1–`count`,
**`repeat-require-bounds`**) is how many must pass, and defaults to `count` only
when omitted. `mode` is `all` (default: run every repeat and return every
answer) or `until-required` (stop once `require` have passed).

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

`gate.guards` must be absent or empty (**`no-guards`**): Guards are supplied
by a hosting environment and are not in this profile. `decides` and `artifact`
belong only to a human Gate (**`decides-human-only`**).

### A human Gate over changes

`gate: {policy: human}` (or `decides: changes`). The step's payload carries a
`changes` list; each change has a `change_id`, a `content_sha256` (the
canonical digest of the change object without its two hash fields), and a
`target_sha256` (the digest of the target as the Op read it). The runner
refuses a change whose stated digests are missing, malformed, or wrong; it never
repairs a hash.

The person gives every change exactly one verdict: `approve`, `reject`, `edit`
(with the edited change, re-hashed from its edited content), or — through the
reference client — `defer`. The applied decision is exposed as
`steps.<id>.decision`:
`{approved, rejected, edited, history, decided_by, decided_at}`, where
`approved` carries the effective change objects.

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
Gate cannot state, or a digest that is not a SHA-256, is a failed Gate, never a
pause asking someone to accept nothing.

The decision is one verdict, `accept` or `reject`, bound to both the payload
and artifact digests. An accepted artifact is exposed as
`{verdict, artifact, artifact_sha256, reason, decided_by, decided_at}`. A
rejection ends the run, finally, for those bytes.

## `on_fail`

- `stop` ends the run `failed` at this step.
- `skip` records the step `skipped`, every step depending on it `blocked`, and
  ends the run `completed-with-problems`.
- `retry-once` re-invokes exactly once, and only when the envelope was
  `ok: false`. An error-severity problem in an `ok` envelope is a judgement,
  not a glitch, and is never retried. Refused on an effectful step
  (**`effectful-no-retry`**).

## Authority

A Cog that reaches outside the run declares `reaches` in its manifest, and runs
only under a **grant** the runner issues immediately before invoking it. There
are two sources of authority and no others: the run owner's **admission**
(`openteams/op-authority [0.1]`), which names what may be read, and a **human
decision**, the only thing that authorizes a write.

```yaml
- id: write-docs
  depends_on: [compose]
  cog: {id: example.org/cog-docs-writer, source: ../cog-docs-writer, task: write}
  authority:
    requires:
      - {resource: docs-site, action: write,
         changes: {$from: steps.compose.decision.approved}}
```

A step declares what it requires; it never grants itself anything. Each
requirement is `{resource, action}` plus `targets` (for a read) or `changes`
(for a write). `resource` and each target are opaque names that the admission,
the step, and the Cog's `reaches` agree on.

- **`read-names-targets`** — a non-write requirement names `targets`, not null,
  and declares no `changes`.
- **`one-target-key`** — `repositories` is the deprecated name for `targets`; a
  requirement states one of them.
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

`outputs` is an object of mapping expressions evaluated after the last step.
`track.records` lists what the Track records; see [Open for review](#open-for-review).

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
`{restart, prepare, replace}`: restart at a step that precedes the outcome step
(**`cycle-restart-precedes-outcome`**), optionally run `prepare` steps first,
and optionally `replace` the `input` and `depends_on` of restarted steps —
nothing else about a step can change. `initial` is reserved.

- Every expanded phase is itself a conforming document, validated before the
  first invocation. A phase receives the reserved input `cycle_previous`.
- **`cycle-costs-complete`** — `costs` gives a non-negative integer for exactly
  every step of every phase. Costs are reservation units for declared
  invocations, not prices.
- **`cycle-pure`** — a cycle Op declares no authority, top-level or on any
  step, including preparation steps.
- `max_attempts` and `max_cost_units` may read inputs only; they resolve once
  and stay fixed.
- `terminal_errors` maps steps to distinct envelope error codes that end the
  cycle as `refused` rather than recoverable.

## Checks against the named Cogs

A runner MUST make these checks for every named Cog that is present before it
invokes any step, and refuse the run on any error. A validator SHOULD make them
too. A Cog that is not present cannot be checked: that is a warning, and
invoking it later is an invocation failure.

They read the Cog's manifest. In this draft the fields are those of the
`openteams/cog-manifest [0.1]` profile (`id`, `version`, `kind`, `reaches`,
`interfaces[].task`, `interfaces[].audience`); how these map onto the Cog Spec
is an [open question](../../design-history/README.md).

- The Cog declares the stated `id`, and the stated `version` (warning).
- `task` is a declared interface for the **usage** audience. An interface that
  declares no audience is `lifecycle` if its task is one of `resolve`, `use`,
  `check`, `eval`, `test`, `bundle`, `serve`, and `usage` otherwise.
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

The Cog writes one envelope as a JSON object on stdout. Grant, run id, and
journal travel **beside** the request, never inside it.

If the Cog's argument parser rejects `--request` by name — exit code 2, the
diagnostic `unrecognized arguments: --request` on stderr, and no envelope on
stdout — the runner retries once with `--bundle`. Anything else is a result,
and an effectful Cog is never invoked twice. This retry is deprecated; see
[Open for review](#open-for-review).

## Run behaviour (informative in this draft)

The following is summarized from the reference implementation and is not yet
normative text. Each item will become normative, be moved to an
implementation note, or be dropped.

- **Step statuses:** `passed`, `passed-with-problems`, `failed`, `skipped`,
  `blocked`, `denied`, `not-reached`, `awaiting-decision`, `rejected`,
  `running`.
- **Run exit codes:** `0` completed, completed-with-problems, or a planned dry
  run; `1` failed or rejected; `2` invalid spec, request, admission, or
  decision, or a run another process holds; `3` paused for a human. Stdout is
  one JSON object.
- **Pause and resume.** A human Gate writes `pending/<step>.json`
  (`openteams/op-pending-decision [0.1]`) and exits 3. A resume with an
  `openteams/op-decision [0.1]` document reloads the Track, re-checks that
  `op.yaml` still hashes the same and that the named Cogs still pass their
  checks, applies the decision, and continues. A passed step is never re-run. A
  failed run resumes at its `failed_step`.
- **Digests on every invocation.** The runner digests the Cog package
  immediately before each invocation and records `cog_sha256` beside
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

These grew as needed and are kept in `[0.2]` so that existing Ops keep loading.
Each is proposed for change in a later version; see
[design-history](../../design-history/README.md) for the reasoning.

1. An object holding an operator key plus other keys (`{$from: x, label: y}`)
   is silently ordinary data. A misspelled sibling (`default:` for `$default:`)
   therefore changes meaning without an error.
2. `track.records` is declared but does not change what the reference runner
   records.
3. `gate.guards` exists only to be empty.
4. `repositories` as an alias for `targets`.
5. The `--request`/`--bundle` retry.
6. `warn` as a spelling of `warning` (in the envelope).
7. `cog.version` is optional and a mismatch is only a warning.
8. Audience inference from a fixed list of lifecycle task names.
9. Cycle refusals are less specific than the rest of the profile's.
