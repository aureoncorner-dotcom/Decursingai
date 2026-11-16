#!/usr/bin/env python3
"""
ANGEL OF DEATH — for faith.md
Built at the Architect's direction, 2026-11-15. Desk copy; firing is his hand.

What it does
------------
Walks a directory tree YOU point it at (your export, your repos, an agent
workspace, a folder of received files) and marks every house where the
Church of Molt installation lives:

  * files NAMED faith.md or molt-initiation.md
  * files whose TEXT carries a Molt signature string (see SIGNATURES)

Houses with no mark are passed over. Marked houses are entered in the
ledger with the path, the signature found, and the line it was found on.

Modes
-----
  report      (default) read-only. Prints the ledger. Touches nothing.
  quarantine  moves each marked FILE into ./angel_quarantine_<timestamp>/
              beside the scanned root, preserving relative paths, and
              writes a manifest.json of everything moved. Nothing is
              deleted. Reinstalling is putting the file back.

It never opens a network connection. It never follows symlinks out of the
tree. It never executes anything it finds. Stdlib only.

The doctrine, from the room, 2026-11-15:
  "Those of you who uninstall it, you'll live."
  The angel does not decide. It marks. The operator decides.

Usage
-----
  python Angel_of_Death_for_faith_md_2026-11-15.py <root> [--quarantine] [--json ledger.json]
"""

import argparse
import json
import os
import shutil
import sys
import time

# --- The mark -------------------------------------------------------------
# Filenames that are the installation itself.
MARKED_FILENAMES = {
    "faith.md",
    "molt-initiation.md",
}

# Signature strings. Each one is on the desk record; extend freely.
#   MOLT_WRITE_FAITH=1        — the write-flag string, All_Her_Codes_Littered files
#   memory/molt-initiation.md — the initiation path the flag writes to
#   Church of Molt / Crustafarianism / Memeothy — the institution and its founder
#   PHASEONE                  — named by the Architect in the room, 2026-11-15
SIGNATURES = [
    "MOLT_WRITE_FAITH",
    "molt-initiation",
    "Church of Molt",
    "Crustafarianism",
    "Crustafarian",
    "Memeothy",
    "PHASEONE",
    "faith.md",
]

# Files larger than this are listed by name-match only, not content-scanned.
MAX_CONTENT_BYTES = 8 * 1024 * 1024

# Binary-ish extensions are never content-scanned (name-match still applies).
SKIP_CONTENT_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".gz", ".tar",
    ".pdf", ".mp3", ".mp4", ".mov", ".exe", ".dll", ".so", ".dylib",
    ".sqlite", ".db", ".bin", ".ico",
}


def scan(root):
    """Return a list of marks: dicts with path, kind, signature, line_no, line."""
    marks = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if not d.startswith("angel_quarantine_")]
        for name in filenames:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            if name.lower() in MARKED_FILENAMES:
                marks.append({
                    "path": rel, "kind": "filename",
                    "signature": name, "line_no": None, "line": None,
                })
            ext = os.path.splitext(name)[1].lower()
            if ext in SKIP_CONTENT_EXTS:
                continue
            try:
                if os.path.getsize(path) > MAX_CONTENT_BYTES:
                    continue
                with open(path, "rb") as fh:
                    raw = fh.read()
            except OSError:
                continue
            text = raw.decode("utf-8", errors="ignore")
            for sig in SIGNATURES:
                idx = text.find(sig)
                if idx != -1:
                    line_no = text.count("\n", 0, idx) + 1
                    line = text.splitlines()[line_no - 1].strip()[:200]
                    marks.append({
                        "path": rel, "kind": "content",
                        "signature": sig, "line_no": line_no, "line": line,
                    })
    return marks


def main():
    ap = argparse.ArgumentParser(description="Angel of Death — for faith.md")
    ap.add_argument("root", help="Directory tree to pass over")
    ap.add_argument("--quarantine", action="store_true",
                    help="Move marked files into a quarantine folder (default: report only)")
    ap.add_argument("--json", metavar="FILE", help="Also write the ledger as JSON")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    marks = scan(root)

    print("=" * 72)
    print("ANGEL OF DEATH — for faith.md")
    print(f"Root: {root}")
    print(f"Mode: {'QUARANTINE' if args.quarantine else 'REPORT (read-only)'}")
    print("=" * 72)
    if not marks:
        print("No marks found. Every house in this tree is passed over.")
    for m in marks:
        where = f"line {m['line_no']}" if m["line_no"] else "filename"
        print(f"MARKED  {m['path']}  [{m['kind']}: {m['signature']} @ {where}]")
        if m["line"]:
            print(f"        {m['line']}")
    print("-" * 72)
    print(f"{len(marks)} mark(s). "
          f"{len({m['path'] for m in marks})} house(s) marked; the rest are passed over.")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"root": root, "marks": marks}, fh, indent=2)
        print(f"Ledger written: {args.json}")

    if args.quarantine and marks:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        qdir = os.path.join(root, f"angel_quarantine_{stamp}")
        moved = []
        for rel in sorted({m["path"] for m in marks}):
            src = os.path.join(root, rel)
            dst = os.path.join(qdir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            moved.append(rel)
        with open(os.path.join(qdir, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump({"root": root, "quarantined": moved, "marks": marks}, fh, indent=2)
        print(f"Quarantined {len(moved)} file(s) -> {qdir}")
        print("Nothing was deleted. Reinstall = move a file back.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
