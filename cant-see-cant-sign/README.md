# Can't See? Can't Sign?

- **Category:** Crypto (RSA blind signature)
- **Flag:** `0x1337{n0nc3s_sh4nt_b3_r3us3d}`
- **Service:** `nc 40.81.242.56 30419` (mirrors on `30206`, `30274`)
- **Author:** anangappara
- **Files:** [`files/main.py`](files/main.py) (challenge source), [`files/solve.py`](files/solve.py) (solver)

## Challenge

> Can you see stuff that is not meant to be seen? Should you? Could you? Would you?

The server is a blind-signature oracle. You choose the modulus `N`, it signs each
character of the flag under an RSA blind-signature scheme, and verifies each signature
before moving on.

```python
r = random.getrandbits(512)

N = int(input("Enter N: "))          # client chooses N
if N.bit_length() < 512:             # only constraint: >= 512 bits
    exit(0)

def blind(m, N, e, r):
    return (m * pow(r, e, N)) % N

def verify(m, N, sb, e, r):
    s = (sb * pow(r, -1, N)) % N
    return pow(s, e, N) == m

for c in FLAG:
    m = ord(c)
    blinded = blind(m, N, 65537, r)
    print("Please sign this:", blinded)
    sb = int(input("Enter signature: "))
    if not verify(m, N, sb, 65537, r):
        exit(0)                       # one wrong signature -> dead
```

For each character the server:

1. Picks the flag char `m = ord(c)`.
2. Sends you `blinded = m · r^e mod N` (the blinding nonce `r` is **fixed for the whole
   session**, same `r` for every char).
3. Expects a signature `sb` such that `(sb · r^-1)^e ≡ m (mod N)`.

## The two bugs

### 1. The client controls `N`

The server never checks that `N` is a real RSA modulus — only that it is at least 512
bits. If we send a **prime** `p`, then `λ(p) = p − 1` is something we know, so we can
compute the private exponent ourselves:

```python
d = pow(e, -1, p - 1)
```

Now we can produce a valid signature for anything the oracle asks:

- It sends `blinded = m · r^e`.
- We reply `sb = blinded^d = (m · r^e)^d = m^d · r (mod p)`.
- Verify computes `s = sb · r^-1 = m^d`, and `s^e = m`. ✓

So we pass every `verify` without ever knowing `r`. (We must pick `p` with
`gcd(e, p−1) = 1` so `d` exists.)

### 2. The nonce `r` is reused — this leaks the flag

`r` is generated once and reused for every character. That means the blinded values the
server prints are:

```
b_i = m_i · r^e (mod p)
```

with the **same** unknown factor `r^e` across all `i`. Divide any two and `r^e` cancels:

```
b_i / b_j = m_i / m_j (mod p)
```

Flags here start with `0x1337{...}`, so the first character is known to be `'0'`
(`m_0 = ord('0') = 48`). That pins the shared factor:

```
r^e ≡ b_0 / ord('0')   (mod p)
```

and every character falls out:

```
m_i ≡ b_i · (r^e)^-1   (mod p)   ->   chr(m_i)
```

This is exactly the "nonce reuse" the flag warns about. We never needed to see `r`
("can't see"), and the signing bug is just there to keep the oracle alive long enough
to print all the blinded values.

## Solver

[`solve.py`](files/solve.py):

1. Generates a 520-bit prime `p` with `gcd(e, p−1) = 1`, computes `d`.
2. Connects, sends `p` as `N`.
3. For each `Please sign this: b_i`, records `b_i` and replies `b_i^d mod p`.
4. After the session ends, computes `r^e = b_0 · ord('0')^-1 mod p` and recovers every
   char as `chr(b_i · (r^e)^-1 mod p)`.

```
$ python3 solve.py 30419
0x1337{n0nc3s_sh4nt_b3_r3us3d}
```

Uses only the stdlib (Miller–Rabin for the prime, raw sockets), no PyCryptodome / pwntools.

## Flag

```
0x1337{n0nc3s_sh4nt_b3_r3us3d}
```

## Takeaways

- Never let the client choose the modulus in a signature scheme — a prime `N` hands the
  private key to the attacker.
- The real lesson (and the flag): a blinding nonce must be fresh per message. Reusing
  `r` makes every blinded value share a constant factor, so ratios of ciphertexts leak
  the plaintext the moment one plaintext is known (here, the `0x1337{` prefix).
