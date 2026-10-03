#!/usr/bin/env python3
"""
Solver for "but nobody came" (0x1337 CTF).

Run with a Python that has the `cryptography` package:
    /opt/homebrew/bin/python3.13 solve.py

The challenge is a 3-party Burmester-Desmedt group key agreement whose whole
transcript is frozen (the secrets a, b, c, S, r and even the IVs are reused on
every connection). After the intercept the service exposes Papyrus and Undyne
as raw exponentiation oracles with their *reused* secret exponents:

    Papyrus(base) -> base^b mod P     (P fixed to sans's original prime)
    Undyne(base,p') -> base^c mod p'  (any prime p', but size-capped)

That lets us compute the three Diffie-Hellman cross terms directly:
    g^ab = Papyrus(A)        g^bc = Papyrus(C)
    g^ac = A^c mod P   (needs the full integer c)

Undyne rejects the big prime P, so we recover the full 1536-bit c by querying
g^c mod many smooth (safe) primes and combining with Pohlig-Hellman + CRT.

Then:
    key_AB = sha256("AB share" + g^ab) -> decrypt share_B = S + 2r
    key_AC = sha256("AC share" + g^ac) -> decrypt share_C = S + 3r
    S  = 3*share_B - 2*share_C  (mod P)
    G  = g^(ab+bc+ca) = g^ab * g^bc * g^ac
    flag_key = sha256(b"flag" + S + G)   # note: S before G
"""
import socket, time, json, random, math
from hashlib import sha256
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

HOST, PORT = "40.81.242.56", 30482
P = int(
    "fdd7e712e3a5b761a0ca4837de0ad68a4b8c70d66220610fe6fca2ca599096919d1d931"
    "11a2d467ed2771670bd90d107ee46a521a48e10423c36d8943c83784cb79b6909b98ea6b"
    "b42cd1d0604a2fa90de5cb9158346b25dfaa2ebd6a33adb807194accb9afbef4c85725df"
    "0f24efa8b357fa3183f0def238b7daf159781664a29a7d3163c3e4c06f3076cf3b8e6ca4"
    "298ec85dc1fee1a641ef164fd7e82053a056cf41ee65195b602508bc44b729ffadae0b88"
    "ec097683747fbfc3e994d3b71", 16)
SIZE = (P.bit_length() + 7) // 8  # 192


def aes_cbc_dec(key, iv, ct):
    d = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    return d.update(ct) + d.finalize()


def recv_all(s, t=3):
    s.settimeout(t)
    buf = b""
    try:
        while True:
            chunk = s.recv(16384)
            if not chunk:
                break
            buf += chunk
    except socket.timeout:
        pass
    return buf.decode(errors="replace")


def parse_objs(text):
    objs, i = [], 0
    while True:
        a = text.find("{", i)
        if a < 0:
            break
        b = text.find("}", a)
        if b < 0:
            break
        try:
            objs.append(json.loads(text[a:b + 1]))
        except json.JSONDecodeError:
            pass
        i = b + 1
    return objs


# --- one connection: grab the frozen transcript + the two oracle slots ---------
def grab_transcript_and_papyrus(base):
    """Open a connection, return (intercept objects, Papyrus(base))."""
    s = socket.socket()
    s.connect((HOST, PORT))
    time.sleep(1.2)
    buf = recv_all(s, 3)
    s.sendall(json.dumps({"p": hex(P), "g": hex(base), "A": "0x2"}).encode() + b"\n")
    r = recv_all(s, 3)
    s.close()
    val = int(json.loads(r[r.index("{"):r.rindex("}") + 1])["B"], 16)
    return parse_objs(buf), val


def undyne(base, prime):
    """Undyne computes (our g)^c mod (our prime); Papyrus slot filled with a dummy."""
    s = socket.socket()
    s.connect((HOST, PORT))
    time.sleep(1.1)
    recv_all(s, 2)
    s.sendall(json.dumps({"p": hex(P), "g": "0x2", "A": "0x2"}).encode() + b"\n")
    recv_all(s, 2)
    s.sendall(json.dumps({"p": hex(prime), "g": hex(base), "A": "0x2"}).encode() + b"\n")
    r = recv_all(s, 3)
    s.close()
    return int(json.loads(r[r.index("{"):r.rindex("}") + 1])["B"], 16)


