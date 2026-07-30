#!/usr/bin/env python3
"""Assert the §0 shared-rules block is identical across every persona (modulo the persona's own name).

The §0 block is baked into all agents/*.md so a dispatched reviewer always has the rules in context
without a file read. Nothing in the harness enforces that the copies stay in sync, so this check does:
it extracts each file's block from the `# Shared rules` heading to EOF, replaces the persona's own name
with a placeholder, and confirms all copies hash to one value. Run it after editing any persona or §0.

Exit 0 = identical; exit 1 = drift (prints the offending files). stdlib only.
"""
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
AGENTS = sorted((ROOT / "agents").glob("*.md"))


def section0(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("# Shared rules"):
            body = "\n".join(lines[i:])
            return body.replace(path.stem, "PERSONA")  # normalise the persona's own name
    return None


def main():
    if not AGENTS:
        print("no agent files found", file=sys.stderr)
        return 1
    hashes = {}
    missing = []
    for a in AGENTS:
        s0 = section0(a)
        if s0 is None:
            missing.append(a.name)
            continue
        hashes.setdefault(hashlib.md5(s0.encode()).hexdigest(), []).append(a.name)

    if missing:
        print("FAIL — no §0 block in:", ", ".join(missing))
        return 1
    if len(hashes) == 1:
        print(f"OK — §0 identical across all {len(AGENTS)} personas.")
        return 0
    print(f"FAIL — §0 has drifted into {len(hashes)} variants:")
    for h, names in sorted(hashes.items(), key=lambda kv: -len(kv[1])):
        print(f"  [{len(names)}] {', '.join(names)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
