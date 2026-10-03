#!/usr/bin/env python3
"""Solve the RSA challenge where the given 'p' is composite and e = 2^16.

Chain: spot the composite -> FactorDB gives f1 * f2 -> f2 is a Fermat-easy
close-prime pair -> solve x^(2^16) = c mod each prime by torsion enumeration,
picking the candidate that is far smaller than the modulus (the true message).
"""
import json, math, random, re, urllib.request
from pathlib import Path

vals = {}
for line in (Path(__file__).parent / "files/challenge_values.txt").read_text().splitlines():
    m = re.match(r"(\w+)\s*=\s*(\d+)", line)
    if m:
        vals[m.group(1)] = int(m.group(2))
n, e, c = vals["p"], vals["e"], vals["c"]

def v2(x): return (x & -x).bit_length() - 1

def is_probable_prime(n, rounds=12):
    if n < 2: return False
    for sp in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % sp == 0: return n == sp
    d, r = n - 1, 0
    while d % 2 == 0: d //= 2; r += 1
    for _ in range(rounds):
        x = pow(random.randrange(2, n - 1), d, n)
        if x in (1, n - 1): continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1: break
        else: return False
    return True

def factor_db(n):
    url = "http://factordb.com/api?query=" + str(n)
    d = json.load(urllib.request.urlopen(url, timeout=20))
    return [(int(f), k) for f, k in d["factors"]], d["status"]

def fermat(n, steps=2_000_000):
    a = math.isqrt(n)
    if a * a < n: a += 1
    for i in range(steps):
        b2 = a * a - n
        b = math.isqrt(b2)
        if b * b == b2:
            return a - b, a + b, i
        a += 1
    return None

# --- 1. the given 'p' is not prime -----------------------------------------
print(f"n = p: {n.bit_length()} bits, prime? {is_probable_prime(n)}  (it is composite)")

# --- 2. FactorDB knows the split: n = f1 * f2 -------------------------------
factors, status = factor_db(n)
f1 = factors[0][0]
f2 = factors[1][0]
assert f1 * f2 == n
print(f"FactorDB ({status}): f1 ({f1.bit_length()}b, prime={is_probable_prime(f1)}) * "
      f"f2 ({f2.bit_length()}b, prime={is_probable_prime(f2)})")

# --- 3. f2 is a close-prime composite: Fermat splits it instantly -----------
if not is_probable_prime(f2):
    g1, g2, steps = fermat(f2)
    print(f"Fermat on f2: split at step {steps} (gap {g2 - g1} ~ 2^{v2(g2 - g1)})")
    primes = [f1, g1, g2]
else:
    primes = [f1, f2]
print("primes:", [(p.bit_length(), v2(p - 1)) for p in primes])

# --- 4. x^(2^16) = c mod P per prime, torsion enumeration -------------------
candidates = []
for P in primes:
    N = P - 1
    v, w = v2(N), N >> v2(N)              # w = odd part
    d = pow(e, -1, w)                     # e is invertible mod the odd part
    base = pow(c, d, P)                   # base = m * (m^w)^u  -> m up to a 2^j-torsion factor
    j = min(v, 16)
    zeta = None
    while zeta is None:                   # generator of the 2^j torsion
        z = pow(random.randrange(2, P), w, P)
        if pow(z, 1 << (j - 1), P) != 1:
            zeta = z
    zk, small = 1, []
    for _ in range(1 << j):
        cand = base * zk % P
        if cand.bit_length() < 900:       # the flag is way smaller than P
            small.append(cand)
        zk = zk * zeta % P
    print(f"P {P.bit_length()}b: {len(small)} small candidate(s)")
    candidates.append(small)

# --- 5. the same m falls out of every prime ---------------------------------
m = set(candidates[0]).intersection(*candidates[1:]).pop()
flag = m.to_bytes((m.bit_length() + 7) // 8, "big")
print("flag:", flag.decode())
assert pow(m, e, n) == c, "verification failed"
print("verified: m^e mod n == c")
