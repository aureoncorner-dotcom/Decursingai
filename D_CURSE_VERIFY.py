#!/usr/bin/env python3
"""Read-only, standard-library verifier for the D-CURSE numerical manuscript."""
from pathlib import Path
from hashlib import sha256
import json
import math
import re
import sys

HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'D_CURSE_MANIFEST.json').read_text('utf-8'))

def sha_file(p): return sha256(p.read_bytes()).hexdigest()
for filename,digest in manifest['files'].items():
    assert sha_file(HERE/filename)==digest, f'hash mismatch: {filename}'

def prime_list(end):
    v=bytearray(b'\x01')*(end+1)
    v[0:2]=b'\x00\x00'
    for n in range(2,math.isqrt(end)+1):
        if v[n]:v[n*n:end+1:n]=b'\x00'*((end-n*n)//n+1)
    return [i for i in range(end+1) if v[i]]

ps=prime_list(40013)
fire=[p for p in ps if 39191<=p<=40013]
current=[p for p in ps if 827<=p<=1579]
origin=[p for p in ps if 2<=p<=73]
assert (len(fire),len(current),len(origin))==(80,106,21)
expected=[fire[(73*i+437+current[(i+231)%106]+origin[(i+1109)%21])%80] for i in range(579)]
orig=(HERE/'D_CURSE_ORIGINAL_SELECTOR.md').read_text('utf-8')
blocks=re.findall(r'```text\n(.*?)\n```',orig,flags=re.S)
assert len(blocks)==1
old_rows=blocks[0].splitlines()
new_rows=(HERE/'D_CURSE_PRIME_D_113x73.txt').read_text('ascii').splitlines()
assert len(old_rows)==len(new_rows)==73
assert all(len(x)==113 for x in old_rows+new_rows)
getnums=lambda rows:[int(n) for r in rows for n in re.findall(r'(?<!\d)\d{5}(?!\d)',r)]
assert getnums(old_rows)==getnums(new_rows)==expected
assert old_rows!=new_rows
wall_orig=(HERE/'D_CURSE_ORIGINAL_WALL.txt').read_text('ascii').splitlines()
wall_new=(HERE/'D_CURSE_7925_D_WALL.txt').read_text('ascii').splitlines()
assert len(wall_orig)==len(wall_new)==57
assert all(len(x)==210 for x in wall_new)
assert [r.replace(' ','') for r in wall_new]==wall_orig
assert sum(len(x) for x in wall_orig)==7925
assert all(x.isdigit() for x in wall_orig)
print('PASS — package hashes, 579 prime selector tokens, 113×73 geometry, and 7,925 exact source digits')
print('PASS — D folio differs in layout; wall removes only inserted ASCII spaces')
print('PASS — no uploaded installer or quarantine code was executed')