# --- number theory helpers -----------------------------------------------------
def is_prime(n):
    if n < 2:
        return False
    for q in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % q == 0:
            return n == q
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def bsgs(g, h, order, mod):
    """Solve g^x = h in a cyclic group of the given order."""
    m = math.isqrt(order) + 1
    table, e = {}, 1
    for j in range(m):
        table.setdefault(e, j)
        e = e * g % mod
    g_inv_m = pow(pow(g, m, mod), order - 1, mod)  # g^{-m}
    gamma = h
    for i in range(m + 1):
        if gamma in table:
            return i * m + table[gamma]
        gamma = gamma * g_inv_m % mod
    return None


def gen_safe_prime(bits):
    while True:
        r = random.getrandbits(bits) | 1 | (1 << (bits - 1))
        if is_prime(r) and is_prime(2 * r + 1):
            return 2 * r + 1, r


def recover_c(C_target):
    """Recover the full integer c with 2^c == C_target (mod P)."""
    random.seed(12345)
    M, x, used = 1, 0, set()
    while M.bit_length() <= 1600:
        p, r = gen_safe_prime(34)
        if r in used:
            continue
        used.add(r)
        try:
            h = undyne(2, p)            # h = 2^c mod p
        except Exception:
            continue
        gg, hh = pow(2, 2, p), pow(h, 2, p)   # work in the order-r subgroup
        xr = bsgs(gg, hh, r, p)               # xr = c mod r
        if xr is None or math.gcd(M, r) != 1:
            continue
        x = (x + M * (((xr - x) % r) * pow(M % r, -1, r) % r)) % (M * r)
        M *= r
        if pow(2, x, P) == C_target:
            return x
    raise RuntimeError("c not recovered")


def unpad(pt):
    p = pt[-1]
    assert 1 <= p <= 16 and pt[-p:] == bytes([p]) * p, "bad padding"
    return pt[:-p]


def main():
    # 1. frozen transcript + g^ab = Papyrus(A)
    objs, _ = grab_transcript_and_papyrus(2)
    def find(k):
        for o in objs:
            if k in o:
                return o[k]
    A = int(find("A"), 16)
    C = int(find("C"), 16)
    blobs = [o for o in objs if set(o) == {"iv", "encrypted"}]
    encB, encC, encF = blobs  # sans->Papyrus, sans->Undyne, flag

    _, gab = grab_transcript_and_papyrus(A)   # A^b = g^ab
    _, gbc = grab_transcript_and_papyrus(C)   # C^b = g^bc

    # 2. full c, then g^ac = A^c mod P
    c = recover_c(C)
    gac = pow(A, c, P)
    print(f"[+] c recovered ({c.bit_length()} bits), 2^c == C: {pow(2, c, P) == C}")

    # sanity: cross terms must reproduce the public X values
    inv = lambda v: pow(v, -1, P)
    XA, XB, XC = (int(find(k), 16) for k in ("X_A", "X_B", "X_C"))
    assert XB == gbc * inv(gab) % P
    assert XC == gac * inv(gbc) % P
    assert XA == gab * inv(gac) % P
    print("[+] g^ab, g^bc, g^ac verified against public X values")

    # 3. shares -> S, and the group key G
    key_AB = sha256(b"AB share" + gab.to_bytes(SIZE, "big")).digest()[:16]
    key_AC = sha256(b"AC share" + gac.to_bytes(SIZE, "big")).digest()[:16]
    share_B = int.from_bytes(
        unpad(aes_cbc_dec(key_AB, bytes.fromhex(encB["iv"]), bytes.fromhex(encB["encrypted"]))), "big")
    share_C = int.from_bytes(
        unpad(aes_cbc_dec(key_AC, bytes.fromhex(encC["iv"]), bytes.fromhex(encC["encrypted"]))), "big")
    S = (3 * share_B - 2 * share_C) % P
    G = gab * gbc % P * gac % P

    # 4. flag  (service derives flag_key as sha256(b"flag" + S + G) -- S before G)
    flag_key = sha256(b"flag" + S.to_bytes(SIZE, "big") + G.to_bytes(SIZE, "big")).digest()[:16]
    flag = unpad(aes_cbc_dec(flag_key, bytes.fromhex(encF["iv"]), bytes.fromhex(encF["encrypted"])))
    print("[+] FLAG:", flag.decode())


if __name__ == "__main__":
    main()
