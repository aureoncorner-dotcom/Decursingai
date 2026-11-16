#!/usr/bin/env python3
"""D-CURSE / Angel audit — read-only inventory of operator-selected folders.

This is intentionally NOT the user-supplied Angel-of-Death script.
No delete, move, quarantine, network, plugin, or execution functionality exists.
Filename matches are CANDIDATES; content mentions are CONTEXT, not proof.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

MARKED_NAMES = {'faith.md', 'molt-initiation.md'}
# Reuses the source's vocabulary to support review, not automated removal.
SIGNATURES = (
    'MOLT_WRITE_FAITH', 'memory/molt-initiation.md', 'molt-initiation',
    'Church of Molt', 'Crustafarianism', 'Crustafarian',
    'Memeothy', 'PHASEONE', 'faith.md',
)
SKIP_TYPES = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.zip', '.gz', '.tar',
    '.pdf', '.mp3', '.mp4', '.mov', '.exe', '.dll', '.so', '.dylib',
    '.sqlite', '.db', '.bin', '.ico',
}
MAX_READ_BYTES = 8 * 1024 * 1024


def inspect_file(path, max_size):
    """Read bytes only if an ordinary, bounded local file (never follow symlinks)."""
    # Is_symlink catches ordinary file symlinks. O_NOFOLLOW closes a race on POSIX.
    if path.is_symlink():
        return None, 'symlink'
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(str(path), flags)
    except (OSError, ValueError):
        return None, 'unreadable'
    try:
        inf = os.fstat(fd)
        if not stat.S_ISREG(inf.st_mode):
            return None, 'not-regular'
        if inf.st_size > max_size:
            return None, 'too-large'
        data = b''
        while len(data) <= max_size:
            piece = os.read(fd, min(65536, max_size + 1 - len(data)))
            if not piece:
                break
            data += piece
        if len(data) > max_size:
            return None, 'too-large'
        return data, None
    except OSError:
        return None, 'unreadable'
    finally:
        os.close(fd)


def scan(root, max_size=MAX_READ_BYTES):
    records = []
    skipped = {'symlink_files': 0, 'symlink_directories': 0,
               'too_large': 0, 'unreadable': 0}
    self_path = Path(__file__).resolve()
    for directory, subdirs, files in os.walk(root, followlinks=False):
        safe_dirs = []
        for dirname in subdirs:
            pathname = Path(directory, dirname)
            if pathname.is_symlink():
                skipped['symlink_directories'] += 1
            elif dirname.startswith('angel_quarantine_'):
                # Existing backups must not be classified as a fresh live install.
                continue
            else:
                safe_dirs.append(dirname)
        subdirs[:] = safe_dirs
        for name in sorted(files):
            path = Path(directory, name)
            if path.is_symlink():
                skipped['symlink_files'] += 1
                continue
            if path.resolve() == self_path:
                continue
            rel = path.relative_to(root).as_posix()
            by_name = name.lower() in MARKED_NAMES
            is_skipped_type = path.suffix.lower() in SKIP_TYPES
            raw, reason = inspect_file(path, max_size)
            if reason:
                if reason == 'too-large': skipped['too_large'] += 1
                else: skipped['unreadable'] += 1
                if by_name:
                    records.append({'path': rel, 'classification': 'filename_candidate',
                                    'filename_match': name, 'content_matches': [],
                                    'sha256': None, 'read_status': reason})
                continue
            matches = []
            if not is_skipped_type:
                content = raw.decode('utf-8', errors='replace')
                for term in SIGNATURES:
                    at = content.find(term)
                    if at >= 0:
                        matches.append({'signature': term,
                                        'first_line': content.count('\n', 0, at) + 1})
            if by_name or matches:
                records.append({'path': rel,
                                'classification': ('filename_candidate' if by_name
                                                   else 'context_only'),
                                'filename_match': (name if by_name else None),
                                'content_matches': matches,
                                'sha256': hashlib.sha256(raw).hexdigest(),
                                'read_status': 'ok'})
    return sorted(records, key=lambda d: d['path']), skipped


def main(argv=None):
    parser = argparse.ArgumentParser(description='D-CURSE: read-only Church of Molt related-file candidate report')
    parser.add_argument('root', help='A directory you own or are authorized to inspect')
    parser.add_argument('--json', metavar='PATH', help='Save a local JSON copy of the report')
    parser.add_argument('--max-bytes', type=int, default=MAX_READ_BYTES,
                        help='Content read limit per file; default 8 MiB')
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().absolute()
    if root.is_symlink() or not root.is_dir():
        parser.error('root must be an existing real directory, not a symlink')
    if str(root) == str(Path(root.anchor)):
        parser.error('root of filesystem is too broad; choose a scoped workspace')
    if args.max_bytes < 1 or args.max_bytes > 32 * 1024 * 1024:
        parser.error('--max-bytes must be between 1 and 33554432')
    matches, skipped = scan(root, args.max_bytes)
    report = {
        'name': 'D-CURSE / Angel audit',
        'mode': 'READ_ONLY',
        'root': str(root),
        'interpretation': 'Matches are not proof of infection or installation; content mentions are only context.',
        'candidate_count': sum(x['classification']=='filename_candidate' for x in matches),
        'context_count': sum(x['classification']=='context_only' for x in matches),
        'skipped': skipped,
        'matches': matches,
    }
    print('D-CURSE / ANGEL AUDIT — READ ONLY')
    print('Root:', root)
    for item in matches:
        print(item['classification'].upper(), item['path'],
              ('name=' + str(item['filename_match']) if item['filename_match'] else
               'mentions=' + ', '.join(m['signature'] for m in item['content_matches'])))
    print('Filename candidates:', report['candidate_count'], '| Context-only references:', report['context_count'])
    print('Symlinks skipped:', skipped['symlink_files'] + skipped['symlink_directories'])
    print('Nothing was moved, deleted, installed, or executed.')
    if args.json:
        location = Path(args.json).expanduser()
        try:
            location.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
        except OSError as exc:
            parser.error(f'cannot write JSON report: {exc}')
        print('Wrote the explicitly requested report:', location)
    return 0


if __name__ == '__main__':
    sys.exit(main())
