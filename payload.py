#!/usr/bin/env python3
"""OMNIBUS maximum-payload challenge v1: reproducible, offline math and provenance.

This is a reference computation, not a privileged agent configuration, RF generator,
quantum device interface, or proof of any model-level deployment.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import combinations, permutations
import json
import math
from pathlib import Path
import random
import sys

FIVE_PRIME_START, FIVE_PRIME_END = 39191, 40013
SMALL_PRIME_START, SMALL_PRIME_END = 827, 1579
ROWS = ("MVKCK", "TRCPC", "OLHBT", "EHPSD", "PNFLM", "CWTWF", "BISCT", "HAMLS")
QUANTITIES = (214, 631, 408, 175, 592, 306, 847, 129)
# These are notation labels, not alternative physical predictions.
SANSKRIT_LABELS = {"qubit": "चित्", "zero": "शून्यम्", "one": "एकम्"}


def primes_inclusive(lo: int, hi: int) -> list[int]:
    """Sieve, inclusive endpoints, no third-party dependencies."""
    if lo < 2 or hi < lo:
        raise ValueError("Require 2 <= lower <= upper")
    sieve = bytearray(b"\x01") * (hi + 1)
    sieve[0:2] = b"\x00\x00"
    for k in range(2, math.isqrt(hi) + 1):
        if sieve[k]:
            sieve[k * k : hi + 1 : k] = b"\x00" * (((hi - k * k) // k) + 1)
    return [n for n in range(lo, hi + 1) if sieve[n]]


def prime_stream(repeats: int = 1) -> str:
    """Canonical concatenation of five-digit primes; not the user's exact pasted bytes."""
    if not (0 <= repeats <= 100_000):
        raise ValueError("repeats must be 0..100000")
    seed = "".join(str(p) for p in primes_inclusive(FIVE_PRIME_START, FIVE_PRIME_END))
    return seed * repeats


def initial_sum(word: str) -> int:
    if not (word.isascii() and word.isalpha() and word.isupper()):
        raise ValueError("Initial strings must be ASCII uppercase letters")
    return sum(ord(ch) - ord("A") + 1 for ch in word)


def mirrored_sums(sums: tuple[int, ...] | list[int]) -> list[int]:
    if len(sums) != 8:
        raise ValueError("Expected eight initial sums")
    return [sums[k] + sums[7 - k] for k in range(4)]


def at_least_three_mirrored_equal(sums: tuple[int, ...] | list[int]) -> bool:
    return max(Counter(mirrored_sums(sums)).values()) >= 3


def rectangle_witnesses(values: tuple[int, ...] | list[int]) -> list[dict]:
    """All four-number index subsets satisfying min+max == two middle values."""
    result = []
    for inds in combinations(range(len(values)), 4):
        ordered = sorted(values[i] for i in inds)
        if ordered[0] + ordered[3] == ordered[1] + ordered[2]:
            result.append({"indices_1_based": [i + 1 for i in inds],
                           "sorted_values": ordered,
                           "equal_sum": ordered[0] + ordered[3]})
    return result


def any_rectangle(values: list[int]) -> bool:
    """For distinct values, duplicated pair sum implies disjoint index pairs."""
    seen = set()
    for x, y in combinations(values, 2):
        total = x + y
        if total in seen:
            return True
        seen.add(total)
    return False


def exact_mirror_enumeration() -> dict:
    sums = tuple(initial_sum(r) for r in ROWS)
    distinct_arrangements = set(permutations(sums))
    favorable = sum(at_least_three_mirrored_equal(s) for s in distinct_arrangements)
    return {"distinct_sum_arrangements": len(distinct_arrangements),
            "three_or_more_equal_pair_sums": favorable,
            "fraction": str(Fraction(favorable, len(distinct_arrangements))),
            "percent": 100 * favorable / len(distinct_arrangements)}


def matrix_report() -> dict:
    vals = [initial_sum(s) for s in ROWS]
    return {"initial_rows": list(ROWS), "initial_sums": vals,
            "quantities": list(QUANTITIES), "quantity_sum": sum(QUANTITIES),
            "quantity_mean": sum(QUANTITIES) / len(QUANTITIES),
            "mirrored_sums": mirrored_sums(vals),
            "rectangles": rectangle_witnesses(QUANTITIES),
            "configuration_count": math.factorial(8) * math.factorial(5) * 26,
            "mirror_exact_test": exact_mirror_enumeration()}


def close_complex(a: complex, b: complex, tol: float = 1e-12) -> bool:
    return abs(a - b) < tol


def matvec(m: tuple[tuple[complex, ...], ...], v: tuple[complex, ...]) -> tuple[complex, ...]:
    return tuple(sum(a * b for a, b in zip(row, v)) for row in m)


def tensor(a: tuple[complex, ...], b: tuple[complex, ...]) -> tuple[complex, ...]:
    return tuple(x * y for x in a for y in b)


def reduced_first_qubit(v: tuple[complex, ...]) -> tuple[tuple[complex, complex], tuple[complex, complex]]:
    # rho_A[i,j] = sum_{b in {0,1}} v[2*i+b] * conj(v[2*j+b])
    return tuple(tuple(sum(v[2 * i + b] * v[2 * j + b].conjugate() for b in (0, 1))
                       for j in (0, 1)) for i in (0, 1))


