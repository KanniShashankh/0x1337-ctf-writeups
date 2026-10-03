#!/usr/bin/env python3
"""Arthur's redstone contraption: recover the seed of the 16-bit redstone LFSR.

Machine (from the map): 16 cells stacked at y = 67, 69, ..., 97. Bits shift down
one cell per press of the "shift" note block, and the top cell loads
c0 ^ c3 ^ c4 ^ c6. output.txt is the bottom-cell stream after sans pressed the
note block 2^6 = 64 times.
"""
import sys

TAPS = (0, 3, 4, 6)
WAIT = 2 ** 6


def berlekamp_massey(s):
    n = len(s)
    c, b = [1] + [0] * n, [1] + [0] * n
    l, m = 0, 1
    for i in range(n):
        d = s[i]
        for j in range(1, l + 1):
            d ^= c[j] & s[i - j]
        if d == 0:
            m += 1
            continue
        t = c[:]
        for j in range(n - m + 1):
            c[j + m] ^= b[j]
        if 2 * l <= i:
            l, b, m = i + 1 - l, t, 1
        else:
            m += 1
    return l, c[: l + 1]


def step(st):
    fb = 0
    for t in TAPS:
        fb ^= st[t]
    return st[1:] + [fb]


def unstep(st):
    # previous c0 = new c15 ^ (old c3, c4, c6, which are now c2, c3, c5)
    return [st[15] ^ st[2] ^ st[3] ^ st[5]] + st[:15]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "files/output.txt"
    out = [int(ch) for ch in open(path).read().strip()]

    # Cross-check: BM recovers the same taps as the wiring.
    l, poly = berlekamp_massey(out)
    print("BM linear complexity", l, "connection poly", poly)

    # The first 16 recorded bits are cells 0..15 at the moment recording began.
    st = out[:16]
    for _ in range(WAIT):
        st = unstep(st)
    seed = st

    # Verify: seed -> 64 presses -> 32 recorded bits == output.txt
    x = seed[:]
    for _ in range(WAIT):
        x = step(x)
    rec = []
    for _ in range(len(out)):
        rec.append(x[0])
        x = step(x)
    assert rec == out, "forward replay does not match output.txt"

    value = sum(bit << i for i, bit in enumerate(seed))  # cell 0 (bottom) = LSB
    print("0x1337{%04x}" % value)


if __name__ == "__main__":
    main()
