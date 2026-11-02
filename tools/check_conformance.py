#!/usr/bin/env python3
"""Check the Op Spec conformance corpus, examples, and fixtures.

Every case under profiles/op-manifest/conformance/cases/<case>/ holds an
op.yaml and an expected.json:

    {"conforms": false, "layer": "schema", "rule": "closed-top-level",
     "reference_finding": "unknown top-level Op spec key"}

`layer` says which part of the profile refuses the document: "schema" means
the JSON Schema alone refuses it; "profile" means the JSON Schema accepts it
and a rule stated only in PROFILE.md refuses it. The checker enforces that
split, so the corpus also documents exactly what the JSON Schema does not
catch.

With --reference PATH, the checker also loads an implementation's op_spec.py
(any module exposing validate(doc), OpSpecError and SCHEMA_STRING) and
requires its verdict to match `conforms` on every case and example. A
reference that implements this profile — one whose SCHEMA_STRING, or whose
SCHEMA_STRINGS list, includes `openteams/op-manifest [0.2]` — is given each
document as written; any other is given it translated to its own identifier
(see reference_verdict).
`reference_finding` is informative: a mismatch is reported but not counted
as a failure, because finding text is not normative. A case whose
expected.json carries `reference_divergence` records a known difference
between this profile and a reference that predates it; for such a reference
a mismatch on it is reported as a note, and so is a match, so the field is
removed once the reference agrees. The waiver never applies to a reference
that implements this profile: it is held to every case exactly, so a
regression in it cannot hide behind a note written for an older one.

It also runs the reference validator, tools/validate_op.py, over every Op
under tools/validate-op-fixtures/<fixture>/, whose expected.json states the
`outcome` and a `finding` its findings must contain:

    {"outcome": "does_not_conform", "finding": "not a string"}

Exit codes: 0 every check passed, 1 at least one failed, 2 usage error.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles" / "op-manifest"
PROFILE_SCHEMA_PATH = PROFILE / "op-manifest-0.2.schema.json"
CASES = PROFILE / "conformance" / "cases"
EXAMPLES = ROOT / "examples"
ENVELOPE_SCHEMA_PATH = ROOT / "schemas" / "envelope-1.schema.json"
ENVELOPE_FIXTURES = ROOT / "schemas" / "envelope-fixtures"
VALIDATOR = ROOT / "tools" / "validate_op.py"
VALIDATOR_FIXTURES = ROOT / "tools" / "validate-op-fixtures"
PROFILE_SCHEMA_STRING = "openteams/op-manifest [0.2]"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_reference(path):
    spec = importlib.util.spec_from_file_location("op_spec_reference", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load reference implementation {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("validate", "OpSpecError", "SCHEMA_STRING"):
        if not hasattr(module, name):
            raise SystemExit(f"{path} does not expose {name}")
    return module


def implements_profile(module):
    """True when the reference accepts this profile's identifier itself:
    its SCHEMA_STRING is it, or its SCHEMA_STRINGS (every identifier it
    runs) include it."""
    strings = getattr(module, "SCHEMA_STRINGS", None) or ()
    return (module.SCHEMA_STRING == PROFILE_SCHEMA_STRING
            or PROFILE_SCHEMA_STRING in strings)


def reference_verdict(module, doc):
    """(conforms, problems) from the reference implementation. A reference
    that implements this profile is given the document as written. One that
    implements this profile's vocabulary under an earlier schema string is
    checked by substituting its own string for this profile's, and by
    reading `title` as that version's `name`, at the top level and on every
    step, including the steps a cycle transition prepares."""
    doc = copy.deepcopy(doc)
    if (isinstance(doc, dict) and doc.get("schema") == PROFILE_SCHEMA_STRING
            and not implements_profile(module)):
        doc["schema"] = module.SCHEMA_STRING
        for item in [doc] + steps_of(doc):
            if isinstance(item, dict) and "title" in item and "name" not in item:
                item["name"] = item.pop("title")
    try:
        module.validate(doc)
    except module.OpSpecError as exc:
        problems = getattr(exc, "problems", None) or [str(exc)]
        if isinstance(problems, str):
            problems = [problems]
        return False, [str(p) for p in problems]
    return True, []


def steps_of(doc):
    """Every step a document declares: its steps, and the steps each cycle
    transition prepares."""
    steps = doc.get("steps")
    found = list(steps) if isinstance(steps, list) else []
    cycle = doc.get("cycle")
    transitions = cycle.get("transitions") if isinstance(cycle, dict) else None
    for transition in (transitions or {}).values() if isinstance(transitions, dict) else []:
        prepare = transition.get("prepare") if isinstance(transition, dict) else None
        if isinstance(prepare, list):
            found.extend(prepare)
    return found


def schema_errors(validator, doc):
    return sorted(validator.iter_errors(doc), key=lambda e: list(e.path))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reference", type=Path,
                        help="an implementation's op_spec.py to compare against")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    validator = jsonschema.Draft202012Validator(
        json.loads(PROFILE_SCHEMA_PATH.read_text()))
    reference = load_reference(args.reference) if args.reference else None
    # Only a reference that predates this profile may be excused by a case's
    # reference_divergence: one that implements [0.2] states it implements
    # every rule, so it must agree on every case.
    waivable = reference is not None and not implements_profile(reference)
    failures, notes, checked = [], [], 0

    for case in sorted(p for p in CASES.iterdir() if p.is_dir()):
        checked += 1
        doc = yaml.safe_load((case / "op.yaml").read_text())
        expected = json.loads((case / "expected.json").read_text())
        errors = schema_errors(validator, doc)
        name = case.name
        if expected["conforms"]:
            if errors:
                failures.append(f"{name}: expected to conform; the JSON Schema "
                                f"refuses it: {errors[0].message}")
        elif expected["layer"] == "schema" and not errors:
            failures.append(f"{name}: layer 'schema', but the JSON Schema "
                            f"accepts it")
        elif expected["layer"] == "profile" and errors:
            failures.append(f"{name}: layer 'profile', but the JSON Schema "
                            f"already refuses it ({errors[0].message}); "
                            f"move it to layer 'schema'")
        if reference is not None:
            conforms, problems = reference_verdict(reference, doc)
            divergence = expected.get("reference_divergence")
            if divergence and conforms == expected["conforms"]:
                notes.append(f"{name}: the reference now agrees; remove "
                             f"reference_divergence")
            elif divergence and waivable:
                notes.append(f"{name}: known divergence: {divergence}")
            elif conforms != expected["conforms"]:
                failures.append(f"{name}: reference says conforms={conforms}, "
                                f"expected {expected['conforms']}"
                                + (f": {problems[0]}" if problems else ""))
            finding = None if divergence else expected.get("reference_finding")
            if finding and not any(finding in p for p in problems):
                notes.append(f"{name}: reference finding text differs "
                             f"(expected to contain {finding!r}; got "
                             f"{problems[:1]})")
        if args.verbose:
            print(f"checked {name}")

    for example in sorted(EXAMPLES.glob("*/op.yaml")):
        checked += 1
        doc = yaml.safe_load(example.read_text())
        rel = example.relative_to(ROOT)
        errors = schema_errors(validator, doc)
        if errors:
            failures.append(f"{rel}: example refused by the JSON Schema: "
                            f"{errors[0].message}")
        if reference is not None:
            conforms, problems = reference_verdict(reference, doc)
            if not conforms:
                failures.append(f"{rel}: example refused by the reference: "
                                f"{problems[0]}")

    envelope_validator = jsonschema.Draft202012Validator(
        json.loads(ENVELOPE_SCHEMA_PATH.read_text()))
    for fixture in sorted(ENVELOPE_FIXTURES.glob("*.json")):
        checked += 1
        doc = json.loads(fixture.read_text())
        well_formed = not fixture.name.startswith("malformed-")
        errors = list(envelope_validator.iter_errors(doc))
        if well_formed and errors:
            failures.append(f"{fixture.name}: refused by the envelope schema: "
                            f"{errors[0].message}")
        if not well_formed and not errors:
            failures.append(f"{fixture.name}: malformed fixture accepted by "
                            f"the envelope schema")

    # The reference validator's own checks, on Ops written to break exactly
    # one of them: a check that coerces or skips is caught here, in CI,
    # rather than by the next Op it wrongly accepts.
    validate_op = load_module("validate_op", VALIDATOR)
    for fixture in sorted(p for p in VALIDATOR_FIXTURES.iterdir() if p.is_dir()):
        checked += 1
        expected = json.loads((fixture / "expected.json").read_text())
        findings, outcome = validate_op.check(fixture, [])
        if outcome != expected["outcome"]:
            failures.append(f"{fixture.name}: validate_op says {outcome!r}, "
                            f"expected {expected['outcome']!r}"
                            + (f": {findings[0]}" if findings else ""))
        elif expected.get("finding") and not any(
                expected["finding"] in f for f in findings):
            failures.append(f"{fixture.name}: no validate_op finding contains "
                            f"{expected['finding']!r}; got {findings}")

    for note in notes:
        print(f"note: {note}")
    for failure in failures:
        print(f"FAIL: {failure}")
    print(f"{checked} checked, {len(failures)} failed"
          + (f", compared with {args.reference}"
             + (" as written" if implements_profile(reference)
                else f" translated to {reference.SCHEMA_STRING!r}")
             if reference else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
