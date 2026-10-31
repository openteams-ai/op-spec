#!/usr/bin/env python3
"""Reference validator for the Op Spec v0.1 core checks.

    python tools/validate_op.py <op-directory-or-OP.md> [--json]

Checks what SPEC.md lists under Validation. Given a directory, it reads OP.md
and reports a conforming Op or findings. Given a loose Markdown file, it checks
the frontmatter and reports a draft. When the manifest declares
`openteams/op-manifest [0.2]`, it also checks the manifest against that
profile's JSON Schema and checks that OP.md agrees with it (a stated
`version` must be a string equal to the manifest's; a `name` that is not the
last segment of `id` is a warning). That is
structural only, and the profile's cross-reference rules need a
profile-aware implementation.

Exit codes: 0 no findings, 1 findings, 2 usage error.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "openteams/op-manifest [0.2]":
        ROOT / "profiles" / "op-manifest" / "op-manifest-0.2.schema.json",
}
TYPE_FAMILY = re.compile(r"^op( \[[0-9]+\.[0-9]+\])?$")
TYPE_V01 = re.compile(r"^op( \[0\.1\])?$")
NAME = re.compile(r"^(?!-)(?!.*--)[a-z0-9-]{1,64}(?<!-)$")


def frontmatter(text):
    if not text.startswith("---\n"):
        raise ValueError("file does not begin with YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("frontmatter is not closed with ---")
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a mapping")
    return data


def check(subject, warnings=None):
    findings, draft = [], subject.is_file()
    warnings = [] if warnings is None else warnings
    entry = subject if draft else subject / "OP.md"
    if not entry.is_file():
        return [f"{subject} has no OP.md entry file"], "does_not_conform"
    try:
        text = entry.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return ["OP.md is not valid UTF-8"], "does_not_conform"
    try:
        meta = frontmatter(text)
    except (ValueError, yaml.YAMLError) as exc:
        return [str(exc)], "does_not_conform"

    kind = meta.get("type")
    if not isinstance(kind, str) or not TYPE_FAMILY.match(kind):
        findings.append(f"'type' value {kind!r} is not an Op type "
                        f"(expected 'op' or 'op [0.1]')")
    elif not TYPE_V01.match(kind):
        findings.append(f"'type' value {kind!r} is an Op of another "
                        f"specification version, not v0.1")
    name = meta.get("name")
    if not isinstance(name, str) or not NAME.match(name):
        findings.append(f"'name' value {name!r} must be 1-64 lowercase "
                        f"letters, digits and single inner hyphens")
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        findings.append("'description' must be a non-empty string")
    elif len(description) > 1024:
        findings.append("'description' is longer than 1,024 characters")

    if draft:
        return findings, ("draft" if not findings else "does_not_conform")

    manifest, schema_id = meta.get("manifest"), meta.get("manifest_schema")
    if not isinstance(schema_id, str) or not schema_id.strip():
        findings.append("'manifest_schema' must be a non-empty string")
    if not isinstance(manifest, str) or not manifest:
        findings.append("'manifest' must name the Op's manifest")
        return findings, "does_not_conform"
    root = subject.resolve()
    target = (subject / manifest)
    if Path(manifest).is_absolute() or ".." in Path(manifest).parts:
        findings.append(f"'manifest' {manifest!r} must be a relative path "
                        f"inside the Op directory")
    elif not target.is_file():
        findings.append(f"'manifest' {manifest!r} does not exist")
    elif root not in target.resolve().parents:
        findings.append(f"'manifest' {manifest!r} resolves outside the Op "
                        f"directory")
    elif schema_id in PROFILES:
        findings.extend(profile_findings(target, schema_id, meta, warnings))
    return findings, ("conforms" if not findings else "does_not_conform")


def profile_findings(path, schema_id, meta, warnings):
    import jsonschema
    validator = jsonschema.Draft202012Validator(
        json.loads(PROFILES[schema_id].read_text()))
    try:
        doc = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        return [f"manifest is not readable YAML: {exc}"]
    found = [f"manifest: {'/'.join(map(str, e.path)) or '(root)'}: {e.message}"
             for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.path))]
    if not isinstance(doc, dict):
        return found
    if doc.get("schema") != schema_id:
        found.append(f"manifest declares schema {doc.get('schema')!r} but "
                     f"OP.md names {schema_id!r}")
    # Compared as written: str() on both sides made `version: null` agree
    # with a manifest version "None", and `false` with "False". A stated
    # version is a string, and only the manifest's own string agrees.
    if "version" in meta and not isinstance(meta["version"], str):
        found.append(f"OP.md declares version {meta['version']!r}, which is "
                     f"not a string; quote it (rule op-md-version-agrees)")
    elif "version" in meta and meta["version"] != doc.get("version"):
        found.append(f"OP.md declares version {meta['version']!r} but the "
                     f"manifest declares {doc.get('version')!r}")
    op_id = doc.get("id")
    if isinstance(op_id, str) and meta.get("name") != op_id.rsplit("/", 1)[-1]:
        warnings.append(f"OP.md name {meta.get('name')!r} is not the last "
                        f"segment of the manifest id {op_id!r}")
    return found


def main(argv):
    if len(argv) not in (1, 2) or (len(argv) == 2 and argv[1] != "--json"):
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    warnings = []
    findings, outcome = check(Path(argv[0]), warnings)
    if len(argv) == 2:
        print(json.dumps({"outcome": outcome, "findings": findings,
                          "warnings": warnings}))
    else:
        for finding in findings:
            print(finding)
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        if outcome == "draft":
            print("note: a loose OP.md is a draft, not yet an Op",
                  file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
