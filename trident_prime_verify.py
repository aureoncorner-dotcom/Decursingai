#!/usr/bin/env python3
"""Offline independent reproduction of TRIDENT/PRIME FIELD 23x23 witness.

Uses one-based positions in concatenated decimal primes, beginning 2,3,5,7,...
Does not authenticate original submitted/displayed/transcribed bytes.
"""
from collections import Counter
from hashlib import sha256
from math import isqrt
from pathlib import Path
import json

N, WIDTH, REFERENCE = 127*113, 23, 437
OBSERVED_GRID = '''+##+x.x+.+x.#++.#.#+..x
+.+++#.x..++.#++.x+x..+
x....+x.+...x.#.++.+x.+
+x+x....+x.++x.+..+x++.
+...x...x.#..+x.x+..#++
+++++.+++++x+..#+.+++#.
#+..++.+++#.x+.++.#+.++
.x+.+#.+++.#+++.+#.x+++
++.+.+#+#++.#.#+..+.+..
...x....+..+..+#.+.x.#.
..x++...x.#..+.+...+x..
...#.++..#+.+++#.x+.+++
#+.+#.x++.++++.+#.++...
....+..#..+x.x.+.x....+
..+.++.+x....+#.++..+..
.#.x+..#..+++#++++.+.#+
+.++#+..+.x+++#.++.+x..
....+x.++x++.+..+x.++.+
+.+.x.#.++.....+x.#..+o
.x...x+..++x....+.+#..+
x+x.++x.+.....+...x...+
...x..+x..+...+#..+x...
..x+........+.x.x...+..'''.splitlines()

def sieve(n):
    prime = bytearray(b'\x01') * (n+1)
    prime[0:2] = b'\x00\x00'
    for p in range(2, isqrt(n)+1):
        if prime[p]:
            prime[p*p:n+1:p] = b'\x00' * (((n-p*p)//p)+1)
    return prime

prime = sieve(50000)
digits = ''
for p in range(2, len(prime)):
    if prime[p]:
        digits += str(p)
        if len(digits) >= N:
            digits = digits[:N]
            break
assert len(digits) == N
symbols = ''.join('#' if prime[i] and d in '2357' else
                  'x' if prime[i] else
                  '+' if d in '2357' else '.'
                  for i,d in enumerate(digits, 1))
witness_symbols = symbols[:529]
witness = witness_symbols[:REFERENCE-1]+'o'+witness_symbols[REFERENCE:]
rows = [witness[i:i+WIDTH] for i in range(0,529,WIDTH)]
assert rows == OBSERVED_GRID, 'The pasted 23x23 grid has a literal mismatch'
assert symbols[REFERENCE-1] == '.' and digits[REFERENCE-1] == '9'
assert (REFERENCE-1)//23+1 == 19 and (REFERENCE-1)%23+1 == 23
assert (REFERENCE-1)//113+1 == 4 and (REFERENCE-1)%113+1 == 98
counts_529 = Counter(witness_symbols)
counts_overlay = Counter(witness)
counts_all = Counter(symbols)
copy_marks = [witness_symbols[i % 529] == '#' for i in range(N)]
true_marks = [s=='#' for s in symbols]
copy_n = sum(copy_marks)
true_n = sum(true_marks)
overlap_n = sum(a and b for a,b in zip(copy_marks,true_marks))
assert (counts_529['#'],counts_529['x'],counts_529['+'],counts_529['.']) == (43,56,184,246)
assert (counts_overlay['#'],counts_overlay['x'],counts_overlay['+'],counts_overlay['.'],counts_overlay['o']) == (43,56,184,245,1)
assert (counts_all['#'],counts_all['x'],counts_all['+'],counts_all['.']) == (732,951,5545,7123)
assert (copy_n, true_n, overlap_n) == (1169,732,104)
result = {
    'source_rule':'concatenate decimal primes from 2 upward, truncate to 14351 characters, index from 1',
    'regenerated_stream_sha256':sha256(digits.encode('ascii')).hexdigest(),
    'regenerated_grid_sha256':sha256(('\n'.join(rows)+'\n').encode('ascii')).hexdigest(),
    'length_full':N,
    'first_529_histogram_no_overlay':dict(counts_529),
    'first_529_histogram_with_437_o':dict(counts_overlay),
    'full_histogram':dict(counts_all),
    'prime_positions_529': counts_529['#']+counts_529['x'],
    'eligible_digits_529': counts_529['#']+counts_529['+'],
    'prime_positions_full': counts_all['#']+counts_all['x'],
    'eligible_digits_full': counts_all['#']+counts_all['+'],
    '437':{'source_digit':digits[436], 'position_is_prime':bool(prime[437]),
           'underlying_symbol':symbols[436], 'annotation':'o',
           'coordinates_23x23':[19,23], 'coordinates_127x113':[4,98]},
    'repetition':{'template_length':529, 'copied_template_double_keys':copy_n,
                  'source_double_keys':true_n,'overlapping_double_keys':overlap_n,
                  'lattice_width':113,'displacement':529%113},
    'literal_grid_matches_supplied_rows':True,
    'canary_v2_v3_provenance':'not evaluated; no original bytes/line-level canary corpus supplied',
    'text_fidelity_observation':'latest legend/histogram use hyphen instead of plus; grid itself uses plus',
}
out = Path('/mnt/data/trident_prime_audit_20261114.json')
out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2,sort_keys=True))
print('REPORT',out,'SCRIPT',Path(__file__))
