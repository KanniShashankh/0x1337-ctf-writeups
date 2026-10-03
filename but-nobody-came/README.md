# but nobody came

- **Category:** Crypto
- **Flag:** `0x1337{f1n3_y0u_c4n_c0m3}`
- **Files:** [`files/but_nobody_came.zip`](files/but_nobody_came.zip) (contains `chall.py`), [`files/solve.py`](files/solve.py)
- **Service:** `nc 40.81.242.56 30482` (also `30194`, `30678`)

## Challenge

> sans, Papyrus, and Undyne are having a party. You are not invited. They designed a fancy three-person cryptographic protocol so the invitation could only be read by the three of them. Unfortunately, Papyrus and Undyne wanted to make absolutely sure you knew you weren't invited. They seem pretty confident in their setup. In fact, they've been using it for a while now. Why change something that already works?

`chall.py` is a three-party **Burmester-Desmedt (BD)** group key agreement. With
exponents `a, b, c` and public values `A = g^a`, `B = g^b`, `C = g^c`:

```
X_A = (B/C)^a   X_B = (C/A)^b   X_C = (A/B)^c
G   = A^(3b) * X_B^2 * X_C        # the BD group key
```

A quick expansion shows `G = g^(ab + bc + ca)`.

An additive secret `S` is split into shares `S+r`, `S+2r`, `S+3r`. The B-share is
sent to Papyrus encrypted under `key_AB = sha256("AB share" + g^ab)`, the C-share
to Undyne under `key_AC = sha256("AC share" + g^ac)`, and the flag under
`flag_key = sha256("flag" + G + S)` (AES-CBC throughout).

Connecting to the service dumps the whole transcript (`p, g, A, B, C`, the `X`
values, both encrypted shares and the encrypted flag), then hands you two
interactive sessions: *"Papyrus connects to you, send him some parameters"* and
the same for Undyne.

## Key observations

1. **Everything is frozen.** Reconnecting gives byte-for-byte identical `A, B, C`,
   `X_*`, both encrypted shares, the encrypted flag, *and the IVs*. So `a, b, c, S,
   r` are long-term reused — the literal meaning of *"why change something that
   already works?"*. We can mix values from different connections freely.

2. **Papyrus is a `base^b` oracle.** Papyrus only accepts sans's original prime
   `P`, but it echoes back `(our g)^b mod P` for **any base we choose** (confirmed
   by feeding a small-order element and reading the result). So `g^ab = Papyrus(A)`
   and `g^bc = Papyrus(C)` fall out immediately — no discrete log needed.

3. **Undyne is a `base^c` oracle with a chooseable prime.** Undyne lets us pick the
   prime `p'` (it rejects the big `P` with *"prime is too big, try smaller"*) and
   returns `(our g)^c mod p'`. That is a static-DH oracle keyed on the reused
   secret `c`.

4. The per-session `encrypted` blob each oracle returns is a decoy — it is freshly
   randomised every call, so it carries no usable information. The leak is purely
   the public `base^exp` value.

## Solution

We need `G` and `S`, both of which reduce to the three DH cross terms
`g^ab`, `g^bc`, `g^ac`.

1. **`g^ab` and `g^bc`** come straight from Papyrus: `Papyrus(A) = A^b = g^ab`,
   `Papyrus(C) = C^b = g^bc`.

2. **`g^ac` needs the full integer `c`.** Papyrus can't raise to `c`, and Undyne
   can't work mod the big `P`, so we recover `c` outright. Query Undyne for
   `2^c mod p'` across many 34-bit **safe primes** `p' = 2r + 1`, solve each with
   Pohlig-Hellman / BSGS inside the order-`r` subgroup to get `c mod r`, and CRT
   the residues together until `2^c == C (mod P)`. `c` is a full 1536-bit secret;
   about 50 primes suffice. Then `g^ac = A^c mod P`.

3. **Sanity check.** The three recovered terms must satisfy the public relations
   `X_B = g^bc / g^ab`, `X_C = g^ac / g^bc`, `X_A = g^ab / g^ac`. They do.

4. **Shares and `S`.** With the DH terms we rebuild both share keys, decrypt the
   intercepted shares to `share_B = S + 2r` and `share_C = S + 3r`, and solve
   `S = 3*share_B - 2*share_C (mod P)`.

5. **Group key and flag.** `G = g^ab * g^bc * g^ac`. The one twist: the live
   service derives the flag key as `sha256(b"flag" + S + G)` — **`S` before `G`**,
   the opposite order from the handout `chall.py`. With that fixed, AES-CBC
   decrypts the flag:

```
0x1337{f1n3_y0u_c4n_c0m3}
```

See [`files/solve.py`](files/solve.py) for the full automated exploit.

## Lessons

- A protocol that reuses long-term secrets turns any "respond to my parameters"
  endpoint into an oracle. Here the two endpoints were effectively
  `base |-> base^b` and `base |-> base^c` — enough to compute every CDH term the
  scheme relied on staying secret.
- Small-subgroup confinement against the *fixed* prime `P` only buys the ~47-bit
  smooth part of `P-1`. The real lever was Undyne letting us *choose* the prime,
  so we could recover the full exponent via many smooth-prime discrete logs + CRT.
- When a decrypt yields valid PKCS#7 padding but "garbage", the key pieces are
  usually right and the derivation is slightly off — here just the order of the two
  hash inputs. Don't throw away verified intermediate values.
- Env note: `pycrypto 2.6.1` is broken on Python 3.13 (`Key cannot be the null
  string`); use the `cryptography` package instead.