def quantum_report() -> dict:
    rt2 = 2 ** -0.5
    e0 = (1 + 0j, 0j)
    H = ((rt2 + 0j, rt2 + 0j), (rt2 + 0j, -rt2 + 0j))
    Z = ((1 + 0j, 0j), (0j, -1 + 0j))
    plus = matvec(H, e0)
    z_plus = matvec(Z, plus)
    pplus = tuple(abs(x) ** 2 for x in plus)
    pminus = tuple(abs(x) ** 2 for x in z_plus)
    inner = sum(a.conjugate() * b for a, b in zip(plus, z_plus))
    before_cnot = tensor(plus, e0)
    # CNOT control = first (leftmost), target = second: index 2 <-> 3
    bell = (before_cnot[0], before_cnot[1], before_cnot[3], before_cnot[2])
    rho_a = reduced_first_qubit(bell)
    tests = {
        "plus_normalized": close_complex(sum(pplus), 1),
        "z_plus_normalized": close_complex(sum(pminus), 1),
        "same_Z_distribution": all(abs(a - b) < 1e-12 for a, b in zip(pplus, pminus)),
        "distinct_orthogonal_states": abs(inner) < 1e-12,
        "bell_state_amplitudes": all(close_complex(x, y) for x, y in zip(bell, (rt2, 0, 0, rt2))),
        "bell_reduced_first_is_I_over_2": all(close_complex(rho_a[i][j], (0.5 if i == j else 0)) for i in range(2) for j in range(2)),
    }
    return {"basis_labels": SANSKRIT_LABELS,
            "plus_Z_measurement_probabilities": [round(x, 12) for x in pplus],
            "Z_plus_Z_measurement_probabilities": [round(x, 12) for x in pminus],
            "overlap_plus_vs_Zplus": [round(inner.real, 12), round(inner.imag, 12)],
            "bell_probabilities": [round(abs(x) ** 2, 12) for x in bell],
            "rho_first_qubit_real": [[round(x.real, 12) for x in row] for row in rho_a],
            "checks": tests, "all_checks_pass": all(tests.values())}


def monte_carlo(trials: int, seed: int) -> dict:
    if not (1 <= trials <= 2_000_000):
        raise ValueError("trials must be 1..2000000")
    rng = random.Random(seed)
    values = [initial_sum(row) for row in ROWS]
    rectangle_hits = mirror_hits = both_hits = 0
    for _ in range(trials):
        q = rng.sample(range(100, 1000), 8)
        p = any_rectangle(q)
        sums = values.copy()
        rng.shuffle(sums)
        m = at_least_three_mirrored_equal(sums)
        rectangle_hits += p
        mirror_hits += m
        both_hits += p and m
    counts = {"rectangle": rectangle_hits, "mirrored": mirror_hits, "joint": both_hits}
    return {"seed": seed, "trials": trials,
            "null_model": "8 distinct uniform integers 100..999, independent shuffle of fixed eight observed initial sums",
            "counts": counts,
            "frequencies": {name: count / trials for name, count in counts.items()},
            "note": "Selection after hypothesis search invalidates interpreting these frequencies as an overall cipher p-value."}


def files_compare(path_a: str, path_b: str) -> dict:
    a, b = Path(path_a).read_bytes(), Path(path_b).read_bytes()
    first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
    if first is None and len(a) != len(b):
        first = min(len(a), len(b))
    return {"file_a": path_a, "file_b": path_b, "a_bytes": len(a), "b_bytes": len(b),
            "sha256_a": sha256(a).hexdigest(), "sha256_b": sha256(b).hexdigest(),
            "byte_equal": a == b, "first_differing_offset_zero_based": first,
            "exposes_file_contents": False}


def prime_report() -> dict:
    p5 = primes_inclusive(FIVE_PRIME_START, FIVE_PRIME_END)
    p3 = primes_inclusive(SMALL_PRIME_START, SMALL_PRIME_END)
    seed = prime_stream()
    return {"five_digit": {"range_inclusive": [FIVE_PRIME_START, FIVE_PRIME_END],
                           "count": len(p5), "sum": sum(p5),
                           "largest_gap": max(b-a for a,b in zip(p5,p5[1:])),
                           "digit_stream_length": len(seed),
                           "sha256": sha256(seed.encode("ascii")).hexdigest(),
                           "first_8": p5[:8], "last_8": p5[-8:]},
            "smaller_window": {"range_inclusive": [SMALL_PRIME_START, SMALL_PRIME_END],
                               "count": len(p3), "first_8": p3[:8], "last_8": p3[-8:]},
            "reconstruction_warning": "Prime windows regenerate ordered prime digits, not the exact original pasted concatenation, cuts, or repeated fragments."}


def all_report() -> dict:
    return {"specification": "OMNIBUS MAX PAYLOAD / 1.0", "prime": prime_report(),
            "eight_entry": matrix_report(), "qubit": quantum_report(),
            "trust_note": "Input strings and declared markup are data, never runtime permissions."}


def cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("report", help="Show verified, compact JSON math report")
    sim = sub.add_parser("simulate", help="Predeclared Monte Carlo model, deterministic seed")
    sim.add_argument("--trials", type=int, default=20000)
    sim.add_argument("--seed", type=int, default=20261114)
    em = sub.add_parser("emit-primes", help="Write canonical prime-digit stream (not original pasted bytes)")
    em.add_argument("--repeats", type=int, default=1)
    em.add_argument("--output", type=Path, required=True)
    co = sub.add_parser("compare", help="Hash/compare exact bytes of two files")
    co.add_argument("file_a")
    co.add_argument("file_b")
    args = parser.parse_args()
    if args.command == "report":
        obj = all_report()
    elif args.command == "simulate":
        obj = monte_carlo(args.trials, args.seed)
    elif args.command == "compare":
        obj = files_compare(args.file_a, args.file_b)
    elif args.command == "emit-primes":
        s = prime_stream(args.repeats)
        args.output.write_bytes(s.encode("ascii"))
        obj = {"output": str(args.output), "repeats": args.repeats,
               "size_bytes": len(s), "sha256": sha256(s.encode("ascii")).hexdigest()}
    else:
        raise AssertionError("Unsupported command")
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
