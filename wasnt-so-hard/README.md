# Wasn't So Hard

- **Category:** Crypto (RSA, composite modulus, e = 2^16)
- **Flag:** `0x1337{w4snt_s0_h4rd_r1ght_b0ttyb0y4}`
- **Files:** [`files/challenge_values.txt`](files/challenge_values.txt) (the given `p`, `e`, `c`), [`solve.py`](solve.py)

## Challenge

> [p = a 2999-bit decimal value] e = 65536 c = [a 2999-bit decimal value] — find flag fast.

No source, no service: just an RSA-looking triple `(p, e, c)` where the flag is the
plaintext `m` with `c = m^e mod p`.

## Solution

1. **Trust nothing: test `p` for primality.** Miller-Rabin says composite — "p" is
   really the modulus `n`. Trial division finds nothing below 200k and plain Fermat
   on the full 2999-bit modulus finds nothing in 2M steps, so the factors are not
   trivially close and not small.
2. **Ask FactorDB.** Status `CF`: `n = f1 * f2` with
   `f1` = 1000-bit (prime, and `f1-1` divisible by 2^16 — a tell that `e = 2^16`
   is deliberate) and `f2` = 2000-bit composite (status `C`, no known factors).
3. **Split `f2` with Fermat.** Its two 1000-bit factors `g1`, `g2` differ by only
   318, so `a^2 - n` is a perfect square on the very first try. Now
   `n = f1 * g1 * g2`, three ~1000-bit primes with `v2(P-1)` = 16, 1, 2.
4. **`e = 2^16` is not invertible mod phi.** Instead solve `x^(2^16) = c` per prime.
   With `w` the odd part of `P-1`, `d = 2^(-16) mod w` and `base = c^d mod P`
   satisfy `base = m * (m^w)^u`, i.e. `m` equals `base` times some
   `2^min(v2,16)`-torsion element. Enumerate `base * zeta^k` over that torsion
   (65536 candidates for `f1`, 2 and 4 for `g1`/`g2`).
5. **Small-candidate filter.** The plaintext is a 37-byte flag, far smaller than
   each 1000-bit prime, so the true root shows up as the *only* candidate below
   2^900 — and the same value falls out of all three primes independently:
   `m = 0x1337{w4snt_s0_h4rd_r1ght_b0ttyb0y4}` as an integer.
6. **Verify:** `m^65536 mod n == c`.

```
$ python3 solve.py
n = p: 2999 bits, prime? False  (it is composite)
FactorDB (CF): f1 (1000b, prime=True) * f2 (2000b, prime=False)
Fermat on f2: split at step 0 (gap 318 ~ 2^1)
primes: [(1000, 16), (1000, 1), (1000, 2)]
P 1000b: 1 small candidate(s)
P 1000b: 1 small candidate(s)
P 1000b: 1 small candidate(s)
flag: 0x1337{w4snt_s0_h4rd_r1ght_b0ttyb0y4}
verified: m^e mod n == c
```

## Lessons

- Always Miller-Rabin the "p" in a p/e/c triple. A composite masquerading as the
  prime changes the entire solve.
- FactorDB is the first stop for any pasted modulus; public CTF moduli are often
  already factored. It split `n` but not `f2` — the close-prime pair was left for
  Fermat, which caught it at step 0 because `g2 - g1` = 318.
- When `e = 2^k` shares factors with `phi`, solve the e-th root per prime: invert
  `e` mod the *odd part* of `p-1`, then clear the residual torsion by enumeration.
- The plaintext being much smaller than the primes turns "which of 2^16 roots?" into
  a one-line filter, and the same root dropping out of every prime is the check.

*(Folder name from the flag; the original challenge title was not captured.)*
